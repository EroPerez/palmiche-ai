"""Google ADK-based universal agentic loop for Jarvis.

Supports multiple model backends through a single agent class:
  - Native Gemini via google-genai       (backend="gemini")
  - LiteLLM bridge to Anthropic Claude   (backend="anthropic")
  - LiteLLM bridge to LM Studio          (backend="lmstudio")

All backends are configured via environment variables in config.py.

Install:
    pip install google-adk litellm          # for Claude/LMStudio via ADK
    pip install google-adk                  # for Gemini native (no litellm needed)
"""
import asyncio
import os
import uuid

from ..config import (
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    JARVIS_GEMINI_MODEL,
    JARVIS_LMSTUDIO_HOST,
    JARVIS_LMSTUDIO_MODEL,
    JARVIS_MODEL,
    JARVIS_NAME,
)
from .adk_tools import get_adk_tools
from .prompts import get_system_prompt
from ..memory.history import ConversationHistory


class JarvisADKAgent:
    """Universal Jarvis agent powered by Google ADK.

    Backends:
      "gemini"    → native Gemini API (GOOGLE_API_KEY required)
      "anthropic" → LiteLLM + Anthropic Claude (ANTHROPIC_API_KEY required)
      "lmstudio"  → LiteLLM + local LM Studio (OpenAI-compatible)
    """

    def __init__(self, backend: str = "anthropic", name: str = JARVIS_NAME, registry=None):
        """Set up the ADK Runner with the appropriate model backend and a fresh session.

        Args:
            backend: Model backend — "gemini", "anthropic", or "lmstudio".
            registry: Optional DynamicToolRegistry. Its dynamically registered
                      tools (A2A/MCP/custom) are synthesized into ADK callables
                      so this backend can use them alongside the built-in tools.
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
        self._backend = backend.strip().lower()

        model = self._resolve_model()

        from .adk_dynamic import adk_tools_from_registry
        tools = list(get_adk_tools()) + adk_tools_from_registry(registry)

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

    def _resolve_model(self):
        """Build the model object for the configured backend."""
        if self._backend == "gemini":
            if not GOOGLE_API_KEY:
                raise ValueError(
                    "GOOGLE_API_KEY no está configurada. "
                    "Agrégala a jarvis/.env para usar el backend Gemini."
                )
            os.environ.setdefault("GOOGLE_API_KEY", GOOGLE_API_KEY)
            return JARVIS_GEMINI_MODEL

        try:
            from google.adk.models.lite_llm import LiteLlm
        except ImportError as exc:
            raise ImportError(
                "LiteLLM no está instalado (requerido para ADK+LiteLLM backends).\n"
                "Instala con: pip install litellm\n"
                f"Error: {exc}"
            ) from exc

        if self._backend == "lmstudio":
            os.environ.setdefault("OPENAI_API_KEY", "lm-studio")
            os.environ.setdefault("OPENAI_API_BASE", JARVIS_LMSTUDIO_HOST)
            return LiteLlm(model=f"openai/{JARVIS_LMSTUDIO_MODEL}")

        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY no está configurada. "
                "Agrégala a jarvis/.env para usar el backend ADK+Claude."
            )
        return LiteLlm(model=f"anthropic/{JARVIS_MODEL}")

    @property
    def model_label(self) -> str:
        """Return a human-readable identifier for the active model."""
        labels = {
            "gemini": JARVIS_GEMINI_MODEL,
            "anthropic": f"anthropic/{JARVIS_MODEL}",
            "lmstudio": f"lmstudio/{JARVIS_LMSTUDIO_MODEL}",
        }
        return labels.get(self._backend, self._backend)

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
        async for event in self._runner.run_async(
            user_id="user",
            session_id=self._session_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text

        if final_text:
            self.history.add("assistant", final_text)

        return final_text or "No se recibió respuesta del agente ADK."
