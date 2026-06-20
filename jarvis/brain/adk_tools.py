"""ADK-compatible tool wrappers for Jarvis.

Google ADK auto-generates tool schemas from function signatures and docstrings,
so each wrapper must have precise type hints and descriptive Args sections.
"""
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
)
from ..tools.web import open_url as _open_url, web_search as _web_search
from ..tools.clipboard import get_clipboard as _get_clipboard, set_clipboard as _set_clipboard
from ..tools.notifications import send_notification as _send_notification
from ..tools.shell import run_shell_command as _run_shell_command


def get_system_info() -> str:
    """Obtiene información del sistema: CPU, RAM, disco y uptime."""
    return _get_system_info()


def get_battery_info() -> str:
    """Obtiene el estado de la batería: porcentaje, estado de carga y tiempo restante."""
    return _get_battery_info()


def control_volume(
    action: Literal["get", "set", "up", "down", "mute", "unmute"],
    value: Optional[int] = None,
) -> str:
    """Controla el volumen del sistema.

    Args:
        action: Acción de volumen: get, set, up, down, mute o unmute.
        value: Valor 0-100 para 'set', o incremento para 'up'/'down'.
    """
    return _control_volume(action, value)


def control_brightness(
    action: Literal["get", "set", "up", "down"],
    value: Optional[int] = None,
) -> str:
    """Controla el brillo de la pantalla. Linux: requiere brightnessctl.

    Args:
        action: Acción de brillo: get, set, up o down.
        value: Valor 0-100 para 'set', o incremento para 'up'/'down'.
    """
    return _control_brightness(action, value)


def power_action(action: Literal["shutdown", "restart", "sleep", "lock"]) -> str:
    """Controla el estado de energía del sistema.

    Args:
        action: shutdown, restart, sleep o lock.
    """
    return _power_action(action)


def open_application(name: str) -> str:
    """Abre una aplicación o programa.

    Args:
        name: Nombre o comando de la aplicación (ej: firefox, code, spotify).
    """
    return _open_application(name)


def close_application(name: str, force: bool = False) -> str:
    """Cierra una aplicación por nombre de proceso.

    Args:
        name: Nombre del proceso a cerrar.
        force: Si es True usa SIGKILL; por defecto SIGTERM.
    """
    return _close_application(name, force)


def list_running_apps(filter: Optional[str] = None) -> str:
    """Lista los procesos en ejecución con uso de memoria.

    Args:
        filter: Filtro opcional por nombre de proceso.
    """
    return _list_running_apps(filter)


def search_files(
    pattern: str,
    directory: str = "~",
    file_type: Literal["any", "file", "directory"] = "any",
) -> str:
    """Busca archivos o directorios en el sistema de archivos.

    Args:
        pattern: Nombre o patrón a buscar (ej: '*.pdf', 'proyecto').
        directory: Directorio donde buscar. Por defecto: ~ (home).
        file_type: Tipo de elemento: any, file o directory.
    """
    return _search_files(pattern, directory, file_type)


def open_file(path: str) -> str:
    """Abre un archivo con la aplicación predeterminada del sistema.

    Args:
        path: Ruta al archivo.
    """
    return _open_file(path)


def list_directory(path: str = "~", show_hidden: bool = False) -> str:
    """Lista el contenido de un directorio.

    Args:
        path: Ruta del directorio. Por defecto: ~ (home).
        show_hidden: Si es True muestra archivos ocultos (que empiezan con punto).
    """
    return _list_directory(path, show_hidden)


def read_file(path: str, max_lines: int = 100) -> str:
    """Lee el contenido de un archivo de texto.

    Args:
        path: Ruta al archivo.
        max_lines: Máximo de líneas a leer. Por defecto: 100.
    """
    return _read_file(path, max_lines)


def create_directory(path: str) -> str:
    """Crea un directorio, incluyendo directorios padre si no existen.

    Args:
        path: Ruta del directorio a crear.
    """
    return _create_directory(path)


def open_url(url: str) -> str:
    """Abre una URL en el navegador predeterminado.

    Args:
        url: URL a abrir.
    """
    return _open_url(url)


def web_search(
    query: str,
    engine: Literal["google", "duckduckgo", "youtube"] = "google",
) -> str:
    """Abre una búsqueda web en el navegador.

    Args:
        query: Término de búsqueda.
        engine: Motor de búsqueda: google, duckduckgo o youtube.
    """
    return _web_search(query, engine)


def get_clipboard() -> str:
    """Obtiene el contenido actual del portapapeles."""
    return _get_clipboard()


def set_clipboard(text: str) -> str:
    """Escribe texto en el portapapeles.

    Args:
        text: Texto a copiar.
    """
    return _set_clipboard(text)


def send_notification(
    title: str,
    message: str,
    urgency: Literal["low", "normal", "critical"] = "normal",
) -> str:
    """Envía una notificación de escritorio.

    Args:
        title: Título de la notificación.
        message: Cuerpo del mensaje.
        urgency: Nivel de urgencia: low, normal o critical.
    """
    return _send_notification(title, message, urgency)


def run_shell_command(command: str, working_dir: str = "~") -> str:
    """Ejecuta un comando de shell arbitrario. Usar solo cuando no haya herramienta dedicada. Timeout: 30 segundos.

    Args:
        command: Comando a ejecutar.
        working_dir: Directorio de trabajo. Por defecto: ~.
    """
    return _run_shell_command(command, working_dir)


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
    open_url,
    web_search,
    get_clipboard,
    set_clipboard,
    send_notification,
    run_shell_command,
]
