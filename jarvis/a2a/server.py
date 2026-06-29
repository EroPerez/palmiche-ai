"""A2A HTTP server — exposes the Jarvis agent via the Google Agent2Agent protocol.

This module is kept for backward compatibility. The A2A protocol routes now
live in :mod:`jarvis.api.routers.a2a` and are mounted on the shared FastAPI
application alongside the Web UI routes.

Start with:
    python -m jarvis --serve-a2a [--a2a-host 0.0.0.0] [--a2a-port 8080]

Combine with the Web UI on a single server:
    python -m jarvis --web --serve-a2a

Other A2A-compatible agents can discover this one via:
    GET http://host:port/.well-known/agent.json

And send tasks via JSON-RPC 2.0:
    POST http://host:port/a2a
"""
from __future__ import annotations

from .models import (  # noqa: F401 — re-export for external consumers
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Artifact,
    Message,
    Task,
    TaskStatus,
    jsonrpc_error,
    jsonrpc_result,
)


def run_a2a_server(
    agent_factory,
    host: str = "0.0.0.0",
    port: int = 8080,
    name: str = "Jarvis",
    description: str = "",
) -> None:
    """Start a standalone A2A server (delegates to the shared FastAPI app).

    Prefer ``python -m jarvis --serve-a2a`` (optionally with ``--web``) which
    uses the unified server in :mod:`jarvis.api.server`.
    """
    from ..api.server import run_web_server

    run_web_server(
        agent=agent_factory(),
        host=host,
        port=port,
        agent_factory=agent_factory,
        name=name,
    )
