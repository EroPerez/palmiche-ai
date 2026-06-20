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
  python -m jarvis -q '¿cuánta RAM tengo?' # Consulta rápida y salir
  python -m jarvis --voice                  # Con reconocimiento de voz
  python -m jarvis --clear                  # Borrar historial y salir
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
        choices=["anthropic", "adk", "gemini", "ollama"],
        default=None,
        help=(
            "Backend: 'anthropic' (default), 'adk' (Google ADK+Claude), "
            "'gemini' (Google ADK+Gemini), 'ollama' (modelo local)"
        ),
    )
    return parser.parse_args()


def _build_agent(backend: str):
    """Construct the agent for the given backend.

    'adk' auto-selects Gemini when GOOGLE_API_KEY is set and
    ANTHROPIC_API_KEY is not, making it easy to run without Anthropic credentials.
    """
    backend = backend.strip().lower()

    if backend == "ollama":
        from .brain.ollama_agent import JarvisOllamaAgent
        return JarvisOllamaAgent()

    if backend == "gemini":
        from .brain.adk_agent import JarvisADKAgent
        return JarvisADKAgent(use_gemini=True)

    if backend == "adk":
        from .config import ANTHROPIC_API_KEY, GOOGLE_API_KEY
        use_gemini = bool(GOOGLE_API_KEY) and not bool(ANTHROPIC_API_KEY)
        from .brain.adk_agent import JarvisADKAgent
        return JarvisADKAgent(use_gemini=use_gemini)

    if backend == "anthropic":
        from .brain.agent import JarvisAgent
        return JarvisAgent()

    raise ValueError(f"Backend inválido: '{backend}'. Usa 'anthropic', 'adk', 'gemini' u 'ollama'.")


def main():
    """Entry point: parse args, validate API keys, build agent, and run the selected mode."""
    args = parse_args()

    from .config import ANTHROPIC_API_KEY, GOOGLE_API_KEY, JARVIS_NAME, VOICE_ENABLED, JARVIS_BACKEND, JARVIS_WAKE_WORD
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

    # Key validation per backend
    if backend == "anthropic" and not ANTHROPIC_API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY no configurada.")
        print("  1. Copia jarvis/.env.example a jarvis/.env")
        print("  2. Edita jarvis/.env y agrega tu clave de API")
        sys.exit(1)
    if backend == "gemini" and not GOOGLE_API_KEY:
        print("[ERROR] GOOGLE_API_KEY no configurada para el backend Gemini.")
        print("  Agrégala a jarvis/.env: GOOGLE_API_KEY=tu-key")
        sys.exit(1)
    # 'ollama' and 'adk' validate their own connections at construction time

    try:
        agent = _build_agent(backend)
    except (ImportError, ValueError) as e:
        print_error(str(e))
        sys.exit(1)

    voice_on = args.voice or VOICE_ENABLED

    if args.clear:
        agent.history.clear()
        print_info("Historial borrado.")
        return

    if args.query:
        print_thinking(JARVIS_NAME)
        response = agent.chat(args.query)
        print_jarvis_response(response, JARVIS_NAME)
        if voice_on:
            from .interface.voice import speak
            speak(response)
        return

    # Tray mode
    if args.tray:
        try:
            from .interface.tray import run_tray
            wake_word = args.wake_word or JARVIS_WAKE_WORD
            run_tray(agent, JARVIS_NAME, wake_word=wake_word)
        except (ImportError, RuntimeError) as e:
            print_error(str(e))
            sys.exit(1)
        return

    # Interactive CLI mode
    print_banner(JARVIS_NAME, backend)

    while True:
        try:
            if voice_on:
                from .interface.voice import listen
                text = listen()
                if text:
                    console.print(f"[bold cyan]Tú:[/bold cyan] {text}")
                else:
                    text = get_user_input()
            else:
                text = get_user_input()

            if not text or not text.strip():
                continue

            cmd = text.strip().lower()
            if cmd in ("salir", "exit", "quit", "q", "bye", "adios", "adiós"):
                print_info(f"{JARVIS_NAME} desconectado. Hasta luego.")
                break

            if cmd in ("limpiar", "clear", "/clear"):
                agent.history.clear()
                console.clear()
                print_banner(JARVIS_NAME, backend)
                print_info("Historial borrado.")
                continue

            print_thinking(JARVIS_NAME)
            response = agent.chat(text)
            print_jarvis_response(response, JARVIS_NAME)

            if voice_on:
                from .interface.voice import speak
                speak(response)

        except KeyboardInterrupt:
            print_info(f"\n{JARVIS_NAME} interrumpido. Hasta luego.")
            break
        except Exception as e:
            print_error(f"Error inesperado: {e}")


if __name__ == "__main__":
    main()
