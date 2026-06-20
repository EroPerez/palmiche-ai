"""Background wake-word listener.

Continuously listens via the microphone and calls a callback when the
configured wake word is heard.

Requires: pip install SpeechRecognition pyaudio
"""
import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)


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
            import pyaudio  # noqa: F401
        except ImportError as exc:
            logger.warning(
                "Wake word desactivado — instala: pip install SpeechRecognition pyaudio "
                "(%s)", exc
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

        # Initial noise calibration
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
        except Exception:
            pass

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
