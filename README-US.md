# J.A.R.V.I.S.

> Just A Rather Very Intelligent System — personal AI assistant for laptop, powered by Claude.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Backends](https://img.shields.io/badge/backends-Anthropic%20%7C%20ADK%20%7C%20Gemini%20%7C%20Ollama-green.svg)](#backends)

## Features

- Natural conversation in Spanish or English with persistent session memory
- **59 built-in tools** to control the system, files, network, media, weather, notes, timers, calculations, and more
- **Computer Use** — full browser and desktop visual control using Gemini (inspired by [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview))
- **External tools via MCP** — connect any MCP server (stdio or SSE/HTTP) and inject its tools directly into the agent; the model uses them automatically
- **Remote agents via A2A** — delegate tasks to other AI agents (Google A2A) as if they were local tools; supports collaborative agent networks
- Four interchangeable backends: Anthropic SDK, Google ADK + LiteLLM, Google ADK + Gemini, and Ollama (local)
- Optional voice input with speech recognition
- Terminal interface with Rich (colors, markdown, panels)
- **Interactive installer** with animated Palmiche-AI splash, module menu, and progress bars

## Requirements

- Python 3.10+
- Linux or macOS

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/EroPerez/palmiche-ai.git
cd palmiche-ai
```

### 2. Virtual environment and base dependencies

```bash
python3 -m venv jarvis/.venv
source jarvis/.venv/bin/activate      # Linux/macOS
pip install -e .                       # installs dependencies from pyproject.toml
```

Or using the included **interactive installer** (recommended):

```bash
cd jarvis
bash install.sh
```

The installer displays an animated Palmiche-AI splash and asks which modules you want to install (all, core only, or custom selection).

### 3. Configure environment variables

```bash
cp jarvis/.env.example jarvis/.env
nano jarvis/.env                      # edit with your API keys
```

---

### Optional components

#### Anthropic backend (default)

Requires an account at [console.anthropic.com](https://console.anthropic.com).

```bash
# In .env:
# ANTHROPIC_API_KEY=sk-ant-...
# JARVIS_MODEL=claude-haiku-4-5-20251001

python -m jarvis --backend anthropic
```

#### Google ADK + Claude backend

```bash
pip install "palmiche-jarvis[adk]"
# or manually:
pip install google-adk litellm

# In .env:
# ANTHROPIC_API_KEY=sk-ant-...
python -m jarvis --backend adk
```

#### Google ADK + Gemini backend

Requires an account at [aistudio.google.com](https://aistudio.google.com) to obtain a `GOOGLE_API_KEY`.

```bash
pip install "palmiche-jarvis[gemini]"
# or manually:
pip install google-adk

# In .env:
# GOOGLE_API_KEY=AIza...
# JARVIS_GEMINI_MODEL=gemini-2.0-flash
python -m jarvis --backend gemini
```

#### Ollama backend (local model, no API key)

1. Install Ollama:

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama
```

2. Download a model:

```bash
ollama pull llama3.2          # ~2 GB, recommended
# alternatives:
ollama pull llama3.2:1b       # ~0.8 GB, faster
ollama pull qwen2.5:3b        # ~2 GB, better tool-use
ollama pull llama3.1:8b       # ~5 GB, more capable
```

3. Start the server (if it doesn't start automatically):

```bash
ollama serve
```

4. Run Jarvis:

```bash
# In .env (optional, these are the default values):
# JARVIS_OLLAMA_HOST=http://localhost:11434
# JARVIS_OLLAMA_MODEL=llama3.2
python -m jarvis --backend ollama
```

#### System tray mode

Requires **PyQt6** and Pillow. On Linux, XCB libraries are also needed.

```bash
# Linux (Ubuntu/Debian)
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                 libxcb-keysyms1 libxcb-render-util0

pip install "palmiche-jarvis[tray]"
# equivalent to: pip install PyQt6 PyQt6-Qt6-Multimedia Pillow

python -m jarvis --tray
```

#### Voice activation

Requires PortAudio headers to compile PyAudio.

```bash
# Linux
sudo apt install python3-dev portaudio19-dev

# macOS
brew install portaudio

pip install "palmiche-jarvis[voice]"
# or manually:
pip install SpeechRecognition pyaudio pyttsx3 gtts

# In .env:
# JARVIS_VOICE_ENABLED=true
python -m jarvis --tray       # voice only works in tray mode
```

#### Computer Use — visual browser and desktop control

Palmiche-AI can control a Chromium browser or the full desktop using the Gemini computer use API, taking screenshots and executing actions (click, type, scroll, navigation...).

```bash
pip install "palmiche-jarvis[computer-use]"
# equivalent to: pip install google-genai playwright pyautogui Pillow mss

# Install Chromium for Playwright (playwright backend only)
playwright install chromium
```

Requires `GOOGLE_API_KEY` in `.env`. Usage from chat:

```
Search for the dollar price today in the browser
Open YouTube and play jazz music
Fill out the contact form at example.com with my details
```

Configuration variables:

```ini
COMPUTER_USE_MODEL=gemini-2.5-flash     # Gemini model for computer use
COMPUTER_USE_BACKEND=playwright          # "playwright" (browser) or "desktop"
COMPUTER_USE_MAX_ITERATIONS=30          # visual agent iteration limit
```

#### Full installation (all components)

```bash
# Linux — system dependencies first
sudo apt install \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-render-util0 \
    python3-dev portaudio19-dev ffmpeg mpg123

pip install "palmiche-jarvis[all]"
# equivalent to: pip install "palmiche-jarvis[voice,tray,adk,assets,a2a,mcp,computer-use]"
```

## Configuration

```bash
cp jarvis/.env.example jarvis/.env
nano jarvis/.env
```

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required for `anthropic` and `adk`+Claude backends |
| `GOOGLE_API_KEY` | — | Required for `gemini` and `adk`+Gemini backends |
| `JARVIS_MODEL` | `claude-haiku-4-5-20251001` | Claude model (anthropic/adk backends) |
| `JARVIS_GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model (gemini backend) |
| `JARVIS_NAME` | `Jarvis` | Assistant name |
| `JARVIS_SPLASH_ENABLED` | `true` | Animated welcome screen (green) on startup |
| `JARVIS_WELCOME_MESSAGE` | `Sistemas en línea. ¿En qué puedo ayudarte?` | Splash welcome phrase (override with `--welcome`) |
| `JARVIS_GOODBYE_MESSAGE` | `{name} desconectado. Hasta luego.` | Farewell phrase on exit (override with `--goodbye`). `{name}` = name |
| `JARVIS_BACKEND` | `anthropic` | Backend: `anthropic`, `adk`, `gemini` or `ollama` |
| `JARVIS_OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL (`ollama` backend) |
| `JARVIS_OLLAMA_MODEL` | `llama3.2` | Ollama model to use |
| `JARVIS_VOICE_ENABLED` | `false` | Enable voice (requires extra dependencies) |
| `JARVIS_MAX_HISTORY` | `50` | Maximum messages in history |
| `JARVIS_EVENTS_FILE` | `~/.jarvis_events.json` | Local event calendar file |
| `JARVIS_NOTES_FILE` | `~/.jarvis_notes.json` | Personal notes file |
| `JARVIS_WAKE_WORD` | `palmiche` | Voice activation wake word in `--tray` mode |
| `JARVIS_HISTORY_FILE` | `~/.jarvis_history.json` | Conversation history file |
| `JARVIS_TRAY_ICON` | — | Path to PNG/ICO image for tray icon (empty = built-in horse icon) |
| `JARVIS_WELCOME_AUDIO` | — | Path to MP3/WAV played on tray startup (generate with `python extract_assets.py`) |
| `JARVIS_A2A_HOST` | `0.0.0.0` | A2A server host (`--serve-a2a` mode) |
| `JARVIS_A2A_PORT` | `8080` | A2A server port |
| `JARVIS_A2A_AGENTS` | — | Remote A2A agent URLs (comma-separated) |
| `JARVIS_MCP_SERVERS` | — | MCP server specs (separated by `;`). Stdio command or SSE URL |
| `JARVIS_LOG_FILE` | `~/.jarvis_tools.log` | Tool execution log file |
| `JARVIS_LOG_ENABLED` | `true` | Enable/disable tool logging |
| `JARVIS_SUDO_PASSWORD` | — | Sudo password for commands requiring privileges (optional) |
| `COMPUTER_USE_MODEL` | `gemini-2.5-flash` | Gemini model for computer use (requires `GOOGLE_API_KEY`) |
| `COMPUTER_USE_BACKEND` | `playwright` | Computer use backend: `playwright` (browser) or `desktop` |
| `COMPUTER_USE_MAX_ITERATIONS` | `30` | Visual agent iteration limit per task |

## Usage guide

### Quick start

```bash
# Anthropic backend (default) — requires ANTHROPIC_API_KEY in .env
python -m jarvis

# Local backend without API key
python -m jarvis --backend ollama

# Change assistant name
python -m jarvis --name "Friday"

# Custom welcome and farewell phrases (animated green splash)
python -m jarvis --welcome "Hello, boss" --goodbye "See you later, {name}"

# Skip the animated welcome screen
python -m jarvis --no-splash

# System tray mode (taskbar icon)
python -m jarvis --tray

# Combine options
python -m jarvis --backend gemini --name "Jarvis" --tray

# A2A server (exposes Jarvis as an HTTP agent)
python -m jarvis --serve-a2a --a2a-port 8080

# MCP stdio server (for Claude Desktop, Cursor, Zed, etc.)
python -m jarvis --serve-mcp

# Connect to A2A agents and remote MCP servers
python -m jarvis --connect-a2a http://other-agent:8080 --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"
```

### Command-line options

| Option | Values | Description |
|---|---|---|
| `--backend` | `anthropic`, `adk`, `gemini`, `ollama` | AI engine (default: `anthropic`) |
| `--name` | any text | Assistant name (default: `Jarvis`) |
| `--welcome` | any text | Splash welcome phrase (default: `JARVIS_WELCOME_MESSAGE`) |
| `--goodbye` | any text | Farewell phrase on exit; supports `{name}` |
| `--no-splash` | — | Don't show the animated welcome screen |
| `--tray` | — | Start in system tray mode |
| `--voice` | — | Enable voice recognition |
| `--wake-word` | text | Voice activation wake word in `--tray` mode (default: `palmiche`) |
| `--query` / `-q` | text | Run a single query and exit |
| `--clear` | — | Clear history and exit |
| `--serve-a2a` | — | Start as A2A server (Agent-to-Agent protocol) |
| `--a2a-host` | host | A2A server host (default: `0.0.0.0`) |
| `--a2a-port` | port | A2A server port (default: `8080`) |
| `--connect-a2a` | URL | Connect to a remote A2A agent as a tool (repeatable) |
| `--serve-mcp` | — | Start as MCP stdio server (Claude Desktop, Cursor, etc.) |
| `--connect-mcp` | spec | Connect to an external MCP server (stdio command or SSE URL, repeatable) |

### In-chat commands

| Command | Action |
|---|---|
| `salir` / `exit` / `quit` | End the session |
| `limpiar` / `clear` | Clear conversation history |
| `voz` / `/voz` / `voice` / `/voice` | Toggle voice input mode ON/OFF |

### Usage examples by category

**System and hardware**
```bash
How are the CPU and RAM doing?
How much battery do I have left?
Turn the volume up to 70%
Set brightness to 50%
Lock the screen
```

**Files and directories**
```bash
List the files in ~/Documents
Search for PDF files on the desktop
Read the file ~/notes.txt
Create the folder ~/projects/new
Move ~/Downloads/photo.jpg to ~/Images/
```

**Applications and processes**
```bash
Open Firefox
Close Spotify
What applications are running?
```

**Network and connectivity**
```bash
What's my IP?
Ping google.com
What WiFi network am I connected to?
```

**Web and search**
```bash
Search YouTube for Python tutorials
Open github.com
Search DuckDuckGo for "best code editors"
Read the article at https://example.com/news
Show me the latest news from the feed https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada
```

**Weather**
```bash
What's the weather like in Madrid?
What will the weather be like this week in Buenos Aires?
Give me the forecast for the next 3 days in imperial
```

**Notes**
```bash
Create a note titled "Project ideas" with these ideas: ...
Show me all my notes with the "work" tag
Search my notes for something about "meeting"
Read the note "Project ideas"
```

**Timers and alarms**
```bash
Set a 25-minute timer for pomodoro
Set an alarm for 08:30 to wake up
What timers do I have active?
Cancel timer abc123
```

**Calculation and unit conversion**
```bash
What is sqrt(144) + 2^10?
Convert 100 km to miles
How many degrees Fahrenheit is 37°C?
How many GB are 1500 MB?
```

**Text tools**
```bash
Analyze this text and tell me how many words it has: "..."
Convert "hello world" to slug
Is "racecar" a palindrome?
```

**Clipboard and utilities**
```bash
What's in the clipboard?
Copy this text to clipboard: Hello world
Send a notification: "Meeting in 5 minutes"
```

**Shell (with explicit confirmation)**
```bash
Run: ls -la ~/
# Jarvis will ask for confirmation before running shell commands
```

**Autostart**
```bash
Enable Jarvis autostart
Disable autostart
```

### Voice activation

With `JARVIS_VOICE_ENABLED=true` in `.env`, say the keyword **"palmiche"** to open the chat. The system listens in the background and activates the window when the keyword is detected.

```bash
# Linux: install system dependencies first
sudo apt install python3-dev portaudio19-dev

# macOS
brew install portaudio

# Then install Python packages
pip install SpeechRecognition pyaudio pyttsx3 gtts
# or with the optional group:
pip install "palmiche-jarvis[voice]"

# In .env:
# JARVIS_VOICE_ENABLED=true
python -m jarvis --tray
```

## External tools (MCP and A2A agents)

Jarvis can consume tools from **external MCP servers** and delegate tasks to **remote A2A agents**, extending its capabilities without limits.

> Full step-by-step guide with concrete examples: **[MCP-AGENTS-US.md](MCP-AGENTS-US.md)**

```bash
# Connect to an external MCP server (filesystem, GitHub, DB, etc.)
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/projects"
python -m jarvis --connect-mcp "http://my-mcp-server:3000"

# Connect to remote A2A agents
python -m jarvis --connect-a2a http://specialized-agent:8080

# Combine everything
python -m jarvis \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/projects" \
  --connect-mcp "npx -y @modelcontextprotocol/server-github" \
  --connect-a2a http://reviewer-agent:8080
```

MCP tools are injected with the `mcp_` prefix (e.g. `mcp_read_file`); A2A agents with the `delegate_to_` prefix (e.g. `delegate_to_analyst`). Also configurable in `.env`:

```ini
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem ~/projects;http://my-server:3000
JARVIS_A2A_AGENTS=http://agent1:8080,http://agent2:9090
```

---

## Available tools (59)

> Complete guide with FAQ per tool: **[TOOLS.md](TOOLS.md)**

### System

| Tool | Description |
|---|---|
| `get_system_info` | CPU, RAM, disk and uptime |
| `get_battery_info` | Battery percentage, charging status and remaining time |
| `control_volume` | Raise, lower, mute or set volume (0-100) |
| `control_brightness` | Control screen brightness (Linux: brightnessctl) |
| `power_action` | Shutdown, restart, suspend or lock screen |

### Applications

| Tool | Description |
|---|---|
| `open_application` | Open an app by name or command |
| `close_application` | Close process by name (SIGTERM or SIGKILL) |
| `list_running_apps` | List running processes with memory usage |

### Files

| Tool | Description |
|---|---|
| `search_files` | Search files or directories by name or pattern |
| `list_directory` | List directory contents |
| `read_file` | Read text (first N lines, default 100) |
| `write_file` | Write or append content to a file |
| `delete_file` | Delete file or empty directory |
| `move_file` | Move or rename file or directory |
| `copy_file` | Copy file or directory |
| `open_file` | Open with the system's default application |
| `create_directory` | Create directory (including parent directories) |

### Network

| Tool | Description |
|---|---|
| `get_network_info` | Local IP, public IP, SSID and WiFi signal |
| `ping_host` | Ping with latency and packet loss summary |

### Media

| Tool | Description |
|---|---|
| `media_control` | Play, pause, next, previous, stop and status |
| `get_media_status` | Title and artist of the active track |

### Screenshots

| Tool | Description |
|---|---|
| `take_screenshot` | Full screen capture or area selection |

### Web

| Tool | Description |
|---|---|
| `open_url` | Open URL in the default browser |
| `web_search` | Search on Google, DuckDuckGo or YouTube (incognito mode) |
| `fetch_webpage` | Download and extract readable text from any URL |
| `get_rss_feed` | Get the latest entries from an RSS or Atom feed |

### Utilities

| Tool | Description |
|---|---|
| `get_clipboard` | Read clipboard contents |
| `set_clipboard` | Write text to clipboard |
| `send_notification` | Desktop notification (low / normal / critical) |
| `run_shell_command` | Run arbitrary shell command (with confirmation) |
| `setup_autostart` | Enable or disable automatic startup with the system |

### Weather

No API key required. Real-time data via [wttr.in](https://wttr.in).

| Tool | Description |
|---|---|
| `get_weather` | Current weather: temperature, humidity, wind, visibility and pressure |
| `get_forecast` | 1-3 day forecast with max/min temperature and precipitation |

### Notes

Local notes in JSON (`~/.jarvis_notes.json`, configurable with `JARVIS_NOTES_FILE`). Tag support and full-text search.

| Tool | Description |
|---|---|
| `create_note` | Create new note or update existing one with same title |
| `list_notes` | List all notes, with optional tag filter |
| `read_note` | Read full content of a note by title or id |
| `search_notes` | Search in title and content of all notes |
| `delete_note` | Delete note by title or id |

### Timers and alarms

Run in the background and trigger desktop notifications on completion.

| Tool | Description |
|---|---|
| `set_timer` | Timer by duration in seconds (max 24h) |
| `set_alarm` | Alarm at a specific time `HH:MM` (rolls to next day if already past) |
| `list_timers` | List active timers with remaining time |
| `cancel_timer` | Cancel a timer by its id |

### Calculator and unit conversion

| Tool | Description |
|---|---|
| `calculate` | Safely evaluates math expressions (AST, no `eval`). Supports `sqrt`, `sin/cos/tan`, `log`, `factorial`, constants `pi`/`e`, and more |
| `convert_units` | Convert between units of length, mass, temperature, speed, area, volume and digital storage |

### Text tools

| Tool | Description |
|---|---|
| `text_stats` | Words, characters, lines, sentences and estimated reading time |
| `text_transform` | Transform text: `upper`, `lower`, `title`, `slug`, `snake`, `camel`, `pascal`, `reverse`, `palindrome`, `strip_accents` and more |

### Calendar and events

Local calendar in JSON (`~/.jarvis_events.json`, configurable with `JARVIS_EVENTS_FILE`). Works offline without external accounts.

| Tool | Description |
|---|---|
| `add_event` | Create event (date `YYYY-MM-DD` or `today`/`tomorrow`, optional time) |
| `list_events` | List events, with optional `start`/`end` range |
| `upcoming_events` | Upcoming events from today for N days (default 7) |
| `delete_event` | Delete event by its id |

### Developer

| Tool | Description |
|---|---|
| `format_json` | Validate and pretty-print JSON |
| `hash_text` | Text hash (md5 / sha1 / sha256 / sha512) |
| `encode_decode` | Encode/decode in base64, url or hex |
| `generate_uuid` | Generate one or more UUID4s |
| `convert_timestamp` | Convert between Unix epoch and ISO-8601 (`now`) |
| `http_request` | HTTP request (GET/POST/...) with status, headers and preview — useful for testing APIs |
| `git_status` | Branch, tree status and latest commits of a git repo |
| `find_process_on_port` | Which process is listening on a TCP port |

### Computer Use ★

Visual automation of browser or full desktop with Gemini visual intelligence. Requires `GOOGLE_API_KEY` and `pip install "palmiche-jarvis[computer-use]"`.

| Tool | Description |
|---|---|
| `computer_use_task` | Visually controls a Chromium browser (Playwright) or the full desktop (pyautogui) to complete tasks described in natural language. Takes screenshots and executes actions: click, double-click, type, scroll, drag, navigation, keys, key combinations |

## Backends

### Anthropic SDK (default)

Manual agentic loop: sends messages to the model, executes tools and repeats until `end_turn`. Maximum 10 iterations per turn. No additional dependencies.

```bash
python -m jarvis --backend anthropic
```

### Google ADK + Claude (`adk`)

ADK orchestrates the loop internally via `Runner` + `InMemorySessionService`, using LiteLLM as a bridge to the Anthropic API.

Auto-detection: if you only have `GOOGLE_API_KEY` (without `ANTHROPIC_API_KEY`), the `adk` backend automatically switches to Gemini.

```bash
pip install google-adk litellm
python -m jarvis --backend adk
```

### Google ADK + Gemini (`gemini`)

Uses Gemini natively without LiteLLM. Only requires `GOOGLE_API_KEY`.

```bash
pip install google-adk
# In .env: GOOGLE_API_KEY=your-key, JARVIS_GEMINI_MODEL=gemini-2.0-flash
python -m jarvis --backend gemini
```

### Ollama — local model (`ollama`)

Runs an LLM locally without sending data to the cloud. No additional pip packages required; uses `requests` (already included).

**Requirements:**
1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Download a model: `ollama pull llama3.2`
3. The server starts automatically, or manually: `ollama serve`

```bash
# In .env (or environment variables):
# JARVIS_OLLAMA_MODEL=llama3.2      # model to use
# JARVIS_OLLAMA_HOST=http://localhost:11434  # server URL

python -m jarvis --backend ollama
```

**Recommended models** (from least to most capable):

| Model | Size | Notes |
|---|---|---|
| `llama3.2:1b` | ~0.8 GB | Very fast, basic tool-use |
| `llama3.2` | ~2 GB | Recommended default |
| `qwen2.5:3b` | ~2 GB | Excellent tool-use for its size |
| `llama3.1:8b` | ~5 GB | More capable, requires more RAM |

## System tray mode

Starts Jarvis as a taskbar icon with a chat window (PyQt6):

```bash
# Linux (Ubuntu/Debian) — required XCB libraries
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                 libxcb-keysyms1 libxcb-render-util0

pip install "palmiche-jarvis[tray]"   # PyQt6 + Pillow
python -m jarvis --tray
# or combine with any backend:
python -m jarvis --tray --backend gemini
```

The app **starts minimized** in the tray. The window appears when:
- Clicking the tray icon
- Saying the voice activation keyword (if `[voice]` is installed)
- Typing `salir` / `exit` / `quit` in chat closes the application completely

The chat window includes:

- **HUD animation** Iron Man style in the header (states: idle / listening / processing)
- **Status bar** at the bottom with color (Ready / processing / listening / error)
- **Timestamps** `[HH:MM]` on each message
- **🗑 Button** and shortcuts: `Esc` hides the window, `Ctrl+L` clears the conversation
- **🎤 Button** for voice input (requires `[voice]`)
- **Centered** window on screen, smooth fade-in/out on show/hide
- **Tray icon** with a horse head (homage to Palmiche)

`.env` variables for tray mode:

| Variable | Description |
|---|---|
| `JARVIS_TRAY_ICON` | Path to custom PNG/ICO image (empty = built-in icon) |
| `JARVIS_WELCOME_AUDIO` | Path to MP3/WAV played on startup (generate with `python extract_assets.py`) |

## Security

- **Destructive tools** (`power_action`, `run_shell_command`, `setup_autostart`) require `confirmed=true` in code before executing — not just in the prompt.
- Notifications on macOS pass title and message as argv arguments to `osascript`, never interpolated in the AppleScript source.
- Clipboard write confirmation only returns the character count, without exposing the content.

## System dependencies (optional)

| Feature | Linux | macOS |
|---|---|---|
| System tray (XCB) | `sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0` | — |
| Media control | `sudo apt install playerctl` | Built-in (Music.app) |
| Screenshots | `sudo apt install scrot` | Built-in (`screencapture`) |
| Brightness control | `sudo apt install brightnessctl` | — |
| WiFi info | `nmcli` (NetworkManager) | Built-in (`airport`) |
| Notifications | `sudo apt install libnotify-bin` | Built-in (osascript) |
| Voice (recognition) | `sudo apt install python3-dev portaudio19-dev` + `pip install "palmiche-jarvis[voice]"` | `brew install portaudio` + pip |
| Voice (audio response) | `sudo apt install mpg123` | `brew install ffmpeg` |
| Assets (icon/audio) | `sudo apt install ffmpeg` + `pip install "palmiche-jarvis[assets]"` | `brew install ffmpeg` + pip |
| Computer Use (Playwright) | `pip install "palmiche-jarvis[computer-use]"` + `playwright install chromium` | same |
| Computer Use (desktop) | `pip install pyautogui mss` | same |

### Passwordless power actions (Linux)

`power_action` (shutdown / restart / suspend) uses `systemctl`, which on many
systems asks for polkit authentication and, in a non-interactive context, fails with
`Interactive authentication required`. To allow them without a password for the
active local session, install the included polkit rule:

```bash
sudo jarvis/scripts/install-power-rules.sh
```

The installer substitutes your user (the one running `sudo`) in the rule, copies
`jarvis/scripts/49-jarvis-power.rules` to `/etc/polkit-1/rules.d/` and restarts
polkit. The rule grants shutdown/restart/suspend/hibernate **only to your
user**. To use another account: `JARVIS_USER=other sudo jarvis/scripts/install-power-rules.sh`.
Screen lock (`lock`) does not require this rule.

## Contributing

1. Fork the repository
2. Create a branch for your feature: `git checkout -b feat/new-tool`
3. Commit with descriptive messages: `git commit -m "feat: add new tool"`
4. Push to your fork: `git push origin feat/new-tool`
5. Open a Pull Request describing the changes

To add a new tool, create a module in `jarvis/tools/` and register it in `jarvis/tools/registry.py` following the pattern of existing tools.

## License

This project is licensed under the [MIT License](LICENSE).

```text
MIT License — Copyright (c) 2026 EroPerez

Permission is hereby granted to use, copy, modify and distribute this software
without restriction, subject to inclusion of the original copyright notice.
```
