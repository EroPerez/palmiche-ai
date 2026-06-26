"""Optional voice I/O. Requires: pip install SpeechRecognition pyaudio"""
from typing import Optional


def listen() -> Optional[str]:
    """Record from microphone and return recognized text, or None on failure."""
    try:
        from .wake_word import _suppress_alsa_errors, _audio_device_available

        _suppress_alsa_errors()
        if not _audio_device_available():
            return None

        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Escuchando... (habla ahora)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)

        return recognizer.recognize_google(audio, language="es-ES")
    except Exception:
        return None


def speak(text: str, block: bool = True):
    """Convert text to speech via AudioEngine."""
    try:
        from .audio_engine import get_engine

        engine = get_engine()
        engine.speak(text, block=block)
    except Exception:
        pass
