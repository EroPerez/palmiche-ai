from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class HealthResponse(BaseModel):
    status: str = "ok"
    agent: str
    version: str = "1.0.0"

class ChatMessage(BaseModel):
    role: str
    content: str

class HistoryResponse(BaseModel):
    messages: List[ChatMessage]

class WSChatRequest(BaseModel):
    message: str
    type: Literal["text", "audio"] = "text"

class WSChatResponse(BaseModel):
    type: Literal["start", "stream", "end", "error"]
    content: str
