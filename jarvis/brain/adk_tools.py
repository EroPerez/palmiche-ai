"""ADK-compatible tool wrappers for Jarvis.

Google ADK auto-generates tool schemas from function signatures and docstrings,
so each wrapper must have precise type hints and descriptive Args sections.

The docstrings here are written in English because ADK derives the tool schema
directly from them and many models invoke tools more reliably with English
schemas. A Spanish overlay (``ADK_TOOL_DOCS_ES``) plus ``get_adk_tools(lang)``
lets the ADK brain present its skills in either language without duplicating the
wrapper logic — see ``get_adk_tools`` for how the docstring is swapped per call.
"""
import functools
import inspect
import types
from typing import Literal, Optional

from ..tools.registry import _log_tool_call


def _with_logging(fn):
    """Wrap an ADK tool function to log its execution via the Jarvis tool logger."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        inputs = dict(bound.arguments)
        try:
            result = fn(*args, **kwargs)
            _log_tool_call(fn.__name__, inputs, str(result))
            return result
        except Exception as exc:
            msg = f"Error ejecutando {fn.__name__}: {exc}"
            _log_tool_call(fn.__name__, inputs, msg, error=True)
            raise
    return wrapper

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
from ..tools.calculator import calculate as _calculate, convert_units as _convert_units
from ..tools.weather import get_weather as _get_weather, get_forecast as _get_forecast
from ..tools.timer import (
    set_timer as _set_timer,
    set_alarm as _set_alarm,
    list_timers as _list_timers,
    cancel_timer as _cancel_timer,
)
from ..tools.events import (
    add_event as _add_event,
    list_events as _list_events,
    upcoming_events as _upcoming_events,
    delete_event as _delete_event,
)
from ..tools.notes import (
    create_note as _create_note,
    list_notes as _list_notes,
    read_note as _read_note,
    search_notes as _search_notes,
    delete_note as _delete_note,
)
from ..tools.text_tools import text_stats as _text_stats, text_transform as _text_transform
from ..tools.dev import (
    format_json as _format_json,
    hash_text as _hash_text,
    encode_decode as _encode_decode,
    generate_uuid as _generate_uuid,
    convert_timestamp as _convert_timestamp,
    http_request as _http_request,
    git_status as _git_status,
    find_process_on_port as _find_process_on_port,
)
from ..tools.computer_use import computer_use_task as _computer_use_task


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


def calculate(expression: str) -> str:
    """Evalúa una expresión matemática de forma segura. Soporta +−×÷^, funciones como sqrt/sin/log y constantes pi/e.

    Args:
        expression: Expresión a evaluar (ej: '2 + 3 * 4', 'sqrt(144)', 'sin(pi/2)').
    """
    return _calculate(expression)


def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convierte un valor entre unidades de medida (longitud, masa, temperatura, velocidad, área, volumen, almacenamiento).

    Args:
        value: Valor numérico a convertir.
        from_unit: Unidad de origen (ej: km, lb, °C, mph, gal).
        to_unit: Unidad de destino (ej: m, kg, °F, km/h, L).
    """
    return _convert_units(value, from_unit, to_unit)


def get_weather(city: str = "", units: Literal["metric", "imperial"] = "metric") -> str:
    """Obtiene las condiciones meteorológicas actuales para una ciudad.

    Args:
        city: Nombre de la ciudad. Si está vacío, se detecta automáticamente por IP.
        units: Sistema de unidades: metric (°C, km/h) o imperial (°F, mph).
    """
    return _get_weather(city, units)


def get_forecast(
    city: str = "",
    days: int = 3,
    units: Literal["metric", "imperial"] = "metric",
) -> str:
    """Obtiene el pronóstico del tiempo para los próximos días.

    Args:
        city: Nombre de la ciudad. Si está vacío, se detecta automáticamente por IP.
        days: Número de días a pronosticar (1-3). Por defecto: 3.
        units: Sistema de unidades: metric (°C) o imperial (°F).
    """
    return _get_forecast(city, days, units)


def set_timer(seconds: int, label: str = "") -> str:
    """Inicia un temporizador de cuenta regresiva. Envía una notificación de escritorio al finalizar.

    Args:
        seconds: Duración en segundos (máximo 86400 = 24h).
        label: Etiqueta descriptiva del temporizador (opcional).
    """
    return _set_timer(seconds, label)


def set_alarm(alarm_time: str, label: str = "") -> str:
    """Programa una alarma para una hora específica del día (formato HH:MM, 24h). Si ya pasó, se programa para mañana.

    Args:
        alarm_time: Hora de la alarma en formato HH:MM (ej: 08:30, 14:00).
        label: Etiqueta descriptiva de la alarma (opcional).
    """
    return _set_alarm(alarm_time, label)


def list_timers() -> str:
    """Lista todos los temporizadores activos con su tiempo restante."""
    return _list_timers()


def cancel_timer(timer_id: str) -> str:
    """Cancela un temporizador activo por su id.

    Args:
        timer_id: Id del temporizador (mostrado entre corchetes al crearlo).
    """
    return _cancel_timer(timer_id)


def add_event(
    title: str,
    date: str,
    time: str = "",
    description: str = "",
    location: str = "",
) -> str:
    """Crea un evento en el calendario local.

    Args:
        title: Título del evento.
        date: Fecha en formato YYYY-MM-DD, o 'hoy'/'mañana'.
        time: Hora en formato HH:MM (24h). Opcional.
        description: Descripción del evento. Opcional.
        location: Ubicación del evento. Opcional.
    """
    return _add_event(title, date, time, description, location)


def list_events(start: str = "", end: str = "") -> str:
    """Lista los eventos del calendario, opcionalmente filtrados por rango de fechas.

    Args:
        start: Fecha de inicio del filtro en formato YYYY-MM-DD o 'hoy'/'mañana'. Opcional.
        end: Fecha de fin del filtro en formato YYYY-MM-DD o 'hoy'/'mañana'. Opcional.
    """
    return _list_events(start, end)


def upcoming_events(days: int = 7) -> str:
    """Lista los próximos eventos desde hoy hasta N días en el futuro.

    Args:
        days: Número de días a mostrar (1-365). Por defecto: 7.
    """
    return _upcoming_events(days)


def delete_event(event_id: str) -> str:
    """Elimina un evento del calendario por su id.

    Args:
        event_id: Id corto del evento (mostrado entre corchetes al listarlo).
    """
    return _delete_event(event_id)


def create_note(title: str, content: str, tags: str = "") -> str:
    """Crea una nota personal o actualiza una existente con el mismo título.

    Args:
        title: Título de la nota.
        content: Contenido de la nota.
        tags: Etiquetas separadas por comas (ej: 'trabajo, ideas'). Opcional.
    """
    return _create_note(title, content, tags)


def list_notes(tag: str = "") -> str:
    """Lista todas las notas guardadas, opcionalmente filtradas por etiqueta.

    Args:
        tag: Etiqueta por la que filtrar. Si está vacío, muestra todas.
    """
    return _list_notes(tag)


def read_note(title: str) -> str:
    """Lee el contenido completo de una nota por título o por id.

    Args:
        title: Título o id corto de la nota.
    """
    return _read_note(title)


def search_notes(query: str) -> str:
    """Busca notas por título o contenido (sin distinción de mayúsculas).

    Args:
        query: Término de búsqueda.
    """
    return _search_notes(query)


def delete_note(title: str) -> str:
    """Elimina una nota por título o id.

    Args:
        title: Título o id corto de la nota a eliminar.
    """
    return _delete_note(title)


def text_stats(text: str) -> str:
    """Cuenta palabras, caracteres, líneas, oraciones y estima el tiempo de lectura de un texto.

    Args:
        text: Texto a analizar.
    """
    return _text_stats(text)


def text_transform(
    text: str,
    operation: Literal[
        "upper", "lower", "title", "capitalize", "reverse", "trim",
        "slug", "snake", "camel", "pascal", "strip_accents",
        "count_vowels", "palindrome",
    ],
) -> str:
    """Aplica una transformación de texto.

    Args:
        text: Texto de entrada.
        operation: Transformación a aplicar: upper, lower, title, capitalize, reverse, trim,
                   slug, snake, camel, pascal, strip_accents, count_vowels o palindrome.
    """
    return _text_transform(text, operation)


def format_json(text: str, indent: int = 2) -> str:
    """Valida y formatea un string JSON con la indentación indicada.

    Args:
        text: String JSON a formatear.
        indent: Nivel de indentación (espacios). Por defecto: 2.
    """
    return _format_json(text, indent)


def hash_text(text: str, algorithm: Literal["md5", "sha1", "sha256", "sha512"] = "sha256") -> str:
    """Calcula el hash hexadecimal de un texto.

    Args:
        text: Texto a hashear.
        algorithm: Algoritmo de hash: md5, sha1, sha256 o sha512. Por defecto: sha256.
    """
    return _hash_text(text, algorithm)


def encode_decode(
    text: str,
    scheme: Literal["base64", "url", "hex"] = "base64",
    operation: Literal["encode", "decode"] = "encode",
) -> str:
    """Codifica o decodifica texto usando base64, URL o hex.

    Args:
        text: Texto a procesar.
        scheme: Esquema de codificación: base64, url o hex.
        operation: encode para codificar, decode para decodificar.
    """
    return _encode_decode(text, scheme, operation)


def generate_uuid(count: int = 1) -> str:
    """Genera uno o más UUID4 aleatorios.

    Args:
        count: Número de UUIDs a generar (1-50). Por defecto: 1.
    """
    return _generate_uuid(count)


def convert_timestamp(value: str = "now") -> str:
    """Convierte entre timestamp Unix (epoch) e ISO-8601. 'now' devuelve la hora actual.

    Args:
        value: Valor a convertir: 'now', número epoch (entero/flotante) o fecha ISO-8601.
    """
    return _convert_timestamp(value)


def http_request(
    url: str,
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"] = "GET",
    body: str = "",
) -> str:
    """Realiza una petición HTTP y devuelve el estado, cabeceras clave y una previsualización del cuerpo.

    Args:
        url: URL de destino (con o sin esquema https://).
        method: Método HTTP: GET, POST, PUT, DELETE, PATCH o HEAD. Por defecto: GET.
        body: Cuerpo de la petición para POST/PUT/PATCH. Opcional.
    """
    return _http_request(url, method, body)


def git_status(path: str = ".") -> str:
    """Muestra la rama, el estado del árbol de trabajo y los últimos commits de un repositorio git.

    Args:
        path: Ruta al repositorio git. Por defecto: directorio actual.
    """
    return _git_status(path)


def find_process_on_port(port: int) -> str:
    """Encuentra qué proceso está escuchando en un puerto TCP.

    Args:
        port: Número de puerto a inspeccionar.
    """
    return _find_process_on_port(port)


def computer_use_task(
    task: str,
    backend: Literal["playwright", "desktop"] = "playwright",
    initial_url: str = "https://www.google.com",
    max_iterations: int = 30,
    model: str = "",
    headless: bool = True,
) -> str:
    """Ejecuta una tarea de uso de computadora usando la inteligencia visual de Gemini.

    Palmiche-AI tomará el control de un navegador (o el escritorio completo) y
    completará la tarea paso a paso usando la capacidad computer use de Gemini.

    Args:
        task: Descripción en lenguaje natural de lo que hacer (ej: 'Busca el clima en La Habana').
        backend: 'playwright' para control de navegador (predeterminado) o 'desktop' para control total del escritorio.
        initial_url: URL inicial al usar el backend playwright.
        max_iterations: Límite de seguridad en el número de iteraciones del agente.
        model: Modelo Gemini a usar. Por defecto usa COMPUTER_USE_MODEL o 'gemini-2.5-flash'.
        headless: Ejecutar el navegador en modo sin cabeza. Por defecto True; False para depurar.
    """
    return _computer_use_task(task, backend, initial_url, max_iterations, model, headless)


# ---------------------------------------------------------------------------
# Camera Vision — multimodal object & gesture recognition
# ---------------------------------------------------------------------------

from ..tools.camera import (
    camera_capture as _camera_capture,
    camera_describe as _camera_describe,
    camera_recognize_objects as _camera_recognize_objects,
    camera_recognize_gestures as _camera_recognize_gestures,
    camera_analyze as _camera_analyze,
    camera_monitor as _camera_monitor,
)


def camera_capture(save_path: str = "", camera_index: int = -1) -> str:
    """Capture a photo from the system camera and save it to a file.

    Args:
        save_path: Where to save the image. Default: ~/Capturas/camera_TIMESTAMP.jpg
        camera_index: Camera device index (0=default). -1 uses the configured default.
    """
    return _camera_capture(save_path, camera_index)


def camera_describe(prompt: str = "", camera_index: int = -1, save_path: str = "") -> str:
    """Capture a photo from the camera and describe the scene using the configured multimodal AI model.

    Identifies people, objects, colors, environment and details in the scene.

    Args:
        prompt: Custom prompt for the AI. Default: general scene description.
        camera_index: Camera device index. -1 uses the configured default.
        save_path: Optional path to save the captured image.
    """
    return _camera_describe(prompt, camera_index, save_path)


def camera_recognize_objects(camera_index: int = -1, save_path: str = "") -> str:
    """Capture a photo from the camera and identify all visible objects.

    Lists each object with its position in the frame, relative size and confidence level.

    Args:
        camera_index: Camera device index. -1 uses the configured default.
        save_path: Optional path to save the captured image.
    """
    return _camera_recognize_objects(camera_index, save_path)


def camera_recognize_gestures(camera_index: int = -1, save_path: str = "") -> str:
    """Capture a photo and recognize hand gestures and body language.

    Detects gestures like thumbs up, peace sign, fist, open palm, pointing, pinch, OK sign, etc.

    Args:
        camera_index: Camera device index. -1 uses the configured default.
        save_path: Optional path to save the captured image.
    """
    return _camera_recognize_gestures(camera_index, save_path)


def camera_analyze(prompt: str, camera_index: int = -1, save_path: str = "") -> str:
    """Capture a photo and analyze it with a custom prompt.

    Flexible visual Q&A: 'how many people?', 'what color is the shirt?', 'is the door open?', 'read the text on the sign', etc.

    Args:
        prompt: Question or instruction about what the camera sees.
        camera_index: Camera device index. -1 uses the configured default.
        save_path: Optional path to save the captured image.
    """
    return _camera_analyze(prompt, camera_index, save_path)


def camera_monitor(task: str = "", duration: int = 10, interval: int = 3, camera_index: int = -1) -> str:
    """Monitor the camera for a period, analyzing frames at regular intervals.

    Useful for detecting changes, counting people over time, watching activity, or waiting for specific events.

    Args:
        task: What to monitor for (e.g. 'count people', 'detect movement'). Default: general scene changes.
        duration: How many seconds to monitor (max 60). Default: 10.
        interval: Seconds between frame captures (min 2). Default: 3.
        camera_index: Camera device index. -1 uses the configured default.
    """
    return _camera_monitor(task, duration, interval, camera_index)


ADK_TOOLS = [
    _with_logging(get_system_info),
    _with_logging(get_battery_info),
    _with_logging(control_volume),
    _with_logging(control_brightness),
    _with_logging(power_action),
    _with_logging(open_application),
    _with_logging(close_application),
    _with_logging(list_running_apps),
    _with_logging(search_files),
    _with_logging(open_file),
    _with_logging(list_directory),
    _with_logging(read_file),
    _with_logging(create_directory),
    _with_logging(write_file),
    _with_logging(delete_file),
    _with_logging(move_file),
    _with_logging(copy_file),
    _with_logging(open_url),
    _with_logging(web_search),
    _with_logging(get_clipboard),
    _with_logging(set_clipboard),
    _with_logging(send_notification),
    _with_logging(run_shell_command),
    _with_logging(get_network_info),
    _with_logging(ping_host),
    _with_logging(media_control),
    _with_logging(get_media_status),
    _with_logging(take_screenshot),
    _with_logging(setup_autostart),
    _with_logging(calculate),
    _with_logging(convert_units),
    _with_logging(get_weather),
    _with_logging(get_forecast),
    _with_logging(set_timer),
    _with_logging(set_alarm),
    _with_logging(list_timers),
    _with_logging(cancel_timer),
    _with_logging(add_event),
    _with_logging(list_events),
    _with_logging(upcoming_events),
    _with_logging(delete_event),
    _with_logging(create_note),
    _with_logging(list_notes),
    _with_logging(read_note),
    _with_logging(search_notes),
    _with_logging(delete_note),
    _with_logging(text_stats),
    _with_logging(text_transform),
    _with_logging(format_json),
    _with_logging(hash_text),
    _with_logging(encode_decode),
    _with_logging(generate_uuid),
    _with_logging(convert_timestamp),
    _with_logging(http_request),
    _with_logging(git_status),
    _with_logging(find_process_on_port),
    _with_logging(computer_use_task),
    _with_logging(camera_capture),
    _with_logging(camera_describe),
    _with_logging(camera_recognize_objects),
    _with_logging(camera_recognize_gestures),
    _with_logging(camera_analyze),
    _with_logging(camera_monitor),
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
    "camera_capture": (
        "Captura una foto desde la cámara del sistema y la guarda en un archivo.\n\n"
        "    Args:\n"
        "        save_path: Ruta donde guardar la imagen. Default: ~/Capturas/camera_TIMESTAMP.jpg\n"
        "        camera_index: Índice del dispositivo de cámara (0=default). -1 usa el configurado.\n"
    ),
    "camera_describe": (
        "Captura una foto desde la cámara y describe la escena usando el modelo de IA multimodal configurado.\n\n"
        "    Args:\n"
        "        prompt: Prompt personalizado para la IA. Default: descripción general de la escena.\n"
        "        camera_index: Índice del dispositivo de cámara. -1 usa el configurado.\n"
        "        save_path: Ruta opcional para guardar la imagen capturada.\n"
    ),
    "camera_recognize_objects": (
        "Captura una foto desde la cámara e identifica todos los objetos visibles con posición, tamaño relativo y confianza.\n\n"
        "    Args:\n"
        "        camera_index: Índice del dispositivo de cámara. -1 usa el configurado.\n"
        "        save_path: Ruta opcional para guardar la imagen capturada.\n"
    ),
    "camera_recognize_gestures": (
        "Captura una foto desde la cámara y reconoce gestos de manos y lenguaje corporal.\n\n"
        "    Args:\n"
        "        camera_index: Índice del dispositivo de cámara. -1 usa el configurado.\n"
        "        save_path: Ruta opcional para guardar la imagen capturada.\n"
    ),
    "camera_analyze": (
        "Captura una foto y la analiza con un prompt personalizado. Flexible para cualquier pregunta visual.\n\n"
        "    Args:\n"
        "        prompt: Pregunta o instrucción sobre lo que se ve en la cámara.\n"
        "        camera_index: Índice del dispositivo de cámara. -1 usa el configurado.\n"
        "        save_path: Ruta opcional para guardar la imagen capturada.\n"
    ),
    "camera_monitor": (
        "Monitorea la cámara durante un período, analizando frames a intervalos regulares.\n\n"
        "    Args:\n"
        "        task: Qué monitorear (ej: 'contar personas', 'detectar movimiento'). Default: cambios generales.\n"
        "        duration: Segundos de monitoreo (máx 60). Default: 10.\n"
        "        interval: Segundos entre capturas (mín 2). Default: 3.\n"
        "        camera_index: Índice del dispositivo de cámara. -1 usa el configurado.\n"
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
