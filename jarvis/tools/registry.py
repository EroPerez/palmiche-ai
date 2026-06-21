from .system import get_system_info, get_battery_info, control_volume, control_brightness, power_action
from .apps import open_application, close_application, list_running_apps
from .files import (
    search_files, open_file, list_directory, read_file, create_directory,
    write_file, delete_file, move_file, copy_file,
)
from .web import open_url, web_search
from .clipboard import get_clipboard, set_clipboard
from .notifications import send_notification
from .shell import run_shell_command
from .network import get_network_info, ping_host
from .media import media_control, get_media_status
from .screenshot import take_screenshot
from .autostart import setup_autostart

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
        "description": "Busca en la web y devuelve resultados como texto, sin abrir el navegador. Para YouTube devuelve la URL de búsqueda.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda"},
                "engine": {
                    "type": "string",
                    "enum": ["google", "duckduckgo", "youtube"],
                    "description": "Motor de búsqueda. Default: duckduckgo",
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
            "Explica al usuario qué hará el comando y confirma antes de llamar con confirmed=true."
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
                "path": {"type": "string", "description": "Ruta del archivo o directorio a eliminar"}
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
            },
            "required": ["enable"],
        },
    },
]


DESTRUCTIVE_TOOLS = {"power_action", "run_shell_command", "setup_autostart"}


def execute_tool(name: str, inputs: dict) -> str:
    """Dispatch *name* to the appropriate tool handler, enforcing confirmation for destructive tools."""
    if name in DESTRUCTIVE_TOOLS and not inputs.get("confirmed", False):
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
        "web_search": lambda i: web_search(i["query"], i.get("engine", "duckduckgo")),
        "get_clipboard": lambda i: get_clipboard(),
        "set_clipboard": lambda i: set_clipboard(i["text"]),
        "send_notification": lambda i: send_notification(
            i["title"], i["message"], i.get("urgency", "normal")
        ),
        "run_shell_command": lambda i: run_shell_command(
            i["command"], i.get("working_dir", "~")
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
    }

    if name not in handlers:
        return f"Error: herramienta '{name}' no encontrada"

    try:
        return handlers[name](inputs)
    except Exception as e:
        return f"Error ejecutando {name}: {e}"
