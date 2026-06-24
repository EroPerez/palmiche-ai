"""Optional voice I/O. Requires: pip install SpeechRecognition pyttsx3 pyaudio"""
from typing import Optional


def listen() -> Optional[str]:
    """Record from microphone and return recognized text, or None on failure."""
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Escuchando... (habla ahora)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)

        return recognizer.recognize_google(audio, language="es-ES")
    except Exception:
        return None


def speak(text: str):
    """Convert text to speech. Silently skipped if dependencies missing."""
    from .wake_word import _speak_sync
    try:
        _speak_sync(text)
    except Exception:
        pass
