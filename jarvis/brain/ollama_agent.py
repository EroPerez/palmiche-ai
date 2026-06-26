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

from ..config import JARVIS_GUARDRAILS_ENABLED, JARVIS_NAME, JARVIS_OLLAMA_HOST, JARVIS_OLLAMA_MODEL
from ..memory.history import ConversationHistory
from ..tools.registry import get_tool_definitions, execute_tool
from .prompts import get_system_prompt

# ---------------------------------------------------------------------------
# Convert Anthropic-style schemas → Ollama/OpenAI function format
# ---------------------------------------------------------------------------

def _to_ollama_tools(definitions: list) -> list:
    """Convert Anthropic tool definitions to Ollama/OpenAI function-calling format."""
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

class JarvisOllamaAgent:
    """Jarvis agent running against a local Ollama instance."""

    def __init__(self, name: str = JARVIS_NAME, registry=None):
        """Initialize agent, connect to Ollama, and verify the configured model is available.

        Args:
            registry: Optional DynamicToolRegistry. When provided, its tools and
                      executor are used instead of the static definitions, so
                      A2A/MCP/custom tools are available to this backend too.
        """
        self.history = ConversationHistory()
        self._host = JARVIS_OLLAMA_HOST.rstrip("/")
        self._model = JARVIS_OLLAMA_MODEL
        self._system = get_system_prompt(name)
        self._registry = registry
        definitions = registry.definitions if registry is not None else get_tool_definitions()
        self._tools = _to_ollama_tools(definitions)
        self._guardrails = None
        if JARVIS_GUARDRAILS_ENABLED:
            from ..guardrails import GuardrailsEngine
            self._guardrails = GuardrailsEngine.from_config()
        self._verify_connection()

    def _execute_tool(self, name: str, inputs: dict) -> str:
        if self._registry is not None:
            return self._registry.execute(name, inputs)
        return execute_tool(name, inputs)

    # ----------------------------------------------------------------- setup

    def _verify_connection(self):
        """Ping Ollama's /api/tags endpoint and confirm the target model is pulled."""
        try:
            r = requests.get(f"{self._host}/api/tags", timeout=5)
            r.raise_for_status()
        except requests.ConnectionError as exc:
            raise ConnectionError(
                f"No se pudo conectar a Ollama en {self._host}.\n"
                "Asegúrate de que Ollama esté corriendo: ollama serve"
            ) from exc
        except requests.RequestException as exc:
            raise ConnectionError(f"Error al verificar Ollama: {exc}") from exc

        available = [m.get("name", "") for m in r.json().get("models", [])]
        base = self._model.split(":")[0]
        has_match = any(
            isinstance(m, str) and (m == self._model or m.split(":")[0] == base)
            for m in available
        )
        if not has_match:
            hint = ", ".join(available) or "ninguno"
            raise ValueError(
                f"Modelo '{self._model}' no encontrado en Ollama.\n"
                f"Descárgalo con:  ollama pull {self._model}\n"
                f"Disponibles: {hint}"
            )

    # ------------------------------------------------------------------ chat

    def chat(self, user_message: str) -> str:
        """Send a message and run the tool-use loop until the model returns plain text."""
        if self._guardrails:
            input_verdict = self._guardrails.check_input(user_message)
            if input_verdict.blocked:
                return input_verdict.message

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
                        "tools":   self._tools,
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

                if self._guardrails:
                    output_verdict = self._guardrails.check_output(text)
                    if output_verdict.blocked:
                        blocked_msg = output_verdict.message
                        self.history.add("assistant", blocked_msg)
                        return blocked_msg
                    if output_verdict.transformed_text is not None:
                        text = output_verdict.transformed_text

                self.history.add("assistant", text)
                return text

            # Append the assistant's tool-call message to context
            messages.append(assistant_msg)

            # Execute each tool and append results
            for call in tool_calls:
                fn        = call.get("function", {})
                tool_name = fn.get("name", "")
                raw_args  = fn.get("arguments", {})

                # Ollama may return arguments as a JSON string or non-dict value
                if isinstance(raw_args, str):
                    try:
                        raw_args = json.loads(raw_args)
                    except (json.JSONDecodeError, ValueError):
                        raw_args = {}
                if not isinstance(raw_args, dict):
                    raw_args = {}

                if self._guardrails:
                    tool_verdict = self._guardrails.check_tool_call(tool_name, raw_args)
                    if tool_verdict.blocked:
                        messages.append({"role": "tool", "content": f"BLOCKED: {tool_verdict.message}"})
                        continue

                result = self._execute_tool(tool_name, raw_args)

                if self._guardrails:
                    result_verdict = self._guardrails.check_tool_result(str(result))
                    if result_verdict.transformed_text is not None:
                        result = result_verdict.transformed_text

                messages.append({"role": "tool", "content": result})

        err = "Se alcanzó el límite de iteraciones de herramientas."
        self.history.add("assistant", err)
        return err
