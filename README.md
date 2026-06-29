# J.A.R.V.I.S.

> Just A Rather Very Intelligent System — asistente de IA personal para laptop, impulsado por Claude.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Backends](https://img.shields.io/badge/backends-Anthropic%20%7C%20ADK%20%7C%20Gemini%20%7C%20Ollama%20%7C%20LM%20Studio-green.svg)](#backends)

## Características

- Conversación natural en español o inglés con memoria de sesión persistente
- **59 herramientas integradas** para controlar el sistema, archivos, red, medios, clima, notas, temporizadores, cálculo y más
- **Computer Use** — control visual de navegador y escritorio completo usando Gemini (inspirado en [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview))
- **Herramientas externas vía MCP** — conecta cualquier servidor MCP (stdio o SSE/HTTP) e inyecta sus herramientas directamente en el agente; el modelo las usa automáticamente
- **Agentes remotos vía A2A** — delega tareas a otros agentes IA (Google A2A) como si fueran herramientas locales; soporta redes de agentes colaborativos
- Cinco backends intercambiables: Anthropic SDK, Google ADK + LiteLLM, Google ADK + Gemini, Ollama (local) y LM Studio (local, OpenAI-compatible)
- **Tres interfaces de usuario**: CLI (Rich), bandeja del sistema (PyQt6) y Web UI (FastAPI + Vue 3)
- Entrada por voz opcional con reconocimiento de habla
- **Servidor unificado** — Web UI y A2A pueden correr en un solo proceso FastAPI
- **Instalador interactivo** con splash animado de Palmiche-AI, menú de módulos y barras de progreso

## Requisitos

- Python 3.10+
- Linux o macOS

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/EroPerez/palmiche-ai.git
cd palmiche-ai
```

### 2. Entorno virtual y dependencias base

```bash
python3 -m venv jarvis/.venv
source jarvis/.venv/bin/activate      # Linux/macOS
pip install -e .                       # instala dependencias del pyproject.toml
```

O usando el **instalador interactivo** incluido (recomendado):

```bash
cd jarvis
bash install.sh
```

El instalador muestra un splash animado de Palmiche-AI y te pregunta qué módulos deseas instalar (todo, solo núcleo, o selección personalizada).

### 3. Configurar variables de entorno

```bash
cp jarvis/.env.example jarvis/.env
nano jarvis/.env                      # edita con tus API keys
```

---

### Componentes opcionales

#### Backend Anthropic (default)

Requiere cuenta en [console.anthropic.com](https://console.anthropic.com).

```bash
# En .env:
# ANTHROPIC_API_KEY=sk-ant-...
# JARVIS_MODEL=claude-haiku-4-5-20251001

python -m jarvis --backend anthropic
```

#### Backend Google ADK + Claude

```bash
pip install "palmiche-jarvis[adk]"
# o manualmente:
pip install google-adk litellm

# En .env:
# ANTHROPIC_API_KEY=sk-ant-...
python -m jarvis --backend adk
```

#### Backend Google ADK + Gemini

Requiere cuenta en [aistudio.google.com](https://aistudio.google.com) para obtener `GOOGLE_API_KEY`.

```bash
pip install "palmiche-jarvis[gemini]"
# o manualmente:
pip install google-adk

# En .env:
# GOOGLE_API_KEY=AIza...
# JARVIS_GEMINI_MODEL=gemini-2.0-flash
python -m jarvis --backend gemini
```

#### Backend Ollama (modelo local, sin API key)

1. Instalar Ollama:

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# macOS
brew install ollama
```

2. Descargar un modelo:

```bash
ollama pull llama3.2          # ~2 GB, recomendado
# alternativas:
ollama pull llama3.2:1b       # ~0.8 GB, más rápido
ollama pull qwen2.5:3b        # ~2 GB, mejor tool-use
ollama pull llama3.1:8b       # ~5 GB, más capaz
```

3. Iniciar el servidor (si no arranca automáticamente):

```bash
ollama serve
```

4. Ejecutar Jarvis:

```bash
# En .env (opcional, estos son los valores por defecto):
# JARVIS_OLLAMA_HOST=http://localhost:11434
# JARVIS_OLLAMA_MODEL=llama3.2
python -m jarvis --backend ollama
```

#### Backend LM Studio (modelo local, OpenAI-compatible)

[LM Studio](https://lmstudio.ai) expone una API compatible con OpenAI. Jarvis se conecta vía LiteLLM dentro del agente ADK universal.

```bash
pip install "palmiche-jarvis[adk]"

# En .env:
# JARVIS_LMSTUDIO_HOST=http://localhost:1234/v1
# JARVIS_LMSTUDIO_MODEL=local-model
python -m jarvis --backend lmstudio
```

> Asegúrate de tener un modelo cargado en LM Studio y el servidor local activo antes de iniciar Jarvis.

#### Web UI (FastAPI + Vue 3)

Interfaz web moderna con chat en tiempo real vía WebSocket, renderizado Markdown, animaciones Siri-style y soporte PWA.

```bash
pip install "palmiche-jarvis[web]"
# equivale a: pip install fastapi uvicorn websockets

# Compilar el frontend (una sola vez)
cd jarvis/frontend && pnpm install && pnpm build && cd ../..

python -m jarvis --web
# Abre http://localhost:8000 en el navegador

# Combinar con A2A en un solo servidor
python -m jarvis --web --serve-a2a

# Modo desarrollo (backend + Vite hot-reload)
python -m jarvis --web-dev
```

#### Modo bandeja del sistema (tray)

Requiere **PyQt6** y Pillow. En Linux también se necesitan las bibliotecas XCB.

```bash
# Linux (Ubuntu/Debian)
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                 libxcb-keysyms1 libxcb-render-util0

pip install "palmiche-jarvis[tray]"
# equivale a: pip install PyQt6 PyQt6-Qt6-Multimedia Pillow

python -m jarvis --tray
```

#### Activación por voz

Requiere las cabeceras de PortAudio para compilar PyAudio.

```bash
# Linux
sudo apt install python3-dev portaudio19-dev

# macOS
brew install portaudio

pip install "palmiche-jarvis[voice]"
# o manualmente:
pip install SpeechRecognition pyaudio pyttsx3 gtts

# En .env:
# JARVIS_VOICE_ENABLED=true
python -m jarvis --tray       # la voz solo funciona en modo tray
```

#### Computer Use — control visual de navegador y escritorio

Palmiche-AI puede controlar un navegador Chromium o el escritorio completo usando la API de Gemini computer use, tomando capturas de pantalla y ejecutando acciones (click, tipo, scroll, navegación…).

```bash
pip install "palmiche-jarvis[computer-use]"
# equivale a: pip install google-genai playwright pyautogui Pillow mss

# Instalar Chromium para Playwright (solo backend playwright)
playwright install chromium
```

Requiere `GOOGLE_API_KEY` en `.env`. Uso desde el chat:

```
Busca el precio del dólar hoy en el navegador
Abre YouTube y pon música de jazz
Rellena el formulario de contacto en example.com con mis datos
```

Variables de configuración:

```ini
COMPUTER_USE_MODEL=gemini-2.5-flash     # modelo Gemini para computer use
COMPUTER_USE_BACKEND=playwright          # "playwright" (browser) o "desktop"
COMPUTER_USE_MAX_ITERATIONS=30          # límite de iteraciones del agente visual
```

#### Instalación completa (todos los componentes)

```bash
# Linux — dependencias del sistema primero
sudo apt install \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-render-util0 \
    python3-dev portaudio19-dev ffmpeg mpg123

pip install "palmiche-jarvis[all]"
# equivale a: pip install "palmiche-jarvis[voice,tray,adk,assets,a2a,mcp,web,computer-use]"
```

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
| `JARVIS_SPLASH_ENABLED` | `true` | Pantalla de bienvenida animada (verde) al iniciar |
| `JARVIS_WELCOME_MESSAGE` | `Sistemas en línea. ¿En qué puedo ayudarte?` | Frase de bienvenida del splash (override con `--welcome`) |
| `JARVIS_GOODBYE_MESSAGE` | `{name} desconectado. Hasta luego.` | Frase de despedida al salir (override con `--goodbye`). `{name}` = nombre |
| `JARVIS_BACKEND` | `anthropic` | Backend: `anthropic`, `adk`, `gemini`, `ollama` o `lmstudio` |
| `JARVIS_OLLAMA_HOST` | `http://localhost:11434` | URL del servidor Ollama (backend `ollama`) |
| `JARVIS_OLLAMA_MODEL` | `llama3.2` | Modelo Ollama a usar |
| `JARVIS_LMSTUDIO_HOST` | `http://localhost:1234/v1` | URL del servidor LM Studio (backend `lmstudio`) |
| `JARVIS_LMSTUDIO_MODEL` | `local-model` | Modelo LM Studio a usar |
| `JARVIS_VOICE_ENABLED` | `false` | Activa voz (requiere dependencias extra) |
| `JARVIS_MAX_HISTORY` | `50` | Máximo de mensajes en historial |
| `JARVIS_EVENTS_FILE` | `~/.jarvis_events.json` | Archivo del calendario local de eventos |
| `JARVIS_NOTES_FILE` | `~/.jarvis_notes.json` | Archivo de notas personales |
| `JARVIS_WAKE_WORD` | `palmiche` | Palabra de activación por voz en modo `--tray` |
| `JARVIS_HISTORY_FILE` | `~/.jarvis_history.json` | Archivo de historial de conversación |
| `JARVIS_TRAY_ICON` | — | Ruta a imagen PNG/ICO para el ícono de bandeja (vacío = ícono de caballo integrado) |
| `JARVIS_WELCOME_AUDIO` | — | Ruta a MP3/WAV reproducido al arrancar la bandeja (genera con `python extract_assets.py`) |
| `JARVIS_A2A_HOST` | `0.0.0.0` | Host del servidor A2A (modo `--serve-a2a`) |
| `JARVIS_A2A_PORT` | `8080` | Puerto del servidor A2A |
| `JARVIS_A2A_AGENTS` | — | URLs de agentes A2A remotos (separados por coma) |
| `JARVIS_MCP_SERVERS` | — | Specs de servidores MCP (separados por `;`). Comando stdio o URL SSE |
| `JARVIS_LOG_FILE` | `~/.jarvis_tools.log` | Archivo de log de ejecución de herramientas |
| `JARVIS_LOG_ENABLED` | `true` | Activar/desactivar logging de herramientas |
| `JARVIS_SUDO_PASSWORD` | — | Contraseña sudo para comandos que requieren privilegios (opcional) |
| `COMPUTER_USE_MODEL` | `gemini-2.5-flash` | Modelo Gemini para computer use (requiere `GOOGLE_API_KEY`) |
| `COMPUTER_USE_BACKEND` | `playwright` | Backend de computer use: `playwright` (browser) o `desktop` |
| `COMPUTER_USE_MAX_ITERATIONS` | `30` | Límite de iteraciones del agente visual por tarea |

## Guía de uso

### Inicio rápido

```bash
# Backend Anthropic (default) — requiere ANTHROPIC_API_KEY en .env
python -m jarvis

# Backend local sin API key
python -m jarvis --backend ollama

# Cambiar nombre del asistente
python -m jarvis --name "Viernes"

# Frase de bienvenida y despedida personalizadas (splash animado en verde)
python -m jarvis --welcome "Hola, jefe" --goodbye "Nos vemos, {name}"

# Saltar la pantalla de bienvenida animada
python -m jarvis --no-splash

# Modo bandeja del sistema (ícono en barra de tareas)
python -m jarvis --tray

# Combinar opciones
python -m jarvis --backend gemini --name "Jarvis" --tray

# Web UI (navegador)
python -m jarvis --web

# Web UI + A2A en un solo servidor
python -m jarvis --web --serve-a2a

# Web UI en modo desarrollo (Vite hot-reload)
python -m jarvis --web-dev

# Backend LM Studio (modelo local, OpenAI-compatible)
python -m jarvis --backend lmstudio

# Servidor A2A (expone Jarvis como agente HTTP)
python -m jarvis --serve-a2a --a2a-port 8080

# Servidor MCP stdio (para Claude Desktop, Cursor, Zed, etc.)
python -m jarvis --serve-mcp

# Conectar a agentes A2A y servidores MCP remotos
python -m jarvis --connect-a2a http://otro-agente:8080 --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"
```

### Opciones de línea de comandos

| Opción | Valores | Descripción |
|---|---|---|
| `--backend` | `anthropic`, `adk`, `gemini`, `ollama`, `lmstudio` | Motor de IA (default: `anthropic`) |
| `--name` | cualquier texto | Nombre del asistente (default: `Jarvis`) |
| `--welcome` | cualquier texto | Frase de bienvenida del splash (default: `JARVIS_WELCOME_MESSAGE`) |
| `--goodbye` | cualquier texto | Frase de despedida al salir; admite `{name}` |
| `--no-splash` | — | No mostrar la pantalla de bienvenida animada |
| `--tray` | — | Iniciar en modo bandeja del sistema |
| `--voice` | — | Activar reconocimiento de voz |
| `--wake-word` | texto | Palabra de activación por voz en modo `--tray` (default: `palmiche`) |
| `--query` / `-q` | texto | Ejecutar una consulta única y salir |
| `--clear` | — | Borrar el historial y salir |
| `--serve-a2a` | — | Iniciar como servidor A2A (protocolo Agent-to-Agent) |
| `--a2a-host` | host | Host del servidor A2A (default: `0.0.0.0`) |
| `--a2a-port` | puerto | Puerto del servidor A2A (default: `8080`) |
| `--connect-a2a` | URL | Conectar a un agente A2A remoto como herramienta (repetible) |
| `--serve-mcp` | — | Iniciar como servidor MCP stdio (Claude Desktop, Cursor, etc.) |
| `--web` / `--serve-web` | — | Iniciar Web UI (FastAPI + Vue 3) en el navegador |
| `--web-host` | host | Host del servidor Web UI (default: `127.0.0.1`) |
| `--web-port` | puerto | Puerto del servidor Web UI (default: `8000`) |
| `--web-dev` | — | Modo desarrollo: backend + Vite hot-reload para el frontend |
| `--connect-mcp` | spec | Conectar a un servidor MCP externo (comando stdio o URL SSE, repetible) |

### Comandos dentro del chat

| Comando | Acción |
|---|---|
| `salir` / `exit` / `quit` | Termina la sesión |
| `limpiar` / `clear` | Borra el historial de conversación |
| `voz` / `/voz` / `voice` / `/voice` | Alterna el modo de entrada por voz ON/OFF |

### Ejemplos de uso por categoría

**Sistema y hardware**
```bash
¿Cómo está la CPU y la RAM?
¿Cuánta batería me queda?
Sube el volumen al 70%
Ajusta el brillo al 50%
Bloquea la pantalla
```

**Archivos y directorios**
```bash
Lista los archivos en ~/Documentos
Busca archivos PDF en el escritorio
Lee el archivo ~/notas.txt
Crea la carpeta ~/proyectos/nuevo
Mueve ~/Descargas/foto.jpg a ~/Imágenes/
```

**Aplicaciones y procesos**
```bash
Abre Firefox
Cierra Spotify
¿Qué aplicaciones están corriendo?
```

**Red y conectividad**
```bash
¿Cuál es mi IP?
Haz ping a google.com
¿A qué red WiFi estoy conectado?
```

**Web y búsqueda**
```bash
Busca en YouTube tutoriales de Python
Abre github.com
Busca en DuckDuckGo "mejores editores de código"
Lee el artículo en https://example.com/noticia
Muéstrame las últimas noticias del feed https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada
```

**Clima**
```bash
¿Qué tiempo hace en Madrid?
¿Cómo estará el tiempo esta semana en Buenos Aires?
Dame el pronóstico para los próximos 3 días en imperial
```

**Notas**
```bash
Crea una nota titulada "Ideas de proyecto" con estas ideas: ...
Muéstrame todas mis notas con la etiqueta "trabajo"
Busca en mis notas algo sobre "reunión"
Lee la nota "Ideas de proyecto"
```

**Temporizadores y alarmas**
```bash
Pon un temporizador de 25 minutos para el pomodoro
Pon una alarma a las 08:30 para levantarme
¿Qué temporizadores tengo activos?
Cancela el temporizador abc123
```

**Cálculo y conversión de unidades**
```bash
¿Cuánto es sqrt(144) + 2^10?
Convierte 100 km a millas
¿Cuántos grados Fahrenheit son 37°C?
¿Cuántos GB son 1500 MB?
```

**Herramientas de texto**
```bash
Analiza este texto y dime cuántas palabras tiene: "..."
Convierte "hola mundo" a slug
¿Es "reconocer" un palíndromo?
```

**Portapapeles y utilidades**
```bash
¿Qué hay en el portapapeles?
Copia este texto al portapapeles: Hola mundo
Manda una notificación: "Reunión en 5 minutos"
```

**Shell (con confirmación explícita)**
```bash
Ejecuta: ls -la ~/
# Jarvis pedirá confirmación antes de correr comandos de shell
```

**Autoarranque**
```bash
Activa el arranque automático de Jarvis
Desactiva el autoarranque
```

### Activación por voz

Con `JARVIS_VOICE_ENABLED=true` en el `.env`, di la palabra clave **"palmiche"** para abrir el chat. El sistema escucha en segundo plano y activa la ventana al detectar la palabra clave.

```bash
# Linux: instalar dependencias del sistema primero
sudo apt install python3-dev portaudio19-dev

# macOS
brew install portaudio

# Luego instalar paquetes Python
pip install SpeechRecognition pyaudio pyttsx3 gtts
# o con el grupo opcional:
pip install "palmiche-jarvis[voice]"

# En .env:
# JARVIS_VOICE_ENABLED=true
python -m jarvis --tray
```

## Herramientas externas (MCP y agentes A2A)

Jarvis puede consumir herramientas de **servidores MCP externos** y delegar tareas a **agentes A2A remotos**, ampliando sus capacidades sin límite.

> Guía completa paso a paso con ejemplos concretos: **[MCP-AGENTS.md](docs/MCP-AGENTS.md)**

```bash
# Conectar a un servidor MCP externo (filesystem, GitHub, DB, etc.)
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/proyectos"
python -m jarvis --connect-mcp "http://mi-servidor-mcp:3000"

# Conectar a agentes A2A remotos
python -m jarvis --connect-a2a http://agente-especializado:8080

# Combinar todo
python -m jarvis \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/proyectos" \
  --connect-mcp "npx -y @modelcontextprotocol/server-github" \
  --connect-a2a http://agente-revisor:8080
```

Las herramientas MCP se inyectan con prefijo `mcp_` (ej. `mcp_read_file`); los agentes A2A con prefijo `delegate_to_` (ej. `delegate_to_analista`). También configurable en `.env`:

```ini
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem ~/proyectos;http://mi-servidor:3000
JARVIS_A2A_AGENTS=http://agente1:8080,http://agente2:9090
```

---

## Herramientas disponibles (59)

> Guía completa con preguntas frecuentes por herramienta: **[TOOLS.md](docs/TOOLS.md)**

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
| `web_search` | Buscar en Google, DuckDuckGo o YouTube (modo incógnito) |
| `fetch_webpage` | Descargar y extraer el texto legible de cualquier URL |
| `get_rss_feed` | Obtener las últimas entradas de un feed RSS o Atom |

### Utilidades

| Herramienta | Descripción |
|---|---|
| `get_clipboard` | Leer contenido del portapapeles |
| `set_clipboard` | Escribir texto en el portapapeles |
| `send_notification` | Notificación de escritorio (low / normal / critical) |
| `run_shell_command` | Ejecutar comando shell arbitrario (con confirmación) |
| `setup_autostart` | Activar o desactivar el arranque automático con el sistema |

### Clima

Sin API key. Datos en tiempo real vía [wttr.in](https://wttr.in).

| Herramienta | Descripción |
|---|---|
| `get_weather` | Clima actual: temperatura, humedad, viento, visibilidad y presión |
| `get_forecast` | Pronóstico de 1-3 días con temperatura máx/mín y precipitación |

### Notas

Notas locales en JSON (`~/.jarvis_notes.json`, configurable con `JARVIS_NOTES_FILE`). Soporte de etiquetas y búsqueda de texto completo.

| Herramienta | Descripción |
|---|---|
| `create_note` | Crear nueva nota o actualizar una existente con mismo título |
| `list_notes` | Listar todas las notas, con filtro opcional por etiqueta |
| `read_note` | Leer el contenido completo de una nota por título o id |
| `search_notes` | Buscar en título y contenido de todas las notas |
| `delete_note` | Eliminar nota por título o id |

### Temporizadores y alarmas

Corren en segundo plano y disparan notificaciones de escritorio al completarse.

| Herramienta | Descripción |
|---|---|
| `set_timer` | Temporizador por duración en segundos (máx 24h) |
| `set_alarm` | Alarma a una hora específica `HH:MM` (pasa al día siguiente si ya pasó) |
| `list_timers` | Listar temporizadores activos con tiempo restante |
| `cancel_timer` | Cancelar un temporizador por su id |

### Calculadora y conversión de unidades

| Herramienta | Descripción |
|---|---|
| `calculate` | Evalúa expresiones matemáticas de forma segura (AST, sin `eval`). Soporta `sqrt`, `sin/cos/tan`, `log`, `factorial`, constantes `pi`/`e`, y más |
| `convert_units` | Convierte entre unidades de longitud, masa, temperatura, velocidad, área, volumen y almacenamiento digital |

### Herramientas de texto

| Herramienta | Descripción |
|---|---|
| `text_stats` | Palabras, caracteres, líneas, oraciones y tiempo estimado de lectura |
| `text_transform` | Transforma texto: `upper`, `lower`, `title`, `slug`, `snake`, `camel`, `pascal`, `reverse`, `palindrome`, `strip_accents` y más |

### Calendario y eventos

Calendario local en JSON (`~/.jarvis_events.json`, configurable con `JARVIS_EVENTS_FILE`). Funciona sin conexión ni cuentas externas.

| Herramienta | Descripción |
|---|---|
| `add_event` | Crear evento (fecha `YYYY-MM-DD` o `hoy`/`mañana`, hora opcional) |
| `list_events` | Listar eventos, con rango opcional `start`/`end` |
| `upcoming_events` | Próximos eventos desde hoy durante N días (default 7) |
| `delete_event` | Eliminar evento por su id |

### Developer

| Herramienta | Descripción |
|---|---|
| `format_json` | Validar e indentar (pretty-print) JSON |
| `hash_text` | Hash de texto (md5 / sha1 / sha256 / sha512) |
| `encode_decode` | Codificar/decodificar en base64, url o hex |
| `generate_uuid` | Generar uno o más UUID4 |
| `convert_timestamp` | Convertir entre epoch Unix e ISO-8601 (`now`) |
| `http_request` | Petición HTTP (GET/POST/…) con status, headers y preview — útil para probar APIs |
| `git_status` | Rama, estado del árbol y últimos commits de un repo git |
| `find_process_on_port` | Qué proceso escucha en un puerto TCP |

### Computer Use ★

Automatización visual de navegador o escritorio completo con inteligencia visual de Gemini. Requiere `GOOGLE_API_KEY` y `pip install "palmiche-jarvis[computer-use]"`.

| Herramienta | Descripción |
|---|---|
| `computer_use_task` | Controla visualmente un navegador Chromium (Playwright) o el escritorio completo (pyautogui) para completar tareas descritas en lenguaje natural. Toma capturas de pantalla y ejecuta acciones: click, doble-click, tipo, scroll, arrastrar, navegación, teclas, combinaciones de teclas |

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

### Ollama — modelo local (`ollama`)

Ejecuta un LLM localmente sin enviar datos a la nube. No requiere paquetes pip adicionales; usa `requests` (ya incluido).

**Requisitos:**
1. Instala Ollama desde [ollama.ai](https://ollama.ai)
2. Descarga un modelo: `ollama pull llama3.2`
3. El servidor inicia automáticamente, o manualmente: `ollama serve`

```bash
# En .env (o variables de entorno):
# JARVIS_OLLAMA_MODEL=llama3.2      # modelo a usar
# JARVIS_OLLAMA_HOST=http://localhost:11434  # URL del servidor

python -m jarvis --backend ollama
```

**Modelos recomendados** (de menor a mayor capacidad):

| Modelo | Tamaño | Notas |
|---|---|---|
| `llama3.2:1b` | ~0.8 GB | Muy rápido, tool-use básico |
| `llama3.2` | ~2 GB | Default recomendado |
| `qwen2.5:3b` | ~2 GB | Excelente tool-use para su tamaño |
| `llama3.1:8b` | ~5 GB | Más capaz, requiere más RAM |

### LM Studio — modelo local OpenAI-compatible (`lmstudio`)

Usa [LM Studio](https://lmstudio.ai) que expone una API compatible con OpenAI. Jarvis se conecta a través de LiteLLM dentro del agente ADK universal, sin necesidad de un brain separado.

**Requisitos:**
1. Instala LM Studio desde [lmstudio.ai](https://lmstudio.ai)
2. Descarga y carga un modelo
3. Inicia el servidor local en LM Studio (puerto 1234 por defecto)

```bash
pip install "palmiche-jarvis[adk]"

# En .env (o variables de entorno):
# JARVIS_LMSTUDIO_HOST=http://localhost:1234/v1
# JARVIS_LMSTUDIO_MODEL=local-model

python -m jarvis --backend lmstudio
```

### Web UI — interfaz web (FastAPI + Vue 3)

Interfaz web moderna con chat en tiempo real, streaming por WebSocket, renderizado Markdown con syntax highlighting, animaciones Siri-style y soporte PWA.

```bash
pip install "palmiche-jarvis[web]"

# Compilar el frontend (una sola vez)
cd jarvis/frontend && pnpm install && pnpm build && cd ../..

# Iniciar
python -m jarvis --web
# Abre http://localhost:8000

# Con A2A en el mismo servidor
python -m jarvis --web --serve-a2a

# Modo desarrollo con hot-reload
python -m jarvis --web-dev
```

La Web UI y el protocolo A2A comparten un único servidor FastAPI. Cuando se usa `--web --serve-a2a`, ambos están disponibles en el mismo proceso y puerto.

## Modo bandeja del sistema

Inicia Jarvis como ícono en la barra de tareas con una ventana de chat (PyQt6):

```bash
# Linux (Ubuntu/Debian) — bibliotecas XCB necesarias
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                 libxcb-keysyms1 libxcb-render-util0

pip install "palmiche-jarvis[tray]"   # PyQt6 + Pillow
python -m jarvis --tray
# o combinar con cualquier backend:
python -m jarvis --tray --backend gemini
```

La app **arranca minimizada** en la bandeja. La ventana aparece al:
- Hacer clic en el ícono de la bandeja
- Decir la palabra clave de activación por voz (si `[voice]` está instalado)
- Escribir `salir` / `exit` / `quit` en el chat cierra la aplicación completamente

La ventana de chat incluye:

- **Animación HUD** estilo Iron Man en el encabezado (estados: idle / escuchando / procesando)
- **Barra de estado** inferior con color (Listo / procesando / escuchando / error)
- **Timestamps** `[HH:MM]` en cada mensaje
- **Botón 🗑** y atajos: `Esc` oculta la ventana, `Ctrl+L` limpia la conversación
- **Botón 🎤** para entrada de voz (requiere `[voice]`)
- Ventana **centrada** en pantalla, fade-in/out suave al mostrar/ocultar
- **Ícono** de bandeja con una cabeza de caballo (homenaje a Palmiche)

Variables `.env` del modo bandeja:

| Variable | Descripción |
|---|---|
| `JARVIS_TRAY_ICON` | Ruta a imagen PNG/ICO propia (vacío = ícono integrado) |
| `JARVIS_WELCOME_AUDIO` | Ruta a MP3/WAV reproducido al arrancar (genera con `python extract_assets.py`) |

## Seguridad

- **Herramientas destructivas** (`power_action`, `run_shell_command`, `setup_autostart`) requieren `confirmed=true` en código antes de ejecutarse — no solo en el prompt.
- Las notificaciones en macOS pasan título y mensaje como argumentos argv a `osascript`, nunca interpolados en el fuente AppleScript.
- La confirmación de escritura en portapapeles solo devuelve el número de caracteres, sin exponer el contenido.

## Dependencias del sistema (opcionales)

| Funcionalidad | Linux | macOS |
|---|---|---|
| Bandeja del sistema (XCB) | `sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0` | — |
| Control de medios | `sudo apt install playerctl` | Integrado (Music.app) |
| Capturas de pantalla | `sudo apt install scrot` | Integrado (`screencapture`) |
| Control de brillo | `sudo apt install brightnessctl` | — |
| Info WiFi | `nmcli` (NetworkManager) | Integrado (`airport`) |
| Notificaciones | `sudo apt install libnotify-bin` | Integrado (osascript) |
| Voz (reconocimiento) | `sudo apt install python3-dev portaudio19-dev` + `pip install "palmiche-jarvis[voice]"` | `brew install portaudio` + pip |
| Voz (respuesta audio) | `sudo apt install mpg123` | `brew install ffmpeg` |
| Assets (ícono/audio) | `sudo apt install ffmpeg` + `pip install "palmiche-jarvis[assets]"` | `brew install ffmpeg` + pip |
| Computer Use (Playwright) | `pip install "palmiche-jarvis[computer-use]"` + `playwright install chromium` | igual |
| Computer Use (desktop) | `pip install pyautogui mss` | igual |

### Acciones de energía sin contraseña (Linux)

`power_action` (apagar / reiniciar / suspender) usa `systemctl`, que en muchos
sistemas pide autenticación de polkit y, en un contexto no interactivo, falla con
`Interactive authentication required`. Para permitirlas sin contraseña a la
sesión local activa, instala la regla de polkit incluida:

```bash
sudo jarvis/scripts/install-power-rules.sh
```

El instalador sustituye tu usuario (el que ejecuta `sudo`) en la regla, copia
`jarvis/scripts/49-jarvis-power.rules` a `/etc/polkit-1/rules.d/` y reinicia
polkit. La regla concede apagado/reinicio/suspensión/hibernación **solo a tu
usuario**. Para usar otra cuenta: `JARVIS_USER=otro sudo jarvis/scripts/install-power-rules.sh`.
El bloqueo de pantalla (`lock`) no requiere esta regla.

## Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feat/nueva-herramienta`
3. Commit con mensajes descriptivos: `git commit -m "feat: add nueva herramienta"`
4. Push a tu fork: `git push origin feat/nueva-herramienta`
5. Abre un Pull Request describiendo los cambios

Para añadir una nueva herramienta, crea un módulo en `jarvis/tools/` y regístrala en `jarvis/tools/registry.py` siguiendo el patrón de las herramientas existentes.

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

```text
MIT License — Copyright (c) 2026 EroPerez

Se permite el uso, copia, modificación y distribución de este software
sin restricciones, sujeto a que se incluya el aviso de copyright original.
```
