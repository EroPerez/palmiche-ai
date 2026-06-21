"""System tray interface for Jarvis.

Features:
- Taskbar icon (pystray) — click to show/hide the chat window
- Dark-themed chat window (tkinter, Catppuccin Mocha)
- Waveform animation in the header (idle / wake / thinking states)
- Message timestamps and a bottom status bar (Listo / procesando / escuchando)
- Clear button (🗑) and keyboard shortcuts: Esc hides, Ctrl+L clears the chat
- Window centered on screen with a sensible minimum size
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
from datetime import datetime

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
        self._mic_btn = None       # microphone input button
        self._status = None        # bottom status-bar label
        self._busy = False         # True while the agent is processing

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
        self.root.minsize(420, 360)
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self._center_window(720, 580)

        # Keyboard shortcuts: Esc hides, Ctrl+L clears the conversation.
        self.root.bind("<Escape>", lambda _e: self.hide())
        self.root.bind("<Control-l>", lambda _e: self._clear_chat())
        self.root.bind("<Control-L>", lambda _e: self._clear_chat())

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
        self._display.tag_configure("time",    foreground="#6c7086",
                                     font=("Monospace", 8))

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

        self._mic_btn = tk.Button(
            row, text="🎤", command=self._start_voice_input,
            bg="#313244", fg="#cdd6f4", relief=tk.FLAT,
            padx=8, font=("Monospace", 11), cursor="hand2",
            activebackground="#45475a", activeforeground="#f9e2af",
        )
        self._mic_btn.pack(side=tk.RIGHT, padx=(4, 0))

        tk.Button(
            row, text="🗑", command=self._clear_chat,
            bg="#313244", fg="#cdd6f4", relief=tk.FLAT,
            padx=8, font=("Monospace", 11), cursor="hand2",
            activebackground="#45475a", activeforeground="#f38ba8",
        ).pack(side=tk.RIGHT, padx=(4, 0))

        # ── Status bar ───────────────────────────────────────────────────────
        self._status = tk.Label(
            self.root, anchor="w", text="", bg="#181825", fg="#a6adc8",
            font=("Monospace", 9), padx=10, pady=3,
        )
        self._status.pack(fill=tk.X)

        self._append(f"Sistema: {self.name} listo\n", "system")
        self._set_status("Listo", "#a6e3a1")

        # ── Wake word listener ───────────────────────────────────────────────
        self._wake_listener = WakeWordListener(
            wake_word=self.wake_word,
            on_wake=self._on_wake,
            on_command=self._on_voice_command,
        )
        self._wake_listener.start()

    # ---------------------------------------------------------------- I/O

    def _append(self, text: str, tag: str = "", stamp: bool = False):
        """Append *text* with *tag* styling; if *stamp*, prefix a dim [HH:MM] timestamp."""
        self._display.config(state="normal")
        if stamp:
            self._display.insert("end", f"[{datetime.now():%H:%M}] ", "time")
        self._display.insert("end", text, tag)
        self._display.config(state="disabled")
        self._display.see("end")

    def _set_status(self, text: str, color: str = "#a6adc8"):
        """Update the bottom status-bar text and color (no-op if not built yet)."""
        if self._status:
            self._status.config(text=text, fg=color)

    def _clear_chat(self):
        """Clear the chat display and the agent's conversation history."""
        if self._busy:
            return
        if self._display:
            self._display.config(state="normal")
            self._display.delete("1.0", "end")
            self._display.config(state="disabled")
        history = getattr(self.agent, "history", None)
        if history is not None and hasattr(history, "clear"):
            try:
                history.clear()
            except Exception:  # noqa: BLE001 - clearing history must never crash the UI
                pass
        self._append(f"Sistema: {self.name} listo\n", "system")
        self._set_status("Historial borrado", "#f5c2e7")

    def _center_window(self, width: int, height: int):
        """Position the window at the center of the screen."""
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 3)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:  # noqa: BLE001 - centering is cosmetic
            pass

    def _on_send(self, _event=None):
        """Read the input field, echo the user message, and dispatch agent call in a thread."""
        msg = self._entry.get().strip()
        if not msg:
            return
        self._entry.delete(0, "end")
        self._entry.config(state="disabled")
        self._busy = True
        self._append(f"Tú: {msg}\n", "user", stamp=True)
        if self._anim:
            self._anim.set_state("thinking")
        self._set_status(f"{self.name} está procesando…", "#89dceb")
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
        self._append(f"{self.name}: {reply}\n\n", tag, stamp=True)
        self._busy = False
        self._entry.config(state="normal")
        self._entry.focus_set()
        if self._anim:
            self._anim.set_state("idle")
        self._set_status("Listo", "#a6e3a1")

    # ----------------------------------------------------------- wake word

    def _on_wake(self):
        """Called from the wake-word background thread."""
        if self.root:
            self.root.after(0, self._handle_wake)

    def _handle_wake(self):
        """Runs on the tkinter main thread."""
        self.show()
        self._append(f"[{self.name} activado por voz]\n", "wake")
        self._set_status("Activado por voz — escuchando…", "#f9e2af")
        if self._anim:
            self._anim.set_state("wake")
            # Return to idle after 1.5 s
            self.root.after(1500, self._wake_to_idle)
        if self._entry:
            self._entry.config(state="normal")
            self._entry.focus_set()

    def _wake_to_idle(self):
        """Return the animation and status bar to idle after a wake burst."""
        if self._anim:
            self._anim.set_state("idle")
        if not self._busy:
            self._set_status("Listo", "#a6e3a1")

    # --------------------------------------------------------- voice input

    def _start_voice_input(self):
        """Activate one-shot voice capture from the mic button."""
        if not self._wake_listener:
            return
        self._append("[Escuchando comando de voz…]\n", "wake")
        self._set_status("Escuchando comando de voz…", "#f9e2af")
        if self._anim:
            self._anim.set_state("wake")
        if self._mic_btn:
            self._mic_btn.config(state="disabled", bg="#45475a")
        if self._entry:
            self._entry.config(state="disabled")
        self._wake_listener.listen_once(self._on_voice_input_done)

    def _on_voice_command(self, text: str):
        """Called from background thread when a post-wake voice command is transcribed."""
        if self.root:
            self.root.after(0, self._dispatch_voice_command, text)

    def _dispatch_voice_command(self, text: str):
        """Populate the entry with the voice command and send it (main thread)."""
        if self._entry:
            self._entry.config(state="normal")
            self._entry.delete(0, "end")
            self._entry.insert(0, text)
        self._on_send()

    def _on_voice_input_done(self, text):
        """Callback from listen_once — schedule UI update on the main thread."""
        if self.root:
            self.root.after(0, self._apply_voice_input, text)

    def _apply_voice_input(self, text):
        """Populate the entry with transcribed text and send, or report failure (main thread)."""
        if self._mic_btn:
            self._mic_btn.config(state="normal", bg="#313244")
        if self._anim:
            self._anim.set_state("idle")
        if text:
            if self._entry:
                self._entry.config(state="normal")
                self._entry.delete(0, "end")
                self._entry.insert(0, text)
            self._on_send()
        else:
            self._append("[No se entendió el comando de voz]\n", "system")
            self._set_status("No se entendió el comando de voz", "#f38ba8")
            if self._entry:
                self._entry.config(state="normal")

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
        ) from None

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
        try:
            w = _ChatWindow(agent, name, wake_word)
            win_holder[0] = w
            w.run()
        except Exception as exc:
            icon.stop()
            raise RuntimeError(f"Error al iniciar la ventana de chat: {exc}") from exc

    def on_open(icon, item):
        w = win_holder[0]
        if w and w.root:
            w.root.after(0, w.show)

    def on_quit(icon, item):
        w = win_holder[0]
        if w and w.root:
            w.root.after(0, w.destroy)
        icon.stop()

    try:
        ico = _make_pystray_icon(name, pystray)
        ico.menu = _build_menu(name, pystray, on_open, on_quit)
        ico.run(setup=setup)
    except Exception as exc:
        raise RuntimeError(f"Error al iniciar la bandeja del sistema en macOS: {exc}") from exc
