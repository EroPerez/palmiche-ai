# Changelog — Palmiche J.A.R.V.I.S.

Todos los cambios notables del proyecto se documentan en este archivo.

---

## [Unreleased] — 2026-06-28

### ADK universal multi-proveedor vía LiteLLM (#45)

El backend `adk` ahora es el motor por defecto y soporta cualquier proveedor LLM compatible con LiteLLM mediante una única interfaz unificada.

#### Nuevo agente universal

- **`jarvis/brain/adk_universal.py`** (nuevo): `JarvisUniversalADKAgent` reemplaza al anterior `JarvisADKAgent`
  - Soporta cualquier proveedor con solo cambiar `JARVIS_MODEL`: Anthropic, OpenAI, Gemini, Ollama, Groq, Mistral, Azure, AWS Bedrock y cualquier proxy compatible con OpenAI
  - Auto-normalización de nombres de modelo legacy (`claude-haiku-*` → `anthropic/claude-haiku-*`, `llama3.2` → `ollama_chat/llama3.2`, etc.)
  - Resolución inteligente de API keys: `JARVIS_API_KEY` > variables de proveedor específico
  - Soporte para endpoint personalizado vía `JARVIS_BASE_URL` (Ollama local, vLLM, llama.cpp, Azure)
  - Gemini nativo sin LiteLLM cuando el modelo no contiene prefijo de proveedor (ej. `gemini-2.0-flash`)
- **`jarvis/brain/adk_agent.py`** (eliminado): reemplazado por `adk_universal.py`
- **Backend por defecto** cambiado de `anthropic` a `adk`
- Los backends `gemini` y `ollama` se convierten en **aliases de compatibilidad** que internamente usan `JarvisUniversalADKAgent`
- Seguridad MCP: los endpoints SSE remotos ahora requieren `https://` (solo `localhost` acepta HTTP)

#### Nuevas variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_API_KEY` | — | Clave API unificada — reemplaza todas las claves de proveedor específico. LiteLLM la usa para el proveedor del modelo seleccionado |
| `JARVIS_BASE_URL` | — | URL base del proveedor (Ollama local, vLLM, llama.cpp, Azure, proxies compatibles con OpenAI) |
| `JARVIS_TOOL_LANG` | `en` | Idioma de los schemas de herramientas y el system prompt interno (`en`/`es`). Solo afecta lo que el modelo ve — el asistente responde en el idioma del usuario |
| `JARVIS_CUSTOM_TOOLS_FILE` | `~/.jarvis_custom_tools.txt` | Archivo de texto plano para definir herramientas personalizadas sin escribir Python |

#### Variables deprecadas (siguen funcionando como fallback)

| Variable | Reemplazada por |
|---|---|
| `JARVIS_GEMINI_MODEL` | `JARVIS_MODEL=gemini-2.0-flash` |
| `JARVIS_OLLAMA_HOST` | `JARVIS_BASE_URL=http://localhost:11434` |
| `JARVIS_OLLAMA_MODEL` | `JARVIS_MODEL=ollama_chat/llama3.2` |

#### `JARVIS_MODEL` — formato LiteLLM

El valor por defecto cambia de `claude-haiku-4-5-20251001` a `anthropic/claude-haiku-4-5-20251001`. Ejemplos de modelos soportados:

```ini
# Anthropic Claude (default)
JARVIS_MODEL=anthropic/claude-haiku-4-5-20251001
JARVIS_MODEL=anthropic/claude-sonnet-4-5-20251001

# OpenAI
JARVIS_MODEL=openai/gpt-4o

# Google Gemini (ADK nativo, sin LiteLLM)
JARVIS_MODEL=gemini-2.0-flash

# Google Gemini (vía LiteLLM)
JARVIS_MODEL=gemini/gemini-2.0-flash

# Ollama local
JARVIS_MODEL=ollama_chat/llama3.2
JARVIS_BASE_URL=http://localhost:11434

# Groq
JARVIS_MODEL=groq/llama-3.1-70b-versatile

# Mistral
JARVIS_MODEL=mistral/mistral-large-latest

# Azure OpenAI
JARVIS_MODEL=azure/gpt-4o
JARVIS_BASE_URL=https://mi-endpoint.openai.azure.com

# AWS Bedrock
JARVIS_MODEL=bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
```

#### Herramientas personalizadas en texto plano

`JARVIS_CUSTOM_TOOLS_FILE` permite definir herramientas sin escribir Python. Cada herramienta mapea un nombre + descripción + parámetros a un comando shell. Disponibles en todos los backends.

#### Tests nuevos

- `tests/test_api_key_resolution.py` — resolución de claves por proveedor
- `tests/test_brain_skills_lang.py` — idioma de herramientas (`JARVIS_TOOL_LANG`)
- `tests/test_dynamic_tools_all_brains.py` — herramientas dinámicas en todos los backends

#### Cambios en archivos

| Archivo | Tipo | Descripción |
|---|---|---|
| `jarvis/brain/adk_universal.py` | Nuevo | `JarvisUniversalADKAgent` multi-proveedor vía LiteLLM |
| `jarvis/brain/adk_agent.py` | Eliminado | Reemplazado por `adk_universal.py` |
| `jarvis/__main__.py` | Modificado | Backend `adk` como default; aliases `gemini`/`ollama`; validación de keys multi-proveedor |
| `jarvis/config.py` | Modificado | `JARVIS_API_KEY`, `JARVIS_BASE_URL`, `JARVIS_TOOL_LANG`, `JARVIS_CUSTOM_TOOLS_FILE`; `JARVIS_MODEL` default `anthropic/...`; `JARVIS_BACKEND` default `adk` |
| `jarvis/.env.example` | Modificado | Documentación del nuevo formato de modelo y variables unificadas |
| `pyproject.toml` | Modificado | Dependencias actualizadas |
| `tests/test_api_key_resolution.py` | Nuevo | Tests de resolución de API keys |
| `tests/test_brain_skills_lang.py` | Nuevo | Tests de idioma de herramientas |
| `tests/test_dynamic_tools_all_brains.py` | Nuevo | Tests de herramientas dinámicas |

---

## [Unreleased] — 2026-06-26

### AI Guardrails — mecanismos de seguridad para IA

Nuevo módulo `jarvis/guardrails/` que implementa un sistema de reglas entre usuarios y modelos de IA para asegurar que la aplicación se comporte de forma confiable, ética y segura.

- **Motor de evaluación** (`engine.py`): evalúa reglas en 4 fases del ciclo de vida (input, output, tool_call, tool_result)
- **13 reglas integradas** (`defaults.py`):
  - Detección de prompt injection (6 patrones regex)
  - Detección de jailbreak (25 patrones: DAN, roleplay malicioso, hypothetical framing, opposite day, liberación, permisos, jailbreak ES/EN)
  - Prevención de extracción del system prompt (15 patrones: show/reveal, how were you programmed, translate/encode/summarize prompt, ES/EN)
  - Filtro de lenguaje ofensivo y discriminatorio (insultos, discurso de odio, EN/ES)
  - Límite de longitud de entrada/salida
  - Redacción de credenciales (API keys, tokens GitHub, claves AWS, claves privadas)
  - Prevención de filtración del prompt del sistema en salida
  - Filtro de lenguaje ofensivo en salida del modelo
  - Bloqueo de contenido dañino en salida
  - Bloqueo de comandos shell peligrosos (`rm -rf /`, `mkfs`, `dd`, fork bombs)
  - Confirmación obligatoria para acciones destructivas
  - Redacción de secretos en resultados de herramientas
- **Configuración vía JSON** (`~/.jarvis_guardrails.json`): sobrescribir, desactivar o añadir reglas
- **4 acciones**: `block` (rechazar), `warn` (advertir), `redact` (reemplazar), `log` (solo registrar)
- **Tipos de regla**: patrones regex, listas de keywords, allowlist/blocklist de herramientas, restricciones de argumentos, longitud máxima, validadores personalizados
- **Integrado en los 3 backends**: Anthropic SDK, Google ADK, Ollama
- **62 tests unitarios** en `tests/test_guardrails.py`

#### Nuevas variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_GUARDRAILS_ENABLED` | `true` | Activar/desactivar guardrails globalmente |
| `JARVIS_GUARDRAILS_FILE` | `~/.jarvis_guardrails.json` | Archivo de reglas personalizadas |

#### Cambios en archivos

| Archivo | Tipo | Descripción |
|---|---|---|
| `jarvis/guardrails/__init__.py` | Nuevo | API pública del módulo |
| `jarvis/guardrails/models.py` | Nuevo | Modelos de datos (GuardrailRule, GuardrailVerdict) |
| `jarvis/guardrails/engine.py` | Nuevo | Motor de evaluación central |
| `jarvis/guardrails/defaults.py` | Nuevo | 13 reglas integradas |
| `jarvis/guardrails/README.md` | Nuevo | Documentación completa del sistema |
| `jarvis/guardrails.example.json` | Nuevo | Ejemplo de configuración personalizada |
| `jarvis/brain/agent.py` | Modificado | Integración de guardrails |
| `jarvis/brain/adk_agent.py` | Modificado | Integración de guardrails |
| `jarvis/brain/ollama_agent.py` | Modificado | Integración de guardrails |
| `jarvis/config.py` | Modificado | Variables `JARVIS_GUARDRAILS_*` |
| `jarvis/.env.example` | Modificado | Documentación de variables guardrails |
| `tests/test_guardrails.py` | Nuevo | 62 tests unitarios |

---

### Motor de audio centralizado (AudioEngine)

Nuevo módulo `jarvis/interface/audio_engine.py` que reemplaza las funciones de audio dispersas en `wake_word.py` y `tray.py` con un motor centralizado y unificado.

- **Cola de reproducción**: previene superposición de audio con un worker thread dedicado
- **Cache de TTS**: almacena MP3 generados por gTTS con hash SHA-256, evitando re-sintetizar frases repetidas (máx. 200 archivos, LRU)
- **Streaming por oraciones**: divide textos largos (>120 chars) en oraciones y reproduce la primera mientras las demás se sintetizan
- **Interrupción**: `stop()` termina la reproducción actual y limpia la cola
- **Control de volumen**: configurable (0-100), normalizado por reproductor (mpg123 `-f`, ffplay `-volume`, espeak-ng `-a`)
- **Callbacks async**: `speak_async()` y `play_file_async()` con callback `on_done`
- **Sistema TTS interruptible**: los backends espeak-ng/say usan Popen rastreado en vez de `subprocess.run()`
- **Patrón singleton**: `get_engine()` / `shutdown_engine()` con defaults desde `jarvis.config`

#### Migración

- **Eliminado**: `_speak_sync()`, `_speak_async()`, `_play_audio_file_sync()`, `_play_audio_file_async()` de `wake_word.py`
- **Eliminado**: `_play_audio_file()`, `_play_activation_audio()` de `tray.py`
- **Movido**: `_clean_for_tts()` a `audio_engine.py` como `clean_for_tts()`
- **Migrado**: `wake_word.py`, `voice.py`, `tray.py` ahora usan `AudioEngine` exclusivamente

#### Nuevas variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_AUDIO_VOLUME` | `100` | Volumen global de audio (0-100) |
| `JARVIS_TTS_CACHE` | `true` | Cache de audio TTS generado |
| `JARVIS_TTS_STREAM` | `true` | Streaming TTS por oraciones |

#### Tests

- 18 tests unitarios en `tests/test_audio_engine.py` con cache aislada por test

---

## [Anterior] — 2026-06-25

### Computer Use — automatización visual con Gemini

Inspirado en [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview), Palmiche-AI ahora puede controlar visualmente un navegador o el escritorio completo.

- **`jarvis/tools/computer_use.py`** (nuevo): módulo completo de computer use
  - `PlaywrightComputer`: backend de navegador Chromium headless con 30+ métodos (click, doble-click, triple-click, type, scroll, drag-and-drop, navigate, go_back/forward, press_key, hotkey, key_down/up, wait, screenshot)
  - `DesktopComputer`: backend de escritorio completo vía pyautogui + mss
  - `PalmicheComputerAgent`: loop agéntico con Gemini computer use API, gestión de historial de screenshots (mantiene solo los 3 más recientes para optimizar el contexto), confirmación de seguridad para acciones sensibles
  - `computer_use_task()`: función pública registrada como herramienta #59
- **`jarvis/tools/registry.py`**: registro de `computer_use_task` con schema completo incluyendo parámetros `task`, `backend`, `initial_url`, `max_iterations`
- **`jarvis/config.py`**: 3 nuevas variables de entorno: `COMPUTER_USE_MODEL` (default: `gemini-2.5-flash`), `COMPUTER_USE_BACKEND` (default: `playwright`), `COMPUTER_USE_MAX_ITERATIONS` (default: 30)
- **`jarvis/.env.example`**: documentadas las nuevas variables de computer use
- **`pyproject.toml`**: nuevo grupo opcional `[computer-use]` con `google-genai>=1.0.0`, `playwright>=1.40.0`, `pyautogui>=0.9.54`, `Pillow>=10.0.0`, `mss>=9.0.1`; `[all]` actualizado para incluirlo

### Rediseño completo del instalador

- **`jarvis/install.sh`** reescrito completamente:
  - Splash animado de **Palmiche-AI** con logo ASCII en verde brillante
  - Spinner de carga animado para operaciones pip
  - Barras de progreso por módulo (`▓▒`)
  - Menú interactivo con 3 opciones: Todo / Solo núcleo / Personalizado
  - Selección personalizada de 9 módulos: voz, GUI/bandeja, ADK+Claude, ADK+Gemini, Ollama, A2A, MCP, Computer Use, assets
  - Verificación de Python 3.10+ antes de instalar
  - Resumen final con comandos de uso rápido

### Documentación actualizada

- **`README.md`**: conteo 58→59 herramientas, nueva sección Computer Use en componentes opcionales, tabla de configuración con variables de computer use, tabla de herramientas con categoría Computer Use, dependencias del sistema actualizadas
- **`INSTALL.md`**: sección dedicada a Computer Use con instalación paso a paso, tabla de backends, troubleshooting específico, instalador interactivo como opción recomendada
- **`TOOLS.md`**: categoría 17 — Computer Use con referencia completa de `computer_use_task`, tabla de acciones, FAQ detallado, índice actualizado
- **`CHANGELOG.md`**: entrada de esta versión

### Cambios en archivos

| Archivo | Tipo | Descripción |
|---|---|---|
| `jarvis/tools/computer_use.py` | Nuevo | Módulo Computer Use completo |
| `jarvis/tools/registry.py` | Modificado | Registro de `computer_use_task` |
| `jarvis/config.py` | Modificado | Variables `COMPUTER_USE_*` |
| `jarvis/.env.example` | Modificado | Documentación de variables computer use |
| `jarvis/install.sh` | Modificado | Reescritura con splash + menú interactivo |
| `pyproject.toml` | Modificado | Grupo `[computer-use]` y `[all]` actualizado |
| `README.md` | Modificado | Sección Computer Use, conteo 59 herramientas |
| `INSTALL.md` | Modificado | Sección Computer Use + instalador interactivo |
| `TOOLS.md` | Modificado | Categoría 17 Computer Use, conteo 59 |
| `CHANGELOG.md` | Modificado | Esta entrada |

---

## [Unreleased] — 2026-06-24 / 2026-06-25

### Migración de GUI: tkinter/pystray a PyQt6

- **Reescritura completa de la interfaz gráfica** de tkinter/pystray a PyQt6 (#13, #14, #15)
  - `WaveformAnimation` reescrita como `QWidget` con `QPainter`
  - `ChatWindow` reescrita como `QMainWindow` con `QSystemTrayIcon`
  - Animación fade-in (500ms, OutCubic) al mostrar y fade-out (250ms) al ocultar
  - Comunicación cross-thread via `pyqtSignal` en lugar de `root.after()`
  - Scrollbar estilizado, placeholder text, estilos de botón deshabilitado
  - `pyproject.toml`: reemplaza `pystray>=0.19.0` con `PyQt6>=6.4.0`
- **Ventana centrada** en pantalla (820x640) en lugar de maximizada
- **Micrófono robusto**: `try/except` previene crash por `ImportError` de SpeechRecognition; botón deshabilitado con tooltip si las dependencias no están instaladas
- **Animación HUD estilo Iron Man** (`hud_animation.py` nuevo) (#15):
  - Tres anillos concéntricos rotantes a distintas velocidades
  - Núcleo pulsante con gradiente radial (cyan/amber/verde según estado)
  - Radar sweep con trail verde desvaneciente
  - Scan line horizontal con glow
  - 24 barras de ecualización animadas
  - Texto de status (hora, coordenadas, estado) en las esquinas
- **Arranque minimizado** en la bandeja; la ventana aparece al hacer clic en el ícono o al detectar la wake word
- **Intercepción de comandos de salida** (`salir`/`exit`/`quit`) directamente en la ventana de chat para cerrar la app limpiamente

### Estética robótica JARVIS con paleta Palmiche (#22)

- **Paleta de colores Palmiche**: verde bosque (#00c853) + crema (#f5eedc) sobre fondo negro-verde (#030d06)
- HUD animation actualizada con verdes Palmiche en todos los anillos, core, radar y barras
- Panel de chat con fondo oscuro, borde izquierdo verde, scrollbar angular, fuente monoespaciada
- Barra de datos informativa entre HUD y chat (nombre configurable // IA / SYS:OK / NEURAL:ACTIVO)
- Botones angulares con borde verde iluminado, estilo militar/HUD
- Colores de mensajes: usuario=verde, jarvis=crema, sistema=verde claro, alerta=ambar
- **Pantalla completa automática** al activar por voz; ESC sale de fullscreen primero, luego oculta
- Mensajes de estado en mayúsculas (LISTO / PROCESANDO / ESCUCHANDO / REPRODUCIENDO)
- Integración de fondo espacial (`space-bg.jpg`) y fuente `TheGoodMonolith.woff` del proyecto openclaw-jarvis-ui
- Script `extract_assets.py` para extraer icono y audio de bienvenida de YouTube

### Modo de voz mejorado (#16-#21)

- **Reproducción de audio con QMediaPlayer** en lugar de subprocess; fallback a mpg123/ffplay/cvlc si QtMultimedia no disponible (#16)
- **Toggle de voz persistente** (#17, #18): botón de micrófono ON/OFF, resaltado rojo mientras está activo, auto-escucha continua tras cada respuesta
- **Comando `/voz`** para alternar modo de voz durante sesión interactiva (#17)
- **Prevención de feedback loop** (#19): el micrófono espera a que el audio TTS termine antes de empezar a escuchar
- **TTS en lugar de archivo de audio** para mensaje de bienvenida (#20)
- **Limpieza de markdown y emojis** antes de TTS para que la voz lea solo prosa natural (#21)
- **Saludo solo en primera activación** por voz; mensaje de despedida al salir (#21)
- **Refuerzo del system prompt** para prevenir respuestas fabricadas sin usar herramientas (#17)
- **Detección de dispositivo de audio** (#26): verifica hardware de entrada antes de inicializar PyAudio para evitar crash fatal de PortAudio
- Audio de bienvenida reproducido en cada activación por voz (no solo la primera vez) (#26)

### 17 nuevas herramientas (41 a 58) (#23)

- **`weather.py`**: `get_weather` + `get_forecast` via wttr.in (sin API key)
- **`notes.py`**: `create_note`, `list_notes`, `read_note`, `search_notes`, `delete_note` — almacenamiento local JSON con etiquetas y busqueda full-text
- **`timer.py`**: `set_timer`, `set_alarm`, `list_timers`, `cancel_timer` — con notificaciones de escritorio
- **`calculator.py`**: evaluador matematico seguro (AST, sin `eval`) + conversor de unidades completo (longitud, masa, temperatura, velocidad, area, volumen, almacenamiento)
- **`text_tools.py`**: `text_stats` (conteo de palabras/caracteres/lineas, tiempo de lectura) + `text_transform` (upper/lower/slug/snake/camel/palindrome/etc.)
- **`web.py` extendido**: `fetch_webpage` (extractor HTML-a-texto) + `get_rss_feed` (lector RSS/Atom)

### Soporte A2A y MCP (#24)

- **Servidor A2A** (`jarvis/a2a/server.py`): servidor HTTP FastAPI con JSON-RPC 2.0
  - Agent Card en `/.well-known/agent.json`
  - Endpoints: `tasks/send`, `tasks/sendSubscribe` (SSE), `tasks/get`, `tasks/cancel`
  - Gestion de sesiones LRU (hasta 50 simultaneas)
- **Cliente A2A** (`jarvis/a2a/client.py`): consume agentes A2A remotos como herramientas locales (`delegate_to_<nombre>`)
- **Modelos A2A** (`jarvis/a2a/models.py`): AgentCard, Task, Message, Artifact, etc.
- **Servidor MCP** (`jarvis/mcp_support/server.py`): servidor stdio que expone las 58 herramientas (compatible con Claude Desktop, Cursor, Zed, Continue.dev)
- **Cliente MCP** (`jarvis/mcp_support/client.py`): carga herramientas de servidores externos como `mcp_<nombre>`
- **DynamicToolRegistry** (`jarvis/tools/dynamic.py`): extiende el registro estatico con herramientas registradas en runtime
- **CLI**: `--serve-a2a`, `--serve-mcp`, `--connect-a2a URL`, `--connect-mcp SPEC`
- **Variables de entorno**: `JARVIS_A2A_HOST`, `JARVIS_A2A_PORT`, `JARVIS_A2A_AGENTS`, `JARVIS_MCP_SERVERS`
- **Dependencias opcionales**: `palmiche-jarvis[a2a]` y `palmiche-jarvis[mcp]`

### Manejo automatico de sudo (#27)

- **`JARVIS_SUDO_PASSWORD`**: cuando esta configurada en `.env`, los comandos que requieren sudo reciben la contrasena automaticamente via `sudo -S`
- **Deteccion de errores de permisos**: si un comando falla con "Permission denied" u otros errores de privilegios, el sistema lo detecta y ofrece reintentar con `use_sudo=true`
- Nuevo parametro `use_sudo` en `run_shell_command`
- Regla en system prompt para guiar al agente en el flujo de sudo

### Logging de herramientas (#28)

- **Registro de ejecucion** de todas las llamadas a herramientas en `~/.jarvis_tools.log`
- Incluye timestamp, inputs y resultado; errores marcados con ERROR, exitos con OK
- Configurable via `JARVIS_LOG_FILE` (ruta) y `JARVIS_LOG_ENABLED` (true/false)

### Documentacion (#23, #24, #25)

- **`TOOLS.md`** (nuevo): guia de referencia de 1200+ lineas con ejemplos de uso y FAQ para las 58 herramientas
- **`docs/ARCHITECTURE.md`** (nuevo): diagrama completo de capas, modos de operacion, flujo de datos, protocolos A2A/MCP y ejemplos de configuracion
- **`INSTALL.md`** (nuevo): guia paso a paso de instalacion con todos los extras opcionales, dependencias del sistema por distro, y tabla de troubleshooting
- **`README.md`** actualizado: conteo de herramientas (41 a 58), nuevas secciones, variables de configuracion, y referencias a PyQt6
- **`requirements.txt`** sincronizado con dependencias actuales (#25)
- **`.env.example`** actualizado con `JARVIS_NOTES_FILE` y comentarios de voz (#25)

### Cambios en archivos

| Archivo | Tipo | Descripcion |
|---|---|---|
| `jarvis/interface/tray.py` | Modificado | Reescritura completa de tkinter a PyQt6, HUD, paleta Palmiche |
| `jarvis/interface/hud_animation.py` | Nuevo | Animacion HUD Iron Man con QPainter |
| `jarvis/interface/animation.py` | Modificado | Adaptacion de animaciones a PyQt6 |
| `jarvis/interface/wake_word.py` | Modificado | Deteccion de audio, TTS cleanup, saludos, despedida |
| `jarvis/interface/voice.py` | Modificado | Delegacion a `_speak_sync`, toggle de voz |
| `jarvis/interface/cli.py` | Modificado | Comando `/voz` |
| `jarvis/tools/weather.py` | Nuevo | Clima via wttr.in |
| `jarvis/tools/notes.py` | Nuevo | Notas locales JSON |
| `jarvis/tools/timer.py` | Nuevo | Temporizadores y alarmas |
| `jarvis/tools/calculator.py` | Nuevo | Calculadora segura + conversor de unidades |
| `jarvis/tools/text_tools.py` | Nuevo | Estadisticas y transformaciones de texto |
| `jarvis/tools/web.py` | Nuevo | Fetch webpage + RSS reader |
| `jarvis/tools/registry.py` | Modificado | Registro de 17 nuevas herramientas + `use_sudo` + logging |
| `jarvis/tools/shell.py` | Modificado | Soporte sudo automatico, deteccion de permisos |
| `jarvis/tools/system.py` | Modificado | Reintento con sudo en acciones de energia |
| `jarvis/tools/dynamic.py` | Nuevo | Registro dinamico de herramientas en runtime |
| `jarvis/a2a/__init__.py` | Nuevo | Paquete A2A |
| `jarvis/a2a/server.py` | Nuevo | Servidor A2A (FastAPI + JSON-RPC) |
| `jarvis/a2a/client.py` | Nuevo | Cliente A2A |
| `jarvis/a2a/models.py` | Nuevo | Modelos de datos A2A |
| `jarvis/mcp_support/__init__.py` | Nuevo | Paquete MCP |
| `jarvis/mcp_support/server.py` | Nuevo | Servidor MCP stdio |
| `jarvis/mcp_support/client.py` | Nuevo | Cliente MCP (stdio/SSE) |
| `jarvis/brain/agent.py` | Modificado | Soporte DynamicToolRegistry opcional |
| `jarvis/brain/prompts.py` | Modificado | Reglas anti-fabricacion + sudo |
| `jarvis/config.py` | Modificado | Nuevas variables de entorno |
| `jarvis/__main__.py` | Modificado | CLI args A2A/MCP, logging, sudo |
| `jarvis/assets/space-bg.jpg` | Nuevo | Fondo espacial para HUD |
| `jarvis/assets/TheGoodMonolith.woff` | Nuevo | Fuente monoespaciada para UI |
| `extract_assets.py` | Nuevo | Extractor de assets de YouTube |
| `TOOLS.md` | Nuevo | Guia completa de herramientas |
| `INSTALL.md` | Nuevo | Guia de instalacion |
| `docs/ARCHITECTURE.md` | Nuevo | Documentacion de arquitectura |
| `pyproject.toml` | Modificado | Nuevos extras: a2a, mcp, assets |
| `jarvis/requirements.txt` | Modificado | Sincronizado con dependencias actuales |
| `jarvis/.env.example` | Modificado | Nuevas variables documentadas |
| `.gitignore` | Modificado | Nuevas exclusiones |

### Estadisticas

- **16 commits** en esta rama
- **39 archivos** modificados o creados
- **+6,159 lineas** agregadas / **-576 lineas** eliminadas
- Herramientas: **41 a 58** (+17 nuevas)
- Nuevos modulos: **13 archivos** Python nuevos
- Nuevos documentos: **3 archivos** de documentacion (TOOLS.md, INSTALL.md, ARCHITECTURE.md)
