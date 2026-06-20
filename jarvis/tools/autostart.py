import platform
import subprocess
import sys
from pathlib import Path

_VALID_BACKENDS = {"anthropic", "adk", "gemini", "ollama"}


def _desktop_escape(s: str) -> str:
    """Escape a string for use in a Desktop Entry Exec value."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace(" ", "\\ ")


def setup_autostart(enable: bool = True, tray: bool = True, backend: str = "anthropic") -> str:
    """Configura o elimina el arranque automático de Jarvis con el sistema.

    Args:
        enable: True para activar, False para desactivar.
        tray: Si True, arranca en modo bandeja del sistema; si False, modo CLI.
        backend: Backend a usar al arrancar: 'anthropic', 'adk', 'gemini' u 'ollama'.
    """
    if backend not in _VALID_BACKENDS:
        return f"Backend inválido: '{backend}'. Usa uno de: {', '.join(sorted(_VALID_BACKENDS))}"

    system = platform.system()
    python = sys.executable
    cmd_parts = [python, "-m", "jarvis", "--backend", backend]
    if tray:
        cmd_parts.append("--tray")

    if system == "Linux":
        return _autostart_linux(enable, cmd_parts)
    if system == "Darwin":
        return _autostart_macos(enable, cmd_parts)
    return f"Arranque automático no soportado en {system}"


def _autostart_linux(enable: bool, cmd_parts: list) -> str:
    autostart_dir = Path.home() / ".config" / "autostart"
    desktop_file = autostart_dir / "jarvis-ai.desktop"

    if not enable:
        if desktop_file.exists():
            desktop_file.unlink()
            return "Arranque automático desactivado"
        return "No había arranque automático configurado"

    autostart_dir.mkdir(parents=True, exist_ok=True)
    exec_line = " ".join(_desktop_escape(p) for p in cmd_parts)
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Jarvis AI\n"
        f"Exec={exec_line}\n"
        "Hidden=false\n"
        "NoDisplay=false\n"
        "X-GNOME-Autostart-enabled=true\n"
        "Comment=Just A Rather Very Intelligent System\n"
    )
    desktop_file.write_text(content, encoding="utf-8")
    return f"Arranque automático activado: {desktop_file}"


def _autostart_macos(enable: bool, cmd_parts: list) -> str:
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_file = plist_dir / "ai.palmiche.jarvis.plist"

    if not enable:
        if plist_file.exists():
            try:
                subprocess.run(["launchctl", "unload", str(plist_file)], check=False)
            except FileNotFoundError:
                pass
            plist_file.unlink()
            return "Arranque automático desactivado"
        return "No había arranque automático configurado"

    plist_dir.mkdir(parents=True, exist_ok=True)
    args_xml = "\n".join(f"        <string>{a}</string>" for a in cmd_parts)
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"'
        ' "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n'
        "    <key>Label</key>\n"
        "    <string>ai.palmiche.jarvis</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"{args_xml}\n"
        "    </array>\n"
        "    <key>RunAtLoad</key>\n"
        "    <true/>\n"
        "    <key>KeepAlive</key>\n"
        "    <false/>\n"
        "</dict>\n</plist>\n"
    )
    plist_file.write_text(content, encoding="utf-8")
    try:
        result = subprocess.run(
            ["launchctl", "load", str(plist_file)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            return (
                f"Archivo creado en {plist_file} pero launchctl falló"
                + (f": {stderr}" if stderr else "")
            )
    except FileNotFoundError:
        return f"Arranque automático configurado: {plist_file} (launchctl no encontrado)"
    return f"Arranque automático activado: {plist_file}"
