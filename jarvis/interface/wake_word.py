"""Background wake-word listener.

Continuously listens via the microphone and calls a callback when the
configured wake word is heard.

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
# Without this, the callback is freed after snd_lib_error_set_handler returns
# and ALSA crashes Python with "TypeError: cannot build parameter of type 'self'".
# ---------------------------------------------------------------------------
_ALSA_HANDLER_TYPE = ctypes.CFUNCTYPE(
    None,                # return type
    ctypes.c_char_p,     # file
    ctypes.c_int,        # line
    ctypes.c_char_p,     # function
    ctypes.c_int,        # err
    ctypes.c_char_p,     # fmt  (variadic args after this are ignored)
)


def _alsa_noop(filename, line, function, err, fmt):
    pass


_ALSA_NOOP_HANDLER = _ALSA_HANDLER_TYPE(_alsa_noop)  # kept alive forever


def _suppress_alsa_errors() -> None:
    """Install a no-op ALSA error handler to silence PyAudio device-probe spam."""
    try:
        ctypes.cdll.LoadLibrary("libasound.so.2").snd_lib_error_set_handler(
            _ALSA_NOOP_HANDLER
        )
    except OSError:
        pass  # libasound not available (macOS, etc.)


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


class WakeWordListener:
    """Daemon thread that listens for a wake word and fires a callback.

    Usage:
        listener = WakeWordListener("palmiche", on_wake=my_callback)
        started  = listener.start()   # False if deps missing
        ...
        listener.stop()
    """

    def __init__(
        self,
        wake_word: str = "palmiche",
        on_wake: Optional[Callable] = None,
        language: str = "es-ES",
    ):
        """Configure the wake word, optional callback, and recognition language."""
        self.wake_word = wake_word.lower()
        self.on_wake = on_wake
        self.language = language
        self._running = False
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

        # Initial noise calibration — suppress JACK stderr on first open
        try:
            source = _open_microphone_quietly(mic)
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
            finally:
                mic.__exit__(None, None, None)
        except Exception as exc:
            logger.debug("Calibración de ruido ambiental fallida: %s", exc)

        while self._running:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=4, phrase_time_limit=3)

                try:
                    text = recognizer.recognize_google(
                        audio, language=self.language
                    ).lower()
                    logger.debug("Escuchado: %s", text)
                    if self.wake_word in text:
                        logger.info("¡Wake word detectada! '%s'", self.wake_word)
                        if self.on_wake:
                            self.on_wake()

                except sr.UnknownValueError:
                    pass  # no speech detected
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


def _sleep(seconds: float):
    """Sleep for *seconds* — isolated so the import stays out of the hot loop."""
    import time
    time.sleep(seconds)
