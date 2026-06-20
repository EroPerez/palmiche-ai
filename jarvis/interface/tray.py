"""System tray interface for Jarvis.

Provides a taskbar icon with a tkinter chat window.
- Linux:  pystray runs in background thread; tkinter on main thread.
- macOS:  pystray on main thread via setup(); tkinter in setup thread.

Requires: pip install pystray Pillow
"""
import platform
import threading

_SYSTEM = platform.system()


# ---------------------------------------------------------------------------
# Icon image
# ---------------------------------------------------------------------------

def _make_icon_image(size: int = 64):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, size - 2, size - 2], fill=(30, 100, 220, 255))
    margin = size // 5
    d.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(255, 255, 255, 40),
    )
    return img


# ---------------------------------------------------------------------------
# Chat window (tkinter)
# ---------------------------------------------------------------------------

class _ChatWindow:
    def __init__(self, agent, name: str):
        self.agent = agent
        self.name = name
        self.root = None
        self._display = None
        self._entry = None

    # --- build ---

    def _build(self):
        import tkinter as tk
        from tkinter import scrolledtext

        self.root = tk.Tk()
        self.root.title(self.name)
        self.root.geometry("700x560")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        # Header bar
        header = tk.Frame(self.root, bg="#181825", pady=6)
        header.pack(fill=tk.X)
        tk.Label(
            header, text=f"  {self.name}",
            bg="#181825", fg="#89b4fa",
            font=("Monospace", 11, "bold"),
        ).pack(side=tk.LEFT)

        # Chat display
        self._display = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap=tk.WORD,
            font=("Monospace", 10), bg="#1e1e2e", fg="#cdd6f4",
            insertbackground="white", padx=10, pady=8, bd=0,
            selectbackground="#313244",
        )
        self._display.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))
        self._display.tag_configure("user", foreground="#89b4fa", font=("Monospace", 10, "bold"))
        self._display.tag_configure("jarvis", foreground="#a6e3a1")
        self._display.tag_configure("system", foreground="#f5c2e7", font=("Monospace", 9, "italic"))
        self._display.tag_configure("error", foreground="#f38ba8")

        # Input row
        row = tk.Frame(self.root, bg="#313244", pady=4)
        row.pack(fill=tk.X, padx=8, pady=8)

        self._entry = tk.Entry(
            row, font=("Monospace", 10),
            bg="#313244", fg="#cdd6f4", insertbackground="white",
            relief=tk.FLAT, bd=6,
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._entry.bind("<Return>", self._on_send)
        self._entry.bind("<KP_Enter>", self._on_send)

        tk.Button(
            row, text="↩", command=self._on_send,
            bg="#89b4fa", fg="#1e1e2e", relief=tk.FLAT,
            padx=12, font=("Monospace", 11, "bold"), cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(4, 0))

        self._append(f"Sistema: {self.name} listo\n", "system")

    # --- I/O helpers ---

    def _append(self, text: str, tag: str = ""):
        self._display.config(state="normal")
        self._display.insert(tk.END, text, tag)
        self._display.config(state="disabled")
        self._display.see(tk.END)

    def _on_send(self, _event=None):
        msg = self._entry.get().strip()
        if not msg:
            return
        self._entry.delete(0, "end")
        self._entry.config(state="disabled")
        self._append(f"Tú: {msg}\n", "user")
        threading.Thread(target=self._call_agent, args=(msg,), daemon=True).start()

    def _call_agent(self, msg: str):
        try:
            reply = self.agent.chat(msg)
            tag = "jarvis"
        except Exception as exc:
            reply = f"Error: {exc}"
            tag = "error"
        self.root.after(0, self._on_reply, reply, tag)

    def _on_reply(self, reply: str, tag: str):
        self._append(f"{self.name}: {reply}\n\n", tag)
        self._entry.config(state="normal")
        self._entry.focus_set()

    # --- window control ---

    def show(self):
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()

    def hide(self):
        if self.root:
            self.root.withdraw()

    def destroy(self):
        if self.root:
            self.root.destroy()

    def run(self):
        """Build window (hidden) and start tkinter mainloop."""
        self._build()
        self.root.withdraw()
        self.root.mainloop()


# ---------------------------------------------------------------------------
# Tray runner
# ---------------------------------------------------------------------------

def _make_pystray_icon(name: str, pystray):
    return pystray.Icon("jarvis", _make_icon_image(), name)


def _build_menu(name: str, pystray, on_open, on_quit):
    return pystray.Menu(
        pystray.MenuItem(f"Abrir {name}", on_open, default=True),
        pystray.MenuItem("Salir", on_quit),
    )


def run_tray(agent, name: str = "Jarvis") -> None:
    """Start the system tray icon with a chat window.

    - Linux: pystray background thread, tkinter on main thread.
    - macOS: pystray on main thread (setup callback), tkinter in setup thread.
    """
    try:
        import pystray  # noqa: F401 (checked here, used below)
    except ImportError:
        raise ImportError(
            "pystray no está instalado.\n"
            "Instala con: pip install pystray Pillow"
        )

    if _SYSTEM == "Linux":
        _run_linux(agent, name)
    elif _SYSTEM == "Darwin":
        _run_macos(agent, name)
    else:
        raise RuntimeError(f"Bandeja del sistema no soportada en {_SYSTEM}")


def _run_linux(agent, name: str) -> None:
    import pystray

    win = _ChatWindow(agent, name)

    def on_open(icon, item):
        if win.root:
            win.root.after(0, win.show)

    def on_quit(icon, item):
        if win.root:
            win.root.after(0, win.destroy)
        icon.stop()

    ico = _make_pystray_icon(name, pystray)
    ico.menu = _build_menu(name, pystray, on_open, on_quit)

    # Run pystray in background; tkinter on main thread
    try:
        ico.run_detached()
    except AttributeError:
        threading.Thread(target=ico.run, daemon=True).start()

    win.run()  # blocks until window closed


def _run_macos(agent, name: str) -> None:
    import pystray

    win_holder: list = [None]

    def setup(icon):
        icon.visible = True
        w = _ChatWindow(agent, name)
        win_holder[0] = w
        w.run()  # tkinter in setup thread (macOS best-effort)

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
    ico.run(setup=setup)  # blocks main thread (required on macOS)
