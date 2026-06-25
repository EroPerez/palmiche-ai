# Installation guide — Palmiche J.A.R.V.I.S.

## Prerequisites

| Requirement | Minimum version |
|---|---|
| Python | 3.10+ |
| Operating system | Linux or macOS |
| pip | Included with Python |

---

## 1. Clone the repository

```bash
git clone https://github.com/EroPerez/palmiche-ai.git
cd palmiche-ai
```

---

## 2. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> In future sessions you only need `source .venv/bin/activate` to activate the environment.

---

## 3. Install base dependencies

### Option A — Interactive installer (recommended)

```bash
cd jarvis
bash install.sh
```

The installer displays a **Palmiche-AI splash** in the terminal, verifies system requirements, installs the core and presents a menu to choose optional modules:

```
  [1]  Everything        Full installation (all modules)
  [2]  Core only         Core + Anthropic Claude (minimum functional)
  [3]  Custom            Select modules individually
```

### Option B — Manual with pip

```bash
pip install -e .
```

This installs the core: `anthropic`, `rich`, `python-dotenv`, `psutil`, `pyperclip` and `requests`.

---

## 4. Configure environment variables

```bash
cp jarvis/.env.example jarvis/.env
nano jarvis/.env          # or your favorite editor
```

Essential variables:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (required for the default backend) |
| `GOOGLE_API_KEY` | Google AI Studio API key (only for `gemini` / `adk`+Gemini backends) |
| `JARVIS_NAME` | Assistant name (default: `Jarvis`) |
| `JARVIS_BACKEND` | AI engine: `anthropic` (default), `adk`, `gemini`, `ollama` |

> Get your Anthropic API key at [console.anthropic.com](https://console.anthropic.com).
> Get your Google API key at [aistudio.google.com](https://aistudio.google.com).

---

## 5. Verify the base installation

```bash
python -m jarvis --help
python -m jarvis -q "hello"     # quick test query
```

---

## Optional components

### Graphical interface (system tray)

The tray interface uses **PyQt6** with an Iron Man-style HUD animation.
Requires graphical support (Xorg or Wayland).

```bash
# Ubuntu / Debian
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                 libxcb-keysyms1 libxcb-render-util0

# Fedora / RHEL
sudo dnf install xcb-util-cursor xcb-util-icccm xcb-util-image \
                 xcb-util-keysyms xcb-util-renderutil

# Install Python packages
pip install "palmiche-jarvis[tray]"
# equivalent to: pip install PyQt6 PyQt6-Qt6-Multimedia Pillow
```

Start in tray mode:

```bash
python -m jarvis --tray
```

`.env` variables for tray mode:

| Variable | Description |
|---|---|
| `JARVIS_TRAY_ICON` | Path to custom PNG/ICO image (empty = built-in horse icon) |
| `JARVIS_WELCOME_AUDIO` | Path to MP3/WAV played on tray startup |

---

### Voice activation and speech recognition

```bash
# Ubuntu / Debian — system dependencies
sudo apt install python3-dev portaudio19-dev

# macOS
brew install portaudio

# Python packages
pip install "palmiche-jarvis[voice]"
# equivalent to: pip install SpeechRecognition pyaudio pyttsx3 gtts

# Audio player (for gTTS responses)
sudo apt install mpg123            # Linux
# macOS already includes ffplay if you have ffmpeg installed
```

Enable in `.env`:

```ini
JARVIS_VOICE_ENABLED=true
JARVIS_WAKE_WORD=palmiche          # activation keyword (default)
```

With voice enabled, say **"palmiche"** at any time for Jarvis to open the window and start listening.

---

### Google ADK + Claude backend

```bash
pip install "palmiche-jarvis[adk]"
# equivalent to: pip install google-adk litellm
```

`.env`:

```ini
JARVIS_BACKEND=adk
ANTHROPIC_API_KEY=sk-ant-...
```

---

### Google ADK + Gemini backend

```bash
pip install "palmiche-jarvis[gemini]"
# equivalent to: pip install google-adk
```

`.env`:

```ini
JARVIS_BACKEND=gemini
GOOGLE_API_KEY=AIza...
JARVIS_GEMINI_MODEL=gemini-2.0-flash
```

---

### Ollama backend (local model, no API key)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh    # Linux
brew install ollama                               # macOS

# 2. Download a model
ollama pull llama3.2        # ~2 GB, recommended
# alternatives:
ollama pull llama3.2:1b     # ~0.8 GB, faster
ollama pull qwen2.5:3b      # ~2 GB, excellent tool-use
ollama pull llama3.1:8b     # ~5 GB, more capable

# 3. Start server (if it doesn't start automatically)
ollama serve
```

`.env`:

```ini
JARVIS_BACKEND=ollama
JARVIS_OLLAMA_HOST=http://localhost:11434
JARVIS_OLLAMA_MODEL=llama3.2
```

---

### A2A protocol (Agent-to-Agent)

Allows Jarvis to act as an HTTP server for other agents, or connect to remote agents as tools.

```bash
pip install "palmiche-jarvis[a2a]"
# equivalent to: pip install fastapi uvicorn
```

Usage:

```bash
# A2A server
python -m jarvis --serve-a2a --a2a-port 8080

# Connect to remote A2A agent as a tool
python -m jarvis --connect-a2a http://other-agent:8080
```

`.env`:

```ini
JARVIS_A2A_HOST=0.0.0.0
JARVIS_A2A_PORT=8080
JARVIS_A2A_AGENTS=http://agent1:8080,http://agent2:9090
```

---

### MCP protocol (Model Context Protocol)

Allows exposing Jarvis tools to IDEs like Claude Desktop, Cursor or Zed, or consuming external MCP servers.

```bash
pip install "palmiche-jarvis[mcp]"
# equivalent to: pip install mcp
```

Usage:

```bash
# MCP server (stdio, for Claude Desktop / Cursor)
python -m jarvis --serve-mcp

# Connect to external MCP server
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"
python -m jarvis --connect-mcp "http://localhost:3000"
```

`.env`:

```ini
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem /tmp;http://localhost:3001
```

---

### Computer Use — visual automation with Gemini ★

Allows Palmiche-AI to visually control a **Chromium browser** (via Playwright) or the **full desktop** (via pyautogui) to execute tasks described in natural language.

Inspired by [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview).

**Requirement:** `GOOGLE_API_KEY` in `jarvis/.env`

```bash
# Ubuntu / Debian — system dependencies for Playwright
sudo apt install libnss3 libatk1.0-0 libatk-bridge2.0-0 \
                 libcups2 libxcomposite1 libxdamage1 libxfixes3 \
                 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 \
                 libcairo2 libasound2

# Python packages
pip install "palmiche-jarvis[computer-use]"
# equivalent to: pip install google-genai playwright pyautogui Pillow mss

# Install Chromium for Playwright
playwright install chromium
```

`.env`:

```ini
GOOGLE_API_KEY=AIza...
COMPUTER_USE_MODEL=gemini-2.5-flash    # Gemini model for vision
COMPUTER_USE_BACKEND=playwright         # "playwright" or "desktop"
COMPUTER_USE_MAX_ITERATIONS=30         # step limit per task
```

**Usage from Jarvis chat:**

```
Search for the dollar price today using the browser
Open YouTube and play jazz music
Fill out the form at example.com with name "John" and email "john@test.com"
Navigate to gmail.com and tell me how many unread emails I have
```

**Available backends:**

| Backend | Controls | Requires |
|---|---|---|
| `playwright` (default) | Headless Chromium browser | `playwright` + `playwright install chromium` |
| `desktop` | Full desktop (any app) | `pyautogui` + `mss` + graphical environment |

> **Note:** The `desktop` backend requires a graphical environment (Xorg/Wayland) and real mouse control. Use with caution in production environments.

---

### Asset extraction (icon and audio from YouTube)

```bash
# System dependencies
sudo apt install ffmpeg     # Linux
brew install ffmpeg         # macOS

# Python package
pip install "palmiche-jarvis[assets]"
# equivalent to: pip install yt-dlp

# Run the extractor
python extract_assets.py
```

The script downloads the video thumbnail as `jarvis/assets/icon.png` and the first 6 seconds of audio as `jarvis/assets/welcome.mp3`. On completion, it prints the lines to add to `.env`.

---

### Full installation (all components)

```bash
# Ubuntu / Debian — system dependencies first
sudo apt install \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-render-util0 \
    python3-dev portaudio19-dev \
    ffmpeg mpg123 \
    playerctl scrot brightnessctl \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libgbm1

# macOS
brew install portaudio ffmpeg

# Python packages (includes computer-use)
pip install "palmiche-jarvis[all]"
# equivalent to: voice + tray + adk + assets + a2a + mcp + computer-use

# Chromium for Computer Use
playwright install chromium
```

Or simply use the interactive installer that manages everything:

```bash
cd jarvis && bash install.sh
# Select [1] Everything
```

---

## System dependencies by feature

| Feature | Linux (apt) | macOS (brew) |
|---|---|---|
| Graphical interface (XCB) | `libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0` | — |
| Speech recognition | `python3-dev portaudio19-dev` | `portaudio` |
| MP3 playback (gTTS) | `mpg123` | Included with `ffmpeg` |
| Asset extraction | `ffmpeg` | `ffmpeg` |
| Media control | `playerctl` | Built-in |
| Screenshots | `scrot` | Built-in (`screencapture`) |
| Brightness control | `brightnessctl` | — |
| Network / WiFi info | `network-manager` (nmcli) | Built-in |
| Desktop notifications | `libnotify-bin` (notify-send) | Built-in (osascript) |

---

## Passwordless power actions (Linux)

`power_action` (shutdown / restart / suspend) uses `systemctl`, which on many systems asks for polkit authentication. To allow them without a password for the active user:

```bash
sudo jarvis/scripts/install-power-rules.sh
```

The script copies the polkit rule to `/etc/polkit-1/rules.d/` and restarts polkit.
To install for a different user: `JARVIS_USER=other sudo jarvis/scripts/install-power-rules.sh`.

---

## Additional configuration

### Tool logging

Jarvis logs all tool calls to a log file for diagnostics. Enabled by default.

```ini
# In .env:
JARVIS_LOG_FILE=~/.jarvis_tools.log   # file path (default)
JARVIS_LOG_ENABLED=true                # disable with false
```

Each entry includes timestamp, inputs and result (OK or ERROR).

### Automatic sudo password

For environments without an interactive terminal (like tray mode), commands requiring sudo may block waiting for input. Configure the password to be sent automatically (the agent always asks for confirmation before using it).

```ini
# In .env:
JARVIS_SUDO_PASSWORD=your-password
```

If a command fails with "Permission denied", Jarvis detects the error and offers to retry with sudo.

---

## Quick start after installation

```bash
# Interactive terminal (Anthropic backend)
python -m jarvis

# Local backend without API key
python -m jarvis --backend ollama

# System tray mode
python -m jarvis --tray

# Tray + Gemini backend + custom name
python -m jarvis --tray --backend gemini --name "Friday"

# Single query and exit
python -m jarvis -q "how much RAM do I have?"

# A2A server
python -m jarvis --serve-a2a

# MCP server (for Claude Desktop, Cursor, Zed)
python -m jarvis --serve-mcp
```

---

## Common troubleshooting

| Symptom | Likely cause | Solution |
|---|---|---|
| `ModuleNotFoundError: PyQt6` | Tray extras not installed | `pip install "palmiche-jarvis[tray]"` |
| `qt.qpa.xcb: could not connect to display` | No graphical server | Verify that `DISPLAY` is defined or use CLI mode |
| `OSError: PortAudio library not found` | portaudio not installed | `sudo apt install portaudio19-dev` |
| `ANTHROPIC_API_KEY not set` | Missing API key | Edit `jarvis/.env` and add the key |
| `ollama: command not found` | Ollama not installed | Follow the Ollama backend steps |
| Mic not available when opening tray | `pyaudio`/`SpeechRecognition` not installed | `pip install "palmiche-jarvis[voice]"` |
| Fatal PortAudio crash when opening mic | No audio input device | Connect a microphone or disable `JARVIS_VOICE_ENABLED` |
| Sudo command hangs waiting for password | Headless mode without terminal | Configure `JARVIS_SUDO_PASSWORD` in `.env` |
| `ModuleNotFoundError: fastapi` | A2A extras not installed | `pip install "palmiche-jarvis[a2a]"` |
| `ModuleNotFoundError: mcp` | MCP extras not installed | `pip install "palmiche-jarvis[mcp]"` |
| Voice feedback loop (Jarvis hears itself) | Fixed bug | Update to the latest version |
| `ModuleNotFoundError: google.genai` | Computer Use not installed | `pip install "palmiche-jarvis[computer-use]"` |
| `playwright._impl._errors.Error: Executable doesn't exist` | Chromium not installed | `playwright install chromium` |
| `GOOGLE_API_KEY not set` (computer use) | Missing Google API key | Add `GOOGLE_API_KEY=AIza...` to `jarvis/.env` |
| Computer Use not responding / infinite loop | Task too complex | Reduce `COMPUTER_USE_MAX_ITERATIONS` or simplify the task |
