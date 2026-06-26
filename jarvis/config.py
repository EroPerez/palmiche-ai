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
NOTES_FILE: Path = Path(
    os.getenv("JARVIS_NOTES_FILE", "~/.jarvis_notes.json")
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

# Language used for the tool/skill schemas and the internal system prompt that
# every brain (anthropic, adk, gemini, ollama) sends to its model. "en" tends to
# improve tool-calling reliability; "es" keeps the original Spanish. This only
# affects what the model sees internally — the assistant still replies to the
# user in the user's own language.
def _get_lang(name: str, default: str) -> str:
    """Read a language env var, accepting only 'en'/'es' and falling back to *default*."""
    value = os.getenv(name, default).strip().lower()
    return value if value in ("en", "es") else default

JARVIS_TOOL_LANG: str = _get_lang("JARVIS_TOOL_LANG", "en")

# Plain-text file where the user can define their own tools/skills (no Python).
# Each tool maps a name + description + parameters to a shell command template.
# See jarvis/tools/custom.py for the format. Missing file → no custom tools.
JARVIS_CUSTOM_TOOLS_FILE: Path = Path(
    os.getenv("JARVIS_CUSTOM_TOOLS_FILE", "~/.jarvis_custom_tools.txt")
).expanduser()
JARVIS_WAKE_WORD: str = os.getenv("JARVIS_WAKE_WORD", "palmiche")
JARVIS_AUDIO_VOLUME: int = _get_positive_int("JARVIS_AUDIO_VOLUME", 100)
JARVIS_TTS_CACHE: bool = os.getenv("JARVIS_TTS_CACHE", "true").lower() == "true"
JARVIS_TTS_STREAM: bool = os.getenv("JARVIS_TTS_STREAM", "true").lower() == "true"
JARVIS_OLLAMA_HOST: str = os.getenv("JARVIS_OLLAMA_HOST", "http://localhost:11434")
JARVIS_OLLAMA_MODEL: str = os.getenv("JARVIS_OLLAMA_MODEL", "llama3.2")
# Optional path to a custom tray icon image (PNG/ICO). Empty → use the built-in
# horse-head icon. Use this to point at your own Palmiche image if you have one.
JARVIS_TRAY_ICON: str = os.getenv("JARVIS_TRAY_ICON", "")

# Optional path to an MP3/WAV file played once on tray startup.
# Run extract_assets.py to generate jarvis/assets/welcome.mp3 from the source video.
_DEFAULT_WELCOME_AUDIO = str(Path(__file__).parent / "assets" / "welcome.mp3")
JARVIS_WELCOME_AUDIO: str = os.getenv(
    "JARVIS_WELCOME_AUDIO",
    _DEFAULT_WELCOME_AUDIO if Path(_DEFAULT_WELCOME_AUDIO).is_file() else "",
)

# ---------------------------------------------------------------------------
# A2A (Agent-to-Agent) configuration
# ---------------------------------------------------------------------------

# Host and port for the built-in A2A HTTP server (--serve-a2a mode).
A2A_HOST: str = os.getenv("JARVIS_A2A_HOST", "0.0.0.0")
A2A_PORT: int = _get_positive_int("JARVIS_A2A_PORT", 8080)

# Comma-separated list of remote A2A agent URLs to connect to as client tools.
# Example: JARVIS_A2A_AGENTS=http://agent1:8080,http://agent2:9090
A2A_AGENTS: list[str] = [
    u.strip() for u in os.getenv("JARVIS_A2A_AGENTS", "").split(",") if u.strip()
]

# ---------------------------------------------------------------------------
# MCP (Model Context Protocol) configuration
# ---------------------------------------------------------------------------

# Semicolon-separated MCP server specs to connect to as client tools.
# Each spec is either:
#   - A command string for stdio:  "npx -y @modelcontextprotocol/server-filesystem /tmp"
#   - An HTTP URL for SSE:         "http://localhost:3000"
# Example: JARVIS_MCP_SERVERS=npx -y @mcp/server-fs /tmp;http://localhost:3001
MCP_SERVERS: list[str] = [
    s.strip() for s in os.getenv("JARVIS_MCP_SERVERS", "").split(";") if s.strip()
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

JARVIS_LOG_FILE: Path = Path(
    os.getenv("JARVIS_LOG_FILE", "~/.jarvis_tools.log")
).expanduser()
JARVIS_LOG_ENABLED: bool = os.getenv("JARVIS_LOG_ENABLED", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Sudo password (optional)
# ---------------------------------------------------------------------------

# When set, commands that require sudo can use this password automatically
# instead of prompting interactively (which would hang in a headless context).
# The agent will ask the user for confirmation before using it.
JARVIS_SUDO_PASSWORD: str = os.getenv("JARVIS_SUDO_PASSWORD", "")

# ---------------------------------------------------------------------------
# Guardrails
# ---------------------------------------------------------------------------

JARVIS_GUARDRAILS_FILE: Path = Path(
    os.getenv("JARVIS_GUARDRAILS_FILE", "~/.jarvis_guardrails.json")
).expanduser()
JARVIS_GUARDRAILS_ENABLED: bool = os.getenv("JARVIS_GUARDRAILS_ENABLED", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Computer Use — Gemini-powered visual browser/desktop automation
# ---------------------------------------------------------------------------

# Gemini model for computer use tasks. Requires google-genai and GOOGLE_API_KEY.
# Recommended: gemini-2.5-flash (supports computer use natively)
COMPUTER_USE_MODEL: str = os.getenv("COMPUTER_USE_MODEL", "gemini-2.5-flash")

# Default backend: "playwright" (browser) or "desktop" (full desktop via pyautogui)
COMPUTER_USE_BACKEND: str = os.getenv("COMPUTER_USE_BACKEND", "playwright")

# Safety cap on agent loop iterations per task
COMPUTER_USE_MAX_ITERATIONS: int = _get_positive_int("COMPUTER_USE_MAX_ITERATIONS", 30)
