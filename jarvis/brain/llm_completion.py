"""Centralized LLM completion via a lightweight ADK agent (no tools).

Uses the same model resolution and configuration as JarvisUniversalADKAgent
so all LLM calls — including multimodal vision — go through ADK infrastructure.
"""
from __future__ import annotations

import asyncio
import sys
import uuid


def completion(messages: list[dict], **kwargs) -> str:
    """Run a one-shot LLM completion through a lightweight ADK agent.

    Args:
        messages: OpenAI-format messages (supports multimodal content blocks
                  with image_url entries).
        **kwargs: Currently unused; reserved for future parameters.

    Returns:
        The model's text response, or an error string on failure.
    """
    try:
        from google.adk.agents import Agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
    except ImportError as exc:
        return (
            "Error: Google ADK no está instalado.\n"
            f"Instala con: pip install google-adk litellm\nDetalle: {exc}"
        )

    from .adk_universal import _resolve_model

    try:
        model = _resolve_model(
            __import__("jarvis.config", fromlist=["JARVIS_MODEL"]).JARVIS_MODEL
        )
    except ImportError as exc:
        return str(exc)

    parts: list = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(types.Part.from_text(text=content))
        elif isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    parts.append(types.Part.from_text(text=block["text"]))
                elif block.get("type") == "image_url":
                    data_url = block["image_url"]["url"]
                    if data_url.startswith("data:"):
                        header, b64_data = data_url.split(",", 1)
                        mime = header.split(":")[1].split(";")[0]
                        import base64
                        image_bytes = base64.b64decode(b64_data)
                        parts.append(types.Part.from_bytes(
                            data=image_bytes, mime_type=mime,
                        ))

    if not parts:
        return "Error: no se proporcionó contenido para analizar."

    agent = Agent(
        name="jarvis_vision",
        model=model,
        instruction="Analyze the provided content and respond accurately.",
        tools=[],
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="jarvis_vision",
        session_service=session_service,
    )

    session_id = str(uuid.uuid4())

    async def _run() -> str:
        await session_service.create_session(
            app_name="jarvis_vision",
            user_id="user",
            session_id=session_id,
        )
        user_content = types.Content(role="user", parts=parts)
        final_text = ""
        try:
            async for event in runner.run_async(
                user_id="user",
                session_id=session_id,
                new_message=user_content,
            ):
                if event.is_final_response() and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_text += part.text
        except Exception as exc:
            if sys.version_info >= (3, 11) and isinstance(exc, BaseExceptionGroup):
                parts_list = [f"{type(e).__name__}: {e}" for e in exc.exceptions]
                msg = " | ".join(parts_list)
            else:
                msg = str(exc)
            return f"Error del agente de visión: {msg}"

        return final_text or "No se recibió respuesta del agente ADK."

    return asyncio.run(_run())
