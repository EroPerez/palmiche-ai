"""Waveform animation widget for the Jarvis chat window.

Renders an equalizer-style bar animation on a tkinter Canvas.
Three states:
  idle      - slow, dim blue pulse (always-on background)
  wake      - bright yellow burst (wake word detected)
  thinking  - fast green wave (agent processing)
"""
import math
import tkinter as tk
from typing import Optional


# Catppuccin Mocha palette
_COLOR = {
    "idle":     "#45475a",   # overlay0 — dim
    "wake":     "#f9e2af",   # yellow
    "thinking": "#89dceb",   # sky blue
}

_SPEED = {
    "idle":     0.035,
    "wake":     0.28,
    "thinking": 0.14,
}

_AMP = {
    "idle":     0.22,
    "wake":     0.90,
    "thinking": 0.62,
}


class WaveformAnimation:
    """Animated equalizer bars embedded in a tk.Canvas."""

    N_BARS = 18
    BAR_W  = 4
    FPS    = 30

    def __init__(self, canvas: tk.Canvas):
        self._canvas = canvas
        self._bars: list[int] = []
        self._t = 0.0
        self._state = "idle"
        self._after_id: Optional[str] = None
        self._built = False

    # ------------------------------------------------------------------ build

    def build(self):
        """Call once after the canvas is placed and sized."""
        self._canvas.update_idletasks()
        w = self._canvas.winfo_width() or int(self._canvas["width"])
        h = self._canvas.winfo_height() or int(self._canvas["height"])
        self._h = h
        self._cx = h // 2

        total_bar_w = self.N_BARS * self.BAR_W
        gap = max(2, (w - total_bar_w) // (self.N_BARS + 1))
        self._gap = gap
        self._bar_w = self.BAR_W

        for i in range(self.N_BARS):
            x = gap + i * (self.BAR_W + gap)
            bid = self._canvas.create_rectangle(
                x, self._cx - 1, x + self.BAR_W, self._cx + 1,
                fill=_COLOR["idle"], outline="",
            )
            self._bars.append(bid)

        self._built = True
        self._tick()

    # ------------------------------------------------------------------ state

    def set_state(self, state: str):
        """Change animation state: 'idle', 'wake', or 'thinking'."""
        if state in _COLOR:
            self._state = state

    # ----------------------------------------------------------------- ticker

    def _tick(self):
        if not self._built:
            return

        state  = self._state
        speed  = _SPEED[state]
        amp    = _AMP[state]
        color  = _COLOR[state]
        cx     = self._cx
        h      = self._h
        n      = self.N_BARS

        for i, bid in enumerate(self._bars):
            phase  = i * (2 * math.pi / n)
            wave   = math.sin(self._t * speed * 20 + phase)
            wave  += math.sin(self._t * speed * 13 + phase * 1.6) * 0.35
            level  = amp * (0.55 + wave * 0.45)
            level  = max(0.04, min(1.0, level))
            bar_h  = max(2, int(level * h * 0.88))
            x      = self._gap + i * (self._bar_w + self._gap)
            self._canvas.coords(
                bid,
                x, cx - bar_h // 2,
                x + self._bar_w, cx + bar_h // 2,
            )
            self._canvas.itemconfig(bid, fill=color)

        self._t += 1
        interval = max(16, 1000 // self.FPS)

        # Slow down tick rate in idle to save CPU
        if state == "idle":
            interval = 80

        self._after_id = self._canvas.after(interval, self._tick)

    def stop(self):
        if self._after_id is not None:
            self._canvas.after_cancel(self._after_id)
            self._after_id = None
