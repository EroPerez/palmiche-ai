"""Waveform animation widget for the Jarvis chat window (PyQt6/PyQt5).

Three states:
  idle      - slow, dim blue pulse (always-on background)
  wake      - bright yellow burst (wake word detected)
  thinking  - fast sky-blue wave (agent processing)
"""
import math

try:
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QColor, QPainter
    from PyQt6.QtWidgets import QWidget
    _QT6 = True
except ImportError:
    from PyQt5.QtCore import QTimer, Qt
    from PyQt5.QtGui import QColor, QPainter
    from PyQt5.QtWidgets import QWidget
    _QT6 = False

# Catppuccin Mocha palette
_COLORS = {
    "idle":     "#45475a",
    "wake":     "#f9e2af",
    "thinking": "#89dceb",
}
_BG = "#181825"

_SPEED = {"idle": 0.035, "wake": 0.28, "thinking": 0.14}
_AMP   = {"idle": 0.22,  "wake": 0.90, "thinking": 0.62}


class WaveformAnimation(QWidget):
    """Animated equalizer bars rendered via QPainter in paintEvent."""

    N_BARS = 18
    BAR_W  = 4
    FPS    = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self._t     = 0.0
        self._state = "idle"
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setFixedHeight(40)
        self.setMinimumWidth(180)
        attr = Qt.WidgetAttribute.WA_OpaquePaintEvent if _QT6 else Qt.WA_OpaquePaintEvent
        self.setAttribute(attr)

    def build(self):
        """Start the animation timer. Call after the widget is shown."""
        self._timer.start(80 if self._state == "idle" else max(16, 1000 // self.FPS))

    def set_state(self, state: str):
        """Change animation state: 'idle', 'wake', or 'thinking'."""
        if state in _COLORS:
            self._state = state
            self._timer.setInterval(
                80 if state == "idle" else max(16, 1000 // self.FPS)
            )

    def _tick(self):
        self._t += 1
        self.update()

    def paintEvent(self, event):  # noqa: N802
        state = self._state
        p     = QPainter(self)

        if _QT6:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setRenderHint(QPainter.Antialiasing)
            p.setPen(Qt.NoPen)

        p.fillRect(self.rect(), QColor(_BG))
        p.setBrush(QColor(_COLORS[state]))

        w, h  = self.width(), self.height()
        cx    = h // 2
        n     = self.N_BARS
        gap   = max(2, (w - n * self.BAR_W) // (n + 1))
        speed = _SPEED[state]
        amp   = _AMP[state]

        for i in range(n):
            phase = i * (2 * math.pi / n)
            wave  = math.sin(self._t * speed * 20 + phase)
            wave += math.sin(self._t * speed * 13 + phase * 1.6) * 0.35
            level = amp * (0.55 + wave * 0.45)
            level = max(0.04, min(1.0, level))
            bar_h = max(2, int(level * h * 0.88))
            x     = gap + i * (self.BAR_W + gap)
            p.drawRect(x, cx - bar_h // 2, self.BAR_W, bar_h)

        p.end()

    def stop(self):
        """Stop the animation timer."""
        self._timer.stop()
