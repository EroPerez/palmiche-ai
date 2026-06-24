"""Background wake-word listener.

Continuously listens via the microphone and calls a callback when the
configured wake word is heard.

Requires: pip install SpeechRecognition pyaudio
"""
import ctypes
import logging
import os
import re
import threading
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Text preprocessing — strip markdown and emojis before TTS
# ---------------------------------------------------------------------------
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U0001F1E0-\U0001F1FF"
    "\U00002500-\U00002BEF"
    "\U00002300-\U000023FF"
    "]+",
    flags=re.UNICODE,
)


def _clean_for_tts(text: str) -> str:
    """Remove markdown syntax and emojis so TTS reads only natural prose."""
    # Code blocks (must come before inline code)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Markdown links → keep label
    text = re.sub(r"!\[[^\]]*\]\([^\)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Bold / italic
    text = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_\n]+)_{1,3}", r"\1", text)
    # Headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Blockquotes and list markers
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Emojis
    text = _EMOJI_RE.sub("", text)
    # Collapse excess whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

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


def _speak_async(text: str, lang: str = "es", on_done=None) -> None:
    """Speak *text* in a daemon thread using the best available TTS engine.

    Quality tiers (tried in order):
    1. gTTS — Google neural voice (internet required); played via mpg123/ffplay.
    2. pyttsx3 — with Spanish voice selection and optimised rate/pitch.
    3. espeak-ng — subprocess fallback with Spanish voice and quality flags.
    4. macOS 'say' — native macOS TTS.
    """
    def _run():
        try:
            _speak_sync(text, lang)
        finally:
            if on_done:
                on_done()

    threading.Thread(target=_run, daemon=True, name="jarvis-tts").start()


def _speak_sync(text: str, lang: str = "es") -> None:
    """Speak *text* synchronously using the best available TTS engine."""
    text = _clean_for_tts(text)
    if not text:
        return
    # ── Tier 1: gTTS (best quality) ──────────────────────────────────────
    try:
        import os
        import subprocess
        import tempfile
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tts.save(tmp.name)
            mp3 = tmp.name
        for player in (["mpg123", "-q", mp3], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", mp3]):
            try:
                subprocess.run(player, check=True, capture_output=True)
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        os.unlink(mp3)
        return
    except Exception:
        pass

    # ── Tier 2: pyttsx3 with Spanish voice + quality settings ────────────
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices") or []
        for v in voices:
            vid = (v.id or "").lower()
            vname = (v.name or "").lower()
            if "es" in vid or "spanish" in vname or "español" in vname:
                engine.setProperty("voice", v.id)
                break
        engine.setProperty("rate", 135)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
        return
    except Exception:
        pass

    # ── Tier 3: espeak-ng / system TTS ───────────────────────────────────
    import platform
    import subprocess
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.run(
                ["espeak-ng", "-v", "es", "-s", "130", "-p", "40", "-a", "200", text],
                check=False, capture_output=True,
            )
        elif system == "Darwin":
            subprocess.run(["say", "-v", "Monica", text], check=False)
    except FileNotFoundError:
        pass


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
        language: str = "es-ES",
        response_text: str = "Kewelta Compay",
    ):
        """Configure the wake word, callbacks, recognition language and audio response."""
        self.wake_word = wake_word.lower()
        self.on_wake = on_wake
        self.on_command = on_command   # called with transcribed voice command text
        self.language = language
        self.response_text = response_text
        self._running = False
        self._paused = False           # pause main loop during listen_once()
        self._greeted = False          # greeting is spoken only once
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
            if self._paused:
                _sleep(0.1)
                continue

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
                        if self.response_text and not self._greeted:
                            self._greeted = True
                            _speak_async(self.response_text)
                        if self.on_wake:
                            self.on_wake()
                        if self.on_command:
                            _sleep(1.5)  # wait for TTS to finish before listening
                            self._paused = True
                            try:
                                self._listen_for_command(recognizer, mic)
                            finally:
                                self._paused = False

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


    def _listen_for_command(self, recognizer, mic) -> None:
        """Listen for one follow-up voice command and fire on_command with the transcript."""
        import speech_recognition as sr
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            try:
                text = recognizer.recognize_google(audio, language=self.language)
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
        """Listen for one phrase and call callback(text_or_None) from a daemon thread.

        Pauses the background wake-word loop while listening so the microphone
        is not contended.
        """
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
                    text = recognizer.recognize_google(audio, language=self.language)
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
    """Sleep for *seconds* — isolated so the import stays out of the hot loop."""
    import time
    time.sleep(seconds)
