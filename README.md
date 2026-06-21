# J.A.R.V.I.S.

> Just A Rather Very Intelligent System — asistente de IA personal para laptop, impulsado por Claude.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Backends](https://img.shields.io/badge/backends-Anthropic%20%7C%20ADK%20%7C%20Gemini%20%7C%20Ollama-green.svg)](#backends)

## Características

- Conversación natural en español o inglés con memoria de sesión persistente
- 28 herramientas integradas para controlar el sistema, archivos, red, medios y más
- Cuatro backends intercambiables: Anthropic SDK, Google ADK + LiteLLM, Google ADK + Gemini, y Ollama (local)
- Entrada por voz opcional con reconocimiento de habla
- Interfaz en terminal con Rich (colores, markdown, paneles)

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

O usando el script de instalación incluido:

```bash
cd jarvis
bash install.sh
```

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

#### Modo bandeja del sistema (tray)

Requiere `tkinter` (no siempre incluido con Python) y `pystray` + `Pillow`.

```bash
# Linux
sudo apt install python3-tk            # Ubuntu/Debian
sudo dnf install python3-tkinter       # Fedora/RHEL

pip install "palmiche-jarvis[tray]"
# o manualmente:
pip install pystray Pillow

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
pip install SpeechRecognition pyttsx3 pyaudio

# En .env:
# JARVIS_VOICE_ENABLED=true
python -m jarvis --tray       # la voz solo funciona en modo tray
```

#### Instalación completa (todos los componentes)

```bash
# Linux: dependencias del sistema primero
sudo apt install python3-tk python3-dev portaudio19-dev

pip install "palmiche-jarvis[all]"
# equivale a: pip install "palmiche-jarvis[voice,tray,adk]"
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
| `JARVIS_BACKEND` | `anthropic` | Backend: `anthropic`, `adk`, `gemini` u `ollama` |
| `JARVIS_OLLAMA_HOST` | `http://localhost:11434` | URL del servidor Ollama (backend `ollama`) |
| `JARVIS_OLLAMA_MODEL` | `llama3.2` | Modelo Ollama a usar |
| `JARVIS_VOICE_ENABLED` | `false` | Activa voz (requiere dependencias extra) |
| `JARVIS_MAX_HISTORY` | `50` | Máximo de mensajes en historial |

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
```

### Opciones de línea de comandos

| Opción | Valores | Descripción |
|---|---|---|
| `--backend` | `anthropic`, `adk`, `gemini`, `ollama` | Motor de IA (default: `anthropic`) |
| `--name` | cualquier texto | Nombre del asistente (default: `Jarvis`) |
| `--welcome` | cualquier texto | Frase de bienvenida del splash (default: `JARVIS_WELCOME_MESSAGE`) |
| `--goodbye` | cualquier texto | Frase de despedida al salir; admite `{name}` |
| `--no-splash` | — | No mostrar la pantalla de bienvenida animada |
| `--tray` | — | Iniciar en modo bandeja del sistema |
| `--voice` | — | Activar reconocimiento de voz |
| `--query` / `-q` | texto | Ejecutar una consulta única y salir |
| `--clear` | — | Borrar el historial y salir |

### Comandos dentro del chat

| Comando | Acción |
|---|---|
| `salir` / `exit` / `quit` | Termina la sesión |
| `limpiar` / `clear` | Borra el historial de conversación |

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
pip install SpeechRecognition pyttsx3 pyaudio
# o con el grupo opcional:
pip install "palmiche-jarvis[voice]"

# En .env:
# JARVIS_VOICE_ENABLED=true
python -m jarvis --tray
```

## Herramientas disponibles (28)

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
| `web_search` | Buscar en Google, DuckDuckGo o YouTube |

### Utilidades

| Herramienta | Descripción |
|---|---|
| `get_clipboard` | Leer contenido del portapapeles |
| `set_clipboard` | Escribir texto en el portapapeles |
| `send_notification` | Notificación de escritorio (low / normal / critical) |
| `run_shell_command` | Ejecutar comando shell arbitrario (con confirmación) |
| `setup_autostart` | Activar o desactivar el arranque automático con el sistema |

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

## Modo bandeja del sistema

Inicia Jarvis como ícono en la barra de tareas con una ventana de chat:

```bash
# Linux: tkinter debe estar instalado (no siempre viene con Python)
sudo apt install python3-tk        # Ubuntu/Debian
sudo dnf install python3-tkinter   # Fedora/RHEL

pip install pystray Pillow
python -m jarvis --tray
# o combinar con cualquier backend:
python -m jarvis --tray --backend gemini
```

Haz clic en el ícono para abrir/cerrar la ventana de chat. La ventana puede ocultarse sin cerrar el proceso.

## Seguridad

- **Herramientas destructivas** (`power_action`, `run_shell_command`, `setup_autostart`) requieren `confirmed=true` en código antes de ejecutarse — no solo en el prompt.
- Las notificaciones en macOS pasan título y mensaje como argumentos argv a `osascript`, nunca interpolados en el fuente AppleScript.
- La confirmación de escritura en portapapeles solo devuelve el número de caracteres, sin exponer el contenido.

## Dependencias del sistema (opcionales)

| Funcionalidad | Linux | macOS |
|---|---|---|
| Control de medios | `sudo apt install playerctl` | Integrado (Music.app) |
| Capturas de pantalla | `sudo apt install scrot` | Integrado (`screencapture`) |
| Control de brillo | `sudo apt install brightnessctl` | — |
| Info WiFi | `nmcli` (NetworkManager) | Integrado (`airport`) |
| Bandeja del sistema | `sudo apt install python3-tk` | Integrado |
| Voz (reconocimiento) | `sudo apt install python3-dev portaudio19-dev` + `pip install SpeechRecognition pyttsx3 pyaudio gtts` | `brew install portaudio` + pip |
| Voz (respuesta audio HD) | `sudo apt install mpg123` (para reproducir gTTS) | Integrado (`ffplay` vía ffmpeg) |

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
