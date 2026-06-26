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
│  ToolRegistry (static, 59 tools)                                       │
│  DynamicToolRegistry (extends static with remote tools)                │
│                                                                         │
│  Local tools:                                                          │
│    system, files, apps, web, shell, clipboard,                         │
│    notifications, network, media, screenshot, autostart,               │
│    events, dev, weather, notes, timers, calculator, text,              │
│    computer_use (Gemini visual), custom (user-defined)                 │
│                                                                         │
│  Dynamic tools (runtime):                                              │
│    delegate_to_<agent>   ← A2A client                                  │
│    mcp_<tool>            ← MCP client                                  │
│    <name>                ← custom tools (plain text)                   │
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
├── README.md
├── README-US.md
├── pyproject.toml               # Package definition, optional groups and CLI entrypoint
├── extract_assets.py            # Icon and audio extractor from YouTube
│
├── jarvis/                      # Main package
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point — argparse, modes: interactive, query, tray,
│   │                            #   --serve-a2a, --serve-mcp, --connect-a2a, --connect-mcp
│   ├── config.py                # All environment variables with defaults
│   ├── install.sh               # Interactive installer (splash, module selection)
│   ├── requirements.txt         # Direct project dependencies
│   ├── custom_tools.example.txt # Example template for custom tools
│   │
│   ├── brain/
│   │   ├── agent.py             # JarvisAgent (Anthropic SDK) — supports DynamicToolRegistry
│   │   ├── adk_agent.py         # JarvisADKAgent (Google ADK: Claude via LiteLLM or native Gemini)
│   │   ├── ollama_agent.py      # JarvisOllamaAgent (local models via Ollama)
│   │   └── prompts.py           # System prompts (EN/ES based on JARVIS_TOOL_LANG)
│   │
│   ├── tools/
│   │   ├── registry.py          # 59 static tools + dispatcher execute_tool()
│   │   ├── dynamic.py           # DynamicToolRegistry — extends registry at runtime
│   │   ├── translations.py      # EN/ES overlay for tool schemas (JARVIS_TOOL_LANG)
│   │   ├── custom.py            # Loader for user-defined tools (plain text file)
│   │   ├── system.py            # CPU, RAM, disk, battery, volume, brightness
│   │   ├── apps.py              # Open/close/list applications
│   │   ├── files.py             # Search/read/write/delete/move files
│   │   ├── web.py               # URLs, web search, page fetch, RSS
│   │   ├── shell.py             # Arbitrary shell commands
│   │   ├── clipboard.py         # Clipboard
│   │   ├── notifications.py     # Desktop notifications
│   │   ├── network.py           # IP, WiFi, ping
│   │   ├── media.py             # Media playback control
│   │   ├── screenshot.py        # Screenshots
│   │   ├── autostart.py         # System automatic startup
│   │   ├── events.py            # Local event calendar
│   │   ├── dev.py               # JSON, hash, encoding, UUID, HTTP, git
│   │   ├── weather.py           # Weather and forecast (wttr.in, no API key)
│   │   ├── notes.py             # Persistent notes (local JSON)
│   │   ├── timer.py             # Timers and alarms (background threads)
│   │   ├── calculator.py        # Safe math expressions (AST), unit conversion
│   │   ├── text_tools.py        # Text processing and transformation
│   │   └── computer_use.py      # Visual automation with Gemini (Playwright / pyautogui)
│   │
│   ├── a2a/                     # Agent-to-Agent protocol (Google spec)
│   │   ├── __init__.py
│   │   ├── models.py            # A2A data models (AgentCard, Task, Message, etc.)
│   │   ├── server.py            # A2A HTTP server with FastAPI + uvicorn
│   │   └── client.py            # A2A client for consuming remote agents
│   │
│   ├── mcp_support/             # Model Context Protocol (Anthropic spec)
│   │   ├── __init__.py
│   │   ├── server.py            # MCP stdio server (exposes the 59 tools)
│   │   └── client.py            # MCP client (stdio and SSE) for consuming external servers
│   │
│   ├── interface/
│   │   ├── cli.py               # CLI interface with Rich (colors, markdown, panels)
│   │   ├── tray.py              # System tray GUI with PyQt6 (Palmiche palette)
│   │   ├── hud_animation.py     # Iron Man-style HUD animation (QPainter, 3 rings, radar)
│   │   ├── animation.py         # WaveformAnimation (QWidget) for visual feedback
│   │   ├── audio_engine.py      # Centralized audio engine (queue, TTS cache, streaming, volume)
│   │   ├── voice.py             # Speech recognition (SpeechRecognition) — TTS via AudioEngine
│   │   ├── wake_word.py         # WakeWordListener — background keyword detection
│   │   └── splash.py            # Animated welcome screen (Rich, Palmiche green)
│   │
│   ├── memory/
│   │   └── history.py           # Persistent conversation history (JSON)
│   │
│   ├── assets/
│   │   ├── space-bg.jpg         # Space background for the HUD
│   │   └── TheGoodMonolith.woff # Robotic monospaced font
│   │
│   └── scripts/
│       ├── 49-jarvis-power.rules      # Polkit rule for passwordless power actions
│       └── install-power-rules.sh     # Installs the polkit rule on the system
│
└── docs/
    ├── ARCHITECTURE.md          # Spanish version of this document
    ├── ARCHITECTURE-US.md       # This document
    ├── TOOLS.md                 # Complete guide for the 59 tools (ES)
    ├── TOOLS-US.md              # Complete guide for the 59 tools (EN)
    ├── INSTALL.md               # Step-by-step installation guide (ES)
    ├── INSTALL-US.md            # Step-by-step installation guide (EN)
    ├── MCP-AGENTS.md            # MCP and external agents guide (ES)
    ├── MCP-AGENTS-US.md         # MCP and external agents guide (EN)
    ├── CHANGELOG.md
    └── CHANGELOG-US.md
```

---

## Operation modes

### 1. Interactive CLI (default)
```bash
python -m jarvis [--backend anthropic|adk|gemini|ollama]
# or with the installed entrypoint:
jarvis
```
Interactive loop in terminal. The agent processes user inputs, executes tools and responds.

### 2. Single query
```bash
python -m jarvis -q "how much RAM do I have?"
```
Executes a query and exits. Useful for scripting and pipes.

### 3. System tray
```bash
python -m jarvis --tray
```
System tray GUI (PyQt6) with chat window, HUD animation and optional voice and wake word support.

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
Exposes the 59 tools via MCP protocol on stdio. Compatible with Claude Desktop, Cursor, Zed, Continue.dev and any MCP client.

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

## Tool schema localization

The `tools/translations.py` module provides an EN/ES overlay for tool schemas. The canonical schemas are written in Spanish in `registry.py`; the `JARVIS_TOOL_LANG` variable (default: `en`) selects the language the model receives in its tool definitions.

```
JARVIS_TOOL_LANG=en  →  model sees schemas in English (better tool-calling reliability)
JARVIS_TOOL_LANG=es  →  model sees original Spanish schemas
```

This is independent of the user-facing reply language: the assistant always responds in the user's own language.

---

## Custom tools

The `tools/custom.py` module loads user-defined tools from a plain text file (`~/.jarvis_custom_tools.txt` by default, configurable with `JARVIS_CUSTOM_TOOLS_FILE`). It allows adding tools without writing Python.

File format:

```
[tool: home_weather]
description: Current weather in my city
command: curl -s "wttr.in/Havana?format=3"

[tool: greet]
description: Greet someone by name
param *name: The person's name
param language: Greeting language (optional)
command: echo "Hello {name} ({language})"
```

Custom tools are registered in the `DynamicToolRegistry` at startup; the model sees them exactly like the 59 built-in tools. Parameters are escaped with `shlex.quote` to prevent command injection.

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

The MCP server exposes Jarvis's 59 tools in standard MCP format.

### Configuration in Claude Desktop
macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "palmiche": {
      "command": "python",
      "args": ["-m", "jarvis", "--serve-mcp"],
      "cwd": "/path/to/palmiche-ai"
    }
  }
}
```

### Exposed tools (59)
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

Allows extending the static registry at runtime with tools from three sources: remote A2A agents, external MCP servers, and plain-text custom tools.

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.a2a.client import load_a2a_agent
from jarvis.mcp_support.client import load_mcp_server

registry = DynamicToolRegistry()

# Tools from a remote A2A agent
load_a2a_agent(registry, "http://specialist-agent:8080")
# → registers: delegate_to_specialist_agent(message: str)

# Tools from an external MCP server
load_mcp_server(registry, "npx -y @modelcontextprotocol/server-filesystem /tmp")
# → registers: mcp_read_file(...), mcp_write_file(...), etc.

# Custom tools from plain text file (loaded automatically on startup)
# → registers: home_weather(), greet(name, language=None), etc.

# Create agent with the extended registry
from jarvis.brain.agent import JarvisAgent
agent = JarvisAgent(name="Jarvis", registry=registry)
```

---

## Environment variables

All variables are read from `jarvis/.env` (or from the process environment).

### Backend and model
| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for `anthropic` and `adk`+Claude backends |
| `GOOGLE_API_KEY` | — | Required for `gemini`, `adk`+Gemini backends and Computer Use |
| `JARVIS_BACKEND` | `anthropic` | Backend: `anthropic` \| `adk` \| `gemini` \| `ollama` |
| `JARVIS_MODEL` | `claude-haiku-4-5-20251001` | Claude model (anthropic/adk backends) |
| `JARVIS_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model (gemini backend) |
| `JARVIS_OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `JARVIS_OLLAMA_MODEL` | `llama3.2` | Ollama model |

### Assistant and interface
| Variable | Default | Description |
|---|---|---|
| `JARVIS_NAME` | `Jarvis` | Assistant name |
| `JARVIS_TOOL_LANG` | `en` | Tool schema language: `en` \| `es` |
| `JARVIS_SPLASH_ENABLED` | `true` | Show animated welcome screen |
| `JARVIS_WELCOME_MESSAGE` | `Systems online...` | Splash phrase |
| `JARVIS_GOODBYE_MESSAGE` | `{name} disconnected...` | Farewell phrase (`{name}` = name) |
| `JARVIS_WAKE_WORD` | `palmiche` | Voice activation keyword (tray mode) |
| `JARVIS_VOICE_ENABLED` | `false` | Enable voice recognition |
| `JARVIS_AUDIO_VOLUME` | `100` | Global audio volume (0-100) |
| `JARVIS_TTS_CACHE` | `true` | Cache generated TTS audio (avoids re-synthesis) |
| `JARVIS_TTS_STREAM` | `true` | Stream TTS by sentence (lower perceived latency) |
| `JARVIS_TRAY_ICON` | — | Path to PNG/ICO for tray icon |
| `JARVIS_WELCOME_AUDIO` | — | Path to MP3/WAV played on tray startup |

### Storage
| Variable | Default | Description |
|---|---|---|
| `JARVIS_HISTORY_FILE` | `~/.jarvis_history.json` | Conversation history |
| `JARVIS_EVENTS_FILE` | `~/.jarvis_events.json` | Local calendar |
| `JARVIS_NOTES_FILE` | `~/.jarvis_notes.json` | Personal notes |
| `JARVIS_MAX_HISTORY` | `50` | Maximum messages in history |
| `JARVIS_CUSTOM_TOOLS_FILE` | `~/.jarvis_custom_tools.txt` | Plain text custom tools |

### A2A and MCP
| Variable | Default | Description |
|---|---|---|
| `JARVIS_A2A_HOST` | `0.0.0.0` | Host for Jarvis's own A2A server |
| `JARVIS_A2A_PORT` | `8080` | Port for Jarvis's own A2A server |
| `JARVIS_A2A_AGENTS` | — | Remote A2A agent URLs (comma-separated) |
| `JARVIS_MCP_SERVERS` | — | Remote MCP server specs (semicolon-separated) |

### Logging and security
| Variable | Default | Description |
|---|---|---|
| `JARVIS_LOG_FILE` | `~/.jarvis_tools.log` | Tool execution log file |
| `JARVIS_LOG_ENABLED` | `true` | Enable/disable tool logging |
| `JARVIS_SUDO_PASSWORD` | — | Automatic sudo password (optional) |

### Computer Use
| Variable | Default | Description |
|---|---|---|
| `COMPUTER_USE_MODEL` | `gemini-2.5-flash` | Gemini model for visual automation |
| `COMPUTER_USE_BACKEND` | `playwright` | `playwright` (browser) \| `desktop` (full desktop) |
| `COMPUTER_USE_MAX_ITERATIONS` | `30` | Visual agent iteration limit per task |

---

## Optional dependencies

```bash
pip install 'palmiche-jarvis[voice]'        # SpeechRecognition, pyaudio, pyttsx3, gTTS
pip install 'palmiche-jarvis[tray]'         # PyQt6, Pillow
pip install 'palmiche-jarvis[adk]'          # google-adk, litellm
pip install 'palmiche-jarvis[gemini]'       # google-adk
pip install 'palmiche-jarvis[assets]'       # yt-dlp
pip install 'palmiche-jarvis[a2a]'          # fastapi, uvicorn
pip install 'palmiche-jarvis[mcp]'          # mcp>=1.0.0
pip install 'palmiche-jarvis[computer-use]' # google-genai, playwright, pyautogui, Pillow, mss
pip install 'palmiche-jarvis[all]'          # all of the above
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
- Plain-text custom tools escape all parameters with `shlex.quote` before substituting them into the shell command.
- The MCP server operates only on stdio (local process), with no network exposure.
- Remote A2A agents connected as clients execute code in their own environment; the result is only returned as text to the local agent.
- **Logging**: all tool calls are logged to `~/.jarvis_tools.log` with timestamp, inputs and result. Can be disabled with `JARVIS_LOG_ENABLED=false`.
- **Automatic sudo**: when `JARVIS_SUDO_PASSWORD` is configured, the agent uses it via `sudo -S` after requesting user confirmation. If a command fails with "Permission denied", the system detects the error and offers to retry with privileges.
- **Polkit rules** (`scripts/49-jarvis-power.rules`): allows power actions (shutdown/restart/suspend) without a password for the configured user, without requiring global sudo.
