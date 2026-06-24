"""System tray interface for Jarvis (PyQt6/PyQt5).

Features:
- QSystemTrayIcon — click to show/hide the chat window
- Dark-themed chat window (Catppuccin Mocha)
- Window launches maximized with a smooth fade-in animation
- Waveform animation in the header (idle / wake / thinking states)
- Message timestamps and a bottom status bar
- Clear button and keyboard shortcuts: Esc hides, Ctrl+L clears chat
- Background wake-word listener: saying the wake word shows the window
  and focuses the input field

Platform notes:
  Linux/macOS → QSystemTrayIcon + QApplication on the main thread.

Requires: pip install PyQt6 Pillow   (or PyQt5 Pillow)
Optional: pip install SpeechRecognition pyaudio   (for wake word)
"""
import platform
import sys
import threading
from datetime import datetime

_SYSTEM = platform.system()
_DEFAULT_WAKE_WORD = "palmiche"

# ---------------------------------------------------------------------------
# Qt compatibility shim — supports PyQt6 and PyQt5
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTextEdit, QLineEdit, QPushButton, QLabel,
        QApplication, QSystemTrayIcon, QMenu,
    )
    from PyQt6.QtCore import (
        Qt, QTimer, QPropertyAnimation, QEasingCurve,
        pyqtSignal, QObject,
    )
    from PyQt6.QtGui import (
        QColor, QTextCharFormat, QFont, QTextCursor,
        QShortcut, QKeySequence, QIcon, QPixmap, QImage, QAction,
    )
    _QT6           = True
    _CURSOR_HAND   = Qt.CursorShape.PointingHandCursor
    _MOVE_END      = QTextCursor.MoveOperation.End
    _FONT_BOLD     = QFont.Weight.Bold
    _EASE_OUT      = QEasingCurve.Type.OutCubic
    _TRAY_TRIGGER  = QSystemTrayIcon.ActivationReason.Trigger
    _TRAY_DBLCLICK = QSystemTrayIcon.ActivationReason.DoubleClick

except ImportError:
    try:
        from PyQt5.QtWidgets import (
            QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
            QTextEdit, QLineEdit, QPushButton, QLabel,
            QApplication, QSystemTrayIcon, QMenu, QAction, QShortcut,
        )
        from PyQt5.QtCore import (
            Qt, QTimer, QPropertyAnimation, QEasingCurve,
            pyqtSignal, QObject,
        )
        from PyQt5.QtGui import (
            QColor, QTextCharFormat, QFont, QTextCursor,
            QKeySequence, QIcon, QPixmap, QImage,
        )
        _QT6           = False
        _CURSOR_HAND   = Qt.PointingHandCursor
        _MOVE_END      = QTextCursor.End
        _FONT_BOLD     = QFont.Bold
        _EASE_OUT      = QEasingCurve.OutCubic
        _TRAY_TRIGGER  = QSystemTrayIcon.Trigger
        _TRAY_DBLCLICK = QSystemTrayIcon.DoubleClick

    except ImportError:
        raise ImportError(
            "PyQt6 (o PyQt5) no está instalado.\n"
            "Instala con:  pip install PyQt6 Pillow"
        ) from None


# ---------------------------------------------------------------------------
# Tray icon — horse-head silhouette (homage to Palmiche)
# ---------------------------------------------------------------------------

_HORSE_HEAD = [
    (30, 90), (31, 64), (33, 50), (37, 40), (40, 26),
    (43, 12), (49, 28), (55, 16), (60, 32), (66, 40),
    (74, 52), (80, 62), (78, 70), (70, 70), (62, 66),
    (55, 70), (50, 80), (56, 90),
]


def _draw_horse_icon(size: int):
    """Draw the built-in circular horse-head icon with Pillow."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    s   = size / 100.0
    d.ellipse([2*s, 2*s, 98*s, 98*s], fill=(34, 110, 64, 255),
              outline=(20, 70, 42, 255), width=max(1, int(2*s)))
    d.polygon([(x*s, y*s) for x, y in _HORSE_HEAD], fill=(245, 238, 220, 255))
    d.ellipse([55*s, 38*s, 59*s, 42*s], fill=(34, 110, 64, 255))
    return img


def _make_pil_icon(size: int = 64):
    """Return the tray icon as a Pillow Image, falling back to the built-in."""
    from PIL import Image
    try:
        from ..config import JARVIS_TRAY_ICON
    except Exception:
        JARVIS_TRAY_ICON = ""
    if JARVIS_TRAY_ICON:
        try:
            return Image.open(JARVIS_TRAY_ICON).convert("RGBA").resize(
                (size, size), Image.LANCZOS
            )
        except Exception:
            pass
    return _draw_horse_icon(size)


def _pil_to_qicon(pil_img) -> QIcon:
    """Convert a Pillow RGBA image to a QIcon."""
    rgba  = pil_img.convert("RGBA")
    data  = rgba.tobytes("raw", "RGBA")
    fmt   = QImage.Format.Format_RGBA8888 if _QT6 else QImage.Format_RGBA8888
    qimg  = QImage(data, rgba.width, rgba.height, fmt)
    return QIcon(QPixmap.fromImage(qimg))


# ---------------------------------------------------------------------------
# Cross-thread bridge — routes background-thread calls to the Qt main thread
# ---------------------------------------------------------------------------

class _Bridge(QObject):
    _sig = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._sig.connect(self._exec)

    def _exec(self, fn):
        fn()

    def call(self, fn):
        """Schedule fn() on the Qt main thread from any thread."""
        self._sig.emit(fn)


# ---------------------------------------------------------------------------
# Tag → text-format mapping
# ---------------------------------------------------------------------------

_TAG_STYLES = {
    "user":   {"color": "#00c853", "bold": True,  "italic": False, "size": 10},
    "jarvis": {"color": "#f5eedc", "bold": False, "italic": False, "size": 10},
    "system": {"color": "#69f0ae", "bold": False, "italic": True,  "size": 9},
    "wake":   {"color": "#ffab00", "bold": False, "italic": True,  "size": 9},
    "error":  {"color": "#ff1744", "bold": False, "italic": False, "size": 10},
    "time":   {"color": "#1b5e32", "bold": False, "italic": False, "size": 8},
}


# ---------------------------------------------------------------------------
# Chat window
# ---------------------------------------------------------------------------

class _ChatWindow(QMainWindow):
    """PyQt chat window with waveform animation and wake-word support."""

    def __init__(self, agent, name: str,
                 wake_word: str = _DEFAULT_WAKE_WORD,
                 welcome_message: str = "",
                 goodbye_message: str = ""):
        super().__init__()
        self.agent           = agent
        self.name            = name
        self.wake_word       = wake_word
        self.welcome_message = welcome_message
        self.goodbye_message = goodbye_message
        self._busy           = False
        self._voice_mode     = False
        self._has_greeted    = False   # welcome is spoken only once
        self._bridge         = _Bridge()
        self._wake_listener  = None
        self._anim           = None
        self._mic_btn        = None
        self._status_label   = None
        self._display        = None
        self._entry          = None
        self._fade_anim      = None   # keep reference to prevent GC
        self._fade_out_anim  = None
        self._build()

    # ------------------------------------------------------------------ build

    def _build(self):
        from .hud_animation import HUDAnimation

        self.setWindowTitle(self.name)
        self.setWindowOpacity(0.0)   # start transparent; show_with_animation fades in

        # ── Central widget ────────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── HUD header ────────────────────────────────────────────────────────
        self._anim = HUDAnimation(name=self.name)
        self._anim.setFixedHeight(240)
        layout.addWidget(self._anim)

        # ── Info data bar ─────────────────────────────────────────────────────
        _data_bar = QLabel(
            f"  PALMICHE // IA  ─────────────────────────"
            f"  SYS:OK  //  NEURAL:ACTIVO  //  {self.name.upper()}"
        )
        _data_bar.setStyleSheet(
            "background-color: #091506;"
            " color: #1b5e32; font-family: Monospace; font-size: 8pt;"
            " padding: 2px 14px;"
            " border-top: 1px solid #0f2914;"
            " border-bottom: 1px solid #0f2914;"
        )
        layout.addWidget(_data_bar)

        # ── Chat display ──────────────────────────────────────────────────────
        self._display = QTextEdit()
        self._display.setReadOnly(True)
        self._display.setStyleSheet(
            "QTextEdit {"
            " background-color: #030d06; color: #b9f6ca;"
            " font-family: 'Courier New', Monospace; font-size: 10pt;"
            " padding: 10px 10px 10px 14px; border: none;"
            " border-left: 2px solid #1a5e32;"
            " selection-background-color: #0a3d1a;"
            " selection-color: #f5eedc;"
            "}"
            "QScrollBar:vertical { background: #030d06; width: 8px; border: none; }"
            "QScrollBar::handle:vertical { background: #1a5e32; border-radius: 0px; }"
            "QScrollBar::handle:vertical:hover { background: #00c853; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        )
        layout.addWidget(self._display, 1)

        # ── Input row ─────────────────────────────────────────────────────────
        input_row = QWidget()
        input_row.setStyleSheet(
            "background-color: #091506; border-top: 1px solid #1a5e32;"
        )
        il = QHBoxLayout(input_row)
        il.setContentsMargins(8, 6, 8, 6)
        il.setSpacing(6)

        self._entry = QLineEdit()
        self._entry.setStyleSheet(
            "QLineEdit {"
            " background-color: #030d06; color: #b9f6ca;"
            " font-family: 'Courier New', Monospace; font-size: 10pt;"
            " border: 1px solid #1a5e32; padding: 5px 8px;"
            "}"
            "QLineEdit:focus { border-color: #00c853; }"
        )
        self._entry.setPlaceholderText("// ENTRADA DE COMANDO ...")
        self._entry.returnPressed.connect(self._on_send)
        il.addWidget(self._entry)

        _btn_send = (
            "QPushButton { background-color: #0a3d1a; color: #00c853;"
            " font-family: Monospace; font-size: 11pt; font-weight: bold;"
            " border: 1px solid #00c853; padding: 5px 12px; }"
            "QPushButton:hover { background-color: #1a5e32; color: #69f0ae;"
            " border-color: #69f0ae; }"
            "QPushButton:disabled { background-color: #030d06; color: #1a5e32;"
            " border-color: #1a5e32; }"
        )
        self._btn_dim = (
            "QPushButton { background-color: #030d06; color: #2e7d52;"
            " font-family: Monospace; font-size: 11pt;"
            " border: 1px solid #1a5e32; padding: 5px 8px; }"
            "QPushButton:hover { background-color: #0a1a0f; color: #00c853;"
            " border-color: #00c853; }"
            "QPushButton:disabled { color: #1a3d22; border-color: #0a2216; }"
        )
        self._btn_mic_active = (
            "QPushButton { background-color: #3d2000; color: #ffab00;"
            " font-family: Monospace; font-size: 11pt; font-weight: bold;"
            " border: 1px solid #ffab00; padding: 5px 8px; }"
            "QPushButton:hover { background-color: #5e3200; color: #ffd740;"
            " border-color: #ffd740; }"
        )

        send_btn = QPushButton("↩")
        send_btn.setStyleSheet(_btn_send)
        send_btn.setCursor(_CURSOR_HAND)
        send_btn.clicked.connect(self._on_send)
        il.addWidget(send_btn)

        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setStyleSheet(self._btn_dim)
        self._mic_btn.setCursor(_CURSOR_HAND)
        self._mic_btn.clicked.connect(self._toggle_voice_mode)
        il.addWidget(self._mic_btn)

        clear_btn = QPushButton("🗑")
        clear_btn.setStyleSheet(self._btn_dim)
        clear_btn.setCursor(_CURSOR_HAND)
        clear_btn.clicked.connect(self._clear_chat)
        il.addWidget(clear_btn)

        layout.addWidget(input_row)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            "background-color: #030d06; color: #1b5e32;"
            " font-family: Monospace; font-size: 9pt; padding: 3px 10px;"
            " border-top: 1px solid #0a1a0f;"
        )
        layout.addWidget(self._status_label)

        self.setStyleSheet("QMainWindow { background-color: #030d06; }")

        # ── Keyboard shortcuts ────────────────────────────────────────────────
        QShortcut(QKeySequence("Escape"), self, self._on_escape)
        QShortcut(QKeySequence("Ctrl+L"), self, self._clear_chat)

        # ── Seed the display ──────────────────────────────────────────────────
        self._append(f"// {self.name.upper()} OPERATIVO\n", "system")
        self._set_status("LISTO", "#00c853")

        # ── Start animation ───────────────────────────────────────────────────
        self._anim.build()

        # ── Wake-word listener ────────────────────────────────────────────────
        from .wake_word import WakeWordListener
        self._wake_listener = WakeWordListener(
            wake_word=self.wake_word,
            on_wake=self._on_wake,
            on_command=self._on_voice_command,
            response_text=self.welcome_message,
        )
        if not self._wake_listener.start():
            # SpeechRecognition/pyaudio not installed — disable mic button
            self._wake_listener = None
            if self._mic_btn:
                self._mic_btn.setEnabled(False)
                self._mic_btn.setToolTip(
                    "Voz no disponible — instala: pip install SpeechRecognition pyaudio"
                )

    # ----------------------------------------------------------------- I/O

    def _append(self, text: str, tag: str = "", stamp: bool = False):
        """Insert styled text into the chat display."""
        cursor = self._display.textCursor()
        cursor.movePosition(_MOVE_END)

        if stamp:
            tfmt = QTextCharFormat()
            tfmt.setForeground(QColor("#1b5e32"))
            tfmt.setFont(QFont("Monospace", 8))
            cursor.insertText(f"[{datetime.now():%H:%M}] ", tfmt)

        fmt   = QTextCharFormat()
        style = _TAG_STYLES.get(tag)
        if style:
            fmt.setForeground(QColor(style["color"]))
            fmt.setFont(QFont("Monospace", style["size"]))
            if style["bold"]:
                fmt.setFontWeight(_FONT_BOLD)
            fmt.setFontItalic(style["italic"])
        else:
            fmt.setForeground(QColor("#cdd6f4"))
            fmt.setFont(QFont("Monospace", 10))

        cursor.insertText(text, fmt)
        self._display.setTextCursor(cursor)
        self._display.ensureCursorVisible()

    def _set_status(self, text: str, color: str = "#2e7d52"):
        if self._status_label:
            self._status_label.setStyleSheet(
                f"background-color: #030d06; color: {color};"
                " font-family: Monospace; font-size: 9pt; padding: 3px 10px;"
                " border-top: 1px solid #0a1a0f;"
            )
            self._status_label.setText(text)

    def _clear_chat(self):
        if self._busy:
            return
        self._display.clear()
        history = getattr(self.agent, "history", None)
        if history is not None and hasattr(history, "clear"):
            try:
                history.clear()
            except Exception:
                pass
        self._append(f"// {self.name.upper()} OPERATIVO\n", "system")
        self._set_status("HISTORIAL BORRADO", "#69f0ae")

    # ----------------------------------------------------------------- send/reply

    _QUIT_CMDS = frozenset(("salir", "exit", "quit", "q", "bye", "adios", "adiós"))

    def _on_send(self):
        msg = self._entry.text().strip()
        if not msg:
            return
        if msg.lower() in self._QUIT_CMDS:
            self._entry.clear()
            self._on_quit()
            return
        self._entry.clear()
        self._entry.setEnabled(False)
        self._busy = True
        self._append(f"Tú: {msg}\n", "user", stamp=True)
        if self._anim:
            self._anim.set_state("thinking")
        self._set_status("PROCESANDO ...", "#69f0ae")
        threading.Thread(target=self._call_agent, args=(msg,), daemon=True).start()

    def _call_agent(self, msg: str):
        """Run agent.chat() in a daemon thread; post reply back to main thread."""
        try:
            reply = self.agent.chat(msg)
            tag   = "jarvis"
        except Exception as exc:
            reply = f"Error: {exc}"
            tag   = "error"
        self._bridge.call(lambda: self._on_reply(reply, tag))

    def _on_reply(self, reply: str, tag: str):
        self._append(f"{self.name}: {reply}\n\n", tag, stamp=True)
        self._busy = False
        if self._anim:
            self._anim.set_state("idle")
        if self._voice_mode:
            from .wake_word import _speak_async
            self._set_status("REPRODUCIENDO ...", "#ffab00")
            _speak_async(reply, on_done=lambda: self._bridge.call(self._on_tts_done))
        else:
            self._entry.setEnabled(True)
            self._entry.setFocus()
            self._set_status("LISTO", "#00c853")

    def _on_tts_done(self):
        if self._voice_mode:
            self._start_voice_listen()

    # ----------------------------------------------------------------- wake word

    def _on_wake(self):
        self._bridge.call(self._handle_wake)

    def _handle_wake(self):
        if not self.isVisible() or self.isMinimized():
            self._show_fullscreen_animated()
        else:
            self.raise_()
            self.activateWindow()
        self._append(f"[{self.name} activado por voz]\n", "wake")
        self._set_status("VOZ DETECTADA — ESCUCHANDO ...", "#ffab00")
        if self._anim:
            self._anim.set_state("wake")
            QTimer.singleShot(1500, self._wake_to_idle)
        if self._entry:
            self._entry.setEnabled(True)
            self._entry.setFocus()

    def _wake_to_idle(self):
        if self._anim:
            self._anim.set_state("idle")
        if not self._busy:
            self._set_status("LISTO", "#00c853")

    # ----------------------------------------------------------------- voice mode

    def _toggle_voice_mode(self):
        if self._voice_mode:
            self._deactivate_voice_mode()
        else:
            self._activate_voice_mode()

    def _activate_voice_mode(self):
        if not self._wake_listener:
            self._append(
                "[Voz no disponible — instala: pip install SpeechRecognition pyaudio]\n",
                "error",
            )
            self._set_status("VOZ NO DISPONIBLE", "#ff1744")
            return
        self._voice_mode = True
        if self._mic_btn:
            self._mic_btn.setStyleSheet(self._btn_mic_active)
            self._mic_btn.setText("🎤 ON")
        self._append("[Modo voz activado — escuchando continuamente]\n", "wake")
        from .wake_word import _speak_async
        if self.welcome_message and not self._has_greeted:
            self._has_greeted = True
            self._set_status("REPRODUCIENDO ...", "#ffab00")
            _speak_async(
                self.welcome_message,
                on_done=lambda: self._bridge.call(self._on_activation_audio_done),
            )
        else:
            self._bridge.call(self._on_activation_audio_done)

    def _on_activation_audio_done(self):
        if self._voice_mode:
            self._set_status("MODO VOZ ACTIVO", "#ffab00")
            self._start_voice_listen()

    def _deactivate_voice_mode(self):
        self._voice_mode = False
        if self._mic_btn:
            self._mic_btn.setStyleSheet(self._btn_dim)
            self._mic_btn.setText("🎤")
        if self._anim:
            self._anim.set_state("idle")
        self._append("[Modo voz desactivado]\n", "system")
        self._set_status("LISTO", "#00c853")
        if self._entry:
            self._entry.setEnabled(True)
            self._entry.setFocus()

    def _start_voice_listen(self):
        if not self._voice_mode or not self._wake_listener:
            return
        self._set_status("ESCUCHANDO ...", "#ffab00")
        if self._anim:
            self._anim.set_state("wake")
        if self._entry:
            self._entry.setEnabled(False)
        self._wake_listener.listen_once(self._on_voice_input_done)

    def _on_voice_command(self, text: str):
        self._bridge.call(lambda: self._dispatch_voice_command(text))

    def _dispatch_voice_command(self, text: str):
        if self._entry:
            self._entry.setEnabled(True)
            self._entry.setText(text)
        self._on_send()

    def _on_voice_input_done(self, text):
        self._bridge.call(lambda: self._apply_voice_input(text))

    def _apply_voice_input(self, text):
        if self._anim:
            self._anim.set_state("idle")
        if text:
            if self._entry:
                self._entry.setEnabled(True)
                self._entry.setText(text)
            self._on_send()
        else:
            if self._voice_mode:
                self._append("[No se entendió — escuchando de nuevo…]\n", "system")
                QTimer.singleShot(500, self._start_voice_listen)
            else:
                self._append("[No se entendió el comando de voz]\n", "system")
                self._set_status("NO SE ENTENDIÓ EL COMANDO", "#ff1744")
                if self._entry:
                    self._entry.setEnabled(True)

    # ----------------------------------------------------------------- window control

    def show_with_animation(self):
        """Show the window centered on screen with a smooth fade-in animation."""
        if self.isVisible() and not self.isMinimized():
            self.raise_()
            self.activateWindow()
            return

        # Size and center on the primary screen
        w, h   = 920, 760
        screen = QApplication.primaryScreen().availableGeometry()
        x      = screen.x() + (screen.width()  - w) // 2
        y      = screen.y() + (screen.height() - h) // 3
        self.resize(w, h)
        self.move(x, y)

        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self.activateWindow()

        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(500)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(_EASE_OUT)
        anim.start()
        self._fade_anim = anim  # prevent GC

    def _show_fullscreen_animated(self):
        """Show the window fullscreen with fade-in (triggered by voice wake)."""
        self.setWindowOpacity(0.0)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(600)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(_EASE_OUT)
        anim.start()
        self._fade_anim = anim

    def _on_escape(self):
        """Exit fullscreen if active, otherwise fade-hide the window."""
        if self.isFullScreen():
            self.showNormal()
            w, h   = 920, 760
            screen = QApplication.primaryScreen().availableGeometry()
            x      = screen.x() + (screen.width()  - w) // 2
            y      = screen.y() + (screen.height() - h) // 3
            self.resize(w, h)
            self.move(x, y)
        else:
            self.hide()

    def hide(self):
        """Fade out and hide the window."""
        anim = QPropertyAnimation(self, b"windowOpacity")
        anim.setDuration(250)
        anim.setStartValue(self.windowOpacity())
        anim.setEndValue(0.0)
        anim.finished.connect(lambda: QWidget.hide(self))
        anim.start()
        self._fade_out_anim = anim

    def closeEvent(self, event):  # noqa: N802
        """Intercept the × button to hide rather than quit."""
        event.ignore()
        self.hide()

    def _on_quit(self):
        """Stop all background workers and exit the Qt application."""
        self._voice_mode = False
        if self._wake_listener:
            self._wake_listener.stop()
        if self._anim:
            self._anim.stop()
        if self.goodbye_message:
            from .wake_word import _speak_sync
            _speak_sync(self.goodbye_message)
        app = QApplication.instance()
        if app:
            app.quit()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_tray(
    agent,
    name: str = "Jarvis",
    wake_word: str = _DEFAULT_WAKE_WORD,
    welcome_message: str = "Sistemas en línea. ¿En qué puedo ayudarte?",
    goodbye_message: str = "",
) -> None:
    """Start the PyQt chat window with system tray icon and wake-word detection.

    The window opens maximized with a fade-in animation.
    The tray icon provides Open/Quit actions.
    """
    if _SYSTEM not in ("Linux", "Darwin"):
        raise RuntimeError(f"Bandeja del sistema no soportada en {_SYSTEM}")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    win = _ChatWindow(agent, name, wake_word, welcome_message, goodbye_message)

    # ── System tray icon ──────────────────────────────────────────────────────
    try:
        icon = _pil_to_qicon(_make_pil_icon(64))
    except Exception:
        icon = app.style().standardIcon(
            app.style().StandardPixmap.SP_ComputerIcon if _QT6
            else app.style().SP_ComputerIcon
        )

    tray = QSystemTrayIcon(icon, app)

    menu = QMenu()
    open_act = menu.addAction(f"Abrir {name}")
    open_act.triggered.connect(win.show_with_animation)
    menu.addSeparator()
    quit_act = menu.addAction("Salir")
    quit_act.triggered.connect(win._on_quit)

    tray.setContextMenu(menu)
    tray.setToolTip(name)

    def _on_tray_activated(reason):
        if reason in (_TRAY_TRIGGER, _TRAY_DBLCLICK):
            win.show_with_animation()

    tray.activated.connect(_on_tray_activated)
    tray.show()

    # ── Play startup audio (if configured via JARVIS_WELCOME_AUDIO) ──────────
    _play_startup_audio(app)

    app.exec()


def _get_welcome_audio_path():
    """Return the absolute path to JARVIS_WELCOME_AUDIO if it exists, else None."""
    try:
        from ..config import JARVIS_WELCOME_AUDIO
    except Exception:
        return None
    if not JARVIS_WELCOME_AUDIO:
        return None
    import os
    path = os.path.abspath(JARVIS_WELCOME_AUDIO)
    return path if os.path.isfile(path) else None


def _play_audio_file(path: str, on_done=None) -> None:
    """Play an audio file via subprocess in a daemon thread."""
    import os

    def _play():
        import subprocess
        ext = os.path.splitext(path)[1].lower()
        candidates = [
            ["mpg123", "-q", path],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
            ["cvlc",   "--play-and-exit", "--quiet", path],
        ]
        if ext in (".wav", ".ogg"):
            candidates += [["paplay", path], ["aplay", path]]
        try:
            for cmd in candidates:
                try:
                    if subprocess.run(cmd, capture_output=True).returncode == 0:
                        return
                except FileNotFoundError:
                    continue
        finally:
            if on_done:
                on_done()

    threading.Thread(target=_play, daemon=True, name="jarvis-audio-play").start()


def _play_activation_audio(on_done=None) -> None:
    """Play the welcome audio when voice mode is activated."""
    path = _get_welcome_audio_path()
    if path:
        _play_audio_file(path, on_done=on_done)
    elif on_done:
        on_done()


def _play_startup_audio(app) -> None:
    """Play JARVIS_WELCOME_AUDIO via QMediaPlayer (primary) or subprocess (fallback)."""
    path = _get_welcome_audio_path()
    if not path:
        return

    # ── Primary: QMediaPlayer — no external tools needed ─────────────────────
    try:
        if _QT6:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PyQt6.QtCore import QUrl
            _player = QMediaPlayer()
            _audio  = QAudioOutput()
            _player.setAudioOutput(_audio)
            _player.setSource(QUrl.fromLocalFile(path))
        else:
            from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
            from PyQt5.QtCore import QUrl
            _player = QMediaPlayer()
            _player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            _audio  = None

        def _start():
            _player.play()

        QTimer.singleShot(300, _start)
        # Keep references alive for the duration of the session
        app._audio_player = _player
        app._audio_output  = _audio
        return
    except Exception:
        pass  # QtMultimedia not available — fall through to subprocess

    _play_audio_file(path)
