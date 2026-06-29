"""Web UI interface for Jarvis (FastAPI + Vue 3).

Features:
- FastAPI backend with WebSocket chat and REST endpoints
- Optional A2A protocol routes on the same server
- Vue 3 frontend (Composition API, Tailwind CSS, PWA)
- Browser Speech API for voice input/output
- Markdown rendering with syntax highlighting
- Siri-style waveform animations (idle / wake / thinking)
- Connection status overlay with auto-reconnect

Platform notes:
  Runs on any OS — requires a modern browser for the frontend.

Requires: pip install 'palmiche-jarvis[web]'
Optional: pnpm install   (in jarvis/frontend/ for development)
"""
import os
import subprocess
import sys
from typing import Callable, Optional


def run_web(
    agent,
    host: str = "127.0.0.1",
    port: int = 8000,
    agent_factory: Optional[Callable] = None,
    name: str = "Jarvis",
):
    """Start the Jarvis Web UI (FastAPI backend serving the Vue frontend).

    This is the main entry point for ``--web`` mode, analogous to
    :func:`jarvis.interface.tray.run_tray` for ``--tray`` mode.

    When *agent_factory* is provided, A2A protocol routes are also mounted
    on the same server — no need for a separate ``--serve-a2a`` process.
    """
    from ..api.server import run_web_server

    run_web_server(agent, host=host, port=port, agent_factory=agent_factory, name=name)


def run_web_dev(
    agent,
    host: str = "127.0.0.1",
    port: int = 8000,
    frontend_port: int = 3000,
    agent_factory: Optional[Callable] = None,
    name: str = "Jarvis",
):
    """Start backend + Vite dev server for local frontend development."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
    frontend_dir = os.path.abspath(frontend_dir)

    if not os.path.isdir(frontend_dir):
        print(f"[ERROR] Directorio frontend no encontrado: {frontend_dir}", file=sys.stderr)
        sys.exit(1)

    import threading

    def _run_backend():
        from ..api.server import run_web_server
        run_web_server(agent, host=host, port=port, agent_factory=agent_factory, name=name)

    backend_thread = threading.Thread(target=_run_backend, daemon=True)
    backend_thread.start()

    print(f"  Frontend Vite dev server en http://localhost:{frontend_port}")
    try:
        subprocess.run(
            ["pnpm", "run", "dev", "--", "--port", str(frontend_port)],
            cwd=frontend_dir,
            check=True,
        )
    except KeyboardInterrupt:
        print("\nCerrando servidores...")
    except FileNotFoundError:
        print(
            "[ERROR] pnpm no encontrado. Instala con: npm install -g pnpm",
            file=sys.stderr,
        )
        sys.exit(1)
