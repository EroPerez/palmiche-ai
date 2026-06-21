"""Animated green splash screen for Jarvis.

Renders a short equalizer-style animation in shades of green directly in the
terminal using Rich, followed by the configurable welcome phrase. The whole
sequence is purely cosmetic and degrades gracefully on terminals that do not
support ANSI control sequences.
"""
import math
import time

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Green gradient (dim → bright) used to color the animated bars.
_GREEN_GRADIENT = [
    "#0b3d0b",
    "#13641a",
    "#1f8a2b",
    "#2fb344",
    "#4ade5e",
    "#86efac",
]

_ASCII_NAME = r"""
   ___  ___   _____   _   _ ___ ___
  |_  |/ _ \ |  _  | | | | |_ _/ __|
   _| / /_\ \| |/| | | |_| || |\__ \
  |___|\___,_|_/ |_|  \___/|___|___/
""".strip("\n")


def _bar_block(level: float) -> tuple[str, str]:
    """Return a (glyph, color) pair for a vertical bar at *level* in [0, 1]."""
    blocks = " ▁▂▃▄▅▆▇█"
    idx = max(0, min(len(blocks) - 1, int(level * (len(blocks) - 1))))
    color = _GREEN_GRADIENT[max(0, min(len(_GREEN_GRADIENT) - 1, int(level * (len(_GREEN_GRADIENT) - 1))))]
    return blocks[idx], color


def _frame(t: float, name: str, n_bars: int = 28) -> Group:
    """Build a single animation frame at virtual time *t*."""
    bars = Text(justify="center")
    for i in range(n_bars):
        phase = i * (2 * math.pi / n_bars)
        wave = math.sin(t * 0.9 + phase) * 0.5
        wave += math.sin(t * 0.55 + phase * 1.7) * 0.3
        level = max(0.05, min(1.0, 0.55 + wave))
        glyph, color = _bar_block(level)
        bars.append(glyph + glyph, style=f"bold {color}")

    title = Text(name.upper(), justify="center", style="bold #4ade5e")
    subtitle = Text(
        "Just A Rather Very Intelligent System",
        justify="center",
        style="dim #86efac",
    )
    return Group(bars, Text(""), title, subtitle, Text(""), bars)


def show_splash(
    console: Console,
    name: str = "Jarvis",
    welcome_message: str = "",
    duration: float = 1.8,
) -> None:
    """Play the green splash animation, then print the welcome phrase.

    *duration* is the animation length in seconds. The function returns once the
    animation finishes; the welcome phrase (if any) is printed afterwards in a
    bordered green panel.
    """
    fps = 24
    n_frames = max(1, int(duration * fps))
    interval = 1.0 / fps

    try:
        with Live(console=console, refresh_per_second=fps, transient=True) as live:
            for f in range(n_frames):
                panel = Panel(
                    Align.center(_frame(f * 0.45, name)),
                    border_style="green",
                    box=box.HEAVY,
                    padding=(1, 4),
                )
                live.update(panel)
                time.sleep(interval)
    except Exception:
        # Any rendering issue (e.g. non-interactive terminal) is non-fatal.
        pass

    if welcome_message:
        console.print(
            Panel(
                Text(welcome_message, justify="center", style="bold #4ade5e"),
                border_style="green",
                box=box.ROUNDED,
                padding=(0, 2),
            )
        )
        console.print()
