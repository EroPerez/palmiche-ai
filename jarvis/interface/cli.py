from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich import box

console = Console()


def print_banner(name: str = "Jarvis", backend: str = "anthropic"):
    """Print the Jarvis startup banner with name, version, and active backend."""
    backend_label = {
        "adk":       "[yellow]Google ADK + Claude[/yellow]",
        "gemini":    "[green]Google ADK + Gemini[/green]",
        "anthropic": "[blue]Anthropic SDK[/blue]",
        "ollama":    "[magenta]Ollama (local)[/magenta]",
    }.get(backend, f"[dim]{backend}[/dim]")

    art = (
        f"[bold cyan]  {name}[/bold cyan]  [dim]v1.0[/dim]  "
        f"[dim]backend:[/dim] {backend_label}\n"
        f"  [dim]Just A Rather Very Intelligent System[/dim]\n\n"
        f"  [dim]Escribe [bold]salir[/bold] para terminar "
        f"| [bold]limpiar[/bold] para borrar historial"
        f"| [bold]/voz[/bold] para alternar modo voz[/dim]"
    )
    console.print()
    console.print(
        Panel(art, border_style="cyan", box=box.DOUBLE_EDGE, padding=(0, 2))
    )
    console.print()


def get_user_input() -> str:
    """Prompt the user for input and return the entered text."""
    return Prompt.ask("[bold cyan]Tú[/bold cyan]")


def print_jarvis_response(text: str, name: str = "Jarvis"):
    """Render the assistant's response inside a Rich panel with Markdown formatting."""
    console.print()
    console.print(
        Panel(
            Markdown(text),
            title=f"[bold green]{name}[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )
    console.print()


def print_thinking(name: str = "Jarvis"):
    """Print a dim 'processing…' indicator while the agent is running."""
    console.print(f"[dim italic]{name} procesando...[/dim italic]")


def print_error(message: str):
    """Print an error message in bold red."""
    console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_info(message: str):
    """Print a dim informational message."""
    console.print(f"[dim]{message}[/dim]")
