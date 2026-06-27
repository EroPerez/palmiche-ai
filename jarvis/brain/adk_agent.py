"""Google ADK-based agentic loop for Jarvis.

Supports two model backends:
  - LiteLLM bridge to Anthropic Claude  (use_gemini=False, default)
  - Native Gemini via google-genai       (use_gemini=True)

Install:
    pip install google-adk litellm          # for Claude via ADK
    pip install google-adk                  # for Gemini native (no litellm needed)
"""
import asyncio
import os
import uuid

from ..config import (
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    JARVIS_GEMINI_MODEL,
    JARVIS_GUARDRAILS_ENABLED,
    JARVIS_MODEL,
    JARVIS_NAME,
)
from .adk_tools import get_adk_tools
from .prompts import get_system_prompt
from ..memory.history import ConversationHistory


class JarvisADKAgent:
    """Jarvis agent powered by Google ADK.

    use_gemini=False  → LiteLLM + Anthropic Claude
    use_gemini=True   → native Gemini API (GOOGLE_API_KEY required)
    """

    def __init__(self, use_gemini: bool = False, name: str = JARVIS_NAME, registry=None):
        """Set up the ADK Runner with the appropriate model backend and a fresh session.

        Args:
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
        self._use_gemini = use_gemini
        self._guardrails = None
        if JARVIS_GUARDRAILS_ENABLED:
            from ..guardrails import GuardrailsEngine
            self._guardrails = GuardrailsEngine.from_config()

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

    @property
    def model_label(self) -> str:
        """Return a human-readable identifier for the active model."""
        return JARVIS_GEMINI_MODEL if self._use_gemini else f"anthropic/{JARVIS_MODEL}"

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's response (blocks until complete)."""
        if self._guardrails:
            input_verdict = self._guardrails.check_input(user_message)
            if input_verdict.blocked:
                return input_verdict.message
            if input_verdict.transformed_text is not None:
                user_message = input_verdict.transformed_text

        result = asyncio.run(self._chat_async(user_message))

        if self._guardrails:
            output_verdict = self._guardrails.check_output(result)
            if output_verdict.blocked:
                result = output_verdict.message
            elif output_verdict.transformed_text is not None:
                result = output_verdict.transformed_text

        self.history.add("assistant", result)
        return result

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

        return final_text or "No se recibió respuesta del agente ADK."
