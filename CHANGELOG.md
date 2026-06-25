# Changelog — Palmiche J.A.R.V.I.S.

Todos los cambios notables del proyecto se documentan en este archivo.

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
