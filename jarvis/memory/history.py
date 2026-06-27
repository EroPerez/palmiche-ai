import json
import logging
from datetime import datetime
from typing import List, Dict

from ..config import HISTORY_FILE, MAX_HISTORY

logger = logging.getLogger(__name__)


class ConversationHistory:
    """Persistent conversation history with a configurable rolling window."""

    def __init__(self):
        """Load existing history from disk, applying the MAX_HISTORY window."""
        self._messages: List[Dict] = []
        self._load()

    def add(self, role: str, content: str):
        """Append a message, trim to MAX_HISTORY turns, and persist to disk."""
        self._messages.append(
            {"role": role, "content": content, "ts": datetime.now().isoformat()}
        )
        # Keep only the last MAX_HISTORY turns (each turn = 1 user + 1 assistant)
        if len(self._messages) > MAX_HISTORY * 2:
            self._messages = self._messages[-(MAX_HISTORY * 2):]
        self._save()

    def get_messages(self) -> List[Dict]:
        """Return messages in the format Claude API expects."""
        return [{"role": m["role"], "content": m["content"]} for m in self._messages]

    def clear(self):
        """Erase all stored messages and persist the empty state."""
        self._messages = []
        self._save()

    def _save(self):
        """Write the current message list to HISTORY_FILE as JSON."""
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_FILE.write_text(
                json.dumps(self._messages, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("No se pudo guardar historial en %s: %s", HISTORY_FILE, exc)

    def _load(self):
        """Read and validate HISTORY_FILE, silently resetting on any parse error."""
        try:
            if HISTORY_FILE.exists():
                raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    cleaned = [
                        {"role": m["role"], "content": m["content"], "ts": m.get("ts")}
                        for m in raw
                        if isinstance(m, dict)
                        and isinstance(m.get("role"), str)
                        and isinstance(m.get("content"), str)
                    ]
                    self._messages = cleaned[-(MAX_HISTORY * 2):]
                else:
                    self._messages = []
        except Exception:
            self._messages = []
