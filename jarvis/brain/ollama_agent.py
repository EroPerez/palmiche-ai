"""Ollama backend for Jarvis.

Runs a tool-use loop against a local Ollama instance using its REST API.
No extra Python packages needed — uses `requests` (already a core dep).

Setup:
    1. Install Ollama:  https://ollama.ai
    2. Pull a model:   ollama pull llama3.2
    3. Start server:   ollama serve   (or it starts automatically on install)
    4. Set in .env:    JARVIS_BACKEND=ollama

Models with good tool-use support (small → large):
    llama3.2:1b   ~0.8 GB   very fast, basic tool use
    llama3.2      ~2 GB     recommended default
    qwen2.5:3b    ~2 GB     strong tool use for its size
    phi3.5:mini   ~2.2 GB   Microsoft, efficient
    llama3.1:8b   ~5 GB     more capable, needs more RAM
"""
import json

import requests

from ..config import JARVIS_NAME, JARVIS_OLLAMA_HOST, JARVIS_OLLAMA_MODEL
from ..memory.history import ConversationHistory
from ..tools.registry import TOOL_DEFINITIONS, execute_tool
from .prompts import SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# Convert Anthropic-style schemas → Ollama/OpenAI function format
# ---------------------------------------------------------------------------

def _to_ollama_tools(definitions: list) -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": d["name"],
                "description": d["description"],
                "parameters": d["input_schema"],
            },
        }
        for d in definitions
    ]


_TOOLS = _to_ollama_tools(TOOL_DEFINITIONS)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class JarvisOllamaAgent:
    """Jarvis agent running against a local Ollama instance."""

    def __init__(self):
        self.history = ConversationHistory()
        self._host = JARVIS_OLLAMA_HOST.rstrip("/")
        self._model = JARVIS_OLLAMA_MODEL
        self._system = SYSTEM_PROMPT.format(name=JARVIS_NAME)
        self._verify_connection()

    # ----------------------------------------------------------------- setup

    def _verify_connection(self):
        try:
            r = requests.get(f"{self._host}/api/tags", timeout=5)
            r.raise_for_status()
        except requests.ConnectionError:
            raise ConnectionError(
                f"No se pudo conectar a Ollama en {self._host}.\n"
                "Asegúrate de que Ollama esté corriendo: ollama serve"
            )
        except requests.RequestException as exc:
            raise ConnectionError(f"Error al verificar Ollama: {exc}")

        available = [m.get("name", "") for m in r.json().get("models", [])]
        base = self._model.split(":")[0]
        if available and not any(base in m for m in available):
            hint = ", ".join(available) or "ninguno"
            raise ValueError(
                f"Modelo '{self._model}' no encontrado en Ollama.\n"
                f"Descárgalo con:  ollama pull {self._model}\n"
                f"Disponibles: {hint}"
            )

    # ------------------------------------------------------------------ chat

    def chat(self, user_message: str) -> str:
        self.history.add("user", user_message)

        # Build message list: system + history
        messages = [
            {"role": "system", "content": self._system},
            *self.history.get_messages(),
        ]

        for _ in range(10):
            try:
                resp = requests.post(
                    f"{self._host}/api/chat",
                    json={
                        "model":   self._model,
                        "messages": messages,
                        "tools":   _TOOLS,
                        "stream":  False,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                err = f"Error al consultar Ollama: {exc}"
                self.history.add("assistant", err)
                return err

            data = resp.json()
            assistant_msg = data.get("message", {})
            tool_calls = assistant_msg.get("tool_calls") or []

            if not tool_calls:
                text = assistant_msg.get("content") or ""
                self.history.add("assistant", text)
                return text

            # Append the assistant's tool-call message to context
            messages.append(assistant_msg)

            # Execute each tool and append results
            for call in tool_calls:
                fn        = call.get("function", {})
                tool_name = fn.get("name", "")
                raw_args  = fn.get("arguments", {})

                # Ollama may return arguments as a JSON string
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except (json.JSONDecodeError, ValueError):
                        raw_args = {}

                result = execute_tool(tool_name, raw_args)
                messages.append({"role": "tool", "content": result})

        err = "Se alcanzó el límite de iteraciones de herramientas."
        self.history.add("assistant", err)
        return err
