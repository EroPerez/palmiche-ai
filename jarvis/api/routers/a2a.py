"""A2A (Agent-to-Agent) router — Google Agent2Agent protocol over the shared FastAPI app.

Endpoints:
  GET  /.well-known/agent.json   — Agent card discovery
  POST /                         — JSON-RPC 2.0 dispatcher (tasks/send, tasks/sendSubscribe, etc.)
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ...a2a.models import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Artifact,
    Task,
    TaskStatus,
    jsonrpc_error,
    jsonrpc_result,
)


class _SessionStore:
    def __init__(self, max_size: int = 50):
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._max = max_size

    def get(self, key: str) -> Optional[Any]:
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._store.move_to_end(key)
        if len(self._store) > self._max:
            self._store.popitem(last=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_text(message_data: dict) -> str:
    parts = message_data.get("parts", [])
    for part in parts:
        if part.get("type") == "text":
            return part.get("text", "")
    return message_data.get("text", "")


def _sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def build_agent_card(name: str, url: str, description: str = "") -> AgentCard:
    return AgentCard(
        name=name,
        description=description or f"{name} — Asistente AI personal (Palmiche J.A.R.V.I.S.)",
        url=url,
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="general-assistant",
                name="General Assistant",
                description=(
                    "Responds to natural-language queries, executes system tools "
                    "(files, apps, web, shell, calendar, weather, notes, etc.)"
                ),
                tags=["general", "system", "productivity"],
            )
        ],
    )


def create_a2a_router(
    agent_factory: Callable,
    name: str = "Jarvis",
    description: str = "",
) -> APIRouter:
    """Build a FastAPI router with A2A protocol endpoints.

    Args:
        agent_factory: Callable that returns a fresh agent per session.
        name: Agent display name for the agent card.
        description: Short description for the agent card.
    """
    router = APIRouter(tags=["A2A"])
    sessions: _SessionStore = _SessionStore()
    tasks: dict[str, Task] = {}

    def _get_or_create_agent(session_id: str):
        agent = sessions.get(session_id)
        if agent is None:
            agent = agent_factory()
            sessions.set(session_id, agent)
        return agent

    @router.get("/.well-known/agent.json")
    async def agent_card_endpoint(request: Request) -> dict:
        url = str(request.base_url).rstrip("/")
        card = build_agent_card(name, url, description)
        return card.to_dict()

    @router.post("/a2a")
    async def jsonrpc_dispatch(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(jsonrpc_error(None, -32700, "Parse error"), status_code=400)

        method = body.get("method", "")
        params = body.get("params", {})
        rpc_id = body.get("id")

        handlers = {
            "tasks/send": _handle_tasks_send,
            "tasks/sendSubscribe": _handle_tasks_send_subscribe,
            "tasks/get": _handle_tasks_get,
            "tasks/cancel": _handle_tasks_cancel,
        }

        handler = handlers.get(method)
        if handler is None:
            return JSONResponse(
                jsonrpc_error(rpc_id, -32601, f"Method not found: {method}"), status_code=404
            )
        return await handler(params, rpc_id)

    async def _handle_tasks_send(params: dict, rpc_id: Any) -> JSONResponse:
        task_id = params.get("id") or str(uuid.uuid4())
        session_id = params.get("sessionId") or str(uuid.uuid4())
        message_data = params.get("message", {})
        user_text = _extract_text(message_data)

        task = Task(
            id=task_id,
            sessionId=session_id,
            status=TaskStatus(state="working", timestamp=_now_iso()),
        )
        tasks[task_id] = task

        try:
            agent = _get_or_create_agent(session_id)
            response_text = await asyncio.to_thread(agent.chat, user_text)
            task.status = TaskStatus(state="completed", timestamp=_now_iso())
            task.artifacts = [Artifact.text(response_text)]
        except Exception as exc:
            task.status = TaskStatus(state="failed", timestamp=_now_iso())
            return JSONResponse(jsonrpc_error(rpc_id, -32603, str(exc)))

        return JSONResponse(jsonrpc_result(rpc_id, task.to_dict()))

    async def _handle_tasks_send_subscribe(params: dict, rpc_id: Any):
        task_id = params.get("id") or str(uuid.uuid4())
        session_id = params.get("sessionId") or str(uuid.uuid4())
        message_data = params.get("message", {})
        user_text = _extract_text(message_data)

        task = Task(
            id=task_id,
            sessionId=session_id,
            status=TaskStatus(state="working", timestamp=_now_iso()),
        )
        tasks[task_id] = task

        async def event_stream():
            yield _sse_event(
                "task_status_update",
                {"id": task_id, "status": {"state": "working", "timestamp": _now_iso()}, "final": False},
            )

            try:
                agent = _get_or_create_agent(session_id)
                response_text = await asyncio.to_thread(agent.chat, user_text)
                task.status = TaskStatus(state="completed", timestamp=_now_iso())
                task.artifacts = [Artifact.text(response_text)]

                yield _sse_event(
                    "task_artifact_update",
                    {
                        "id": task_id,
                        "artifact": {"parts": [{"type": "text", "text": response_text}], "index": 0},
                        "final": False,
                    },
                )
                yield _sse_event(
                    "task_status_update",
                    {"id": task_id, "status": {"state": "completed", "timestamp": _now_iso()}, "final": True},
                )

            except Exception as exc:
                task.status = TaskStatus(state="failed", timestamp=_now_iso())
                yield _sse_event(
                    "task_status_update",
                    {"id": task_id, "status": {"state": "failed", "timestamp": _now_iso()}, "error": str(exc), "final": True},
                )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def _handle_tasks_get(params: dict, rpc_id: Any) -> JSONResponse:
        task_id = params.get("id")
        if not task_id or task_id not in tasks:
            return JSONResponse(jsonrpc_error(rpc_id, -32001, f"Task not found: {task_id}"))
        return JSONResponse(jsonrpc_result(rpc_id, tasks[task_id].to_dict()))

    async def _handle_tasks_cancel(params: dict, rpc_id: Any) -> JSONResponse:
        task_id = params.get("id")
        if not task_id or task_id not in tasks:
            return JSONResponse(jsonrpc_error(rpc_id, -32001, f"Task not found: {task_id}"))
        task = tasks[task_id]
        if task.status.state not in ("completed", "failed", "cancelled"):
            task.status = TaskStatus(state="cancelled", timestamp=_now_iso())
        return JSONResponse(jsonrpc_result(rpc_id, task.to_dict()))

    return router
