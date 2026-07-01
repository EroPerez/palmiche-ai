import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from ..schemas import WSChatRequest, WSChatResponse

router = APIRouter(tags=["Chat"])

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    agent = websocket.app.state.agent

    try:
        while True:
            data = await websocket.receive_text()

            try:
                # Validate input
                req = WSChatRequest.parse_raw(data)
            except ValidationError as e:
                resp = WSChatResponse(type="error", content=f"Invalid request: {e}")
                await websocket.send_text(resp.json())
                continue

            if req.type != "text":
                await websocket.send_text(
                    WSChatResponse(
                        type="error",
                        content=f"Unsupported request type: {req.type}",
                    ).json()
                )
                continue

            # Start event
            await websocket.send_text(WSChatResponse(type="start", content="").json())

            try:
                # Execute chat logic in a thread to avoid blocking the asyncio event loop
                response_text = await asyncio.to_thread(agent.chat, req.message)

                # For a simple, functional first version, we simulate streaming
                # by sending chunks (or just the whole text in one stream block).
                # A robust version would integrate directly with the LLM's stream generator.
                # Simulated streaming (word by word) to show UI animations
                words = response_text.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    await websocket.send_text(WSChatResponse(type="stream", content=chunk).json())
                    await asyncio.sleep(0.01)  # small delay for UI effect

                # End event
                await websocket.send_text(WSChatResponse(type="end", content=response_text).json())

            except Exception as exc:
                resp = WSChatResponse(type="error", content=f"Agent Error: {exc}")
                await websocket.send_text(resp.json())

    except WebSocketDisconnect:
        print("Cliente Web desconectado.")
