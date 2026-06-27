"""LM Studio backend for Jarvis.

Runs a tool-use loop against a local LM Studio instance using its OpenAI-compatible REST API.
No extra Python packages needed — uses `requests` (already a core dep).

Setup:
    1. Install LM Studio: https://lmstudio.ai
    2. Start the local server in the Developer tab (port 1234)
    3. Set in .env:    JARVIS_BACKEND=lmstudio
"""
import json
import requests

from ..config import JARVIS_NAME
import os
from ..config import _env_file
from dotenv import load_dotenv

load_dotenv(_env_file)
JARVIS_LMSTUDIO_HOST = os.getenv("JARVIS_LMSTUDIO_HOST", "http://localhost:1234/v1")
JARVIS_LMSTUDIO_MODEL = os.getenv("JARVIS_LMSTUDIO_MODEL", "local-model")

from ..memory.history import ConversationHistory
from ..tools.registry import get_tool_definitions, execute_tool
from .prompts import get_system_prompt

# ---------------------------------------------------------------------------
# Convert Anthropic-style schemas → OpenAI function format
# ---------------------------------------------------------------------------

def _to_openai_tools(definitions: list) -> list:
    """Convert Anthropic tool definitions to OpenAI function-calling format."""
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


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class JarvisLMStudioAgent:
    """Jarvis agent running against a local LM Studio (OpenAI-compatible) instance."""

    def __init__(self, name: str = JARVIS_NAME, registry=None):
        """Initialize agent, connect to LM Studio, and verify connection.

        Args:
            registry: Optional DynamicToolRegistry. When provided, its tools and
                      executor are used instead of the static definitions, so
                      A2A/MCP/custom tools are available to this backend too.
        """
        self.history = ConversationHistory()
        self._host = JARVIS_LMSTUDIO_HOST.rstrip("/")
        self._model = JARVIS_LMSTUDIO_MODEL
        self._system = get_system_prompt(name)
        self._registry = registry
        definitions = registry.definitions if registry is not None else get_tool_definitions()
        self._tools = _to_openai_tools(definitions)
        self._verify_connection()

    def _execute_tool(self, name: str, inputs: dict) -> str:
        if self._registry is not None:
            return self._registry.execute(name, inputs)
        return execute_tool(name, inputs)

    # ----------------------------------------------------------------- setup

    def _verify_connection(self):
        """Ping LM Studio's /models endpoint to confirm it's running."""
        try:
            r = requests.get(f"{self._host}/models", timeout=5)
            r.raise_for_status()
        except requests.ConnectionError as exc:
            raise ConnectionError(
                f"No se pudo conectar a LM Studio en {self._host}.\n"
                "Asegúrate de que el servidor local de LM Studio esté encendido."
            ) from exc
        except requests.RequestException as exc:
            raise ConnectionError(f"Error al verificar LM Studio: {exc}") from exc

    # ------------------------------------------------------------------ chat

    def chat(self, user_message: str) -> str:
        """Send a message and run the tool-use loop until the model returns plain text."""
        self.history.add("user", user_message)

        # Build message list: system + history
        messages = [
            {"role": "system", "content": self._system},
            *self.history.get_messages(),
        ]

        for _ in range(10):
            try:
                resp = requests.post(
                    f"{self._host}/chat/completions",
                    json={
                        "model":   self._model,
                        "messages": messages,
                        "tools":   self._tools,
                        "stream":  False,
                    },
                    timeout=120,
                )
                resp.raise_for_status()
            except requests.HTTPError as exc:
                err_text = exc.response.text if (exc.response is not None and exc.response.text) else str(exc)
                err = f"Error HTTP de LM Studio: {exc}\nDetalle: {err_text}"
                self.history.add("assistant", err)
                return err
            except requests.RequestException as exc:
                err = f"Error al consultar LM Studio: {exc}"
                self.history.add("assistant", err)
                return err

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                err = "Respuesta vacía de LM Studio."
                self.history.add("assistant", err)
                return err
                
            assistant_msg = choices[0].get("message", {})
            tool_calls = assistant_msg.get("tool_calls") or []

            if not tool_calls:
                text = assistant_msg.get("content") or ""
                self.history.add("assistant", text)
                return text

            # Append the assistant's tool-call message to context
            # It must not include None content if the API is strict, but usually empty string is fine
            if assistant_msg.get("content") is None:
                assistant_msg["content"] = ""
            messages.append(assistant_msg)

            # Execute each tool and append results
            for call in tool_calls:
                tool_call_id = call.get("id", "")
                fn = call.get("function", {})
                tool_name = fn.get("name", "")
                raw_args = fn.get("arguments", {})

                # OpenAI format returns arguments as a JSON string
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except (json.JSONDecodeError, ValueError):
                        raw_args = {}
                if not isinstance(raw_args, dict):
                    raw_args = {}

                result = self._execute_tool(tool_name, raw_args)
                
                # Append tool result matching OpenAI spec
                messages.append({
                    "role": "tool",
                    "content": str(result),
                    "tool_call_id": tool_call_id
                })

        err = "Se alcanzó el límite de iteraciones de herramientas."
        self.history.add("assistant", err)
        return err
