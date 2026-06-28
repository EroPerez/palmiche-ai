"""Background wake-word listener.

Continuously listens via the microphone and calls a callback when the
configured wake word is heard. Audio playback is delegated to AudioEngine.

Requires: pip install SpeechRecognition pyaudio
"""
import ctypes
import logging
import os
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ALSA error suppression — module-level reference prevents garbage collection.
# ---------------------------------------------------------------------------
_ALSA_HANDLER_TYPE = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
)


def _alsa_noop(filename, line, function, err, fmt):
    pass


_ALSA_NOOP_HANDLER = _ALSA_HANDLER_TYPE(_alsa_noop)


def _suppress_alsa_errors() -> None:
    """Install a no-op ALSA error handler to silence PyAudio device-probe spam."""
    try:
        ctypes.cdll.LoadLibrary("libasound.so.2").snd_lib_error_set_handler(
            _ALSA_NOOP_HANDLER
        )
    except OSError:
        pass


def _audio_device_available() -> bool:
    """Return True if at least one input audio device is available."""
    try:
        import sounddevice as sd
        devs = sd.query_devices()
        for d in (devs if isinstance(devs, list) else [devs]):
            if d.get("max_input_channels", 0) > 0:
                return True
        return False
    except Exception:
        pass

    try:
        cards = os.path.exists("/proc/asound/cards")
        if not cards:
            return False
        with open("/proc/asound/cards") as f:
            return bool(f.read().strip())
    except Exception:
        pass

    try:
        import subprocess
        result = subprocess.run(
            ["arecord", "-l"], capture_output=True, text=True, timeout=5,
        )
        return "card" in result.stdout.lower()
    except Exception:
        pass

    return True


def _open_microphone_quietly(mic):
    """Enter the Microphone context while redirecting fd 2 to suppress JACK messages."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved = os.dup(2)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        source = mic.__enter__()
    finally:
        os.dup2(saved, 2)
        os.close(saved)
    return source

from ..config import JARVIS_TOOL_LANG

_SPEECH_LANG_MAP: dict[str, str] = {
    "es": "es-ES",
    "en": "en-US",
}

def _get_lang(code: str, default: str = "es-ES") -> str:
    """Map a short language code ('en', 'es') to a BCP-47 speech locale."""
    return _SPEECH_LANG_MAP.get(code, default)

class WakeWordListener:
    """Daemon thread that listens for a wake word and fires a callback.

    Usage:
        listener = WakeWordListener("palmiche", on_wake=my_callback,
                                    on_command=my_command_callback)
        started  = listener.start()   # False if deps missing
        ...
        listener.stop()
    """

    def __init__(
        self,
        wake_word: str = "palmiche",
        on_wake: Optional[Callable] = None,
        on_command: Optional[Callable[[str], None]] = None,
        language: str = JARVIS_TOOL_LANG,
        response_text: str = "Kewelta Compay",
        welcome_audio: str = "",
    ):
        self.wake_word = wake_word.lower()
        self.on_wake = on_wake
        self.on_command = on_command
        self.language = language
        self.response_text = response_text
        self.welcome_audio = welcome_audio
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None

    # ----------------------------------------------------------------- public

    def start(self) -> bool:
        """Start listening. Returns False (and logs) if deps are not installed."""
        try:
            import speech_recognition as sr  # noqa: F401
        except ImportError as exc:
            logger.warning(
                "Wake word desactivado — instala: pip install SpeechRecognition pyaudio "
                "(%s)", exc
            )
            return False

        _suppress_alsa_errors()

        if not _audio_device_available():
            logger.warning(
                "Wake word desactivado — no se encontró dispositivo de audio de entrada"
            )
            return False

        self._running = True
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="jarvis-wake-word"
        )
        self._thread.start()
        logger.info("Wake word listener iniciado (palabra: '%s')", self.wake_word)
        return True

    def stop(self):
        """Signal the listener thread to exit on its next iteration."""
        self._running = False

    # ------------------------------------------------------------------ loop

    def _loop(self):
        """Continuously listen for audio and fire on_wake when the wake word is heard."""
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.5

        try:
            mic = sr.Microphone()
        except OSError as exc:
            logger.warning("No se pudo abrir el micrófono: %s", exc)
            return

        try:
            source = _open_microphone_quietly(mic)
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
            finally:
                mic.__exit__(None, None, None)
        except Exception as exc:
            logger.debug("Calibración de ruido ambiental fallida: %s", exc)

        while self._running:
            if self._paused:
                _sleep(0.1)
                continue

            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=4, phrase_time_limit=3)

                try:
                    text = recognizer.recognize_google(
                        audio, language=_get_lang(self.language)
                    ).lower()
                    logger.debug("Escuchado: %s", text)
                    if self.wake_word in text:
                        logger.info("¡Wake word detectada! '%s'", self.wake_word)
                        from .audio_engine import get_engine
                        engine = get_engine(lang=self.language)
                        if self.welcome_audio and os.path.isfile(self.welcome_audio):
                            engine.play_file(self.welcome_audio)
                        elif self.response_text:
                            engine.speak(self.response_text)
                        if self.on_wake:
                            self.on_wake()
                        if self.on_command:
                            _sleep(1.5)
                            self._paused = True
                            try:
                                self._listen_for_command(recognizer, mic)
                            finally:
                                self._paused = False

                except sr.UnknownValueError:
                    pass
                except sr.RequestError as exc:
                    logger.warning("Error de reconocimiento de voz: %s", exc)
                    _sleep(10)

            except sr.WaitTimeoutError:
                pass
            except OSError:
                _sleep(2)
            except Exception as exc:
                logger.debug("Wake word loop: %s", exc)
                _sleep(1)

    def _listen_for_command(self, recognizer, mic) -> None:
        """Listen for one follow-up voice command and fire on_command with the transcript."""
        import speech_recognition as sr
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            try:
                text = recognizer.recognize_google(audio, language=_get_lang(self.language))
                logger.info("Comando de voz: %s", text)
                if self.on_command:
                    self.on_command(text)
            except sr.UnknownValueError:
                logger.debug("Comando de voz no entendido")
            except sr.RequestError as exc:
                logger.warning("Error de reconocimiento: %s", exc)
        except sr.WaitTimeoutError:
            logger.debug("Tiempo de espera agotado para comando de voz")
        except Exception as exc:
            logger.debug("Error escuchando comando: %s", exc)

    def listen_once(self, callback: "Callable[[Optional[str]], None]") -> None:
        """Listen for one phrase and call callback(text_or_None) from a daemon thread."""
        import speech_recognition as sr

        def _run():
            self._paused = True
            try:
                recognizer = sr.Recognizer()
                recognizer.energy_threshold = 300
                recognizer.dynamic_energy_threshold = True
                recognizer.pause_threshold = 0.5
                mic = sr.Microphone()
                with mic as source:
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
                try:
                    text = recognizer.recognize_google(audio, language=_get_lang(self.language))
                    callback(text)
                except sr.UnknownValueError:
                    callback(None)
                except sr.RequestError as exc:
                    logger.warning("Error de reconocimiento: %s", exc)
                    callback(None)
            except Exception as exc:
                logger.debug("listen_once error: %s", exc)
                callback(None)
            finally:
                self._paused = False

        threading.Thread(target=_run, daemon=True, name="jarvis-listen-once").start()


def _sleep(seconds: float):
    import time
    time.sleep(seconds)
