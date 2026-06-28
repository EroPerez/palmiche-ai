"""Google ADK universal agent — any LiteLLM-compatible provider via a single interface.

Model string format (JARVIS_MODEL env var):
  anthropic/claude-haiku-4-5-20251001  → Anthropic Claude
  openai/gpt-4o                         → OpenAI
  gemini/gemini-2.0-flash               → Google Gemini (via LiteLLM)
  gemini-2.0-flash                      → Google Gemini (ADK native, no LiteLLM)
  ollama_chat/llama3.2                  → Ollama local
  groq/llama-3.1-70b-versatile          → Groq
  mistral/mistral-large-latest          → Mistral
  azure/gpt-4o                          → Azure OpenAI

Authentication (in order of priority):
  JARVIS_API_KEY  → unified key, takes precedence over provider-specific keys
  ANTHROPIC_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY, etc. → provider fallbacks

Custom endpoint:
  JARVIS_BASE_URL → base URL for the provider API
                    (e.g. http://localhost:11434 for Ollama,
                           https://my-azure-endpoint.openai.azure.com for Azure)

Install:
    pip install google-adk litellm
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import os
import sys
import uuid

from ..config import (
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    JARVIS_API_KEY,
    JARVIS_BASE_URL,
    JARVIS_GUARDRAILS_ENABLED,
    JARVIS_MODEL,
    JARVIS_NAME,
)
from .adk_tools import get_adk_tools
from .prompts import get_system_prompt
from ..memory.history import ConversationHistory


def _normalize_model_str(model_str: str) -> str:
    """Add provider prefix to legacy bare model names (no '/' present).

    Handles old JARVIS_MODEL values like 'claude-haiku-4-5-20251001', 'llama3.2',
    or 'gpt-4o' that pre-date the unified LiteLLM format.
    """
    if "/" in model_str:
        return model_str

    name = model_str.lower()
    if name.startswith("claude"):
        return f"anthropic/{model_str}"
    if name.startswith(("gpt", "o1", "o3")):
        return f"openai/{model_str}"
    if name.startswith(("llama", "codellama", "qwen", "deepseek", "phi")):
        return f"ollama_chat/{model_str}"
    # Bare gemini names (e.g. "gemini-2.0-flash") stay as-is — ADK handles them natively.
    return model_str


def _effective_api_key(provider: str, api_key_override: str | None = None) -> str:
    """Return the best available API key for the given provider.

    Priority: api_key_override > JARVIS_API_KEY > provider-specific env vars.
    """
    if api_key_override:
        return api_key_override
    if JARVIS_API_KEY:
        return JARVIS_API_KEY
    if provider == "anthropic":
        return ANTHROPIC_API_KEY
    if provider in ("gemini", "google", "vertex_ai", "vertex_ai_beta"):
        return GOOGLE_API_KEY
    # For everything else LiteLLM picks up the right env var automatically
    # (OPENAI_API_KEY, GROQ_API_KEY, MISTRAL_API_KEY, etc.)
    return ""


def _resolve_model(
    model_str: str,
    *,
    api_key_override: str | None = None,
    base_url_override: str | None = None,
):
    """Build the ADK-compatible model object for the given LiteLLM model string.

    - Bare gemini names → returned as-is (ADK native, no LiteLLM overhead)
    - Everything else  → wrapped in LiteLlm with optional api_key / api_base
    """
    model_str = _normalize_model_str(model_str)

    # Native Gemini: ADK supports these directly without LiteLLM
    if "/" not in model_str:
        api_key = _effective_api_key("gemini", api_key_override)
        if api_key:
            # Overwrite (not setdefault) so JARVIS_API_KEY always wins
            os.environ["GOOGLE_API_KEY"] = api_key
        return model_str

    provider = model_str.split("/")[0].lower()

    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as exc:
        raise ImportError(
            "LiteLLM no está instalado (requerido para modelos no-Gemini).\n"
            "Instala con: pip install litellm\n"
            f"Error: {exc}"
        ) from exc

    kwargs: dict = {"model": model_str}

    api_key = _effective_api_key(provider, api_key_override)
    if api_key:
        kwargs["api_key"] = api_key

    base_url = base_url_override or JARVIS_BASE_URL
    if base_url:
        kwargs["api_base"] = base_url

    return LiteLlm(**kwargs)


def _mcp_spec_to_toolset(spec: str):
    """Convert an MCP spec string to an ADK McpToolset."""
    import shlex
    from urllib.parse import urlparse
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        SseConnectionParams,
        StdioConnectionParams,
    )
    from mcp import StdioServerParameters

    if spec.startswith(("http://", "https://")):
        parsed = urlparse(spec)
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError(
                f"Remote MCP SSE endpoints must use https:// (got {spec!r}). "
                "Only localhost HTTP is allowed for local development."
            )
        return McpToolset(connection_params=SseConnectionParams(url=spec))

    parts = shlex.split(spec)
    filter_script = str(
        (__import__("pathlib").Path(__file__).resolve().parent.parent
         / "mcp_support" / "json_filter.py")
    )
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[filter_script, "--", *parts],
                env=None,
            ),
        ),
    )


class JarvisUniversalADKAgent:
    """Jarvis agent powered by Google ADK with multi-provider support.

    Supports any LiteLLM-compatible provider by setting JARVIS_MODEL to the
    appropriate model string (e.g. 'anthropic/claude-haiku-4-5-20251001',
    'openai/gpt-4o', 'ollama_chat/llama3.2', 'gemini-2.0-flash').

    A single JARVIS_API_KEY replaces all provider-specific key variables,
    and JARVIS_BASE_URL lets you point at a custom or local endpoint.
    """

    def __init__(
        self,
        name: str = JARVIS_NAME,
        registry=None,
        mcp_specs=None,
        _model_override: str | None = None,
        _api_key_override: str | None = None,
        _base_url_override: str | None = None,
    ):
        """Build the ADK Runner with the resolved model and tool surface.

        Args:
            registry: Optional DynamicToolRegistry (A2A/MCP/custom tools).
            mcp_specs: Optional list of MCP specs for native ADK McpToolsets.
            _model_override: Internal — lets _build_agent pass a derived model string
                             when mapping legacy backends (gemini, ollama) to this agent.
            _api_key_override: Internal — override api key (e.g. from GOOGLE_API_KEY).
            _base_url_override: Internal — override base URL (e.g. from JARVIS_OLLAMA_HOST).
        """
        try:
            from google.adk.agents import Agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
        except ImportError as exc:
            raise ImportError(
                "Google ADK no está instalado.\n"
                "Instala con: pip install google-adk litellm\n"
                f"Error: {exc}"
            ) from exc

        self.history = ConversationHistory()
        self._session_id = str(uuid.uuid4())
        self._guardrails = None
        if JARVIS_GUARDRAILS_ENABLED:
            from ..guardrails import GuardrailsEngine
            self._guardrails = GuardrailsEngine.from_config()

        model_str = _model_override or JARVIS_MODEL
        model = _resolve_model(
            model_str,
            api_key_override=_api_key_override,
            base_url_override=_base_url_override,
        )
        self._model_label = _normalize_model_str(model_str)

        from .adk_dynamic import adk_tools_from_registry
        tools: list = list(get_adk_tools()) + adk_tools_from_registry(registry)

        if mcp_specs:
            for spec in mcp_specs:
                try:
                    tools.append(_mcp_spec_to_toolset(spec))
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"  [MCP] Error creando McpToolset para '{spec}': {exc}",
                        file=sys.stderr,
                    )

        agent = Agent(
            name="jarvis",
            model=model,
            instruction=get_system_prompt(name),
            tools=tools,
        )

        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=agent,
            app_name="jarvis",
            session_service=self._session_service,
        )
        JarvisUniversalADKAgent._run_async(
            self._session_service.create_session(
                app_name="jarvis",
                user_id="user",
                session_id=self._session_id,
            )
        )

    @property
    def model_label(self) -> str:
        return self._model_label

    def clear(self) -> None:
        """Reset both the persistent conversation history and the active ADK session.

        The ADK InMemorySessionService is the live context used by run_async().
        Clearing only agent.history leaves stale context in the ADK session, so
        this method resets both stores atomically.
        """
        self.history.clear()
        # Create a fresh session to drop all ADK in-memory context
        self._session_id = str(uuid.uuid4())
        self._run_async(
            self._session_service.create_session(
                app_name="jarvis",
                user_id="user",
                session_id=self._session_id,
            )
        )

    @staticmethod
    def _run_async(coro):
        """Run a coroutine, handling the case where a loop is already running.

        When camera or other tools call this from inside the ADK agent's own
        async event loop, asyncio.run() would raise "cannot be called from a
        running event loop". We detect that and delegate to a worker thread
        that starts its own fresh event loop instead.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return asyncio.run(coro)

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's response (blocks until complete)."""
        if self._guardrails:
            input_verdict = self._guardrails.check_input(user_message)
            if input_verdict.blocked:
                return input_verdict.message
            if input_verdict.transformed_text is not None:
                user_message = input_verdict.transformed_text

        result = self._run_async(self._chat_async(user_message))

        if self._guardrails:
            output_verdict = self._guardrails.check_output(result)
            if output_verdict.blocked:
                result = output_verdict.message
            elif output_verdict.transformed_text is not None:
                result = output_verdict.transformed_text

        self.history.add("assistant", result)
        return result

    async def _chat_async(self, user_message: str) -> str:
        from google.genai import types

        self.history.add("user", user_message)

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )

        final_text = ""
        try:
            async for event in self._runner.run_async(
                user_id="user",
                session_id=self._session_id,
                new_message=content,
            ):
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text
        except Exception as exc:  # noqa: BLE001
            # BaseExceptionGroup is only available on Python 3.11+
            if sys.version_info >= (3, 11) and isinstance(exc, BaseExceptionGroup):
                parts_list = [f"{type(e).__name__}: {e}" for e in exc.exceptions]
                msg = " | ".join(parts_list)
            else:
                msg = str(exc)

            if "500" in msg or "Internal error" in msg or "INTERNAL" in msg:
                return (
                    "Ocurrió un error interno en el modelo de lenguaje (500). "
                    "Puede deberse a que el contexto es demasiado grande "
                    "(muchas herramientas o resultados extensos). "
                    "Intentá reformular la consulta o reducir la cantidad "
                    f"de herramientas MCP.\n\nDetalle: {msg}"
                )
            return f"Error del agente: {msg}"

        return final_text or "No se recibió respuesta del agente ADK."

    def vision_chat(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> str:
        """Send an image + text prompt and return the agent's response."""
        return self._run_async(self._vision_chat_async(image_bytes, prompt, mime_type))

    async def _vision_chat_async(
        self, image_bytes: bytes, prompt: str, mime_type: str,
    ) -> str:
        from google.genai import types

        content = types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                types.Part.from_text(text=prompt),
            ],
        )

        final_text = ""
        try:
            async for event in self._runner.run_async(
                user_id="user",
                session_id=self._session_id,
                new_message=content,
            ):
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text
        except Exception as exc:  # noqa: BLE001
            if sys.version_info >= (3, 11) and isinstance(exc, BaseExceptionGroup):
                parts_list = [f"{type(e).__name__}: {e}" for e in exc.exceptions]
                msg = " | ".join(parts_list)
            else:
                msg = str(exc)
            return f"Error de visión: {msg}"

        return final_text or "No se recibió respuesta del agente ADK."
