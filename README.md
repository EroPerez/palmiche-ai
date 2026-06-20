# J.A.R.V.I.S.

> Just A Rather Very Intelligent System — asistente de IA personal para laptop, impulsado por Claude.

## Características

- Conversación natural en español o inglés con memoria de sesión persistente
- 28 herramientas integradas para controlar el sistema, archivos, red, medios y más
- Dos backends intercambiables: Anthropic SDK (default) y Google ADK + LiteLLM
- Entrada por voz opcional con reconocimiento de habla
- Interfaz en terminal con Rich (colores, markdown, paneles)

## Requisitos

- Python 3.10+
- API key de Anthropic ([console.anthropic.com](https://console.anthropic.com))
- Linux o macOS

## Instalación

```bash
cd jarvis
bash install.sh
```

El script crea un entorno virtual, instala dependencias y configura el archivo `.env`.

## Configuración

```bash
cp jarvis/.env.example jarvis/.env
nano jarvis/.env
```

| Variable | Default | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Requerida para backends `anthropic` y `adk`+Claude |
| `GOOGLE_API_KEY` | — | Requerida para backends `gemini` y `adk`+Gemini |
| `JARVIS_MODEL` | `claude-haiku-4-5-20251001` | Modelo Claude (backends anthropic/adk) |
| `JARVIS_GEMINI_MODEL` | `gemini-2.0-flash` | Modelo Gemini (backend gemini) |
| `JARVIS_NAME` | `Jarvis` | Nombre del asistente |
| `JARVIS_BACKEND` | `anthropic` | Backend: `anthropic`, `adk` o `gemini` |
| `JARVIS_VOICE_ENABLED` | `false` | Activa voz (requiere dependencias extra) |
| `JARVIS_MAX_HISTORY` | `50` | Máximo de mensajes en historial |

## Uso

```bash
# Backend Anthropic (default)
python -m jarvis

# Backend Google ADK
python -m jarvis --backend adk

# Con nombre personalizado
python -m jarvis --name "Viernes"
```

Comandos dentro del chat:

| Comando | Acción |
|---|---|
| `salir` | Termina la sesión |
| `limpiar` | Borra el historial de conversación |

## Herramientas disponibles (28)

### Sistema

| Herramienta | Descripción |
|---|---|
| `get_system_info` | CPU, RAM, disco y uptime |
| `get_battery_info` | Porcentaje de batería, estado de carga y tiempo restante |
| `control_volume` | Subir, bajar, silenciar o establecer volumen (0-100) |
| `control_brightness` | Controlar brillo de pantalla (Linux: brightnessctl) |
| `power_action` | Apagar, reiniciar, suspender o bloquear pantalla |

### Aplicaciones

| Herramienta | Descripción |
|---|---|
| `open_application` | Abrir una app por nombre o comando |
| `close_application` | Cerrar proceso por nombre (SIGTERM o SIGKILL) |
| `list_running_apps` | Listar procesos en ejecución con uso de memoria |

### Archivos

| Herramienta | Descripción |
|---|---|
| `search_files` | Buscar archivos o directorios por nombre o patrón |
| `list_directory` | Listar contenido de un directorio |
| `read_file` | Leer texto (primeras N líneas, default 100) |
| `write_file` | Escribir o agregar contenido en un archivo |
| `delete_file` | Eliminar archivo o directorio vacío |
| `move_file` | Mover o renombrar archivo o directorio |
| `copy_file` | Copiar archivo o directorio |
| `open_file` | Abrir con la aplicación predeterminada del sistema |
| `create_directory` | Crear directorio (incluyendo directorios padre) |

### Red

| Herramienta | Descripción |
|---|---|
| `get_network_info` | IP local, IP pública, SSID y señal WiFi |
| `ping_host` | Ping con latencia y resumen de pérdida de paquetes |

### Medios

| Herramienta | Descripción |
|---|---|
| `media_control` | Play, pause, siguiente, anterior, stop y estado |
| `get_media_status` | Título y artista del track activo |

### Capturas de pantalla

| Herramienta | Descripción |
|---|---|
| `take_screenshot` | Captura de pantalla completa o selección de área |

### Web

| Herramienta | Descripción |
|---|---|
| `open_url` | Abrir URL en el navegador predeterminado |
| `web_search` | Buscar en Google, DuckDuckGo o YouTube |

### Utilidades

| Herramienta | Descripción |
|---|---|
| `get_clipboard` | Leer contenido del portapapeles |
| `set_clipboard` | Escribir texto en el portapapeles |
| `send_notification` | Notificación de escritorio (low / normal / critical) |
| `run_shell_command` | Ejecutar comando shell arbitrario (con confirmación) |
| `setup_autostart` | Activar o desactivar el arranque automático con el sistema |

## Backends

### Anthropic SDK (default)

Loop agéntico manual: envía mensajes al modelo, ejecuta herramientas y repite hasta `end_turn`. Máximo 10 iteraciones por turno. Sin dependencias adicionales.

```bash
python -m jarvis --backend anthropic
```

### Google ADK + Claude (`adk`)

ADK orquesta el loop internamente vía `Runner` + `InMemorySessionService`, usando LiteLLM como puente hacia la API de Anthropic.

Auto-detección: si solo tienes `GOOGLE_API_KEY` (sin `ANTHROPIC_API_KEY`), el backend `adk` cambia automáticamente a Gemini.

```bash
pip install google-adk litellm
python -m jarvis --backend adk
```

### Google ADK + Gemini (`gemini`)

Usa Gemini de forma nativa sin LiteLLM. Solo requiere `GOOGLE_API_KEY`.

```bash
pip install google-adk
# En .env: GOOGLE_API_KEY=tu-key, JARVIS_GEMINI_MODEL=gemini-2.0-flash
python -m jarvis --backend gemini
```

## Modo bandeja del sistema

Inicia Jarvis como ícono en la barra de tareas con una ventana de chat:

```bash
pip install pystray Pillow
python -m jarvis --tray
# o combinar con cualquier backend:
python -m jarvis --tray --backend gemini
```

Haz clic en el ícono para abrir/cerrar la ventana de chat. La ventana puede ocultarse sin cerrar el proceso.

## Seguridad

- **Herramientas destructivas** (`power_action`, `run_shell_command`) requieren `confirmed=true` en código antes de ejecutarse — no solo en el prompt.
- Las notificaciones en macOS pasan título y mensaje como argumentos argv a `osascript`, nunca interpolados en el fuente AppleScript.
- La confirmación de escritura en portapapeles solo devuelve el número de caracteres, sin exponer el contenido.

## Dependencias del sistema (opcionales)

| Funcionalidad | Linux | macOS |
|---|---|---|
| Control de medios | `sudo apt install playerctl` | Integrado (Music.app) |
| Capturas de pantalla | `sudo apt install scrot` | Integrado (`screencapture`) |
| Control de brillo | `sudo apt install brightnessctl` | — |
| Info WiFi | `nmcli` (NetworkManager) | Integrado (`airport`) |
| Voz | `pip install SpeechRecognition pyttsx3 pyaudio` | Igual |
