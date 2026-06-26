"""ADK-compatible tool wrappers for Jarvis.

Google ADK auto-generates tool schemas from function signatures and docstrings,
so each wrapper must have precise type hints and descriptive Args sections.

The docstrings here are written in English because ADK derives the tool schema
directly from them and many models invoke tools more reliably with English
schemas. A Spanish overlay (``ADK_TOOL_DOCS_ES``) plus ``get_adk_tools(lang)``
lets the ADK brain present its skills in either language without duplicating the
wrapper logic — see ``get_adk_tools`` for how the docstring is swapped per call.
"""
import types
from typing import Literal, Optional

from ..tools.system import (
    get_system_info as _get_system_info,
    get_battery_info as _get_battery_info,
    control_volume as _control_volume,
    control_brightness as _control_brightness,
    power_action as _power_action,
)
from ..tools.apps import (
    open_application as _open_application,
    close_application as _close_application,
    list_running_apps as _list_running_apps,
)
from ..tools.files import (
    search_files as _search_files,
    open_file as _open_file,
    list_directory as _list_directory,
    read_file as _read_file,
    create_directory as _create_directory,
    write_file as _write_file,
    delete_file as _delete_file,
    move_file as _move_file,
    copy_file as _copy_file,
)
from ..tools.web import open_url as _open_url, web_search as _web_search
from ..tools.clipboard import get_clipboard as _get_clipboard, set_clipboard as _set_clipboard
from ..tools.notifications import send_notification as _send_notification
from ..tools.shell import run_shell_command as _run_shell_command
from ..tools.network import get_network_info as _get_network_info, ping_host as _ping_host
from ..tools.media import media_control as _media_control, get_media_status as _get_media_status
from ..tools.screenshot import take_screenshot as _take_screenshot
from ..tools.autostart import setup_autostart as _setup_autostart


def get_system_info() -> str:
    """Get system information: CPU, RAM, disk and uptime."""
    return _get_system_info()


def get_battery_info() -> str:
    """Get battery status: percentage, charging state and time remaining."""
    return _get_battery_info()


def control_volume(
    action: Literal["get", "set", "up", "down", "mute", "unmute"],
    value: Optional[int] = None,
) -> str:
    """Control the system volume.

    Args:
        action: Volume action: get, set, up, down, mute or unmute.
        value: Value 0-100 for 'set', or step for 'up'/'down'.
    """
    return _control_volume(action, value)


def control_brightness(
    action: Literal["get", "set", "up", "down"],
    value: Optional[int] = None,
) -> str:
    """Control screen brightness. Linux: requires brightnessctl.

    Args:
        action: Brightness action: get, set, up or down.
        value: Value 0-100 for 'set', or step for 'up'/'down'.
    """
    return _control_brightness(action, value)


def power_action(action: Literal["shutdown", "restart", "sleep", "lock"]) -> str:
    """Control the system power state.

    Args:
        action: shutdown, restart, sleep or lock.
    """
    return _power_action(action)


def open_application(name: str) -> str:
    """Open an application or program.

    Args:
        name: Application name or command (e.g. firefox, code, spotify).
    """
    return _open_application(name)


def close_application(name: str, force: bool = False) -> str:
    """Close an application by process name.

    Args:
        name: Name of the process to close.
        force: If True uses SIGKILL; defaults to SIGTERM.
    """
    return _close_application(name, force)


def list_running_apps(filter: Optional[str] = None) -> str:  # noqa: A002
    """List running processes with memory usage.

    Args:
        filter: Optional filter by process name.
    """
    return _list_running_apps(filter)


def search_files(
    pattern: str,
    directory: str = "~",
    file_type: Literal["any", "file", "directory"] = "any",
) -> str:
    """Search for files or directories in the filesystem.

    Args:
        pattern: Name or pattern to search for (e.g. '*.pdf', 'project').
        directory: Directory to search in. Default: ~ (home).
        file_type: Item type: any, file or directory.
    """
    return _search_files(pattern, directory, file_type)


def open_file(path: str) -> str:
    """Open a file with the system's default application.

    Args:
        path: Path to the file.
    """
    return _open_file(path)


def list_directory(path: str = "~", show_hidden: bool = False) -> str:
    """List the contents of a directory.

    Args:
        path: Directory path. Default: ~ (home).
        show_hidden: If True, show hidden files (those starting with a dot).
    """
    return _list_directory(path, show_hidden)


def read_file(path: str, max_lines: int = 100) -> str:
    """Read the contents of a text file.

    Args:
        path: Path to the file.
        max_lines: Maximum number of lines to read. Default: 100.
    """
    return _read_file(path, max_lines)


def create_directory(path: str) -> str:
    """Create a directory, including parent directories if missing.

    Args:
        path: Path of the directory to create.
    """
    return _create_directory(path)


def open_url(url: str) -> str:
    """Open a URL in the default browser.

    Args:
        url: URL to open.
    """
    return _open_url(url)


def web_search(
    query: str,
    engine: Literal["google", "duckduckgo", "youtube"] = "google",
) -> str:
    """Open a web search in the browser.

    Args:
        query: Search term.
        engine: Search engine: google, duckduckgo or youtube.
    """
    return _web_search(query, engine)


def get_clipboard() -> str:
    """Get the current clipboard contents."""
    return _get_clipboard()


def set_clipboard(text: str) -> str:
    """Write text to the clipboard.

    Args:
        text: Text to copy.
    """
    return _set_clipboard(text)


def send_notification(
    title: str,
    message: str,
    urgency: Literal["low", "normal", "critical"] = "normal",
) -> str:
    """Send a desktop notification.

    Args:
        title: Notification title.
        message: Message body.
        urgency: Urgency level: low, normal or critical.
    """
    return _send_notification(title, message, urgency)


def run_shell_command(command: str, working_dir: str = "~") -> str:
    """Run an arbitrary shell command. Use only when there is no dedicated tool. Timeout: 30 seconds.

    Args:
        command: Command to run.
        working_dir: Working directory. Default: ~.
    """
    return _run_shell_command(command, working_dir)


def write_file(path: str, content: str, mode: str = "write") -> str:
    """Write or append content to a text file.

    Args:
        path: Target file path.
        content: Content to write.
        mode: 'write' to overwrite (default) or 'append' to add to the end.
    """
    return _write_file(path, content, mode)


def delete_file(path: str) -> str:
    """Delete a file or empty directory.

    Args:
        path: Path of the file or directory to delete.
    """
    return _delete_file(path)


def move_file(source: str, destination: str) -> str:
    """Move or rename a file or directory.

    Args:
        source: Source path.
        destination: Destination path.
    """
    return _move_file(source, destination)


def copy_file(source: str, destination: str) -> str:
    """Copy a file or directory to another location.

    Args:
        source: Source path.
        destination: Destination path.
    """
    return _copy_file(source, destination)


def get_network_info() -> str:
    """Get local IP, public IP, active WiFi SSID and connection status."""
    return _get_network_info()


def ping_host(host: str, count: int = 4) -> str:
    """Ping a host and return latency and packet loss.

    Args:
        host: Hostname or IP to ping.
        count: Number of packets to send (1-10). Default: 4.
    """
    return _ping_host(host, count)


def media_control(action: Literal["play", "pause", "next", "previous", "stop", "status"]) -> str:
    """Control media playback (music/video).

    Args:
        action: play, pause, next, previous, stop or status.
    """
    return _media_control(action)


def get_media_status() -> str:
    """Get the title, artist and current state of the active media player."""
    return _get_media_status()


def take_screenshot(path: Optional[str] = None, selection: bool = False) -> str:
    """Take a screenshot and save it to a file.

    Args:
        path: Target file path. If omitted, saved to ~/Capturas/ with a timestamp.
        selection: If True, lets you select a screen area.
    """
    return _take_screenshot(path, selection)


def setup_autostart(
    enable: bool = True,
    tray: bool = True,
    backend: Literal["anthropic", "adk", "gemini"] = "anthropic",
) -> str:
    """Enable or disable Jarvis autostart with the system.

    Args:
        enable: True to enable autostart, False to disable it.
        tray: If True, start in system tray mode. Default: True.
        backend: Backend to use on startup: anthropic, adk or gemini. Default: anthropic.
    """
    return _setup_autostart(enable, tray, backend)


ADK_TOOLS = [
    get_system_info,
    get_battery_info,
    control_volume,
    control_brightness,
    power_action,
    open_application,
    close_application,
    list_running_apps,
    search_files,
    open_file,
    list_directory,
    read_file,
    create_directory,
    write_file,
    delete_file,
    move_file,
    copy_file,
    open_url,
    web_search,
    get_clipboard,
    set_clipboard,
    send_notification,
    run_shell_command,
    get_network_info,
    ping_host,
    media_control,
    get_media_status,
    take_screenshot,
    setup_autostart,
]


# ---------------------------------------------------------------------------
# Spanish docstring overlay
#
# ADK reads each tool's schema from its ``__doc__`` when the Agent is built, so
# to offer Spanish skills we hand ADK fresh function objects whose ``__doc__``
# has been swapped — the code, signature and annotations are untouched.
# ---------------------------------------------------------------------------
ADK_TOOL_DOCS_ES: dict[str, str] = {
    "get_system_info": "Obtiene información del sistema: CPU, RAM, disco y uptime.",
    "get_battery_info": "Obtiene el estado de la batería: porcentaje, estado de carga y tiempo restante.",
    "control_volume": (
        "Controla el volumen del sistema.\n\n"
        "    Args:\n"
        "        action: Acción de volumen: get, set, up, down, mute o unmute.\n"
        "        value: Valor 0-100 para 'set', o incremento para 'up'/'down'.\n"
    ),
    "control_brightness": (
        "Controla el brillo de la pantalla. Linux: requiere brightnessctl.\n\n"
        "    Args:\n"
        "        action: Acción de brillo: get, set, up o down.\n"
        "        value: Valor 0-100 para 'set', o incremento para 'up'/'down'.\n"
    ),
    "power_action": (
        "Controla el estado de energía del sistema.\n\n"
        "    Args:\n"
        "        action: shutdown, restart, sleep o lock.\n"
    ),
    "open_application": (
        "Abre una aplicación o programa.\n\n"
        "    Args:\n"
        "        name: Nombre o comando de la aplicación (ej: firefox, code, spotify).\n"
    ),
    "close_application": (
        "Cierra una aplicación por nombre de proceso.\n\n"
        "    Args:\n"
        "        name: Nombre del proceso a cerrar.\n"
        "        force: Si es True usa SIGKILL; por defecto SIGTERM.\n"
    ),
    "list_running_apps": (
        "Lista los procesos en ejecución con uso de memoria.\n\n"
        "    Args:\n"
        "        filter: Filtro opcional por nombre de proceso.\n"
    ),
    "search_files": (
        "Busca archivos o directorios en el sistema de archivos.\n\n"
        "    Args:\n"
        "        pattern: Nombre o patrón a buscar (ej: '*.pdf', 'proyecto').\n"
        "        directory: Directorio donde buscar. Por defecto: ~ (home).\n"
        "        file_type: Tipo de elemento: any, file o directory.\n"
    ),
    "open_file": (
        "Abre un archivo con la aplicación predeterminada del sistema.\n\n"
        "    Args:\n"
        "        path: Ruta al archivo.\n"
    ),
    "list_directory": (
        "Lista el contenido de un directorio.\n\n"
        "    Args:\n"
        "        path: Ruta del directorio. Por defecto: ~ (home).\n"
        "        show_hidden: Si es True muestra archivos ocultos (que empiezan con punto).\n"
    ),
    "read_file": (
        "Lee el contenido de un archivo de texto.\n\n"
        "    Args:\n"
        "        path: Ruta al archivo.\n"
        "        max_lines: Máximo de líneas a leer. Por defecto: 100.\n"
    ),
    "create_directory": (
        "Crea un directorio, incluyendo directorios padre si no existen.\n\n"
        "    Args:\n"
        "        path: Ruta del directorio a crear.\n"
    ),
    "open_url": (
        "Abre una URL en el navegador predeterminado.\n\n"
        "    Args:\n"
        "        url: URL a abrir.\n"
    ),
    "web_search": (
        "Abre una búsqueda web en el navegador.\n\n"
        "    Args:\n"
        "        query: Término de búsqueda.\n"
        "        engine: Motor de búsqueda: google, duckduckgo o youtube.\n"
    ),
    "get_clipboard": "Obtiene el contenido actual del portapapeles.",
    "set_clipboard": (
        "Escribe texto en el portapapeles.\n\n"
        "    Args:\n"
        "        text: Texto a copiar.\n"
    ),
    "send_notification": (
        "Envía una notificación de escritorio.\n\n"
        "    Args:\n"
        "        title: Título de la notificación.\n"
        "        message: Cuerpo del mensaje.\n"
        "        urgency: Nivel de urgencia: low, normal o critical.\n"
    ),
    "run_shell_command": (
        "Ejecuta un comando de shell arbitrario. Usar solo cuando no haya herramienta dedicada. Timeout: 30 segundos.\n\n"
        "    Args:\n"
        "        command: Comando a ejecutar.\n"
        "        working_dir: Directorio de trabajo. Por defecto: ~.\n"
    ),
    "write_file": (
        "Escribe o agrega contenido en un archivo de texto.\n\n"
        "    Args:\n"
        "        path: Ruta del archivo de destino.\n"
        "        content: Contenido a escribir.\n"
        "        mode: 'write' para sobreescribir (default) o 'append' para añadir al final.\n"
    ),
    "delete_file": (
        "Elimina un archivo o directorio vacío.\n\n"
        "    Args:\n"
        "        path: Ruta del archivo o directorio a eliminar.\n"
    ),
    "move_file": (
        "Mueve o renombra un archivo o directorio.\n\n"
        "    Args:\n"
        "        source: Ruta de origen.\n"
        "        destination: Ruta de destino.\n"
    ),
    "copy_file": (
        "Copia un archivo o directorio a otra ubicación.\n\n"
        "    Args:\n"
        "        source: Ruta de origen.\n"
        "        destination: Ruta de destino.\n"
    ),
    "get_network_info": "Obtiene IP local, IP pública, SSID de WiFi activo y estado de conexión.",
    "ping_host": (
        "Hace ping a un host y devuelve latencia y pérdida de paquetes.\n\n"
        "    Args:\n"
        "        host: Hostname o IP a hacer ping.\n"
        "        count: Número de paquetes a enviar (1-10). Por defecto: 4.\n"
    ),
    "media_control": (
        "Controla la reproducción de medios (música/video).\n\n"
        "    Args:\n"
        "        action: play, pause, next, previous, stop o status.\n"
    ),
    "get_media_status": "Obtiene el título, artista y estado actual del reproductor de medios activo.",
    "take_screenshot": (
        "Toma una captura de pantalla y la guarda en un archivo.\n\n"
        "    Args:\n"
        "        path: Ruta del archivo de destino. Si no se indica, se guarda en ~/Capturas/ con timestamp.\n"
        "        selection: Si es True, permite seleccionar un área de la pantalla.\n"
    ),
    "setup_autostart": (
        "Configura o desactiva el arranque automático de Jarvis con el sistema.\n\n"
        "    Args:\n"
        "        enable: True para activar el arranque automático, False para desactivarlo.\n"
        "        tray: Si True arranca en modo bandeja del sistema. Por defecto: True.\n"
        "        backend: Backend a usar al arrancar: anthropic, adk o gemini. Por defecto: anthropic.\n"
    ),
}


def _with_docstring(fn, doc: str):
    """Return a fresh function object identical to *fn* but with ``__doc__`` set to *doc*."""
    clone = types.FunctionType(
        fn.__code__,
        fn.__globals__,
        name=fn.__name__,
        argdefs=fn.__defaults__,
        closure=fn.__closure__,
    )
    clone.__dict__.update(fn.__dict__)
    clone.__annotations__ = dict(fn.__annotations__)
    clone.__kwdefaults__ = fn.__kwdefaults__
    clone.__doc__ = doc
    return clone


def get_adk_tools(lang: str | None = None) -> list:
    """Return the ADK tool callables with docstrings localized to *lang*.

    English ('en') returns the canonical wrappers as-is. Spanish ('es') returns
    clones whose docstrings come from ``ADK_TOOL_DOCS_ES``. When *lang* is None,
    the configured ``JARVIS_TOOL_LANG`` is used.
    """
    if lang is None:
        from ..config import JARVIS_TOOL_LANG
        lang = JARVIS_TOOL_LANG
    if lang != "es":
        return ADK_TOOLS
    return [
        _with_docstring(fn, ADK_TOOL_DOCS_ES[fn.__name__]) if fn.__name__ in ADK_TOOL_DOCS_ES else fn
        for fn in ADK_TOOLS
    ]
