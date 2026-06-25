# Palmiche J.A.R.V.I.S. — Architecture

## Overview

Palmiche J.A.R.V.I.S. is a personal AI assistant that runs as a CLI, system tray, A2A server and/or MCP server. It can act **simultaneously** as an agent server (A2A/MCP) and as a client for remote agents, forming collaborative agent networks.

---

## Layer diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INPUT INTERFACES                              │
│                                                                         │
│   Interactive CLI   │   --query (-q)   │   Tray (--tray)   │   Voice   │
│   A2A HTTP server   │   MCP stdio server                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                            AGENT LAYER                                  │
│                                                                         │
│  JarvisAgent (Anthropic SDK)  │  JarvisADKAgent (Google ADK)           │
│  JarvisOllamaAgent (Ollama)   │                                        │
│                                                                         │
│  Agentic loop: user → model → tool_use → execute → response           │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                          TOOL REGISTRY                                  │
│                                                                         │
│  ToolRegistry (static, 58 tools)                                       │
│  DynamicToolRegistry (extends static with remote tools)                │
│                                                                         │
│  Local tools:                                                          │
│    system, files, apps, web, shell, clipboard,                         │
│    notifications, network, media, screenshot, autostart,               │
│    events, dev, weather, notes, timers, calculator, text               │
│                                                                         │
│  Dynamic tools (runtime):                                              │
│    delegate_to_<agent>   ← A2A client                                  │
│    mcp_<tool>            ← MCP client                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                       EXTERNAL INTEGRATIONS                             │
│                                                                         │
│  A2A Server  ←→  External agents (Claude, Gemini, Copilot, etc.)      │
│  MCP Server  ←→  Claude Desktop, Cursor, Zed, Continue.dev, etc.      │
│  A2A Client  →   Remote A2A agents (as agent tools)                    │
│  MCP Client  →   External MCP servers (filesystem, DB, APIs, etc.)    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File structure

```
palmiche-ai/
├── jarvis/
│   ├── __main__.py          # CLI entry point, modes: interactive, query, tray,
│   │                        #   --serve-a2a, --serve-mcp, --connect-a2a, --connect-mcp
│   ├── config.py            # Environment variables (includes A2A and MCP)
│   │
│   ├── brain/
│   │   ├── agent.py         # JarvisAgent (Anthropic SDK) — supports DynamicToolRegistry
│   │   ├── adk_agent.py     # JarvisADKAgent (Google ADK: Claude or Gemini)
│   │   ├── ollama_agent.py  # JarvisOllamaAgent (local models via Ollama)
│   │   └── prompts.py       # System prompts
│   │
│   ├── tools/
│   │   ├── registry.py      # 58 static tools + dispatcher execute_tool()
│   │   ├── dynamic.py       # DynamicToolRegistry — extends registry at runtime
│   │   ├── system.py        # CPU, RAM, disk, battery, volume, brightness
│   │   ├── apps.py          # Open/close/list applications
│   │   ├── files.py         # Search/read/write/delete/move files
│   │   ├── web.py           # URLs, web search, page fetch, RSS
│   │   ├── shell.py         # Arbitrary shell commands
│   │   ├── clipboard.py     # Clipboard
│   │   ├── notifications.py # Desktop notifications
│   │   ├── network.py       # IP, WiFi, ping
│   │   ├── media.py         # Media playback control
│   │   ├── screenshot.py    # Screenshots
│   │   ├── autostart.py     # System automatic startup
│   │   ├── events.py        # Local event calendar
│   │   ├── dev.py           # JSON, hash, encoding, UUID, HTTP, git
│   │   ├── weather.py       # Weather and forecast
│   │   ├── notes.py         # Persistent notes
│   │   ├── timer.py         # Timers and alarms
│   │   ├── calculator.py    # Math expressions, unit conversion
│   │   └── text_tools.py    # Text processing and transformation
│   │
│   ├── a2a/                 # Agent-to-Agent protocol (Google spec)
│   │   ├── __init__.py
│   │   ├── models.py        # A2A data models (AgentCard, Task, Message, etc.)
│   │   ├── server.py        # A2A HTTP server with FastAPI + uvicorn
│   │   └── client.py        # A2A client for consuming remote agents
│   │
│   ├── mcp_support/         # Model Context Protocol (Anthropic spec)
│   │   ├── __init__.py
│   │   ├── server.py        # MCP stdio server (exposes the 58 tools)
│   │   └── client.py        # MCP client (stdio and SSE) for consuming external servers
│   │
│   ├── interface/
│   │   ├── cli.py           # CLI interface with Rich
│   │   ├── tray.py          # System tray GUI with PyQt6 (Palmiche palette)
│   │   ├── hud_animation.py # Iron Man-style HUD animation (QPainter, 3 rings, radar)
│   │   ├── animation.py     # WaveformAnimation (QWidget) for visual feedback
│   │   ├── voice.py         # Speech recognition and TTS
│   │   ├── wake_word.py     # WakeWordListener — background keyword detection
│   │   └── splash.py        # Animated welcome screen
│   │
│   └── memory/
│       └── history.py       # Persistent conversation history (JSON)
│
│   └── assets/
│       ├── space-bg.jpg     # Space background for HUD
│       └── TheGoodMonolith.woff  # Robotic monospaced font
│
├── docs/
│   └── ARCHITECTURE.md      # This document
├── extract_assets.py        # Icon and audio extractor from YouTube
├── CHANGELOG.md             # Change history
├── TOOLS.md                 # Complete tools guide
├── INSTALL.md               # Step-by-step installation guide
├── pyproject.toml
└── README.md
```

---

## Operation modes

### 1. Interactive CLI (default)
```bash
python -m jarvis [--backend anthropic|adk|gemini|ollama]
```
Interactive loop in terminal. The agent processes user inputs, executes tools and responds.

### 2. Single query
```bash
python -m jarvis -q "how much RAM do I have?"
```
Executes a query and exits. Useful for scripting.

### 3. System tray
```bash
python -m jarvis --tray
```
System tray GUI with chat window. Optional voice and wake word support.

### 4. A2A server (`--serve-a2a`)
```bash
python -m jarvis --serve-a2a [--a2a-host 0.0.0.0] [--a2a-port 8080]
```
Exposes the agent as an HTTP server compatible with Google's A2A protocol.
- `GET /.well-known/agent.json` → Agent Card (agent description)
- `POST /` → JSON-RPC 2.0 endpoint
  - `tasks/send` → synchronous task
  - `tasks/sendSubscribe` → task with SSE streaming
  - `tasks/get` → task status
  - `tasks/cancel` → cancel task
- `GET /health` → health check

### 5. MCP server (`--serve-mcp`)
```bash
python -m jarvis --serve-mcp
```
Exposes the 58 tools via MCP protocol on stdio. Compatible with Claude Desktop, Cursor, Zed, Continue.dev and any MCP client.

### 6. A2A client (`--connect-a2a`)
```bash
python -m jarvis --connect-a2a http://agent1:8080 --connect-a2a http://agent2:9090
```
Discovers remote A2A agents and registers them as tools (`delegate_to_<name>`). The local agent can delegate tasks to them during the agentic loop.

### 7. MCP client (`--connect-mcp`)
```bash
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"
python -m jarvis --connect-mcp "http://localhost:3000"
```
Connects to external MCP servers (stdio or SSE) and loads their tools as `mcp_<name>`.

### 8. Combinations
```bash
# A2A server that also uses tools from other agents
python -m jarvis --serve-a2a --connect-a2a http://specialist:8080

# CLI that uses tools from an MCP server and an A2A agent
python -m jarvis --connect-mcp "npx -y @mcp/server-db" --connect-a2a http://analyzer:8080
```

---

## A2A protocol

### Agent Card (discovery)
```json
GET /.well-known/agent.json

{
  "name": "Jarvis",
  "description": "Personal AI assistant — Palmiche J.A.R.V.I.S.",
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

### Task submission (synchronous)
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
      "parts": [{"type": "text", "text": "How much RAM do I have available?"}]
    }
  },
  "id": 1
}

→ Response:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "task-uuid",
    "sessionId": "session-uuid",
    "status": {"state": "completed", "timestamp": "..."},
    "artifacts": [
      {"parts": [{"type": "text", "text": "You have 8 GB of RAM..."}], "index": 0}
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

### Session management
Each unique `sessionId` maintains its own agent instance with independent conversation history. Maximum 50 simultaneous sessions (LRU).

---

## MCP protocol

The MCP server exposes Jarvis's 58 tools in standard MCP format.

### Configuration in Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json`)
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

### Exposed tools
All static registry tools are exposed with their identical schemas:
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

Allows extending the static registry at runtime:

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.a2a.client import load_a2a_agent
from jarvis.mcp_support.client import load_mcp_server

registry = DynamicToolRegistry()

# Add A2A agent as a tool
load_a2a_agent(registry, "http://specialist-agent:8080")
# → registers: delegate_to_specialist_agent(message: str)

# Add MCP server tools
load_mcp_server(registry, "npx -y @modelcontextprotocol/server-filesystem /tmp")
# → registers: mcp_read_file(...), mcp_write_file(...), etc.

# Create agent with the extended registry
from jarvis.brain.agent import JarvisAgent
agent = JarvisAgent(name="Jarvis", registry=registry)
```

---

## Environment variables (A2A / MCP)

| Variable | Default | Description |
|---|---|---|
| `JARVIS_A2A_HOST` | `0.0.0.0` | A2A server host |
| `JARVIS_A2A_PORT` | `8080` | A2A server port |
| `JARVIS_A2A_AGENTS` | `` | A2A agent URLs (comma-separated) |
| `JARVIS_MCP_SERVERS` | `` | MCP server specs (separated by `;`) |
| `JARVIS_LOG_FILE` | `~/.jarvis_tools.log` | Tool log file |
| `JARVIS_LOG_ENABLED` | `true` | Enable/disable tool logging |
| `JARVIS_SUDO_PASSWORD` | `` | Automatic sudo password (optional) |

---

## Optional dependencies

```bash
# A2A server only
pip install 'palmiche-jarvis[a2a]'
# → fastapi>=0.110.0, uvicorn>=0.29.0

# MCP only (server + client)
pip install 'palmiche-jarvis[mcp]'
# → mcp>=1.0.0

# Everything
pip install 'palmiche-jarvis[all]'
```

---

## Data flow: agentic loop with remote tools

```
User: "Analyze this file and ask agent2 what it thinks"
         │
         ▼
JarvisAgent.chat()
         │
         ▼
Anthropic API  ←  tools: [local_tools + delegate_to_agent2 + mcp_read_file]
         │
         ▼ stop_reason=tool_use
         │
         ├─→ read_file("file.txt")                ← local execution
         │
         └─→ delegate_to_agent2("content...")      ← A2AClient.send_task()
                    │                                    │
                    │                                    ▼
                    │                              http://agent2:8080/
                    │                                    │
                    │                              agent2.chat(...)
                    │                                    │
                    ◄────────────────────────────────────┘ response text
         │
         ▼ tool_result
Anthropic API (second call with results)
         │
         ▼ stop_reason=end_turn
User: "Agent2 thinks that..."
```

---

## Security

- The A2A server does not include authentication by default. For production, use a reverse proxy (nginx, Caddy) with TLS and authentication.
- Destructive tools (`power_action`, `run_shell_command`, `setup_autostart`) require `confirmed=true` in their inputs to execute.
- The MCP server operates only on stdio (local process), with no network exposure.
- Remote A2A agents connected as clients execute code in their own environment; the result is only returned as text to the local agent.
- **Logging**: all tool calls are logged to `~/.jarvis_tools.log` with timestamp, inputs and result. Can be disabled with `JARVIS_LOG_ENABLED=false`.
- **Automatic sudo**: when `JARVIS_SUDO_PASSWORD` is configured, the agent uses it via `sudo -S` after requesting user confirmation. If a command fails with "Permission denied", the system detects the error and offers to retry with privileges.
