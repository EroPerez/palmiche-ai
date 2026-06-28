"""Optional voice I/O. Requires: pip install SpeechRecognition pyaudio"""
from typing import Optional


_SPEECH_LANG_MAP: dict[str, str] = {
    "es": "es-ES",
    "en": "en-US",
}


def listen() -> Optional[str]:
    """Record from microphone and return recognized text, or None on failure."""
    try:
        from .wake_word import _suppress_alsa_errors, _audio_device_available

        _suppress_alsa_errors()
        if not _audio_device_available():
            return None

        import speech_recognition as sr
        from ..config import JARVIS_TOOL_LANG

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Escuchando... (habla ahora)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)

        speech_lang = _SPEECH_LANG_MAP.get(JARVIS_TOOL_LANG, f"{JARVIS_TOOL_LANG}-{JARVIS_TOOL_LANG.upper()}")
        return recognizer.recognize_google(audio, language=speech_lang)
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
