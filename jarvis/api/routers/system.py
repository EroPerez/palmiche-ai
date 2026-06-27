from fastapi import APIRouter, Request
from ..schemas import HealthResponse, HistoryResponse, ChatMessage

router = APIRouter(prefix="/api/v1", tags=["System"])

@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    agent = request.app.state.agent
    # agent.name isn't directly exposed as a property in all agents,
    # but we can try to extract it, or use a default.
    name = getattr(agent, "name", "Jarvis")
    return HealthResponse(agent=name)

@router.get("/history", response_model=HistoryResponse)
async def get_history(request: Request):
    agent = request.app.state.agent
    messages = agent.history.get_messages()
    
    formatted_msgs = []
    for msg in messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            # We filter out complex tool_use messages for the simple UI history for now
            if isinstance(msg["content"], str):
                formatted_msgs.append(ChatMessage(role=msg["role"], content=msg["content"]))
                
    return HistoryResponse(messages=formatted_msgs)
