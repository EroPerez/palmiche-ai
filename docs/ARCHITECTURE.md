# Palmiche J.A.R.V.I.S. — Arquitectura

## Visión general

Palmiche J.A.R.V.I.S. es un asistente personal AI que corre como CLI, bandeja del sistema, servidor A2A y/o servidor MCP. Puede actuar **simultáneamente** como servidor de agentes (A2A/MCP) y como cliente de agentes remotos, formando redes de agentes colaborativos.

---

## Diagrama de capas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INTERFACES DE ENTRADA                           │
│                                                                         │
│   CLI interactiva   │   --query (-q)   │   Bandeja (--tray)   │  Voz   │
│   A2A HTTP server   │   MCP stdio server                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                            CAPA DE AGENTES                              │
│                                                                         │
│  JarvisUniversalADKAgent (ADK + LiteLLM, default)                      │
│    └─ Anthropic · OpenAI · Gemini · Ollama · Groq · Mistral · Azure   │
│  JarvisAgent (Anthropic SDK, loop nativo sin ADK)                      │
│                                                                         │
│  Bucle agéntico: user → modelo → tool_use → execute → respuesta        │
│                                                                         │
│  GuardrailsEngine: valida input, output, tool_call y tool_result       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                        REGISTRO DE HERRAMIENTAS                         │
│                                                                         │
│  ToolRegistry (estático, 59 herramientas)                              │
│  DynamicToolRegistry (extiende el estático con herramientas remotas)   │
│                                                                         │
│  Herramientas locales:                                                 │
│    sistema, archivos, apps, web, shell, clipboard,                     │
│    notificaciones, red, media, captura, autostart,                     │
│    eventos, dev, clima, notas, timers, calculadora, texto,             │
│    computer_use (visual Gemini), custom (definidas por el usuario)     │
│                                                                         │
│  Herramientas dinámicas (runtime):                                     │
│    delegate_to_<agente>  ← A2A client                                 │
│    mcp_<herramienta>     ← MCP client                                 │
│    <nombre>              ← custom tools (texto plano)                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                         INTEGRACIONES EXTERNAS                          │
│                                                                         │
│  A2A Server  ←→  Agentes externos (Claude, Gemini, Copilot, etc.)     │
│  MCP Server  ←→  Claude Desktop, Cursor, Zed, Continue.dev, etc.      │
│  A2A Client  →   Agentes A2A remotos (como herramientas del agente)   │
│  MCP Client  →   Servidores MCP externos (filesystem, DB, APIs, etc.) │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Estructura de archivos

```
palmiche-ai/
├── README.md
├── README-US.md
├── pyproject.toml               # Definición del paquete, grupos opcionales y entrypoint CLI
├── extract_assets.py            # Extractor de ícono y audio desde YouTube
│
├── jarvis/                      # Paquete principal
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point — argparse, modos: interactivo, query, tray,
│   │                            #   --serve-a2a, --serve-mcp, --connect-a2a, --connect-mcp
│   ├── config.py                # Todas las variables de entorno con valores por defecto
│   ├── install.sh               # Instalador interactivo (splash, selección de módulos)
│   ├── requirements.txt         # Dependencias directas del proyecto
│   ├── custom_tools.example.txt # Plantilla de ejemplo para herramientas personalizadas
│   │
│   ├── brain/
│   │   ├── agent.py             # JarvisAgent (Anthropic SDK) — loop nativo sin ADK + guardrails
│   │   ├── adk_universal.py     # JarvisUniversalADKAgent (ADK + LiteLLM multi-proveedor) + guardrails
│   │   └── prompts.py           # System prompts (ES/EN según JARVIS_TOOL_LANG)
│   │
│   ├── guardrails/
│   │   ├── __init__.py          # API pública: GuardrailsEngine, modelos
│   │   ├── models.py            # GuardrailRule, GuardrailVerdict, enums (Phase, Action)
│   │   ├── engine.py            # Motor de evaluación central (regex, keywords, validators)
│   │   ├── defaults.py          # 13 reglas integradas (jailbreak, prompt injection, credential leak, etc.)
│   │   └── README.md            # Documentación completa del sistema de guardrails
│   │
│   ├── tools/
│   │   ├── registry.py          # 59 herramientas estáticas + dispatcher execute_tool()
│   │   ├── dynamic.py           # DynamicToolRegistry — extiende el registro en runtime
│   │   ├── translations.py      # Overlay EN/ES para schemas de herramientas (JARVIS_TOOL_LANG)
│   │   ├── custom.py            # Cargador de herramientas definidas por el usuario (texto plano)
│   │   ├── system.py            # CPU, RAM, disco, batería, volumen, brillo
│   │   ├── apps.py              # Abrir/cerrar/listar aplicaciones
│   │   ├── files.py             # Buscar/leer/escribir/eliminar/mover archivos
│   │   ├── web.py               # URLs, búsqueda web, fetch páginas, RSS
│   │   ├── shell.py             # Comandos de shell arbitrarios
│   │   ├── clipboard.py         # Portapapeles
│   │   ├── notifications.py     # Notificaciones de escritorio
│   │   ├── network.py           # IP, WiFi, ping
│   │   ├── media.py             # Control de reproducción multimedia
│   │   ├── screenshot.py        # Capturas de pantalla
│   │   ├── autostart.py         # Inicio automático del sistema
│   │   ├── events.py            # Calendario local de eventos
│   │   ├── dev.py               # JSON, hash, encoding, UUID, HTTP, git
│   │   ├── weather.py           # Clima y pronóstico (wttr.in, sin API key)
│   │   ├── notes.py             # Notas persistentes (JSON local)
│   │   ├── timer.py             # Temporizadores y alarmas (hilos de fondo)
│   │   ├── calculator.py        # Expresiones matemáticas seguras (AST), conversión de unidades
│   │   ├── text_tools.py        # Procesamiento y transformación de texto
│   │   └── computer_use.py      # Automatización visual con Gemini (Playwright / pyautogui)
│   │
│   ├── a2a/                     # Agent-to-Agent protocol (Google spec)
│   │   ├── __init__.py
│   │   ├── models.py            # Modelos de datos A2A (AgentCard, Task, Message, etc.)
│   │   ├── server.py            # Servidor HTTP A2A con FastAPI + uvicorn
│   │   └── client.py            # Cliente A2A para consumir agentes remotos
│   │
│   ├── mcp_support/             # Model Context Protocol (Anthropic spec)
│   │   ├── __init__.py
│   │   ├── server.py            # Servidor MCP stdio (expone las 59 herramientas)
│   │   └── client.py            # Cliente MCP (stdio y SSE) para consumir servidores externos
│   │
│   ├── interface/
│   │   ├── cli.py               # Interfaz CLI con Rich (colores, markdown, paneles)
│   │   ├── tray.py              # GUI de bandeja del sistema con PyQt6 (paleta Palmiche)
│   │   ├── hud_animation.py     # Animación HUD estilo Iron Man (QPainter, 3 anillos, radar)
│   │   ├── animation.py         # WaveformAnimation (QWidget) para feedback visual
│   │   ├── audio_engine.py      # Motor de audio centralizado (cola, cache TTS, streaming, volumen)
│   │   ├── voice.py             # Reconocimiento de voz (SpeechRecognition) — TTS via AudioEngine
│   │   ├── wake_word.py         # WakeWordListener — detección de palabra clave en segundo plano
│   │   └── splash.py            # Pantalla de bienvenida animada (Rich, verde Palmiche)
│   │
│   ├── memory/
│   │   └── history.py           # Historial de conversación persistente (JSON)
│   │
│   ├── assets/
│   │   ├── space-bg.jpg         # Fondo espacial para el HUD
│   │   └── TheGoodMonolith.woff # Fuente monoespaciada robótica
│   │
│   └── scripts/
│       ├── 49-jarvis-power.rules      # Regla polkit para acciones de energía sin contraseña
│       └── install-power-rules.sh     # Instala la regla polkit en el sistema
│
└── docs/
    ├── ARCHITECTURE.md          # Este documento
    ├── ARCHITECTURE-US.md
    ├── TOOLS.md                 # Guía completa de las 59 herramientas
    ├── TOOLS-US.md
    ├── INSTALL.md               # Guía de instalación paso a paso
    ├── INSTALL-US.md
    ├── MCP-AGENTS.md            # Guía de MCP y agentes externos
    ├── MCP-AGENTS-US.md
    ├── CHANGELOG.md
    └── CHANGELOG-US.md
```

---

## Modos de operación

### 1. CLI interactiva (default)
```bash
python -m jarvis [--backend anthropic|adk|gemini|ollama]
# o con el entrypoint instalado:
jarvis
```
Loop interactivo en terminal. El agente procesa entradas del usuario, ejecuta herramientas y responde.

### 2. Consulta única
```bash
python -m jarvis -q "¿cuánta RAM tengo?"
```
Ejecuta una consulta y termina. Útil para scripting y pipes.

### 3. Bandeja del sistema
```bash
python -m jarvis --tray
```
GUI en sistema de bandeja (PyQt6) con ventana de chat, animación HUD y soporte opcional de voz y wake word.

### 4. Servidor A2A (`--serve-a2a`)
```bash
python -m jarvis --serve-a2a [--a2a-host 0.0.0.0] [--a2a-port 8080]
```
Expone el agente como servidor HTTP compatible con el protocolo A2A de Google.
- `GET /.well-known/agent.json` → Agent Card (descripción del agente)
- `POST /` → JSON-RPC 2.0 endpoint
  - `tasks/send` → tarea síncrona
  - `tasks/sendSubscribe` → tarea con streaming SSE
  - `tasks/get` → estado de tarea
  - `tasks/cancel` → cancelar tarea
- `GET /health` → health check

### 5. Servidor MCP (`--serve-mcp`)
```bash
python -m jarvis --serve-mcp
```
Expone las 59 herramientas vía protocolo MCP en stdio. Compatible con Claude Desktop, Cursor, Zed, Continue.dev y cualquier cliente MCP.

### 6. Cliente A2A (`--connect-a2a`)
```bash
python -m jarvis --connect-a2a http://agent1:8080 --connect-a2a http://agent2:9090
```
Descubre agentes A2A remotos y los registra como herramientas (`delegate_to_<nombre>`). El agente local puede delegar tareas a ellos durante el bucle agéntico.

### 7. Cliente MCP (`--connect-mcp`)
```bash
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"
python -m jarvis --connect-mcp "http://localhost:3000"
```
Conecta a servidores MCP externos (stdio o SSE) y carga sus herramientas como `mcp_<nombre>`.

### 8. Combinaciones
```bash
# Servidor A2A que también usa herramientas de otros agentes
python -m jarvis --serve-a2a --connect-a2a http://specialist:8080

# CLI que usa herramientas de un servidor MCP y un agente A2A
python -m jarvis --connect-mcp "npx -y @mcp/server-db" --connect-a2a http://analyzer:8080
```

---

## Localización de schemas de herramientas

El módulo `tools/translations.py` proporciona un overlay EN/ES para los schemas de herramientas. Los schemas canónicos están en español en `registry.py`; la variable `JARVIS_TOOL_LANG` (default: `en`) selecciona el idioma que el modelo recibe en sus definiciones de herramientas.

```
JARVIS_TOOL_LANG=en  →  el modelo ve los schemas en inglés (mejor tool-calling reliability)
JARVIS_TOOL_LANG=es  →  el modelo ve los schemas en español original
```

Esto es independiente del idioma de respuesta al usuario: el asistente siempre responde en el idioma del usuario.

---

## Herramientas personalizadas (Custom Tools)

El módulo `tools/custom.py` carga herramientas definidas por el usuario desde un archivo de texto plano (`~/.jarvis_custom_tools.txt` por defecto, configurable con `JARVIS_CUSTOM_TOOLS_FILE`). Permite añadir herramientas sin escribir Python.

Formato del archivo:

```
[tool: clima_casa]
description: Clima actual en mi ciudad
command: curl -s "wttr.in/Havana?format=3"

[tool: saludar]
description: Saluda a alguien por su nombre
param *nombre: Nombre de la persona
param idioma: Idioma del saludo (opcional)
command: echo "Hola {nombre} ({idioma})"
```

Las herramientas personalizadas se registran en el `DynamicToolRegistry` al arrancar; el modelo las ve exactamente igual que las 59 integradas. Los parámetros se escapan con `shlex.quote` para prevenir inyección de comandos.

---

## Protocolo A2A

### Agent Card (discovery)
```json
GET /.well-known/agent.json

{
  "name": "Jarvis",
  "description": "Asistente AI personal — Palmiche J.A.R.V.I.S.",
  "url": "http://localhost:8080",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": false
  },
  "skills": [
    {
      "id": "general-assistant",
      "name": "General Assistant",
      "description": "...",
      "tags": ["general", "system", "productivity"]
    }
  ],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"]
}
```

### Envío de tarea (síncrono)
```json
POST /
{
  "jsonrpc": "2.0",
  "method": "tasks/send",
  "params": {
    "id": "task-uuid",
    "sessionId": "session-uuid",
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "¿Cuánta RAM tengo disponible?"}]
    }
  },
  "id": 1
}

→ Respuesta:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "task-uuid",
    "sessionId": "session-uuid",
    "status": {"state": "completed", "timestamp": "..."},
    "artifacts": [
      {"parts": [{"type": "text", "text": "Tienes 8 GB de RAM..."}], "index": 0}
    ]
  }
}
```

### Streaming (SSE)
```
POST /  → method: "tasks/sendSubscribe"

text/event-stream:
  event: task_status_update   data: {"id": ..., "status": {"state": "working"}, "final": false}
  event: task_artifact_update data: {"id": ..., "artifact": {...}, "final": false}
  event: task_status_update   data: {"id": ..., "status": {"state": "completed"}, "final": true}
```

### Gestión de sesiones
Cada `sessionId` único mantiene su propia instancia de agente con historial de conversación independiente. Máximo 50 sesiones simultáneas (LRU).

---

## Protocolo MCP

El servidor MCP expone las 59 herramientas de Jarvis en formato MCP estándar.

### Configuración en Claude Desktop
macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "palmiche": {
      "command": "python",
      "args": ["-m", "jarvis", "--serve-mcp"],
      "cwd": "/ruta/a/palmiche-ai"
    }
  }
}
```

### Herramientas expuestas (59)
```
get_system_info, get_battery_info, control_volume, control_brightness,
power_action, open_application, close_application, list_running_apps,
search_files, open_file, list_directory, read_file, create_directory,
write_file, delete_file, move_file, copy_file, open_url, web_search,
fetch_webpage, get_rss_feed, get_clipboard, set_clipboard,
send_notification, run_shell_command, get_network_info, ping_host,
media_control, get_media_status, take_screenshot, setup_autostart,
add_event, list_events, upcoming_events, delete_event, format_json,
hash_text, encode_decode, generate_uuid, convert_timestamp, http_request,
git_status, find_process_on_port, get_weather, get_forecast, create_note,
list_notes, read_note, search_notes, delete_note, set_timer, set_alarm,
list_timers, cancel_timer, calculate, convert_units, text_stats,
text_transform, computer_use_task
```

---

## DynamicToolRegistry

Permite extender el registro estático en tiempo de ejecución con herramientas de tres fuentes: agentes A2A remotos, servidores MCP externos y herramientas personalizadas de texto plano.

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.a2a.client import load_a2a_agent
from jarvis.mcp_support.client import load_mcp_server

registry = DynamicToolRegistry()

# Herramientas de agente A2A remoto
load_a2a_agent(registry, "http://specialist-agent:8080")
# → registra: delegate_to_specialist_agent(message: str)

# Herramientas de servidor MCP externo
load_mcp_server(registry, "npx -y @modelcontextprotocol/server-filesystem /tmp")
# → registra: mcp_read_file(...), mcp_write_file(...), etc.

# Herramientas personalizadas desde archivo de texto (cargadas automáticamente al arrancar)
# → registra: clima_casa(), saludar(nombre, idioma=None), etc.

# Crear agente con el registro extendido
from jarvis.brain.agent import JarvisAgent
agent = JarvisAgent(name="Jarvis", registry=registry)
```

---

## Variables de entorno

Todas las variables se leen desde `jarvis/.env` (o del entorno del proceso).

### Backend y modelo
| Variable | Default | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Requerida para backends `anthropic` y `adk`+Claude |
| `GOOGLE_API_KEY` | — | Requerida para backends `gemini`, `adk`+Gemini y Computer Use |
| `JARVIS_BACKEND` | `anthropic` | Backend: `anthropic` \| `adk` \| `gemini` \| `ollama` |
| `JARVIS_MODEL` | `claude-haiku-4-5-20251001` | Modelo Claude (backends anthropic/adk) |
| `JARVIS_GEMINI_MODEL` | `gemini-2.0-flash` | Modelo Gemini (backend gemini) |
| `JARVIS_OLLAMA_HOST` | `http://localhost:11434` | URL del servidor Ollama |
| `JARVIS_OLLAMA_MODEL` | `llama3.2` | Modelo Ollama |

### Asistente e interfaz
| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_NAME` | `Jarvis` | Nombre del asistente |
| `JARVIS_TOOL_LANG` | `en` | Idioma de los schemas de herramientas: `en` \| `es` |
| `JARVIS_SPLASH_ENABLED` | `true` | Mostrar pantalla de bienvenida animada |
| `JARVIS_WELCOME_MESSAGE` | `Sistemas en línea...` | Frase del splash |
| `JARVIS_GOODBYE_MESSAGE` | `{name} desconectado...` | Frase de despedida (`{name}` = nombre) |
| `JARVIS_WAKE_WORD` | `palmiche` | Palabra de activación por voz (modo tray) |
| `JARVIS_VOICE_ENABLED` | `false` | Activar reconocimiento de voz |
| `JARVIS_AUDIO_VOLUME` | `100` | Volumen global de audio (0-100) |
| `JARVIS_TTS_CACHE` | `true` | Cache de audio TTS generado (evita re-sintetizar) |
| `JARVIS_TTS_STREAM` | `true` | Streaming TTS por oraciones (menor latencia) |
| `JARVIS_TRAY_ICON` | — | Ruta a imagen PNG/ICO para ícono de bandeja |
| `JARVIS_WELCOME_AUDIO` | — | Ruta a MP3/WAV reproducido al arrancar bandeja |

### Almacenamiento
| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_HISTORY_FILE` | `~/.jarvis_history.json` | Historial de conversación |
| `JARVIS_EVENTS_FILE` | `~/.jarvis_events.json` | Calendario local |
| `JARVIS_NOTES_FILE` | `~/.jarvis_notes.json` | Notas personales |
| `JARVIS_MAX_HISTORY` | `50` | Máximo de mensajes en historial |
| `JARVIS_CUSTOM_TOOLS_FILE` | `~/.jarvis_custom_tools.txt` | Herramientas personalizadas de texto plano |

### A2A y MCP
| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_A2A_HOST` | `0.0.0.0` | Host del servidor A2A propio |
| `JARVIS_A2A_PORT` | `8080` | Puerto del servidor A2A propio |
| `JARVIS_A2A_AGENTS` | — | URLs de agentes A2A remotos (separadas por `,`) |
| `JARVIS_MCP_SERVERS` | — | Specs de servidores MCP remotos (separadas por `;`) |

### Logging y seguridad
| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_LOG_FILE` | `~/.jarvis_tools.log` | Archivo de log de ejecución de herramientas |
| `JARVIS_LOG_ENABLED` | `true` | Activar/desactivar logging de herramientas |
| `JARVIS_SUDO_PASSWORD` | — | Contraseña sudo automática (opcional) |
| `JARVIS_GUARDRAILS_ENABLED` | `true` | Activar/desactivar guardrails de seguridad IA |
| `JARVIS_GUARDRAILS_FILE` | `~/.jarvis_guardrails.json` | Archivo de reglas de guardrails personalizadas |

### Computer Use
| Variable | Default | Descripción |
|---|---|---|
| `COMPUTER_USE_MODEL` | `gemini-2.5-flash` | Modelo Gemini para automatización visual |
| `COMPUTER_USE_BACKEND` | `playwright` | `playwright` (browser) \| `desktop` (escritorio) |
| `COMPUTER_USE_MAX_ITERATIONS` | `30` | Límite de iteraciones del agente visual |

---

## Dependencias opcionales

```bash
pip install 'palmiche-jarvis[voice]'        # SpeechRecognition, pyaudio, pyttsx3, gTTS
pip install 'palmiche-jarvis[tray]'         # PyQt6, Pillow
pip install 'palmiche-jarvis[adk]'          # google-adk, litellm
pip install 'palmiche-jarvis[gemini]'       # google-adk
pip install 'palmiche-jarvis[assets]'       # yt-dlp
pip install 'palmiche-jarvis[a2a]'          # fastapi, uvicorn
pip install 'palmiche-jarvis[mcp]'          # mcp>=1.0.0
pip install 'palmiche-jarvis[computer-use]' # google-genai, playwright, pyautogui, Pillow, mss
pip install 'palmiche-jarvis[all]'          # todos los anteriores
```

---

## Flujo de datos: bucle agéntico con herramientas remotas

```
Usuario: "Analiza este archivo y pregúntale a agent2 qué opina"
         │
         ▼
JarvisAgent.chat()
         │
         ▼
Anthropic API  ←  tools: [herramientas_locales + delegate_to_agent2 + mcp_read_file]
         │
         ▼ stop_reason=tool_use
         │
         ├─→ read_file("archivo.txt")              ← ejecución local
         │
         └─→ delegate_to_agent2("contenido...")    ← A2AClient.send_task()
                    │                                    │
                    │                                    ▼
                    │                              http://agent2:8080/
                    │                                    │
                    │                              agent2.chat(...)
                    │                                    │
                    ◄────────────────────────────────────┘ texto de respuesta
         │
         ▼ tool_result
Anthropic API (segunda llamada con resultados)
         │
         ▼ stop_reason=end_turn
Usuario: "Agent2 opina que..."
```

---

## Seguridad

- El servidor A2A no incluye autenticación por defecto. Para producción, usa un proxy reverso (nginx, Caddy) con TLS y autenticación.
- Las herramientas destructivas (`power_action`, `run_shell_command`, `setup_autostart`) requieren `confirmed=true` en sus inputs para ejecutarse.
- Las herramientas personalizadas de texto plano escapan todos los parámetros con `shlex.quote` antes de sustituirlos en el comando shell.
- El servidor MCP opera solo en stdio (proceso local), sin exposición de red.
- Los agentes A2A remotos conectados como clientes ejecutan código en su propio entorno; el resultado solo se devuelve como texto al agente local.
- **Logging**: todas las llamadas a herramientas se registran en `~/.jarvis_tools.log` con timestamp, inputs y resultado. Desactivable con `JARVIS_LOG_ENABLED=false`.
- **Sudo automático**: cuando `JARVIS_SUDO_PASSWORD` está configurada, el agente la usa via `sudo -S` tras pedir confirmación al usuario. Si un comando falla con "Permission denied", el sistema detecta el error y ofrece reintentar con privilegios.
- **Polkit rules** (`scripts/49-jarvis-power.rules`): permite acciones de energía (apagado/reinicio/suspensión) sin contraseña para el usuario configurado, sin requerir sudo global.
- **AI Guardrails** (`jarvis/guardrails/`): sistema de reglas que valida entradas (detección de prompt injection), salidas (redacción de credenciales, bloqueo de contenido dañino), llamadas a herramientas (comandos peligrosos, confirmación de acciones destructivas) y resultados (redacción de secretos). Configurable vía `~/.jarvis_guardrails.json`. Ver `jarvis/guardrails/README.md` para la documentación completa.
