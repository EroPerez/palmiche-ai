# Changelog — Palmiche J.A.R.V.I.S.

All notable changes to the project are documented in this file.

---

## [Unreleased] — 2026-06-26

### AI Guardrails — AI safety mechanisms

New module `jarvis/guardrails/` implementing a rule-based system between users and AI models to ensure the application behaves reliably, ethically, and securely.

- **Evaluation engine** (`engine.py`): evaluates rules at 4 lifecycle phases (input, output, tool_call, tool_result)
- **13 built-in rules** (`defaults.py`):
  - Prompt injection detection (6 regex patterns)
  - Jailbreak attempt detection (25 patterns: DAN, malicious roleplay, hypothetical framing, opposite day, liberation, permissions, ES/EN jailbreak)
  - System prompt extraction prevention (15 patterns: show/reveal, how were you programmed, translate/encode/summarize prompt, ES/EN)
  - Offensive and discriminatory language filter (slurs, hate speech, EN/ES)
  - Input/output length limits
  - Credential redaction (API keys, GitHub tokens, AWS keys, private keys)
  - System prompt leak prevention in model output
  - Offensive language filter for model output
  - Harmful content blocking in output
  - Dangerous shell command blocking (`rm -rf /`, `mkfs`, `dd`, fork bombs)
  - Mandatory confirmation for destructive actions
  - Secret redaction in tool results
- **JSON configuration** (`~/.jarvis_guardrails.json`): override, disable, or add rules
- **4 actions**: `block` (reject), `warn` (advisory), `redact` (replace), `log` (record only)
- **Rule types**: regex patterns, keyword lists, tool allow/block lists, argument constraints, max length, custom validators
- **Integrated into all 3 backends**: Anthropic SDK, Google ADK, Ollama
- **62 unit tests** in `tests/test_guardrails.py`

#### New environment variables

| Variable | Default | Description |
|---|---|---|
| `JARVIS_GUARDRAILS_ENABLED` | `true` | Enable/disable guardrails globally |
| `JARVIS_GUARDRAILS_FILE` | `~/.jarvis_guardrails.json` | Custom guardrail rules file |

#### File changes

| File | Type | Description |
|---|---|---|
| `jarvis/guardrails/__init__.py` | New | Module public API |
| `jarvis/guardrails/models.py` | New | Data models (GuardrailRule, GuardrailVerdict) |
| `jarvis/guardrails/engine.py` | New | Core evaluation engine |
| `jarvis/guardrails/defaults.py` | New | 13 built-in rules |
| `jarvis/guardrails/README.md` | New | Full system documentation |
| `jarvis/guardrails.example.json` | New | Custom configuration example |
| `jarvis/brain/agent.py` | Modified | Guardrails integration |
| `jarvis/brain/adk_agent.py` | Modified | Guardrails integration |
| `jarvis/brain/ollama_agent.py` | Modified | Guardrails integration |
| `jarvis/config.py` | Modified | `JARVIS_GUARDRAILS_*` variables |
| `jarvis/.env.example` | Modified | Guardrails variable documentation |
| `tests/test_guardrails.py` | New | 62 unit tests |

---

### Centralized Audio Engine (AudioEngine)

New module `jarvis/interface/audio_engine.py` replacing scattered audio functions in `wake_word.py` and `tray.py` with a unified, centralized engine.

- **Playback queue**: prevents audio overlap with a dedicated worker thread
- **TTS cache**: stores gTTS-generated MP3s with SHA-256 hash keys, avoiding re-synthesis of repeated phrases (max 200 files, LRU eviction)
- **Sentence streaming**: splits long text (>120 chars) at sentence boundaries and plays the first while the rest are synthesized
- **Interrupt support**: `stop()` terminates current playback and clears the queue
- **Volume control**: configurable (0-100), normalized per player (mpg123 `-f`, ffplay `-volume`, espeak-ng `-a`)
- **Async callbacks**: `speak_async()` and `play_file_async()` with `on_done` callback
- **Interruptible system TTS**: espeak-ng/say backends use tracked Popen instead of `subprocess.run()`
- **Singleton pattern**: `get_engine()` / `shutdown_engine()` with defaults from `jarvis.config`

#### Migration

- **Removed**: `_speak_sync()`, `_speak_async()`, `_play_audio_file_sync()`, `_play_audio_file_async()` from `wake_word.py`
- **Removed**: `_play_audio_file()`, `_play_activation_audio()` from `tray.py`
- **Moved**: `_clean_for_tts()` to `audio_engine.py` as `clean_for_tts()`
- **Migrated**: `wake_word.py`, `voice.py`, `tray.py` now use `AudioEngine` exclusively

#### New environment variables

| Variable | Default | Description |
|---|---|---|
| `JARVIS_AUDIO_VOLUME` | `100` | Global audio volume (0-100) |
| `JARVIS_TTS_CACHE` | `true` | Cache generated TTS audio |
| `JARVIS_TTS_STREAM` | `true` | Stream TTS by sentence |

#### Tests

- 18 unit tests in `tests/test_audio_engine.py` with isolated per-test cache directories

---

## [Previous] — 2026-06-25

### Computer Use — visual automation with Gemini

Inspired by [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview), Palmiche-AI can now visually control a browser or the full desktop.

- **`jarvis/tools/computer_use.py`** (new): complete computer use module
  - `PlaywrightComputer`: headless Chromium browser backend with 30+ methods (click, double-click, triple-click, type, scroll, drag-and-drop, navigate, go_back/forward, press_key, hotkey, key_down/up, wait, screenshot)
  - `DesktopComputer`: full desktop backend via pyautogui + mss
  - `PalmicheComputerAgent`: agentic loop with Gemini computer use API, screenshot history management (keeps only the 3 most recent to optimize context), security confirmation for sensitive actions
  - `computer_use_task()`: public function registered as tool #59
- **`jarvis/tools/registry.py`**: registration of `computer_use_task` with complete schema including `task`, `backend`, `initial_url`, `max_iterations` parameters
- **`jarvis/config.py`**: 3 new environment variables: `COMPUTER_USE_MODEL` (default: `gemini-2.5-flash`), `COMPUTER_USE_BACKEND` (default: `playwright`), `COMPUTER_USE_MAX_ITERATIONS` (default: 30)
- **`jarvis/.env.example`**: documented new computer use variables
- **`pyproject.toml`**: new optional group `[computer-use]` with `google-genai>=1.0.0`, `playwright>=1.40.0`, `pyautogui>=0.9.54`, `Pillow>=10.0.0`, `mss>=9.0.1`; `[all]` updated to include it

### Complete installer redesign

- **`jarvis/install.sh`** completely rewritten:
  - Animated **Palmiche-AI** splash with bright green ASCII logo
  - Animated loading spinner for pip operations
  - Per-module progress bars (`▓▒`)
  - Interactive menu with 3 options: Everything / Core only / Custom
  - Custom selection of 9 modules: voice, GUI/tray, ADK+Claude, ADK+Gemini, Ollama, A2A, MCP, Computer Use, assets
  - Python 3.10+ verification before installing
  - Final summary with quick-start commands

### Updated documentation

- **`README.md`**: tool count 58→59, new Computer Use section in optional components, configuration table with computer use variables, tool table with Computer Use category, updated system dependencies
- **`INSTALL.md`**: dedicated Computer Use section with step-by-step installation, backend table, specific troubleshooting, interactive installer as recommended option
- **`TOOLS.md`**: category 17 — Computer Use with complete `computer_use_task` reference, action table, detailed FAQ, updated index
- **`CHANGELOG.md`**: this version's entry

### File changes

| File | Type | Description |
|---|---|---|
| `jarvis/tools/computer_use.py` | New | Complete Computer Use module |
| `jarvis/tools/registry.py` | Modified | Registration of `computer_use_task` |
| `jarvis/config.py` | Modified | `COMPUTER_USE_*` variables |
| `jarvis/.env.example` | Modified | Computer use variable documentation |
| `jarvis/install.sh` | Modified | Rewrite with splash + interactive menu |
| `pyproject.toml` | Modified | `[computer-use]` group and updated `[all]` |
| `README.md` | Modified | Computer Use section, 59 tools count |
| `INSTALL.md` | Modified | Computer Use section + interactive installer |
| `TOOLS.md` | Modified | Category 17 Computer Use, 59 count |
| `CHANGELOG.md` | Modified | This entry |

---

## [Unreleased] — 2026-06-24 / 2026-06-25

### GUI migration: tkinter/pystray to PyQt6

- **Complete GUI rewrite** from tkinter/pystray to PyQt6 (#13, #14, #15)
  - `WaveformAnimation` rewritten as `QWidget` with `QPainter`
  - `ChatWindow` rewritten as `QMainWindow` with `QSystemTrayIcon`
  - Fade-in animation (500ms, OutCubic) on show and fade-out (250ms) on hide
  - Cross-thread communication via `pyqtSignal` instead of `root.after()`
  - Styled scrollbar, placeholder text, disabled button styles
  - `pyproject.toml`: replaces `pystray>=0.19.0` with `PyQt6>=6.4.0`
- **Centered window** on screen (820x640) instead of maximized
- **Robust microphone**: `try/except` prevents crash from SpeechRecognition `ImportError`; button disabled with tooltip if dependencies not installed
- **Iron Man-style HUD animation** (`hud_animation.py` new) (#15):
  - Three concentric rings rotating at different speeds
  - Pulsating core with radial gradient (cyan/amber/green per state)
  - Radar sweep with fading green trail
  - Horizontal scan line with glow
  - 24 animated equalizer bars
  - Status text (time, coordinates, state) in corners
- **Minimized startup** in the tray; window appears on clicking the icon or detecting the wake word
- **Exit command interception** (`salir`/`exit`/`quit`) directly in the chat window for clean app shutdown

### Robotic JARVIS aesthetic with Palmiche palette (#22)

- **Palmiche color palette**: forest green (#00c853) + cream (#f5eedc) on black-green background (#030d06)
- HUD animation updated with Palmiche greens in all rings, core, radar and bars
- Chat panel with dark background, green left border, angular scrollbar, monospaced font
- Informative data bar between HUD and chat (configurable name // AI / SYS:OK / NEURAL:ACTIVE)
- Angular buttons with illuminated green border, military/HUD style
- Message colors: user=green, jarvis=cream, system=light green, alert=amber
- **Automatic fullscreen** on voice activation; ESC exits fullscreen first, then hides
- Status messages in uppercase (READY / PROCESSING / LISTENING / PLAYING)
- Space background integration (`space-bg.jpg`) and `TheGoodMonolith.woff` font from openclaw-jarvis-ui project
- `extract_assets.py` script to extract icon and welcome audio from YouTube

### Improved voice mode (#16-#21)

- **Audio playback with QMediaPlayer** instead of subprocess; fallback to mpg123/ffplay/cvlc if QtMultimedia not available (#16)
- **Persistent voice toggle** (#17, #18): microphone ON/OFF button, highlighted red while active, continuous auto-listening after each response
- **`/voz` command** to toggle voice mode during interactive session (#17)
- **Feedback loop prevention** (#19): microphone waits for TTS audio to finish before starting to listen
- **TTS instead of audio file** for welcome message (#20)
- **Markdown and emoji cleanup** before TTS so voice reads only natural prose (#21)
- **Greeting only on first voice activation**; farewell message on exit (#21)
- **System prompt reinforcement** to prevent fabricated responses without using tools (#17)
- **Audio device detection** (#26): verifies input hardware before initializing PyAudio to prevent fatal PortAudio crash
- Welcome audio played on each voice activation (not just the first time) (#26)

### 17 new tools (41 to 58) (#23)

- **`weather.py`**: `get_weather` + `get_forecast` via wttr.in (no API key)
- **`notes.py`**: `create_note`, `list_notes`, `read_note`, `search_notes`, `delete_note` — local JSON storage with tags and full-text search
- **`timer.py`**: `set_timer`, `set_alarm`, `list_timers`, `cancel_timer` — with desktop notifications
- **`calculator.py`**: safe math evaluator (AST, no `eval`) + comprehensive unit converter (length, mass, temperature, speed, area, volume, storage)
- **`text_tools.py`**: `text_stats` (word/character/line count, reading time) + `text_transform` (upper/lower/slug/snake/camel/palindrome/etc.)
- **`web.py` extended**: `fetch_webpage` (HTML-to-text extractor) + `get_rss_feed` (RSS/Atom reader)

### A2A and MCP support (#24)

- **A2A Server** (`jarvis/a2a/server.py`): FastAPI HTTP server with JSON-RPC 2.0
  - Agent Card at `/.well-known/agent.json`
  - Endpoints: `tasks/send`, `tasks/sendSubscribe` (SSE), `tasks/get`, `tasks/cancel`
  - LRU session management (up to 50 simultaneous)
- **A2A Client** (`jarvis/a2a/client.py`): consumes remote A2A agents as local tools (`delegate_to_<name>`)
- **A2A Models** (`jarvis/a2a/models.py`): AgentCard, Task, Message, Artifact, etc.
- **MCP Server** (`jarvis/mcp_support/server.py`): stdio server exposing all 58 tools (compatible with Claude Desktop, Cursor, Zed, Continue.dev)
- **MCP Client** (`jarvis/mcp_support/client.py`): loads external server tools as `mcp_<name>`
- **DynamicToolRegistry** (`jarvis/tools/dynamic.py`): extends the static registry with runtime-registered tools
- **CLI**: `--serve-a2a`, `--serve-mcp`, `--connect-a2a URL`, `--connect-mcp SPEC`
- **Environment variables**: `JARVIS_A2A_HOST`, `JARVIS_A2A_PORT`, `JARVIS_A2A_AGENTS`, `JARVIS_MCP_SERVERS`
- **Optional dependencies**: `palmiche-jarvis[a2a]` and `palmiche-jarvis[mcp]`

### Automatic sudo handling (#27)

- **`JARVIS_SUDO_PASSWORD`**: when configured in `.env`, commands requiring sudo receive the password automatically via `sudo -S`
- **Permission error detection**: if a command fails with "Permission denied" or other privilege errors, the system detects it and offers to retry with `use_sudo=true`
- New `use_sudo` parameter in `run_shell_command`
- System prompt rule to guide the agent in the sudo flow

### Tool logging (#28)

- **Execution logging** of all tool calls to `~/.jarvis_tools.log`
- Includes timestamp, inputs and result; errors marked with ERROR, successes with OK
- Configurable via `JARVIS_LOG_FILE` (path) and `JARVIS_LOG_ENABLED` (true/false)

### Documentation (#23, #24, #25)

- **`TOOLS.md`** (new): 1200+ line reference guide with usage examples and FAQ for all 58 tools
- **`docs/ARCHITECTURE.md`** (new): complete layer diagram, operation modes, data flow, A2A/MCP protocols and configuration examples
- **`INSTALL.md`** (new): step-by-step installation guide with all optional extras, system dependencies by distro, and troubleshooting table
- **`README.md`** updated: tool count (41 to 58), new sections, configuration variables, and PyQt6 references
- **`requirements.txt`** synchronized with current dependencies (#25)
- **`.env.example`** updated with `JARVIS_NOTES_FILE` and voice comments (#25)

### File changes

| File | Type | Description |
|---|---|---|
| `jarvis/interface/tray.py` | Modified | Complete rewrite from tkinter to PyQt6, HUD, Palmiche palette |
| `jarvis/interface/hud_animation.py` | New | Iron Man HUD animation with QPainter |
| `jarvis/interface/animation.py` | Modified | Animation adaptation to PyQt6 |
| `jarvis/interface/wake_word.py` | Modified | Audio detection, TTS cleanup, greetings, farewell |
| `jarvis/interface/voice.py` | Modified | Delegation to `_speak_sync`, voice toggle |
| `jarvis/interface/cli.py` | Modified | `/voz` command |
| `jarvis/tools/weather.py` | New | Weather via wttr.in |
| `jarvis/tools/notes.py` | New | Local JSON notes |
| `jarvis/tools/timer.py` | New | Timers and alarms |
| `jarvis/tools/calculator.py` | New | Safe calculator + unit converter |
| `jarvis/tools/text_tools.py` | New | Text statistics and transformations |
| `jarvis/tools/web.py` | New | Fetch webpage + RSS reader |
| `jarvis/tools/registry.py` | Modified | Registration of 17 new tools + `use_sudo` + logging |
| `jarvis/tools/shell.py` | Modified | Automatic sudo support, permission detection |
| `jarvis/tools/system.py` | Modified | Retry with sudo on power actions |
| `jarvis/tools/dynamic.py` | New | Dynamic runtime tool registration |
| `jarvis/a2a/__init__.py` | New | A2A package |
| `jarvis/a2a/server.py` | New | A2A server (FastAPI + JSON-RPC) |
| `jarvis/a2a/client.py` | New | A2A client |
| `jarvis/a2a/models.py` | New | A2A data models |
| `jarvis/mcp_support/__init__.py` | New | MCP package |
| `jarvis/mcp_support/server.py` | New | MCP stdio server |
| `jarvis/mcp_support/client.py` | New | MCP client (stdio/SSE) |
| `jarvis/brain/agent.py` | Modified | Optional DynamicToolRegistry support |
| `jarvis/brain/prompts.py` | Modified | Anti-fabrication rules + sudo |
| `jarvis/config.py` | Modified | New environment variables |
| `jarvis/__main__.py` | Modified | A2A/MCP CLI args, logging, sudo |
| `jarvis/assets/space-bg.jpg` | New | Space background for HUD |
| `jarvis/assets/TheGoodMonolith.woff` | New | Robotic monospaced font for UI |
| `extract_assets.py` | New | YouTube asset extractor |
| `TOOLS.md` | New | Complete tools guide |
| `INSTALL.md` | New | Installation guide |
| `docs/ARCHITECTURE.md` | New | Architecture documentation |
| `pyproject.toml` | Modified | New extras: a2a, mcp, assets |
| `jarvis/requirements.txt` | Modified | Synchronized with current dependencies |
| `jarvis/.env.example` | Modified | New documented variables |
| `.gitignore` | Modified | New exclusions |

### Statistics

- **16 commits** on this branch
- **39 files** modified or created
- **+6,159 lines** added / **-576 lines** deleted
- Tools: **41 to 58** (+17 new)
- New modules: **13 Python files** new
- New documents: **3 documentation files** (TOOLS.md, INSTALL.md, ARCHITECTURE.md)
