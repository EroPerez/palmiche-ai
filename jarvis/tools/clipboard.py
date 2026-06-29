import platform
import shutil
import subprocess

from ..config import JARVIS_SUDO_PASSWORD


def _ensure_clipboard_backend() -> None:
    """Install xclip on Linux if no clipboard backend is available."""
    if platform.system() != "Linux":
        return
    for cmd in ("xclip", "xsel", "wl-copy"):
        if shutil.which(cmd):
            return
    if not JARVIS_SUDO_PASSWORD:
        return
    try:
        subprocess.run(
            ["sudo", "-S", "apt-get", "install", "-y", "-qq", "xclip"],
            input=JARVIS_SUDO_PASSWORD + "\n",
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        pass


def get_clipboard() -> str:
    """Return a preview (up to 500 chars) of the current clipboard content."""
    try:
        _ensure_clipboard_backend()
        import pyperclip
        content = pyperclip.paste()
        if not content:
            return "El portapapeles está vacío"
        preview = content if len(content) <= 500 else content[:500] + "..."
        return f"Portapapeles:\n{preview}"
    except ImportError:
        return "pyperclip no instalado. Instala: pip install pyperclip"
    except Exception as e:
        return f"Error al leer portapapeles: {e}"


def set_clipboard(text: str) -> str:
    """Copy *text* to the clipboard and return the character count written."""
    try:
        _ensure_clipboard_backend()
        import pyperclip
        pyperclip.copy(text)
        return f"Texto copiado al portapapeles ({len(text)} caracteres)."
    except ImportError:
        return "pyperclip no instalado. Instala: pip install pyperclip"
    except Exception as e:
        return f"Error al escribir portapapeles: {e}"
