#!/usr/bin/env python3
"""Jarvis - Personal AI Laptop Assistant"""
import sys
import argparse


def parse_args():
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Jarvis - Tu asistente AI personal para la laptop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m jarvis                          # Modo interactivo (backend por defecto)
  python -m jarvis --backend adk            # Google ADK + Claude (via LiteLLM)
  python -m jarvis --backend gemini         # Google ADK + Gemini nativo
  python -m jarvis --tray                   # Bandeja del sistema + ventana de chat
  python -m jarvis --web                    # Web UI (FastAPI + Vue 3)
  python -m jarvis --web --serve-a2a        # Web UI + A2A en un solo servidor
  python -m jarvis --serve-a2a              # Solo A2A (sin frontend)
  python -m jarvis -q '¿cuánta RAM tengo?' # Consulta rápida y salir
  python -m jarvis --voice                  # Con reconocimiento de voz
  python -m jarvis --clear                  # Borrar historial y salir
  python -m jarvis --name 'Viernes'         # Cambiar el nombre del asistente
  python -m jarvis --welcome 'Hola, jefe'   # Frase de bienvenida personalizada
  python -m jarvis --goodbye 'Nos vemos'    # Frase de despedida personalizada
  python -m jarvis --no-splash              # Sin pantalla de bienvenida animada
        """,
    )
    parser.add_argument("--voice", action="store_true", help="Activar reconocimiento de voz")
    parser.add_argument("--query", "-q", type=str, help="Ejecutar consulta única y salir")
    parser.add_argument("--clear", action="store_true", help="Borrar historial y salir")
    parser.add_argument("--tray", action="store_true", help="Iniciar en bandeja del sistema con ventana de chat")
    parser.add_argument(
        "--wake-word",
        type=str,
        default=None,
        metavar="PALABRA",
        help="Palabra de activación por voz en modo --tray (default: palmiche)",
    )
    parser.add_argument(
        "--backend",
        choices=["adk", "anthropic", "gemini", "ollama"],
        default=None,
        help=(
            "Backend del agente. 'adk' (default) usa Google ADK + LiteLLM y "
            "soporta cualquier proveedor según JARVIS_MODEL "
            "(ej. anthropic/claude-*, openai/gpt-*, gemini-*, ollama_chat/*). "
            "'anthropic' es el loop nativo sin ADK. "
            "'gemini' y 'ollama' son aliases de compatibilidad."
        ),
    )
    parser.add_argument(
        "--welcome",
        type=str,
        default=None,
        metavar="FRASE",
        help="Frase de bienvenida del splash (default: JARVIS_WELCOME_MESSAGE)",
    )
    parser.add_argument(
        "--goodbye",
        type=str,
        default=None,
        metavar="FRASE",
        help="Frase de despedida al salir. Usa {name} para el nombre del asistente.",
    )
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="No mostrar la pantalla de bienvenida animada (splash screen)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        metavar="NOMBRE",
        help="Nombre del asistente (default: JARVIS_NAME)",
    )

    # ------------------------------------------------------------------
    # Web UI flags
    # ------------------------------------------------------------------
    web = parser.add_argument_group("Web UI")
    web.add_argument(
        "--web",
        "--serve-web",
        action="store_true",
        dest="web",
        help="Iniciar Web UI (FastAPI + Vue 3) en el navegador",
    )
    web.add_argument(
        "--web-host",
        type=str,
        default="127.0.0.1",
        help="Host del servidor Web UI (default: 127.0.0.1)",
    )
    web.add_argument(
        "--web-port",
        type=int,
        default=8000,
        help="Puerto del servidor Web UI (default: 8000)",
    )
    web.add_argument(
        "--web-dev",
        action="store_true",
        help="Modo desarrollo: Backend + Vite dev server para hot-reload del frontend",
    )

    # ------------------------------------------------------------------
    # A2A (Agent-to-Agent) flags
    # ------------------------------------------------------------------
    a2a = parser.add_argument_group("A2A — Agent-to-Agent protocol")
    a2a.add_argument(
        "--serve-a2a",
        action="store_true",
        help="Iniciar como servidor A2A (Google Agent2Agent protocol) en HTTP",
    )
    a2a.add_argument(
        "--a2a-host",
        type=str,
        default=None,
        metavar="HOST",
        help="Host del servidor A2A (default: JARVIS_A2A_HOST / 0.0.0.0)",
    )
    a2a.add_argument(
        "--a2a-port",
        type=int,
        default=None,
        metavar="PUERTO",
        help="Puerto del servidor A2A (default: JARVIS_A2A_PORT / 8080)",
    )
    a2a.add_argument(
        "--connect-a2a",
        action="append",
        default=[],
        metavar="URL",
        help="URL de un agente A2A remoto a conectar como herramienta (puede repetirse)",
    )

    # ------------------------------------------------------------------
    # MCP (Model Context Protocol) flags
    # ------------------------------------------------------------------
    mcp = parser.add_argument_group("MCP — Model Context Protocol")
    mcp.add_argument(
        "--serve-mcp",
        action="store_true",
        help=(
            "Iniciar como servidor MCP en stdio "
            "(compatible con Claude Desktop, Cursor, etc.)"
        ),
    )
    mcp.add_argument(
        "--connect-mcp",
        action="append",
        default=[],
        metavar="SPEC",
        help=(
            "Conectar a un servidor MCP como cliente. "
            "SPEC puede ser un comando stdio ('npx -y @mcp/server /tmp') "
            "o una URL SSE ('http://localhost:3000'). Puede repetirse."
        ),
    )

    return parser.parse_args()


def _build_dynamic_registry(a2a_urls: list[str], mcp_specs: list[str]):
    """Build a DynamicToolRegistry if any extra tools are configured, else return None.

    Extra tools come from A2A agents, MCP servers, and the user's plain-text
    custom tools file (JARVIS_CUSTOM_TOOLS_FILE).
    """
    from .config import JARVIS_CUSTOM_TOOLS_FILE

    has_custom_file = JARVIS_CUSTOM_TOOLS_FILE.is_file()
    if not a2a_urls and not mcp_specs and not has_custom_file:
        return None

    from .tools.dynamic import DynamicToolRegistry

    registry = DynamicToolRegistry()
    loaded_count = 0

    for url in a2a_urls:
        from .a2a.client import load_a2a_agent
        tool_name = load_a2a_agent(registry, url)
        print(f"  [A2A] Agente conectado: {url} → herramienta '{tool_name}'")
        loaded_count += 1

    for spec in mcp_specs:
        from .mcp_support.client import load_mcp_server
        names = load_mcp_server(registry, spec)
        if names:
            print(f"  [MCP] Servidor conectado: {spec} → {len(names)} herramienta(s)")
            loaded_count += len(names)

    if has_custom_file:
        from .tools.custom import load_custom_tools
        names = load_custom_tools(registry)
        if names:
            print(
                f"  [tools] Herramientas personalizadas cargadas desde "
                f"{JARVIS_CUSTOM_TOOLS_FILE}: {', '.join(names)}"
            )
            loaded_count += len(names)

    if loaded_count:
        print(f"  Herramientas dinámicas cargadas: {loaded_count} adicional(es)")

    return registry


def _build_agent(backend: str, name: str, registry=None, mcp_specs=None):
    """Construct the agent for the given backend, using *name* as the assistant name.

    'adk' (default) → JarvisUniversalADKAgent with JARVIS_MODEL (LiteLLM format).
                       Supports any provider: Anthropic, OpenAI, Gemini, Ollama, Groq…
    'anthropic'      → JarvisAgent (lightweight Anthropic SDK loop, no ADK).
    'gemini'         → compatibility alias: ADK universal with native Gemini model.
    'ollama'         → compatibility alias: ADK universal with ollama_chat/... model.

    Args:
        registry: Optional DynamicToolRegistry with extra tools (A2A/MCP/custom).
        mcp_specs: Optional list of MCP specs for native ADK McpToolsets.
    """
    backend = backend.strip().lower()

    if backend == "anthropic":
        # Pure Anthropic SDK loop — kept for users who prefer no ADK overhead.
        # JarvisAgent auto-strips any "anthropic/" prefix from JARVIS_MODEL so
        # the bare model name is sent to the Anthropic SDK.
        from .brain.agent import JarvisAgent
        return JarvisAgent(name=name, registry=registry)

    if backend == "gemini":
        # Compatibility alias: universal ADK agent with native Gemini model string.
        from .config import JARVIS_GEMINI_MODEL, GOOGLE_API_KEY, JARVIS_API_KEY
        model = JARVIS_GEMINI_MODEL  # bare gemini name → ADK native (no LiteLLM)
        api_key = JARVIS_API_KEY or GOOGLE_API_KEY
        from .brain.adk_universal import JarvisUniversalADKAgent
        return JarvisUniversalADKAgent(
            name=name, registry=registry, mcp_specs=mcp_specs,
            _model_override=model,
            _api_key_override=api_key or None,
        )

    if backend == "ollama":
        # Compatibility alias: universal ADK agent with Ollama via LiteLLM.
        from .config import JARVIS_OLLAMA_HOST, JARVIS_OLLAMA_MODEL, JARVIS_BASE_URL
        model = f"ollama_chat/{JARVIS_OLLAMA_MODEL}"
        base_url = JARVIS_BASE_URL or JARVIS_OLLAMA_HOST
        from .brain.adk_universal import JarvisUniversalADKAgent
        return JarvisUniversalADKAgent(
            name=name, registry=registry, mcp_specs=mcp_specs,
            _model_override=model,
            _base_url_override=base_url,
        )

    if backend == "adk":
        from .brain.adk_universal import JarvisUniversalADKAgent
        return JarvisUniversalADKAgent(name=name, registry=registry, mcp_specs=mcp_specs)

    raise ValueError(
        f"Backend inválido: '{backend}'. "
        "Opciones: 'adk' (default, multi-proveedor), 'anthropic', 'gemini', 'ollama'."
    )


def main():
    """Entry point: parse args, validate API keys, build agent, and run the selected mode."""
    args = parse_args()

    from .config import (
        A2A_AGENTS,
        A2A_HOST,
        A2A_PORT,
        ANTHROPIC_API_KEY,
        GOOGLE_API_KEY,
        JARVIS_API_KEY,
        JARVIS_BACKEND,
        JARVIS_BASE_URL,
        JARVIS_GOODBYE_MESSAGE,
        JARVIS_MODEL,
        JARVIS_NAME,
        JARVIS_SPLASH_ENABLED,
        JARVIS_WAKE_WORD,
        JARVIS_WELCOME_MESSAGE,
        MCP_SERVERS,
        VOICE_ENABLED,
    )
    from .interface.cli import (
        print_banner,
        get_user_input,
        print_jarvis_response,
        print_thinking,
        print_error,
        print_info,
        console,
    )

    backend = (args.backend or JARVIS_BACKEND).strip().lower()

    # Assistant name: CLI param overrides env, env overrides default.
    name = args.name if args.name is not None else JARVIS_NAME

    # ------------------------------------------------------------------
    # MCP server mode — takes over stdio, no interactive CLI
    # ------------------------------------------------------------------
    if args.serve_mcp:
        from .mcp_support.server import run_mcp_server
        print(f"  Iniciando servidor MCP stdio para '{name}'...", file=sys.stderr)
        run_mcp_server()
        return

    # Key validation per backend
    if backend == "anthropic" and not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY no configurada.")
        print("  1. Copia jarvis/.env.example a jarvis/.env")
        print("  2. Edita jarvis/.env y agrega tu clave de API")
        sys.exit(1)
    if backend == "gemini" and not (JARVIS_API_KEY or GOOGLE_API_KEY):
        print("[ERROR] Ninguna API key configurada para el backend Gemini.")
        print("  Agrega a jarvis/.env: JARVIS_API_KEY=tu-key  (o GOOGLE_API_KEY=tu-key)")
        sys.exit(1)
    if backend == "adk":
        # Use the same normalization as the universal agent to determine the provider
        # so bare names like "claude-*" or "gpt-*" resolve correctly.
        from .brain.adk_universal import _normalize_model_str
        normalized = _normalize_model_str(JARVIS_MODEL)
        model_provider = normalized.split("/")[0].lower() if "/" in normalized else ""
        local_providers = {"ollama", "ollama_chat"}
        needs_key = model_provider not in local_providers and bool(model_provider)
        has_key = bool(JARVIS_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY)
        if needs_key and not has_key and not JARVIS_BASE_URL:
            print(f"[ERROR] No se encontró una API key para el modelo '{JARVIS_MODEL}'.")
            print("  Agrega a jarvis/.env: JARVIS_API_KEY=tu-api-key")
            print("  O usa la variable específica del proveedor (ANTHROPIC_API_KEY, GOOGLE_API_KEY, etc.)")
            sys.exit(1)
    # 'ollama' validates its own connection at construction time

    # Collect A2A and MCP client specs (CLI args override/extend env vars)
    a2a_urls = list(A2A_AGENTS) + list(args.connect_a2a)
    mcp_specs = list(MCP_SERVERS) + list(args.connect_mcp)

    # Build dynamic registry if remote tools are configured.
    # For ADK backends, MCP tools use the native McpToolset so they're
    # passed separately — the registry handles A2A and custom tools only.
    # ADK backends (adk, gemini, ollama) consume mcp_specs as native McpToolsets,
    # so exclude them from the sync dynamic registry to avoid duplicate connections.
    _adk_backends = {"adk", "gemini", "ollama"}
    registry = _build_dynamic_registry(a2a_urls, mcp_specs if backend not in _adk_backends else [])

    try:
        agent = _build_agent(backend, name, registry=registry, mcp_specs=mcp_specs)
    except (ImportError, ValueError) as e:
        print_error(str(e))
        sys.exit(1)

    # ------------------------------------------------------------------
    # Web UI / A2A server mode — single FastAPI server for both
    # ------------------------------------------------------------------
    if args.web or args.web_dev or args.serve_a2a:
        web_host = args.web_host
        web_port = args.web_port

        if args.serve_a2a:
            web_host = args.a2a_host or web_host
            web_port = args.a2a_port or web_port

        agent_factory = None
        if args.serve_a2a:
            def agent_factory():
                return _build_agent(backend, name, registry=registry)

        if args.web_dev:
            from .interface.web import run_web_dev
            run_web_dev(agent, host=web_host, port=web_port, agent_factory=agent_factory, name=name)
        else:
            from .interface.web import run_web
            run_web(agent, host=web_host, port=web_port, agent_factory=agent_factory, name=name)
        return

    voice_on = args.voice or VOICE_ENABLED

    # Welcome/goodbye phrases: CLI param overrides env, env overrides default.
    welcome_message = args.welcome if args.welcome is not None else JARVIS_WELCOME_MESSAGE
    goodbye_template = args.goodbye if args.goodbye is not None else JARVIS_GOODBYE_MESSAGE
    splash_on = JARVIS_SPLASH_ENABLED and not args.no_splash

    def _goodbye() -> str:
        """Render the goodbye phrase, expanding the optional {name} placeholder."""
        try:
            return goodbye_template.format(name=name)
        except (KeyError, IndexError, ValueError, AttributeError):
            return goodbye_template

    if args.clear:
        if hasattr(agent, "clear"):
            agent.clear()
        else:
            agent.history.clear()
        print_info("Historial borrado.")
        return

    if args.query:
        print_thinking(name)
        response = agent.chat(args.query)
        print_jarvis_response(response, name)
        if voice_on:
            from .interface.voice import speak
            speak(response)
        return

    # Tray mode
    if args.tray:
        try:
            from .interface.tray import run_tray
            wake_word = args.wake_word or JARVIS_WAKE_WORD
            run_tray(agent, name, wake_word=wake_word, welcome_message=welcome_message, goodbye_message=_goodbye())
        except (ImportError, RuntimeError) as e:
            print_error(str(e))
            sys.exit(1)
        return

    # Interactive CLI mode
    if splash_on:
        from .interface.splash import show_splash
        show_splash(console, name, welcome_message)
    print_banner(name, backend)

    while True:
        try:
            if voice_on:
                from .interface.voice import listen
                print_info("🎤 Escuchando... (di algo o presiona Ctrl+C para escribir)")
                try:
                    text = listen()
                except KeyboardInterrupt:
                    text = get_user_input()
                if text:
                    console.print(f"[bold cyan]Tú:[/bold cyan] {text}")
                else:
                    print_info("No se detectó voz. Intenta de nuevo o escribe /voz para desactivar.")
                    text = get_user_input()
            else:
                text = get_user_input()

            if not text or not text.strip():
                continue

            cmd = text.strip().lower()
            if cmd in ("salir", "exit", "quit", "q", "bye", "adios", "adiós"):
                if voice_on:
                    from .interface.voice import speak
                    speak(_goodbye())
                print_info(_goodbye())
                break

            if cmd in ("limpiar", "clear", "/clear"):
                if hasattr(agent, "clear"):
                    agent.clear()
                else:
                    agent.history.clear()
                console.clear()
                print_banner(name, backend)
                print_info("Historial borrado.")
                continue

            if cmd in ("voz", "/voz", "voice", "/voice"):
                was_voice_on = voice_on
                voice_on = not voice_on
                status = "activado 🎤" if voice_on else "desactivado ⌨️"
                msg = f"Modo voz {status}"
                print_info(msg)
                if voice_on or was_voice_on:
                    from .interface.voice import speak
                    speak(msg)
                continue

            print_thinking(name)
            response = agent.chat(text)
            print_jarvis_response(response, name)

            if voice_on:
                from .interface.voice import speak
                speak(response)

        except KeyboardInterrupt:
            print_info(f"\n{_goodbye()}")
            break
        except Exception as e:
            print_error(f"Error inesperado: {e}")


if __name__ == "__main__":
    main()
