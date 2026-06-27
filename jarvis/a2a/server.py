"""A2A HTTP server — exposes the Jarvis agent via the Google Agent2Agent protocol.

Start with:
    python -m jarvis --serve-a2a [--a2a-host 0.0.0.0] [--a2a-port 8080]

Other A2A-compatible agents can discover this one via:
    GET http://host:port/.well-known/agent.json

And send tasks via JSON-RPC 2.0:
    POST http://host:port/
"""
from __future__ import annotations

import asyncio
import json
import sys
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Artifact,
    Task,
    TaskStatus,
    jsonrpc_error,
    jsonrpc_result,
)


# Simple LRU session store (max 50 concurrent sessions).
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


def build_agent_card(name: str, host: str, port: int, description: str = "") -> AgentCard:
    url = f"http://{host}:{port}"
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


def run_a2a_server(
    agent_factory,
    host: str = "0.0.0.0",
    port: int = 8080,
    name: str = "Jarvis",
    description: str = "",
) -> None:
    """Start the A2A HTTP server (blocking call — runs until interrupted).

    Args:
        agent_factory: Callable() -> agent  (called once per new session)
        host: Bind address.
        port: TCP port.
        name: Agent display name (from config/CLI).
        description: Short description shown in the agent card.
    """
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse, StreamingResponse
        import uvicorn
    except ImportError:
        print(
            "[ERROR] El módulo 'fastapi' y/o 'uvicorn' no están instalados.\n"
            "  Instálalos con:  pip install 'palmiche-jarvis[a2a]'",
            file=sys.stderr,
        )
        sys.exit(1)

    app = FastAPI(title=f"{name} — A2A Server", version="1.0.0")
    card = build_agent_card(name, host if host != "0.0.0.0" else "localhost", port, description)
    sessions: _SessionStore = _SessionStore()
    tasks: dict[str, Task] = {}

    def _get_or_create_agent(session_id: str):
        agent = sessions.get(session_id)
        if agent is None:
            agent = agent_factory()
            sessions.set(session_id, agent)
        return agent

    # ------------------------------------------------------------------
    # Agent card discovery
    # ------------------------------------------------------------------

    @app.get("/.well-known/agent.json", tags=["A2A"])
    async def agent_card_endpoint() -> dict:
        return card.to_dict()

    # ------------------------------------------------------------------
    # JSON-RPC 2.0 dispatcher
    # ------------------------------------------------------------------

    @app.post("/", tags=["A2A"])
    async def jsonrpc_dispatch(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(jsonrpc_error(None, -32700, "Parse error"), status_code=400)

        method = body.get("method", "")
        params = body.get("params", {})
        rpc_id = body.get("id")

        if method == "tasks/send":
            return await _handle_tasks_send(params, rpc_id)
        elif method == "tasks/sendSubscribe":
            return await _handle_tasks_send_subscribe(params, rpc_id)
        elif method == "tasks/get":
            return await _handle_tasks_get(params, rpc_id)
        elif method == "tasks/cancel":
            return await _handle_tasks_cancel(params, rpc_id)
        else:
            return JSONResponse(
                jsonrpc_error(rpc_id, -32601, f"Method not found: {method}"), status_code=404
            )

    # ------------------------------------------------------------------
    # tasks/send  (synchronous — returns full result)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # tasks/sendSubscribe  (SSE streaming)
    # ------------------------------------------------------------------

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
            # Emit "working" status event
            working_event = _sse_event(
                "task_status_update",
                {
                    "id": task_id,
                    "status": {"state": "working", "timestamp": _now_iso()},
                    "final": False,
                },
            )
            yield working_event

            try:
                agent = _get_or_create_agent(session_id)
                response_text = await asyncio.to_thread(agent.chat, user_text)
                task.status = TaskStatus(state="completed", timestamp=_now_iso())
                task.artifacts = [Artifact.text(response_text)]

                artifact_event = _sse_event(
                    "task_artifact_update",
                    {
                        "id": task_id,
                        "artifact": Artifact.text(response_text).to_dict()
                        if hasattr(Artifact.text(response_text), "to_dict")
                        else {"parts": [{"type": "text", "text": response_text}], "index": 0},
                        "final": False,
                    },
                )
                yield artifact_event

                done_event = _sse_event(
                    "task_status_update",
                    {
                        "id": task_id,
                        "status": {"state": "completed", "timestamp": _now_iso()},
                        "final": True,
                    },
                )
                yield done_event

            except Exception as exc:
                task.status = TaskStatus(state="failed", timestamp=_now_iso())
                yield _sse_event(
                    "task_status_update",
                    {
                        "id": task_id,
                        "status": {"state": "failed", "timestamp": _now_iso()},
                        "error": str(exc),
                        "final": True,
                    },
                )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ------------------------------------------------------------------
    # tasks/get
    # ------------------------------------------------------------------

    async def _handle_tasks_get(params: dict, rpc_id: Any) -> JSONResponse:
        task_id = params.get("id")
        if not task_id or task_id not in tasks:
            return JSONResponse(jsonrpc_error(rpc_id, -32001, f"Task not found: {task_id}"))
        return JSONResponse(jsonrpc_result(rpc_id, tasks[task_id].to_dict()))

    # ------------------------------------------------------------------
    # tasks/cancel
    # ------------------------------------------------------------------

    async def _handle_tasks_cancel(params: dict, rpc_id: Any) -> JSONResponse:
        task_id = params.get("id")
        if not task_id or task_id not in tasks:
            return JSONResponse(jsonrpc_error(rpc_id, -32001, f"Task not found: {task_id}"))
        task = tasks[task_id]
        if task.status.state not in ("completed", "failed", "cancelled"):
            task.status = TaskStatus(state="cancelled", timestamp=_now_iso())
        return JSONResponse(jsonrpc_result(rpc_id, task.to_dict()))

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _extract_text(message_data: dict) -> str:
        parts = message_data.get("parts", [])
        for part in parts:
            if part.get("type") == "text":
                return part.get("text", "")
        return message_data.get("text", "")

    def _sse_event(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.get("/health", tags=["Info"])
    async def health() -> dict:
        return {"status": "ok", "agent": name}

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    print(f"  A2A server iniciando en http://{host}:{port}")
    print(f"  Agent card: http://{'localhost' if host == '0.0.0.0' else host}:{port}/.well-known/agent.json")
    uvicorn.run(app, host=host, port=port, log_level="warning")
