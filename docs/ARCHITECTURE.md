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
│  JarvisAgent (Anthropic SDK)  │  JarvisADKAgent (Google ADK)           │
│  JarvisOllamaAgent (Ollama)   │                                        │
│                                                                         │
│  Bucle agéntico: user → modelo → tool_use → execute → respuesta        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                        REGISTRO DE HERRAMIENTAS                         │
│                                                                         │
│  ToolRegistry (estático, 58 herramientas)                              │
│  DynamicToolRegistry (extiende el estático con herramientas remotas)   │
│                                                                         │
│  Herramientas locales:                                                 │
│    sistema, archivos, apps, web, shell, clipboard,                     │
│    notificaciones, red, media, captura, autostart,                     │
│    eventos, dev, clima, notas, timers, calculadora, texto              │
│                                                                         │
│  Herramientas dinámicas (runtime):                                     │
│    delegate_to_<agente>  ← A2A client                                 │
│    mcp_<herramienta>     ← MCP client                                 │
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
├── jarvis/
│   ├── __main__.py          # CLI entry point, modos: interactivo, query, tray,
│   │                        #   --serve-a2a, --serve-mcp, --connect-a2a, --connect-mcp
│   ├── config.py            # Variables de entorno (incluye A2A y MCP)
│   │
│   ├── brain/
│   │   ├── agent.py         # JarvisAgent (Anthropic SDK) — soporta DynamicToolRegistry
│   │   ├── adk_agent.py     # JarvisADKAgent (Google ADK: Claude o Gemini)
│   │   ├── ollama_agent.py  # JarvisOllamaAgent (modelos locales via Ollama)
│   │   └── prompts.py       # System prompts
│   │
│   ├── tools/
│   │   ├── registry.py      # 58 herramientas estáticas + dispatcher execute_tool()
│   │   ├── dynamic.py       # DynamicToolRegistry — extiende el registro en runtime
│   │   ├── system.py        # CPU, RAM, disco, batería, volumen, brillo
│   │   ├── apps.py          # Abrir/cerrar/listar aplicaciones
│   │   ├── files.py         # Buscar/leer/escribir/eliminar/mover archivos
│   │   ├── web.py           # URLs, búsqueda web, fetch páginas, RSS
│   │   ├── shell.py         # Comandos de shell arbitrarios
│   │   ├── clipboard.py     # Portapapeles
│   │   ├── notifications.py # Notificaciones de escritorio
│   │   ├── network.py       # IP, WiFi, ping
│   │   ├── media.py         # Control de reproducción multimedia
│   │   ├── screenshot.py    # Capturas de pantalla
│   │   ├── autostart.py     # Inicio automático del sistema
│   │   ├── events.py        # Calendario local de eventos
│   │   ├── dev.py           # JSON, hash, encoding, UUID, HTTP, git
│   │   ├── weather.py       # Clima y pronóstico
│   │   ├── notes.py         # Notas persistentes
│   │   ├── timer.py         # Temporizadores y alarmas
│   │   ├── calculator.py    # Expresiones matemáticas, conversión de unidades
│   │   └── text_tools.py    # Procesamiento y transformación de texto
│   │
│   ├── a2a/                 # Agent-to-Agent protocol (Google spec)
│   │   ├── __init__.py
│   │   ├── models.py        # Modelos de datos A2A (AgentCard, Task, Message, etc.)
│   │   ├── server.py        # Servidor HTTP A2A con FastAPI + uvicorn
│   │   └── client.py        # Cliente A2A para consumir agentes remotos
│   │
│   ├── mcp_support/         # Model Context Protocol (Anthropic spec)
│   │   ├── __init__.py
│   │   ├── server.py        # Servidor MCP stdio (expone las 58 herramientas)
│   │   └── client.py        # Cliente MCP (stdio y SSE) para consumir servidores externos
│   │
│   ├── interface/
│   │   ├── cli.py           # Interfaz CLI con Rich
│   │   ├── tray.py          # GUI de bandeja del sistema con PyQt6 (paleta Palmiche)
│   │   ├── hud_animation.py # Animación HUD estilo Iron Man (QPainter, 3 anillos, radar)
│   │   ├── animation.py     # WaveformAnimation (QWidget) para feedback visual
│   │   ├── voice.py         # Reconocimiento de voz y TTS
│   │   ├── wake_word.py     # WakeWordListener — detección de palabra clave en segundo plano
│   │   └── splash.py        # Pantalla de bienvenida animada
│   │
│   └── memory/
│       └── history.py       # Historial de conversación persistente (JSON)
│
│   └── assets/
│       ├── space-bg.jpg     # Fondo espacial para HUD
│       └── TheGoodMonolith.woff  # Fuente monoespaciada robótica
│
├── docs/
│   └── ARCHITECTURE.md      # Este documento
├── extract_assets.py        # Extractor de ícono y audio desde YouTube
├── CHANGELOG.md             # Historial de cambios
├── TOOLS.md                 # Guía completa de las 58 herramientas
├── INSTALL.md               # Guía de instalación paso a paso
├── pyproject.toml
└── README.md
```

---

## Modos de operación

### 1. CLI interactiva (default)
```bash
python -m jarvis [--backend anthropic|adk|gemini|ollama]
```
Loop interactivo en terminal. El agente procesa entradas del usuario, ejecuta herramientas y responde.

### 2. Consulta única
```bash
python -m jarvis -q "¿cuánta RAM tengo?"
```
Ejecuta una consulta y termina. Útil para scripting.

### 3. Bandeja del sistema
```bash
python -m jarvis --tray
```
GUI en sistema de bandeja con ventana de chat. Soporte opcional de voz y wake word.

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
Expone las 58 herramientas vía protocolo MCP en stdio. Compatible con Claude Desktop, Cursor, Zed, Continue.dev y cualquier cliente MCP.

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

El servidor MCP expone las 58 herramientas de Jarvis en formato MCP estándar.

### Configuración en Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "palmiche": {
      "command": "python",
      "args": ["-m", "jarvis", "--serve-mcp"]
    }
  }
}
```

### Herramientas expuestas
Todas las herramientas del registro estático se exponen con sus schemas idénticos:
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
text_transform
```

---

## DynamicToolRegistry

Permite extender el registro estático en tiempo de ejecución:

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.a2a.client import load_a2a_agent
from jarvis.mcp_support.client import load_mcp_server

registry = DynamicToolRegistry()

# Agregar agente A2A como herramienta
load_a2a_agent(registry, "http://specialist-agent:8080")
# → registra: delegate_to_specialist_agent(message: str)

# Agregar herramientas de servidor MCP
load_mcp_server(registry, "npx -y @modelcontextprotocol/server-filesystem /tmp")
# → registra: mcp_read_file(...), mcp_write_file(...), etc.

# Crear agente con el registro extendido
from jarvis.brain.agent import JarvisAgent
agent = JarvisAgent(name="Jarvis", registry=registry)
```

---

## Variables de entorno (A2A / MCP)

| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_A2A_HOST` | `0.0.0.0` | Host del servidor A2A |
| `JARVIS_A2A_PORT` | `8080` | Puerto del servidor A2A |
| `JARVIS_A2A_AGENTS` | `` | URLs de agentes A2A (separados por coma) |
| `JARVIS_MCP_SERVERS` | `` | Specs de servidores MCP (separados por `;`) |
| `JARVIS_LOG_FILE` | `~/.jarvis_tools.log` | Archivo de log de herramientas |
| `JARVIS_LOG_ENABLED` | `true` | Activar/desactivar logging de herramientas |
| `JARVIS_SUDO_PASSWORD` | `` | Contraseña sudo automática (opcional) |

---

## Dependencias opcionales

```bash
# Solo A2A server
pip install 'palmiche-jarvis[a2a]'
# → fastapi>=0.110.0, uvicorn>=0.29.0

# Solo MCP (server + client)
pip install 'palmiche-jarvis[mcp]'
# → mcp>=1.0.0

# Todo
pip install 'palmiche-jarvis[all]'
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
- El servidor MCP opera solo en stdio (proceso local), sin exposición de red.
- Los agentes A2A remotos conectados como clientes ejecutan código en su propio entorno; el resultado solo se devuelve como texto al agente local.
- **Logging**: todas las llamadas a herramientas se registran en `~/.jarvis_tools.log` con timestamp, inputs y resultado. Desactivable con `JARVIS_LOG_ENABLED=false`.
- **Sudo automático**: cuando `JARVIS_SUDO_PASSWORD` está configurada, el agente la usa via `sudo -S` tras pedir confirmación al usuario. Si un comando falla con "Permission denied", el sistema detecta el error y ofrece reintentar con privilegios.
