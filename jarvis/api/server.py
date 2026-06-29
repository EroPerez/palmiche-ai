import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routers import system, chat

def create_app(agent) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Jarvis API",
        description="Backend API for Palmiche Jarvis Web UI",
        version="1.0.0",
    )

    # Enable CORS for the Vue frontend during development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, this should be restricted
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store the agent in app.state so routers can access it
    app.state.agent = agent

    # Include routers
    app.include_router(system.router)
    app.include_router(chat.router)

    # Serve static frontend in production if dist/ exists
    import os
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
    if os.path.isdir(dist_path):
        app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

        @app.get("/")
        async def serve_index():
            return FileResponse(os.path.join(dist_path, "index.html"))

        @app.get("/{catchall:path}")
        async def serve_fallback(catchall: str):
            # Fallback to index.html for Vue Router (if used in future)
            return FileResponse(os.path.join(dist_path, "index.html"))

    return app

def run_web_server(agent, host: str = "127.0.0.1", port: int = 8000):
    """Run the FastAPI web server using uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print(
            "[ERROR] Uvicorn no está instalado. "
            "Instala con: pip install uvicorn fastapi",
            file=sys.stderr,
        )
        sys.exit(1)

    app = create_app(agent)
    print(f"🚀 Servidor Web (API) iniciando en http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
