import os
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).parent / ".env"
load_dotenv(_env_file)

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
JARVIS_MODEL: str = os.getenv("JARVIS_MODEL", "claude-haiku-4-5-20251001")
JARVIS_GEMINI_MODEL: str = os.getenv("JARVIS_GEMINI_MODEL", "gemini-2.0-flash")
JARVIS_NAME: str = os.getenv("JARVIS_NAME", "Jarvis")
JARVIS_WELCOME_MESSAGE: str = os.getenv(
    "JARVIS_WELCOME_MESSAGE", "Sistemas en línea. ¿En qué puedo ayudarte?"
)
JARVIS_GOODBYE_MESSAGE: str = os.getenv(
    "JARVIS_GOODBYE_MESSAGE", "{name} desconectado. Hasta luego."
)
JARVIS_SPLASH_ENABLED: bool = os.getenv("JARVIS_SPLASH_ENABLED", "true").lower() == "true"
VOICE_ENABLED: bool = os.getenv("JARVIS_VOICE_ENABLED", "false").lower() == "true"
HISTORY_FILE: Path = Path(
    os.getenv("JARVIS_HISTORY_FILE", "~/.jarvis_history.json")
).expanduser()
EVENTS_FILE: Path = Path(
    os.getenv("JARVIS_EVENTS_FILE", "~/.jarvis_events.json")
).expanduser()
def _get_positive_int(name: str, default: int) -> int:
    """Read an env var as a positive int, falling back to *default* on invalid values."""
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default

MAX_HISTORY: int = _get_positive_int("JARVIS_MAX_HISTORY", 50)
JARVIS_BACKEND: str = os.getenv("JARVIS_BACKEND", "anthropic")
JARVIS_WAKE_WORD: str = os.getenv("JARVIS_WAKE_WORD", "palmiche")
JARVIS_OLLAMA_HOST: str = os.getenv("JARVIS_OLLAMA_HOST", "http://localhost:11434")
JARVIS_OLLAMA_MODEL: str = os.getenv("JARVIS_OLLAMA_MODEL", "llama3.2")
