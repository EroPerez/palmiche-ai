"""Iron Man J.A.R.V.I.S. HUD animation widget (PyQt6/PyQt5).

Rendered entirely with QPainter — no external asset files required:
  - Three concentric rotating arcs with endpoint dots
  - Central pulsing radial glow (colour changes per state)
  - Radar sweep with fading green trail
  - Corner HUD brackets + inner tick marks
  - Horizontal scan line with soft glow band
  - Subtle grid background
  - 24-bar audio equaliser (bottom strip)
  - Status data readout text (top-left / top-right)

States:
  idle     → cyan   #00d4ff  (slow, dim)
  wake     → amber  #ffaa00  (fast, bright burst)
  thinking → green  #00ff88  (medium, pulsing)
"""
import math
import random
from datetime import datetime

try:
    from PyQt6.QtCore import QTimer, Qt, QPointF, QRectF
    from PyQt6.QtGui import (
        QColor, QPainter, QPen, QBrush, QFont, QRadialGradient, QPixmap,
    )
    from PyQt6.QtWidgets import QWidget
    _QT6 = True
    _AA          = QPainter.RenderHint.Antialiasing
    _TXTAA       = QPainter.RenderHint.TextAntialiasing
    _NOBRUSH     = Qt.BrushStyle.NoBrush
    _NOPEN       = Qt.PenStyle.NoPen
    _KEEP_EXPAND = Qt.AspectRatioMode.KeepAspectRatioByExpanding
    _SMOOTH_XFM  = Qt.TransformationMode.SmoothTransformation
except ImportError:
    from PyQt5.QtCore import QTimer, Qt, QPointF, QRectF
    from PyQt5.QtGui import (
        QColor, QPainter, QPen, QBrush, QFont, QRadialGradient, QPixmap,
    )
    from PyQt5.QtWidgets import QWidget
    _QT6 = False
    _AA          = QPainter.Antialiasing
    _TXTAA       = QPainter.TextAntialiasing
    _NOBRUSH     = Qt.NoBrush
    _NOPEN       = Qt.NoPen
    _KEEP_EXPAND = Qt.KeepAspectRatioByExpanding
    _SMOOTH_XFM  = Qt.SmoothTransformation

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
_BG     = "#030d06"
_GRID   = "#091506"
_CYAN   = "#00c853"
_BLUE   = "#0a3d1a"
_LTBLUE = "#1b7a3d"
_AMBER  = "#ffab00"
_GREEN  = "#69f0ae"
_DIM    = "#1a4a28"
_WHITE  = "#f5eedc"

_STATE_COL = {"idle": _CYAN, "wake": _AMBER, "thinking": _GREEN}

_STATE_LBL = {
    "idle":     "SISTEMA ACTIVO",
    "wake":     "ESCUCHANDO ...",
    "thinking": "PROCESANDO  ...",
}

# (ring1 °/tick, ring2 °/tick, ring3 °/tick, radar °/tick)
_SPEEDS = {
    "idle":     (0.40, -0.65, 1.20, 0.8),
    "wake":     (1.80, -2.80, 4.50, 3.5),
    "thinking": (0.90, -1.50, 2.80, 2.0),
}


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

class HUDAnimation(QWidget):
    """Iron Man HUD rendered via QPainter at 30 FPS."""

    N_BARS = 24
    FPS    = 30

    def __init__(self, parent=None, name: str = "J.A.R.V.I.S", bg_path: str = ""):
        super().__init__(parent)
        self._name   = name
        self._t      = 0
        self._state  = "idle"
        self._bg_pixmap = QPixmap(bg_path) if bg_path else QPixmap()
        if self._bg_pixmap.isNull():
            self._bg_pixmap = None

        # Ring angles (degrees, 0 = top, CW)
        self._a1 = 0.0
        self._a2 = 0.0
        self._a3 = 0.0
        self._ar = 0.0   # radar

        # Scan line (0.0–1.0 of widget height)
        self._scan = 0.0

        # Radar trail: list of [angle_deg, alpha_0-255]
        self._trail: list = []

        # Equaliser bars (0.0–1.0)
        self._bars = [0.05] * self.N_BARS

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        attr = Qt.WidgetAttribute.WA_OpaquePaintEvent if _QT6 else Qt.WA_OpaquePaintEvent
        self.setAttribute(attr)
        self.setMinimumSize(400, 180)

    # ---------------------------------------------------------------- public

    def build(self):
        """Start the animation timer. Call after the widget is placed."""
        self._timer.start(1000 // self.FPS)

    def set_state(self, state: str):
        """Change visual state: 'idle', 'wake', or 'thinking'."""
        if state in _STATE_COL:
            self._state = state

    def stop(self):
        self._timer.stop()

    # ----------------------------------------------------------------- tick

    def _tick(self):
        sp = _SPEEDS[self._state]
        self._a1  = (self._a1 + sp[0]) % 360
        self._a2  = (self._a2 + sp[1]) % 360
        self._a3  = (self._a3 + sp[2]) % 360
        self._ar  = (self._ar + sp[3]) % 360

        # Scan line: slower when idle
        self._scan = (self._scan + (0.003 if self._state == "idle" else 0.007)) % 1.0

        # Radar trail decay
        self._trail.append([self._ar, 230])
        self._trail = [[a, al - 9] for a, al in self._trail if al > 0]

        # Equaliser bars
        self._t += 1
        state = self._state
        for i in range(self.N_BARS):
            ph = i * (2 * math.pi / self.N_BARS)
            if state == "idle":
                tgt = 0.06 + 0.11 * abs(math.sin(self._t * 0.025 + ph))
            elif state == "wake":
                tgt = 0.30 + 0.60 * abs(math.sin(self._t * 0.20 + ph))
                tgt = min(1.0, tgt + 0.18 * random.random())
            else:
                tgt = 0.15 + 0.50 * abs(math.sin(self._t * 0.09 + ph))
                tgt += 0.22 * abs(math.sin(self._t * 0.055 + ph * 1.8))
            self._bars[i] = min(1.0, max(0.04, tgt))

        self.update()

    # --------------------------------------------------------------- paint

    def paintEvent(self, event):  # noqa: N802
        p  = QPainter(self)
        p.setRenderHint(_AA)
        p.setRenderHint(_TXTAA)

        W   = self.width()
        H   = self.height()
        cx  = W / 2.0
        cy  = H * 0.42          # ring centre — slightly above visual middle
        R   = min(cx * 0.82, cy * 0.90)
        col = QColor(_STATE_COL[self._state])

        if self._bg_pixmap:
            scaled = self._bg_pixmap.scaled(self.size(), _KEEP_EXPAND, _SMOOTH_XFM)
            sx = (scaled.width()  - W) // 2
            sy = (scaled.height() - H) // 2
            p.drawPixmap(-sx, -sy, scaled)
            ovl = QColor(_BG)
            ovl.setAlpha(200)
            p.fillRect(self.rect(), ovl)
        else:
            p.fillRect(self.rect(), QColor(_BG))
        self._draw_grid(p, W, H)
        self._draw_scan(p, W, H)
        self._draw_brackets(p, W, H)
        self._draw_radar(p, cx, cy, R * 0.80)
        self._draw_ring(p, cx, cy, R * 0.94, self._a1, 240, col,           2.0, dash=True)
        self._draw_ring(p, cx, cy, R * 0.70, self._a2, 195, QColor(_BLUE), 1.5, dash=False)
        self._draw_ring(p, cx, cy, R * 0.48, self._a3, 130, col,           1.0, dash=True)
        self._draw_core(p, cx, cy, R * 0.17)
        self._draw_text(p, W, H, col)
        self._draw_bars(p, W, H, col)
        p.end()

    # -------------------------------------------------------- draw helpers

    def _draw_grid(self, p, W, H):
        pen = QPen(QColor(_GRID), 0.5)
        p.setPen(pen)
        for x in range(0, W + 32, 32):
            p.drawLine(x, 0, x, H)
        for y in range(0, H + 32, 32):
            p.drawLine(0, y, W, y)

    def _draw_scan(self, p, W, H):
        sy = int(H * self._scan)
        for dy in range(5, -1, -1):
            c = QColor(_CYAN)
            c.setAlpha(max(0, 35 - dy * 7))
            p.setPen(QPen(c, 1))
            if sy - dy >= 0:
                p.drawLine(0, sy - dy, W, sy - dy)
            if dy > 0 and sy + dy < H:
                p.drawLine(0, sy + dy, W, sy + dy)

    def _draw_brackets(self, p, W, H):
        sz = 28
        m  = 14
        pen = QPen(QColor(_CYAN), 1.8)
        p.setPen(pen)
        # TL
        p.drawLine(m, m + sz, m, m)
        p.drawLine(m, m, m + sz, m)
        # TR
        p.drawLine(W - m - sz, m, W - m, m)
        p.drawLine(W - m, m, W - m, m + sz)
        # BL
        p.drawLine(m, H - m - sz, m, H - m)
        p.drawLine(m, H - m, m + sz, H - m)
        # BR
        p.drawLine(W - m - sz, H - m, W - m, H - m)
        p.drawLine(W - m, H - m, W - m, H - m - sz)
        # Tick extensions
        pen2 = QPen(QColor("#00c85555"), 1)
        p.setPen(pen2)
        tk = 9
        p.drawLine(m + sz + 3, m,         m + sz + 3 + tk, m)
        p.drawLine(m,         m + sz + 3, m,               m + sz + 3 + tk)
        p.drawLine(W - m - sz - 3 - tk, H - m, W - m - sz - 3, H - m)
        p.drawLine(W - m, H - m - sz - 3 - tk, W - m, H - m - sz - 3)

    def _draw_radar(self, p, cx, cy, R):
        # Fading trail
        for entry in self._trail:
            a, alpha = entry[0], entry[1]
            if alpha <= 0:
                continue
            col = QColor(_GREEN)
            col.setAlpha(min(255, int(alpha * 0.30)))
            p.setPen(QPen(col, 0.8))
            rad = math.radians(a - 90)
            p.drawLine(int(cx), int(cy),
                       int(cx + R * math.cos(rad)),
                       int(cy + R * math.sin(rad)))
        # Active sweep line
        col = QColor(_GREEN)
        col.setAlpha(210)
        p.setPen(QPen(col, 1.6))
        rad = math.radians(self._ar - 90)
        p.drawLine(int(cx), int(cy),
                   int(cx + R * math.cos(rad)),
                   int(cy + R * math.sin(rad)))

    def _draw_ring(self, p, cx, cy, R, start_a, span, color, width, dash):
        c   = QColor(color)
        if self._state == "idle":
            c.setAlpha(170)
        pen = QPen(c, width)
        if dash:
            pen.setDashPattern([10.0, 5.0])
        p.setPen(pen)
        p.setBrush(QBrush())  # NoBrush

        rect      = QRectF(cx - R, cy - R, R * 2, R * 2)
        qt_start  = int((90 - start_a) * 16)
        qt_span   = int(-span * 16)
        p.drawArc(rect, qt_start, qt_span)

        # Endpoint dots
        p.setPen(_NOPEN)
        p.setBrush(QBrush(c))
        dr = max(2.5, width * 1.8)
        for offset in (0, span):
            rad = math.radians(start_a + offset)
            ex  = cx + R * math.cos(rad)
            ey  = cy - R * math.sin(rad)
            p.drawEllipse(QPointF(ex, ey), dr, dr)

    def _draw_core(self, p, cx, cy, R):
        pulse_rate = {"idle": 0.08, "wake": 0.28, "thinking": 0.16}[self._state]
        r          = R * (0.82 + 0.18 * math.sin(self._t * pulse_rate))

        inner_hex = {"idle": "#00c853", "wake": "#ffcc00", "thinking": "#69f0ae"}[self._state]
        inner     = QColor(inner_hex)

        # Outer glow
        g1 = QRadialGradient(cx, cy, r * 3.5)
        g1c = QColor(inner); g1c.setAlpha(55)
        g1z = QColor(inner); g1z.setAlpha(0)
        g1.setColorAt(0.0, g1c); g1.setColorAt(1.0, g1z)
        p.setPen(_NOPEN)
        p.setBrush(QBrush(g1))
        p.drawEllipse(QPointF(cx, cy), r * 3.5, r * 3.5)

        # Core glow
        g2 = QRadialGradient(cx, cy, r * 1.6)
        ginner = QColor(inner); ginner.setAlpha(255)
        gouter = QColor(inner); gouter.setAlpha(0)
        g2.setColorAt(0.0, ginner)
        g2.setColorAt(0.5, ginner)
        g2.setColorAt(1.0, gouter)
        p.setBrush(QBrush(g2))
        p.drawEllipse(QPointF(cx, cy), r * 1.6, r * 1.6)

        # Bright centre dot
        p.setBrush(QBrush(QColor(_WHITE)))
        p.drawEllipse(QPointF(cx, cy), r * 0.35, r * 0.35)

    def _draw_text(self, p, W, H, col):
        now   = datetime.now()
        state = self._state
        dim   = QColor(_DIM)
        font  = QFont("Monospace", 7)
        p.setFont(font)

        # Top-left readout
        p.setPen(QPen(col))
        p.drawText(46, 26, f"SYS / {now:%H:%M:%S}")
        p.drawText(46, 38, f"STATUS : {_STATE_LBL[state]}")
        p.setPen(QPen(dim))
        p.drawText(46, 50, f"CORE   : {23 + int(self._t * 0.05) % 4}°C  |  OK")

        # Top-right readout
        p.setPen(QPen(dim))
        p.drawText(W - 135, 26, "LAT :  23.136°N")
        p.drawText(W - 135, 38, "LON :  82.358°W")
        p.drawText(W - 135, 50, "ALT :  0056 m  ")

        # Name label near core
        name_font = QFont("Monospace", 9)
        name_font.setBold(True)
        p.setFont(name_font)
        p.setPen(QPen(col))
        name_text = self._name.upper()
        fm_w      = len(name_text) * 7          # rough char width estimate
        cx        = W / 2
        cy        = H * 0.42
        p.drawText(int(cx + 12), int(cy - 16), name_text)

    def _draw_bars(self, p, W, H, col):
        n       = self.N_BARS
        bar_h   = H * 0.20
        pad     = 22
        total_w = W - pad * 2
        bar_w   = total_w / (n * 1.5)
        gap     = bar_w * 0.5

        p.setPen(_NOPEN)
        for i, frac in enumerate(self._bars):
            x   = pad + i * (bar_w + gap)
            bh  = max(2.0, frac * bar_h)
            y   = H - bh
            c   = QColor(col)
            c.setAlpha(195 if frac > 0.45 else 100)
            p.setBrush(QBrush(c))
            p.drawRect(int(x), int(y), max(1, int(bar_w)), int(bh))

        # Baseline
        p.setPen(QPen(QColor(_DIM), 1))
        p.drawLine(pad, H - 2, W - pad, H - 2)
