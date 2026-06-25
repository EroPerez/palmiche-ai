"""A2A protocol data models (Agent2Agent spec by Google).

Minimal implementation covering the core task-exchange lifecycle.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Message parts
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TextPart:
    text: str
    type: str = "text"


# ---------------------------------------------------------------------------
# Task lifecycle
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A single conversational turn (user or agent)."""
    role: str  # "user" | "agent"
    parts: list[dict] = field(default_factory=list)

    @classmethod
    def user(cls, text: str) -> "Message":
        return cls(role="user", parts=[{"type": "text", "text": text}])

    @classmethod
    def agent(cls, text: str) -> "Message":
        return cls(role="agent", parts=[{"type": "text", "text": text}])

    def first_text(self) -> str:
        for part in self.parts:
            if part.get("type") == "text":
                return part.get("text", "")
        return ""


@dataclass
class TaskStatus:
    state: str  # submitted | working | completed | failed | cancelled
    message: Optional[dict] = None
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class Artifact:
    parts: list[dict] = field(default_factory=list)
    index: int = 0
    name: Optional[str] = None

    @classmethod
    def text(cls, content: str) -> "Artifact":
        return cls(parts=[{"type": "text", "text": content}])

    def first_text(self) -> str:
        for part in self.parts:
            if part.get("type") == "text":
                return part.get("text", "")
        return ""


@dataclass
class Task:
    id: str
    status: TaskStatus = field(default_factory=lambda: TaskStatus(state="submitted"))
    sessionId: str = field(default_factory=lambda: str(uuid.uuid4()))
    artifacts: list[Artifact] = field(default_factory=list)
    history: list[Message] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Agent card (discovery / /.well-known/agent.json)
# ---------------------------------------------------------------------------

@dataclass
class AgentCapabilities:
    streaming: bool = True
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


@dataclass
class AgentSkill:
    id: str
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class AgentCard:
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    skills: list[AgentSkill] = field(default_factory=list)
    defaultInputModes: list[str] = field(default_factory=lambda: ["text"])
    defaultOutputModes: list[str] = field(default_factory=lambda: ["text"])

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

def jsonrpc_result(rpc_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


def jsonrpc_error(rpc_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": code, "message": message}}
