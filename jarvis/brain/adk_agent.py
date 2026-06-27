"""Google ADK-based agentic loop for Jarvis.

Supports two model backends:
  - LiteLLM bridge to Anthropic Claude  (use_gemini=False, default)
  - Native Gemini via google-genai       (use_gemini=True)

Install:
    pip install google-adk litellm          # for Claude via ADK
    pip install google-adk                  # for Gemini native (no litellm needed)
"""
from __future__ import annotations

import asyncio
import os
import uuid

from ..config import (
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    JARVIS_GEMINI_MODEL,
    JARVIS_MODEL,
    JARVIS_NAME,
)
from .adk_tools import get_adk_tools
from .prompts import get_system_prompt
from ..memory.history import ConversationHistory


def _mcp_spec_to_toolset(spec: str):
    """Convert an MCP spec string to an ADK McpToolset.

    *command arg1 arg2* → ``StdioServerParameters`` (wrapped with a JSON-line
                          filter for servers that write debug output to stdout)
    *http://...*        → ``SseConnectionParams``
    """
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import (
        SseConnectionParams,
        StdioConnectionParams,
    )
    from mcp import StdioServerParameters

    if spec.startswith("http://") or spec.startswith("https://"):
        return McpToolset(
            connection_params=SseConnectionParams(url=spec),
        )
    parts = spec.split()
    import sys
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


class JarvisADKAgent:
    """Jarvis agent powered by Google ADK.

    use_gemini=False  → LiteLLM + Anthropic Claude
    use_gemini=True   → native Gemini API (GOOGLE_API_KEY required)
    """

    def __init__(self, use_gemini: bool = False, name: str = JARVIS_NAME, registry=None, mcp_specs=None):
        """Set up the ADK Runner with the appropriate model backend and a fresh session.

        Args:
            registry: Optional DynamicToolRegistry. Its dynamically registered
                      tools (A2A/custom) are synthesized into ADK callables
                      so this backend can use them alongside the built-in tools.
            mcp_specs: Optional list of MCP connection specs (command strings
                       or HTTP URLs). Each creates an ADK-native McpToolset
                       instead of going through the sync bridge.
        """
        try:
            from google.adk.agents import Agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
        except ImportError as exc:
            raise ImportError(
                "Google ADK no está instalado.\n"
                "Instala con: pip install google-adk\n"
                f"Error: {exc}"
            ) from exc

        self.history = ConversationHistory()
        self._session_id = str(uuid.uuid4())
        self._use_gemini = use_gemini

        if use_gemini:
            if not GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY no está configurada. "
                    "Agrégala a jarvis/.env para usar el backend Gemini."
                )
            os.environ.setdefault("GOOGLE_API_KEY", GOOGLE_API_KEY)
            model: object = JARVIS_GEMINI_MODEL
        else:
            if not ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY no está configurada. "
                    "Agrégala a jarvis/.env para usar el backend ADK+Claude."
                )
            try:
                from google.adk.models.lite_llm import LiteLlm
            except ImportError as exc:
                raise ImportError(
                    "LiteLLM no está instalado (requerido para ADK+Claude).\n"
                    "Instala con: pip install litellm\n"
                    f"Error: {exc}"
                ) from exc
            model = LiteLlm(model=f"anthropic/{JARVIS_MODEL}")

        from .adk_dynamic import adk_tools_from_registry

        tools: list = list(get_adk_tools()) + adk_tools_from_registry(registry)

        if mcp_specs:
            for spec in mcp_specs:
                try:
                    tools.append(_mcp_spec_to_toolset(spec))
                except Exception as exc:
                    print(
                        f"  [MCP] Error creando McpToolset para '{spec}': {exc}",
                        file=__import__("sys").stderr,
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
        asyncio.run(
            self._session_service.create_session(
                app_name="jarvis",
                user_id="user",
                session_id=self._session_id,
            )
        )

    @property
    def model_label(self) -> str:
        """Return a human-readable identifier for the active model."""
        return JARVIS_GEMINI_MODEL if self._use_gemini else f"anthropic/{JARVIS_MODEL}"

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's response (blocks until complete)."""
        return asyncio.run(self._chat_async(user_message))

    async def _chat_async(self, user_message: str) -> str:
        """Async implementation: stream ADK events and collect the final text response."""
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
        except Exception as exc:
            # Unpack nested exception groups for clearer diagnostics
            if isinstance(exc, BaseExceptionGroup):
                parts = [f"{type(e).__name__}: {e}" for e in exc.exceptions]
                msg = " | ".join(parts)
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

        if final_text:
            self.history.add("assistant", final_text)

        return final_text or "No se recibió respuesta del agente ADK."
