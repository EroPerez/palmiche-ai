"""Google ADK-based agentic loop for Jarvis.

Uses google-adk with LiteLLM to run Claude as the underlying model,
replacing the manual tool-use loop with ADK's built-in orchestration.

Install extras:
    pip install google-adk litellm
"""
import asyncio
import uuid

from ..config import JARVIS_MODEL, JARVIS_NAME
from .prompts import SYSTEM_PROMPT
from ..memory.history import ConversationHistory
from .adk_tools import ADK_TOOLS


class JarvisADKAgent:
    """Jarvis agent powered by Google ADK + LiteLLM + Claude."""

    def __init__(self):
        try:
            from google.adk.agents import Agent
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.adk.models.lite_llm import LiteLlm
        except ImportError as exc:
            raise ImportError(
                "Google ADK no está instalado.\n"
                "Instala con: pip install google-adk litellm\n"
                f"Error: {exc}"
            ) from exc

        self.history = ConversationHistory()
        self._session_id = str(uuid.uuid4())

        agent = Agent(
            name="jarvis",
            model=LiteLlm(model=f"anthropic/{JARVIS_MODEL}"),
            instruction=SYSTEM_PROMPT.format(name=JARVIS_NAME),
            tools=ADK_TOOLS,
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

    def chat(self, user_message: str) -> str:
        return asyncio.run(self._chat_async(user_message))

    async def _chat_async(self, user_message: str) -> str:
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
