"""ADK-compatible tool wrappers for Jarvis.

Google ADK auto-generates tool schemas from function signatures and docstrings,
so each wrapper must have precise type hints and descriptive Args sections.
"""
import functools
import inspect
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


def list_running_apps(filter: Optional[str] = None) -> str:  # noqa: A002
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


def write_file(path: str, content: str, mode: str = "write") -> str:
    """Escribe o agrega contenido en un archivo de texto.

    Args:
        path: Ruta del archivo de destino.
        content: Contenido a escribir.
        mode: 'write' para sobreescribir (default) o 'append' para añadir al final.
    """
    return _write_file(path, content, mode)


def delete_file(path: str) -> str:
    """Elimina un archivo o directorio vacío.

    Args:
        path: Ruta del archivo o directorio a eliminar.
    """
    return _delete_file(path)


def move_file(source: str, destination: str) -> str:
    """Mueve o renombra un archivo o directorio.

    Args:
        source: Ruta de origen.
        destination: Ruta de destino.
    """
    return _move_file(source, destination)


def copy_file(source: str, destination: str) -> str:
    """Copia un archivo o directorio a otra ubicación.

    Args:
        source: Ruta de origen.
        destination: Ruta de destino.
    """
    return _copy_file(source, destination)


def get_network_info() -> str:
    """Obtiene IP local, IP pública, SSID de WiFi activo y estado de conexión."""
    return _get_network_info()


def ping_host(host: str, count: int = 4) -> str:
    """Hace ping a un host y devuelve latencia y pérdida de paquetes.

    Args:
        host: Hostname o IP a hacer ping.
        count: Número de paquetes a enviar (1-10). Por defecto: 4.
    """
    return _ping_host(host, count)


def media_control(action: Literal["play", "pause", "next", "previous", "stop", "status"]) -> str:
    """Controla la reproducción de medios (música/video).

    Args:
        action: play, pause, next, previous, stop o status.
    """
    return _media_control(action)


def get_media_status() -> str:
    """Obtiene el título, artista y estado actual del reproductor de medios activo."""
    return _get_media_status()


def take_screenshot(path: Optional[str] = None, selection: bool = False) -> str:
    """Toma una captura de pantalla y la guarda en un archivo.

    Args:
        path: Ruta del archivo de destino. Si no se indica, se guarda en ~/Capturas/ con timestamp.
        selection: Si es True, permite seleccionar un área de la pantalla.
    """
    return _take_screenshot(path, selection)


def setup_autostart(
    enable: bool = True,
    tray: bool = True,
    backend: Literal["anthropic", "adk", "gemini"] = "anthropic",
) -> str:
    """Configura o desactiva el arranque automático de Jarvis con el sistema.

    Args:
        enable: True para activar el arranque automático, False para desactivarlo.
        tray: Si True arranca en modo bandeja del sistema. Por defecto: True.
        backend: Backend a usar al arrancar: anthropic, adk o gemini. Por defecto: anthropic.
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
]
