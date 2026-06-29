import os
import sys
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import system, chat


def create_app(
    agent,
    agent_factory: Optional[Callable] = None,
    name: str = "Jarvis",
) -> FastAPI:
    """Create and configure the shared FastAPI application.

    Args:
        agent: Shared agent instance for the Web UI (chat, history, health).
        agent_factory: When provided, A2A protocol routes are mounted too.
                       Called once per A2A session to create an isolated agent.
        name: Agent display name (used in A2A agent card).
    """
    app = FastAPI(
        title="Jarvis API",
        description="Backend API for Palmiche Jarvis",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.agent = agent

    app.include_router(system.router)
    app.include_router(chat.router)

    if agent_factory is not None:
        from .routers.a2a import create_a2a_router
        a2a_router = create_a2a_router(agent_factory=agent_factory, name=name)
        app.include_router(a2a_router)

    dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.isdir(dist_path):
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse

        app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

        @app.get("/")
        async def serve_index():
            return FileResponse(os.path.join(dist_path, "index.html"))

        @app.get("/{catchall:path}")
        async def serve_fallback(catchall: str):
            return FileResponse(os.path.join(dist_path, "index.html"))

    return app


def run_web_server(
    agent,
    host: str = "127.0.0.1",
    port: int = 8000,
    agent_factory: Optional[Callable] = None,
    name: str = "Jarvis",
):
    """Run the shared FastAPI server using uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print(
            "[ERROR] Uvicorn no está instalado. "
            "Instala con: pip install uvicorn fastapi",
            file=sys.stderr,
        )
        sys.exit(1)

    app = create_app(agent, agent_factory=agent_factory, name=name)

    features = ["Web UI"]
    if agent_factory is not None:
        features.append("A2A")
    label = " + ".join(features)

    print(f"  Servidor ({label}) iniciando en http://{host}:{port}")
    if agent_factory is not None:
        base = f"http://{'localhost' if host == '0.0.0.0' else host}:{port}"
        print(f"  A2A agent card: {base}/.well-known/agent.json")
        print(f"  A2A JSON-RPC:   {base}/a2a")

    uvicorn.run(app, host=host, port=port, log_level="info")
