"""System tray interface for Jarvis.

Features:
- Taskbar icon (pystray) — click to show/hide the chat window
- Dark-themed chat window (tkinter, Catppuccin Mocha)
- Waveform animation in the header (idle / wake / thinking states)
- Background wake-word listener: saying "palmiche" shows the window and
  focuses the input field, ready for a voice or text command

Platform notes:
  Linux  → pystray runs in a background thread; tkinter on the main thread.
  macOS  → pystray runs on the main thread via setup(); tkinter in that thread.

Requires: pip install pystray Pillow
Optional: pip install SpeechRecognition pyaudio   (for wake word)
"""
import platform
import threading

_SYSTEM = platform.system()

# Wake word — can be overridden via config
_DEFAULT_WAKE_WORD = "palmiche"


# ---------------------------------------------------------------------------
# Tray icon image
# ---------------------------------------------------------------------------

def _make_icon_image(size: int = 64):
    """Generate a circular RGBA icon for the system tray."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, size - 2, size - 2], fill=(30, 100, 220, 255))
    m = size // 5
    d.ellipse([m, m, size - m, size - m], fill=(255, 255, 255, 40))
    return img


# ---------------------------------------------------------------------------
# Chat window
# ---------------------------------------------------------------------------

class _ChatWindow:
    """Tkinter chat window with waveform animation and wake-word support."""

    def __init__(self, agent, name: str, wake_word: str = _DEFAULT_WAKE_WORD):
        """Store agent reference and UI state; call run() to build and start the window."""
        self.agent = agent
        self.name = name
        self.wake_word = wake_word
        self.root = None
        self._display = None
        self._entry = None
        self._anim = None          # WaveformAnimation
        self._wake_listener = None # WakeWordListener

    # ------------------------------------------------------------------ build

    def _build(self):
        """Construct and configure all tkinter widgets, then start the wake-word listener."""
        import tkinter as tk
        from tkinter import scrolledtext
        from .animation import WaveformAnimation
        from .wake_word import WakeWordListener

        self.root = tk.Tk()
        self.root.title(self.name)
        self.root.geometry("720x580")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#181825", pady=0)
        header.pack(fill=tk.X)

        tk.Label(
            header, text=f"  {self.name}",
            bg="#181825", fg="#89b4fa",
            font=("Monospace", 11, "bold"),
        ).pack(side=tk.LEFT, pady=6)

        # Waveform canvas in the header
        wave_canvas = tk.Canvas(
            header, width=260, height=40,
            bg="#181825", bd=0, highlightthickness=0,
        )
        wave_canvas.pack(side=tk.RIGHT, padx=12, pady=2)

        self._anim = WaveformAnimation(wave_canvas)
        # Build after packing so winfo_width() has real values
        self.root.after(50, self._anim.build)

        # ── Chat display ─────────────────────────────────────────────────────
        self._display = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap=tk.WORD,
            font=("Monospace", 10), bg="#1e1e2e", fg="#cdd6f4",
            insertbackground="white", padx=10, pady=8, bd=0,
            selectbackground="#313244",
        )
        self._display.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))
        self._display.tag_configure(
            "user", foreground="#89b4fa", font=("Monospace", 10, "bold")
        )
        self._display.tag_configure("jarvis",  foreground="#a6e3a1")
        self._display.tag_configure(
            "system", foreground="#f5c2e7", font=("Monospace", 9, "italic")
        )
        self._display.tag_configure("wake",    foreground="#f9e2af",
                                     font=("Monospace", 9, "italic"))
        self._display.tag_configure("error",   foreground="#f38ba8")

        # ── Input row ────────────────────────────────────────────────────────
        row = tk.Frame(self.root, bg="#313244", pady=4)
        row.pack(fill=tk.X, padx=8, pady=8)

        self._entry = tk.Entry(
            row, font=("Monospace", 10),
            bg="#313244", fg="#cdd6f4", insertbackground="white",
            relief=tk.FLAT, bd=6,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._entry.bind("<Return>",   self._on_send)
        self._entry.bind("<KP_Enter>", self._on_send)

        tk.Button(
            row, text="↩", command=self._on_send,
            bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT,
            padx=12, font=("Monospace", 11, "bold"), cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(4, 0))

        self._append(f"Sistema: {self.name} listo\n", "system")

        # ── Wake word listener ───────────────────────────────────────────────
        self._wake_listener = WakeWordListener(
            wake_word=self.wake_word,
            on_wake=self._on_wake,
        )
        self._wake_listener.start()

    # ---------------------------------------------------------------- I/O

    def _append(self, text: str, tag: str = ""):
        """Append *text* with *tag* styling to the read-only chat display."""
        self._display.config(state="normal")
        self._display.insert("end", text, tag)
        self._display.config(state="disabled")
        self._display.see("end")

    def _on_send(self, _event=None):
        """Read the input field, echo the user message, and dispatch agent call in a thread."""
        msg = self._entry.get().strip()
        if not msg:
            return
        self._entry.delete(0, "end")
        self._entry.config(state="disabled")
        self._append(f"Tú: {msg}\n", "user")
        if self._anim:
            self._anim.set_state("thinking")
        threading.Thread(
            target=self._call_agent, args=(msg,), daemon=True
        ).start()

    def _call_agent(self, msg: str):
        """Run agent.chat() in a daemon thread and schedule the reply on the main thread."""
        try:
            reply = self.agent.chat(msg)
            tag   = "jarvis"
        except Exception as exc:
            reply = f"Error: {exc}"
            tag   = "error"
        self.root.after(0, self._on_reply, reply, tag)

    def _on_reply(self, reply: str, tag: str):
        """Display the agent reply and reset the UI to idle state (main thread)."""
        self._append(f"{self.name}: {reply}\n\n", tag)
        self._entry.config(state="normal")
        self._entry.focus_set()
        if self._anim:
            self._anim.set_state("idle")

    # ----------------------------------------------------------- wake word

    def _on_wake(self):
        """Called from the wake-word background thread."""
        if self.root:
            self.root.after(0, self._handle_wake)

    def _handle_wake(self):
        """Runs on the tkinter main thread."""
        self.show()
        self._append(f"[{self.name} activado por voz]\n", "wake")
        if self._anim:
            self._anim.set_state("wake")
            # Return to idle after 1.5 s
            self.root.after(1500, lambda: self._anim.set_state("idle") if self._anim else None)
        if self._entry:
            self._entry.config(state="normal")
            self._entry.focus_set()

    # -------------------------------------------------------- window control

    def show(self):
        """Restore the window from minimized/hidden state and bring it to the front."""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

    def hide(self):
        """Withdraw the window without stopping the tray icon or agent."""
        if self.root:
            self.root.withdraw()

    def destroy(self):
        """Stop the wake-word listener, animation, and destroy the tkinter window."""
        if self._wake_listener:
            self._wake_listener.stop()
        if self._anim:
            self._anim.stop()
        if self.root:
            self.root.destroy()

    def run(self):
        """Build the window (hidden) and start the tkinter event loop."""
        self._build()
        self.root.withdraw()
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Pystray helpers
# ---------------------------------------------------------------------------

def _make_pystray_icon(name: str, pystray_mod):
    """Create a pystray Icon instance with the Jarvis circular icon image."""
    return pystray_mod.Icon("jarvis", _make_icon_image(), name)


def _build_menu(name: str, pystray_mod, on_open, on_quit):
    """Build the right-click context menu with Open and Quit items."""
    return pystray_mod.Menu(
        pystray_mod.MenuItem(f"Abrir {name}", on_open, default=True),
        pystray_mod.MenuItem("Salir", on_quit),
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_tray(
    agent,
    name: str = "Jarvis",
    wake_word: str = _DEFAULT_WAKE_WORD,
) -> None:
    """Start the system tray icon with animated chat window and wake-word detection.

    Linux  → pystray in background thread; tkinter on main thread.
    macOS  → pystray on main thread via setup(); tkinter in setup thread.
    """
    try:
        import pystray  # noqa: F401
    except ImportError:
        raise ImportError(
            "pystray no está instalado.\n"
            "Instala con: pip install pystray Pillow"
        )

    if _SYSTEM == "Linux":
        _run_linux(agent, name, wake_word)
    elif _SYSTEM == "Darwin":
        _run_macos(agent, name, wake_word)
    else:
        raise RuntimeError(f"Bandeja del sistema no soportada en {_SYSTEM}")


def _run_linux(agent, name: str, wake_word: str) -> None:
    """Linux path: pystray in a background thread, tkinter mainloop on the main thread."""
    import pystray

    win = _ChatWindow(agent, name, wake_word)

    def on_open(icon, item):
        if win.root:
            win.root.after(0, win.show)

    def on_quit(icon, item):
        if win.root:
            win.root.after(0, win.destroy)
        icon.stop()

    ico = _make_pystray_icon(name, pystray)
    ico.menu = _build_menu(name, pystray, on_open, on_quit)

    try:
        ico.run_detached()
    except AttributeError:
        threading.Thread(target=ico.run, daemon=True).start()

    win.run()   # tkinter mainloop on main thread


def _run_macos(agent, name: str, wake_word: str) -> None:
    """macOS path: pystray on the main thread via setup(); tkinter built inside setup()."""
    import pystray

    win_holder: list = [None]

    def setup(icon):
        icon.visible = True
        w = _ChatWindow(agent, name, wake_word)
        win_holder[0] = w
        w.run()

    def on_open(icon, item):
        w = win_holder[0]
        if w and w.root:
            w.root.after(0, w.show)

    def on_quit(icon, item):
        w = win_holder[0]
        if w and w.root:
            w.root.after(0, w.destroy)
        icon.stop()

    ico = _make_pystray_icon(name, pystray)
    ico.menu = _build_menu(name, pystray, on_open, on_quit)
    ico.run(setup=setup)
