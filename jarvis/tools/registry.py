from .system import get_system_info, get_battery_info, control_volume, control_brightness, power_action
from .apps import open_application, close_application, list_running_apps
from .files import (
    search_files, open_file, list_directory, read_file, create_directory,
    write_file, delete_file, move_file, copy_file,
)
from .web import open_url, web_search, fetch_webpage, get_rss_feed
from .clipboard import get_clipboard, set_clipboard
from .notifications import send_notification
from .shell import run_shell_command
from .network import get_network_info, ping_host
from .media import media_control, get_media_status
from .screenshot import take_screenshot
from .autostart import setup_autostart
from .events import add_event, list_events, upcoming_events, delete_event
from .dev import (
    format_json, hash_text, encode_decode, generate_uuid,
    convert_timestamp, http_request, git_status, find_process_on_port,
)
from .weather import get_weather, get_forecast
from .notes import create_note, list_notes, read_note, search_notes, delete_note
from .timer import set_timer, set_alarm, list_timers, cancel_timer
from .calculator import calculate, convert_units
from .text_tools import text_stats, text_transform

TOOL_DEFINITIONS = [
    {
        "name": "get_system_info",
        "description": "Obtiene información del sistema: CPU, RAM, disco, uptime",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_battery_info",
        "description": "Obtiene estado de la batería: porcentaje, estado de carga, tiempo restante",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "control_volume",
        "description": "Controla el volumen del sistema (get/set/up/down/mute/unmute)",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "up", "down", "mute", "unmute"],
                    "description": "Acción de volumen",
                },
                "value": {
                    "type": "integer",
                    "description": "Valor 0-100 para 'set', o incremento para 'up'/'down'",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "control_brightness",
        "description": "Controla el brillo de la pantalla (get/set/up/down). Linux: requiere brightnessctl.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "up", "down"],
                    "description": "Acción de brillo",
                },
                "value": {
                    "type": "integer",
                    "description": "Valor 0-100 para 'set', o incremento para 'up'/'down'",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "power_action",
        "description": (
            "Controla el estado de energía: apagar, reiniciar, suspender o bloquear pantalla. "
            "Para shutdown/restart/sleep pide confirmación explícita al usuario antes de llamar esta herramienta con confirmed=true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["shutdown", "restart", "sleep", "lock"],
                    "description": "Acción de energía",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó explícitamente esta acción destructiva",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "open_application",
        "description": "Abre una aplicación o programa",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre o comando de la aplicación (ej: firefox, code, spotify, nautilus)",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "close_application",
        "description": "Cierra una aplicación por nombre de proceso",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre del proceso a cerrar",
                },
                "force": {
                    "type": "boolean",
                    "description": "Forzar cierre inmediato (SIGKILL). Default: false (SIGTERM)",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó explícitamente cerrar esta aplicación. Pasar true tras obtener confirmación.",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "list_running_apps",
        "description": "Lista los procesos/aplicaciones en ejecución con uso de memoria",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Filtro opcional por nombre de proceso",
                }
            },
            "required": [],
        },
    },
    {
        "name": "search_files",
        "description": "Busca archivos o directorios en el sistema de archivos",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Nombre o patrón a buscar (ej: '*.pdf', 'proyecto')",
                },
                "directory": {
                    "type": "string",
                    "description": "Directorio donde buscar. Default: ~ (home)",
                },
                "file_type": {
                    "type": "string",
                    "enum": ["any", "file", "directory"],
                    "description": "Tipo de elemento. Default: any",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "open_file",
        "description": "Abre un archivo con la aplicación predeterminada del sistema",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta al archivo"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "Lista el contenido de un directorio",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ruta del directorio. Default: ~ (home)",
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Mostrar archivos ocultos (comenzando con punto)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "read_file",
        "description": "Lee el contenido de un archivo de texto",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta al archivo"},
                "max_lines": {
                    "type": "integer",
                    "description": "Máximo de líneas a leer. Default: 100",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "create_directory",
        "description": "Crea un directorio (incluyendo directorios padre si no existen)",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del directorio a crear"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "open_url",
        "description": "Abre una URL en el navegador predeterminado",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL a abrir"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_search",
        "description": "Abre una búsqueda web en el navegador en modo incógnito/privado para no dejar historial. Default: Google.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda"},
                "engine": {
                    "type": "string",
                    "enum": ["google", "duckduckgo", "youtube"],
                    "description": "Motor de búsqueda. Default: google",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_clipboard",
        "description": "Obtiene el contenido actual del portapapeles",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_clipboard",
        "description": "Escribe texto en el portapapeles",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a copiar"}
            },
            "required": ["text"],
        },
    },
    {
        "name": "send_notification",
        "description": "Envía una notificación de escritorio",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título"},
                "message": {"type": "string", "description": "Cuerpo del mensaje"},
                "urgency": {
                    "type": "string",
                    "enum": ["low", "normal", "critical"],
                    "description": "Nivel de urgencia. Default: normal",
                },
            },
            "required": ["title", "message"],
        },
    },
    {
        "name": "run_shell_command",
        "description": (
            "Ejecuta un comando de shell arbitrario. "
            "Usar solo cuando no haya herramienta dedicada. Timeout: 30 segundos. "
            "Explica al usuario qué hará el comando y confirma antes de llamar con confirmed=true. "
            "Si el comando usa sudo y JARVIS_SUDO_PASSWORD está configurada, la contraseña se pasa automáticamente. "
            "Si el comando falla por permisos insuficientes, el resultado lo indicará y puedes reintentar con use_sudo=true "
            "después de informar al usuario y obtener su confirmación."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Comando a ejecutar"},
                "working_dir": {
                    "type": "string",
                    "description": "Directorio de trabajo. Default: ~",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó que este comando puede ejecutarse",
                },
                "use_sudo": {
                    "type": "boolean",
                    "description": (
                        "Reintentar el comando con sudo. Usar cuando un comando previo falló por permisos. "
                        "Requiere confirmación del usuario y JARVIS_SUDO_PASSWORD configurada."
                    ),
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "write_file",
        "description": "Escribe o agrega contenido en un archivo de texto",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del archivo de destino"},
                "content": {"type": "string", "description": "Contenido a escribir"},
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "description": "'write' para sobreescribir (default) o 'append' para añadir al final",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó explícitamente la escritura/sobreescritura. Pasar true tras obtener confirmación.",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "delete_file",
        "description": "Elimina un archivo o directorio vacío",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del archivo o directorio a eliminar"},
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó explícitamente la eliminación. Pasar true tras obtener confirmación.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "move_file",
        "description": "Mueve o renombra un archivo o directorio",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Ruta de origen"},
                "destination": {"type": "string", "description": "Ruta de destino"},
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó explícitamente la operación. Pasar true tras obtener confirmación.",
                },
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "copy_file",
        "description": "Copia un archivo o directorio a otra ubicación",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Ruta de origen"},
                "destination": {"type": "string", "description": "Ruta de destino"},
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "get_network_info",
        "description": "Obtiene IP local, IP pública, SSID de WiFi y estado de red",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ping_host",
        "description": "Hace ping a un host y devuelve latencia y pérdida de paquetes",
        "input_schema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Hostname o IP a hacer ping"},
                "count": {
                    "type": "integer",
                    "description": "Número de paquetes a enviar (1-10). Default: 4",
                },
            },
            "required": ["host"],
        },
    },
    {
        "name": "media_control",
        "description": "Controla la reproducción de medios: música, video (play/pause/next/previous/stop/status)",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play", "pause", "next", "previous", "stop", "status"],
                    "description": "Acción de reproducción",
                }
            },
            "required": ["action"],
        },
    },
    {
        "name": "get_media_status",
        "description": "Obtiene el título, artista y estado actual del reproductor de medios activo",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "take_screenshot",
        "description": "Toma una captura de pantalla y la guarda en un archivo",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Ruta del archivo de destino. Si no se indica, se guarda en ~/Capturas/ con timestamp",
                },
                "selection": {
                    "type": "boolean",
                    "description": "Si es true, permite seleccionar un área de la pantalla",
                },
            },
            "required": [],
        },
    },
    {
        "name": "setup_autostart",
        "description": "Configura o desactiva el arranque automático de Jarvis con el sistema",
        "input_schema": {
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "True para activar el arranque automático, False para desactivarlo",
                },
                "tray": {
                    "type": "boolean",
                    "description": "Si True arranca en modo bandeja del sistema (default: True)",
                },
                "backend": {
                    "type": "string",
                    "enum": ["anthropic", "adk", "gemini", "ollama"],
                    "description": "Backend a usar al arrancar. Default: anthropic",
                },
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó explícitamente el cambio de configuración de arranque. Pasar true tras obtener confirmación.",
                },
            },
            "required": ["enable"],
        },
    },
    {
        "name": "add_event",
        "description": "Crea un evento en el calendario local. Fecha en YYYY-MM-DD (o 'hoy'/'mañana'), hora opcional HH:MM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título del evento"},
                "date": {"type": "string", "description": "Fecha YYYY-MM-DD o 'hoy'/'mañana'"},
                "time": {"type": "string", "description": "Hora HH:MM (24h), opcional"},
                "description": {"type": "string", "description": "Descripción opcional"},
                "location": {"type": "string", "description": "Lugar opcional"},
            },
            "required": ["title", "date"],
        },
    },
    {
        "name": "list_events",
        "description": "Lista eventos del calendario ordenados por fecha. Acepta un rango opcional start/end (YYYY-MM-DD).",
        "input_schema": {
            "type": "object",
            "properties": {
                "start": {"type": "string", "description": "Fecha inicial del rango (YYYY-MM-DD), opcional"},
                "end": {"type": "string", "description": "Fecha final del rango (YYYY-MM-DD), opcional"},
            },
            "required": [],
        },
    },
    {
        "name": "upcoming_events",
        "description": "Lista los próximos eventos desde hoy durante N días (default 7).",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Número de días a futuro (default 7)"},
            },
            "required": [],
        },
    },
    {
        "name": "delete_event",
        "description": "Elimina un evento del calendario por su id (el que aparece entre corchetes al listar).",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "Id del evento a eliminar"},
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "format_json",
        "description": "Valida e indenta (pretty-print) una cadena JSON.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Cadena JSON a formatear"},
                "indent": {"type": "integer", "description": "Espacios de indentación (default 2)"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "hash_text",
        "description": "Calcula el hash de un texto (md5, sha1, sha256 o sha512).",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a hashear"},
                "algorithm": {
                    "type": "string",
                    "enum": ["md5", "sha1", "sha256", "sha512"],
                    "description": "Algoritmo (default sha256)",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "encode_decode",
        "description": "Codifica o decodifica texto con base64, url o hex.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto de entrada"},
                "scheme": {
                    "type": "string",
                    "enum": ["base64", "url", "hex"],
                    "description": "Esquema (default base64)",
                },
                "operation": {
                    "type": "string",
                    "enum": ["encode", "decode"],
                    "description": "Operación (default encode)",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "generate_uuid",
        "description": "Genera uno o más UUID4 aleatorios.",
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Cantidad de UUIDs (default 1, máx 50)"},
            },
            "required": [],
        },
    },
    {
        "name": "convert_timestamp",
        "description": "Convierte entre epoch Unix e ISO-8601. Usa 'now' para la hora actual.",
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {"type": "string", "description": "Epoch (número), fecha ISO-8601, o 'now'"},
            },
            "required": [],
        },
    },
    {
        "name": "http_request",
        "description": (
            "Hace una petición HTTP y devuelve status, headers clave y un preview del cuerpo. Útil para probar APIs. "
            "GET/HEAD no requieren confirmación. POST/PUT/PATCH/DELETE mutan estado externo: informa al usuario y llama con confirmed=true."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL a consultar"},
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
                    "description": "Método HTTP (default GET)",
                },
                "body": {"type": "string", "description": "Cuerpo de la petición (para POST/PUT/PATCH)"},
                "confirmed": {
                    "type": "boolean",
                    "description": "El usuario confirmó la petición mutante (POST/PUT/PATCH/DELETE). No requerido para GET/HEAD.",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "git_status",
        "description": "Muestra rama, estado del árbol de trabajo y últimos commits de un repositorio git.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del repositorio (default: directorio actual)"},
            },
            "required": [],
        },
    },
    {
        "name": "find_process_on_port",
        "description": "Indica qué proceso está escuchando en un puerto TCP.",
        "input_schema": {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "description": "Número de puerto"},
            },
            "required": ["port"],
        },
    },
    # ── Weather ──────────────────────────────────────────────────────────────
    {
        "name": "get_weather",
        "description": (
            "Obtiene el clima actual para una ciudad (temperatura, humedad, viento, visibilidad). "
            "Si no se especifica ciudad, usa la ubicación por IP. No requiere API key."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Ciudad o lugar (ej: 'Madrid', 'New York'). Vacío = detectar por IP.",
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "Sistema de unidades: metric (°C, km/h) o imperial (°F, mph). Default: metric.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_forecast",
        "description": "Obtiene el pronóstico del tiempo para los próximos 1-3 días.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Ciudad o lugar. Vacío = detectar por IP.",
                },
                "days": {
                    "type": "integer",
                    "description": "Número de días de pronóstico (1-3). Default: 3.",
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "Sistema de unidades. Default: metric.",
                },
            },
            "required": [],
        },
    },
    # ── Notes ─────────────────────────────────────────────────────────────────
    {
        "name": "create_note",
        "description": "Crea o actualiza una nota personal con título, contenido y etiquetas opcionales.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título de la nota"},
                "content": {"type": "string", "description": "Contenido de la nota"},
                "tags": {
                    "type": "string",
                    "description": "Etiquetas separadas por coma (ej: 'trabajo, ideas')",
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "list_notes",
        "description": "Lista todas las notas guardadas, opcionalmente filtradas por etiqueta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tag": {"type": "string", "description": "Filtrar por etiqueta (opcional)"},
            },
            "required": [],
        },
    },
    {
        "name": "read_note",
        "description": "Lee el contenido completo de una nota por título o id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título o id de la nota"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "search_notes",
        "description": "Busca notas por título o contenido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "delete_note",
        "description": "Elimina una nota por título o id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Título o id de la nota a eliminar"},
            },
            "required": ["title"],
        },
    },
    # ── Timers & Alarms ───────────────────────────────────────────────────────
    {
        "name": "set_timer",
        "description": (
            "Inicia un temporizador que envía una notificación de escritorio al finalizar. "
            "Corre en segundo plano; el proceso debe seguir activo."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "integer",
                    "description": "Duración en segundos (máx 86400 = 24h)",
                },
                "label": {
                    "type": "string",
                    "description": "Descripción del temporizador (opcional)",
                },
            },
            "required": ["seconds"],
        },
    },
    {
        "name": "set_alarm",
        "description": "Configura una alarma para una hora específica del día (formato HH:MM, 24h). Si ya pasó, se programa para mañana.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alarm_time": {
                    "type": "string",
                    "description": "Hora de la alarma en formato HH:MM (ej: '08:30', '14:00')",
                },
                "label": {
                    "type": "string",
                    "description": "Descripción de la alarma (opcional)",
                },
            },
            "required": ["alarm_time"],
        },
    },
    {
        "name": "list_timers",
        "description": "Muestra todos los temporizadores activos con el tiempo restante.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "cancel_timer",
        "description": "Cancela un temporizador activo por su id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timer_id": {"type": "string", "description": "Id del temporizador (6 caracteres)"},
            },
            "required": ["timer_id"],
        },
    },
    # ── Calculator & Unit Converter ───────────────────────────────────────────
    {
        "name": "calculate",
        "description": (
            "Evalúa expresiones matemáticas de forma segura. Soporta +−×÷^, sqrt, sin/cos/tan, "
            "log, abs, round, factorial, y constantes pi/e. Ej: 'sqrt(144)', '2^10', 'sin(pi/2)'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Expresión matemática a evaluar",
                },
            },
            "required": ["expression"],
        },
    },
    {
        "name": "convert_units",
        "description": (
            "Convierte entre unidades de medida. Categorías: longitud (m, km, mi, ft, in…), "
            "masa (kg, g, lb, oz…), temperatura (°C, °F, K), velocidad (km/h, mph, m/s, kt), "
            "área, volumen, almacenamiento digital (GB, MB…)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "description": "Valor numérico a convertir",
                },
                "from_unit": {
                    "type": "string",
                    "description": "Unidad de origen (ej: 'km', 'lb', '°C', 'GB')",
                },
                "to_unit": {
                    "type": "string",
                    "description": "Unidad de destino (ej: 'mi', 'kg', '°F', 'MB')",
                },
            },
            "required": ["value", "from_unit", "to_unit"],
        },
    },
    # ── Text Tools ────────────────────────────────────────────────────────────
    {
        "name": "text_stats",
        "description": "Analiza un texto y devuelve estadísticas: palabras, caracteres, líneas, oraciones y tiempo estimado de lectura.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a analizar"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "text_transform",
        "description": (
            "Transforma un texto aplicando una operación. Operaciones disponibles: "
            "upper, lower, title, capitalize, reverse, trim, slug, snake, camel, pascal, "
            "strip_accents, count_vowels, palindrome."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a transformar"},
                "operation": {
                    "type": "string",
                    "enum": [
                        "upper", "lower", "title", "capitalize", "reverse", "trim",
                        "slug", "snake", "camel", "pascal", "strip_accents",
                        "count_vowels", "palindrome",
                    ],
                    "description": "Transformación a aplicar",
                },
            },
            "required": ["text", "operation"],
        },
    },
    # ── Web content ───────────────────────────────────────────────────────────
    {
        "name": "fetch_webpage",
        "description": (
            "Descarga y extrae el texto legible de una página web (elimina HTML, scripts y estilos). "
            "Útil para leer artículos, documentación o cualquier contenido web."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL de la página a leer"},
                "max_chars": {
                    "type": "integer",
                    "description": "Máximo de caracteres a devolver (500-10000, default 3000)",
                },
            },
            "required": ["url"],
        },
    },
    {
        "name": "get_rss_feed",
        "description": "Obtiene las últimas entradas de un feed RSS o Atom: título, enlace y fecha de publicación.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL del feed RSS/Atom"},
                "max_items": {
                    "type": "integer",
                    "description": "Número máximo de entradas a mostrar (default 10)",
                },
            },
            "required": ["url"],
        },
    },
]


DESTRUCTIVE_TOOLS = {
    # System power — irreversible state changes; may invoke sudo
    "power_action",
    # Arbitrary shell execution; explicit use_sudo parameter
    "run_shell_command",
    # Modifies user/session startup config
    "setup_autostart",
    # File mutations — data loss risk
    "write_file",
    "delete_file",
    "move_file",
    # Process termination (SIGTERM / SIGKILL with force=True)
    "close_application",
    # Non-GET HTTP requests mutate external state (POST/PUT/PATCH/DELETE)
    # Note: confirmation is checked per-method in execute_tool, not via this set
    "http_request",
}


import json
import logging
from datetime import datetime
from ..config import JARVIS_LOG_FILE, JARVIS_LOG_ENABLED

_tool_logger: logging.Logger | None = None


def _get_tool_logger() -> logging.Logger | None:
    """Return (and lazily configure) the tool-execution logger."""
    global _tool_logger
    if not JARVIS_LOG_ENABLED:
        return None
    if _tool_logger is not None:
        return _tool_logger
    _tool_logger = logging.getLogger("jarvis.tools")
    _tool_logger.setLevel(logging.DEBUG)
    _tool_logger.propagate = False
    try:
        handler = logging.FileHandler(str(JARVIS_LOG_FILE), encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        _tool_logger.addHandler(handler)
    except OSError:
        _tool_logger = None
    return _tool_logger


def _log_tool_call(name: str, inputs: dict, result: str, error: bool = False) -> None:
    """Write a structured log entry for a tool execution."""
    logger = _get_tool_logger()
    if logger is None:
        return
    safe_inputs = {k: v for k, v in inputs.items() if k != "confirmed"}
    entry = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"{'ERROR' if error else 'OK'} | {name}\n"
        f"  inputs: {json.dumps(safe_inputs, ensure_ascii=False, default=str)}\n"
        f"  result: {result[:1000]}"
    )
    if len(result) > 1000:
        entry += "\n  ... (truncado en log)"
    logger.info(entry + "\n")


def execute_tool(name: str, inputs: dict) -> str:
    """Dispatch *name* to the appropriate tool handler, enforcing confirmation for destructive tools."""
    needs_confirm = name in DESTRUCTIVE_TOOLS
    if name == "http_request":
        # Only mutating methods require confirmation; GET/HEAD are safe reads
        needs_confirm = inputs.get("method", "GET").upper() not in ("GET", "HEAD")
    if needs_confirm and not inputs.get("confirmed", False):
        return (
            f"Confirmación requerida para '{name}'. "
            "Informa al usuario qué acción se va a realizar y pide confirmación explícita. "
            "Luego vuelve a llamar con confirmed=true."
        )

    handlers = {
        "get_system_info": lambda i: get_system_info(),
        "get_battery_info": lambda i: get_battery_info(),
        "control_volume": lambda i: control_volume(i.get("action"), i.get("value")),
        "control_brightness": lambda i: control_brightness(i.get("action"), i.get("value")),
        "power_action": lambda i: power_action(i["action"]),
        "open_application": lambda i: open_application(i["name"]),
        "close_application": lambda i: close_application(i["name"], i.get("force", False)),
        "list_running_apps": lambda i: list_running_apps(i.get("filter")),
        "search_files": lambda i: search_files(
            i["pattern"], i.get("directory", "~"), i.get("file_type", "any")
        ),
        "open_file": lambda i: open_file(i["path"]),
        "list_directory": lambda i: list_directory(
            i.get("path", "~"), i.get("show_hidden", False)
        ),
        "read_file": lambda i: read_file(i["path"], i.get("max_lines", 100)),
        "create_directory": lambda i: create_directory(i["path"]),
        "open_url": lambda i: open_url(i["url"]),
        "web_search": lambda i: web_search(i["query"], i.get("engine", "google")),
        "get_clipboard": lambda i: get_clipboard(),
        "set_clipboard": lambda i: set_clipboard(i["text"]),
        "send_notification": lambda i: send_notification(
            i["title"], i["message"], i.get("urgency", "normal")
        ),
        "run_shell_command": lambda i: run_shell_command(
            i["command"], i.get("working_dir", "~"), i.get("use_sudo", False)
        ),
        "write_file": lambda i: write_file(i["path"], i["content"], i.get("mode", "write")),
        "delete_file": lambda i: delete_file(i["path"]),
        "move_file": lambda i: move_file(i["source"], i["destination"]),
        "copy_file": lambda i: copy_file(i["source"], i["destination"]),
        "get_network_info": lambda i: get_network_info(),
        "ping_host": lambda i: ping_host(i["host"], i.get("count", 4)),
        "media_control": lambda i: media_control(i["action"]),
        "get_media_status": lambda i: get_media_status(),
        "take_screenshot": lambda i: take_screenshot(i.get("path"), i.get("selection", False)),
        "setup_autostart": lambda i: setup_autostart(
            i["enable"], i.get("tray", True), i.get("backend", "anthropic")
        ),
        "add_event": lambda i: add_event(
            i["title"], i["date"], i.get("time", ""),
            i.get("description", ""), i.get("location", ""),
        ),
        "list_events": lambda i: list_events(i.get("start", ""), i.get("end", "")),
        "upcoming_events": lambda i: upcoming_events(i.get("days", 7)),
        "delete_event": lambda i: delete_event(i["event_id"]),
        "format_json": lambda i: format_json(i["text"], i.get("indent", 2)),
        "hash_text": lambda i: hash_text(i["text"], i.get("algorithm", "sha256")),
        "encode_decode": lambda i: encode_decode(
            i["text"], i.get("scheme", "base64"), i.get("operation", "encode")
        ),
        "generate_uuid": lambda i: generate_uuid(i.get("count", 1)),
        "convert_timestamp": lambda i: convert_timestamp(i.get("value", "now")),
        "http_request": lambda i: http_request(
            i["url"], i.get("method", "GET"), i.get("body", "")
        ),
        "git_status": lambda i: git_status(i.get("path", ".")),
        "find_process_on_port": lambda i: find_process_on_port(i["port"]),
        # Weather
        "get_weather": lambda i: get_weather(i.get("city", ""), i.get("units", "metric")),
        "get_forecast": lambda i: get_forecast(i.get("city", ""), i.get("days", 3), i.get("units", "metric")),
        # Notes
        "create_note": lambda i: create_note(i["title"], i["content"], i.get("tags", "")),
        "list_notes": lambda i: list_notes(i.get("tag", "")),
        "read_note": lambda i: read_note(i["title"]),
        "search_notes": lambda i: search_notes(i["query"]),
        "delete_note": lambda i: delete_note(i["title"]),
        # Timers
        "set_timer": lambda i: set_timer(i["seconds"], i.get("label", "")),
        "set_alarm": lambda i: set_alarm(i["alarm_time"], i.get("label", "")),
        "list_timers": lambda i: list_timers(),
        "cancel_timer": lambda i: cancel_timer(i["timer_id"]),
        # Calculator & units
        "calculate": lambda i: calculate(i["expression"]),
        "convert_units": lambda i: convert_units(i["value"], i["from_unit"], i["to_unit"]),
        # Text tools
        "text_stats": lambda i: text_stats(i["text"]),
        "text_transform": lambda i: text_transform(i["text"], i["operation"]),
        # Web content
        "fetch_webpage": lambda i: fetch_webpage(i["url"], i.get("max_chars", 3000)),
        "get_rss_feed": lambda i: get_rss_feed(i["url"], i.get("max_items", 10)),
    }

    if name not in handlers:
        msg = f"Error: herramienta '{name}' no encontrada"
        _log_tool_call(name, inputs, msg, error=True)
        return msg

    try:
        result = handlers[name](inputs)
        _log_tool_call(name, inputs, result)
        return result
    except Exception as e:
        msg = f"Error ejecutando {name}: {e}"
        _log_tool_call(name, inputs, msg, error=True)
        return msg
