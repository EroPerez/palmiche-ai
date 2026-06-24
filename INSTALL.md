# Guía de instalación — Palmiche J.A.R.V.I.S.

## Requisitos previos

| Requisito | Versión mínima |
|---|---|
| Python | 3.10+ |
| Sistema operativo | Linux o macOS |
| pip | Incluido con Python |

---

## 1. Clonar el repositorio

```bash
git clone https://github.com/EroPerez/palmiche-ai.git
cd palmiche-ai
```

---

## 2. Entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> En sesiones futuras solo necesitas `source .venv/bin/activate` para activar el entorno.

---

## 3. Instalar dependencias base

```bash
pip install -e .
```

Esto instala el núcleo: `anthropic`, `rich`, `python-dotenv`, `psutil`, `pyperclip` y `requests`.

---

## 4. Configurar variables de entorno

```bash
cp jarvis/.env.example jarvis/.env
nano jarvis/.env          # o tu editor favorito
```

Variables esenciales:

| Variable | Descripción |
|---|---|
| `ANTHROPIC_API_KEY` | API key de Anthropic (requerida para el backend por defecto) |
| `GOOGLE_API_KEY` | API key de Google AI Studio (solo backends `gemini` / `adk`+Gemini) |
| `JARVIS_NAME` | Nombre del asistente (default: `Jarvis`) |
| `JARVIS_BACKEND` | Motor de IA: `anthropic` (default), `adk`, `gemini`, `ollama` |

> Obtén tu API key de Anthropic en [console.anthropic.com](https://console.anthropic.com).
> Obtén tu API key de Google en [aistudio.google.com](https://aistudio.google.com).

---

## 5. Verificar la instalación base

```bash
python -m jarvis --help
python -m jarvis -q "hola"     # consulta rápida de prueba
```

---

## Componentes opcionales

### Interfaz gráfica (bandeja del sistema)

La interfaz de bandeja usa **PyQt6** con una animación HUD estilo Iron Man.
Requiere que el sistema tenga soporte gráfico (Xorg o Wayland).

```bash
# Ubuntu / Debian
sudo apt install libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                 libxcb-keysyms1 libxcb-render-util0

# Fedora / RHEL
sudo dnf install xcb-util-cursor xcb-util-icccm xcb-util-image \
                 xcb-util-keysyms xcb-util-renderutil

# Instalar paquetes Python
pip install "palmiche-jarvis[tray]"
# equivale a: pip install PyQt6 Pillow
```

Iniciar en modo bandeja:

```bash
python -m jarvis --tray
```

Variables `.env` del modo bandeja:

| Variable | Descripción |
|---|---|
| `JARVIS_TRAY_ICON` | Ruta a imagen PNG/ICO propia (vacío = ícono de caballo integrado) |
| `JARVIS_WELCOME_AUDIO` | Ruta a MP3/WAV que se reproduce al arrancar la bandeja |

---

### Activación por voz y reconocimiento de habla

```bash
# Ubuntu / Debian — dependencias del sistema
sudo apt install python3-dev portaudio19-dev

# macOS
brew install portaudio

# Paquetes Python
pip install "palmiche-jarvis[voice]"
# equivale a: pip install SpeechRecognition pyaudio pyttsx3 gtts

# Reproductor de audio (para respuestas gTTS)
sudo apt install mpg123            # Linux
# macOS ya incluye ffplay si tienes ffmpeg instalado
```

Activar en `.env`:

```ini
JARVIS_VOICE_ENABLED=true
JARVIS_WAKE_WORD=palmiche          # palabra clave de activación (default)
```

Con voz habilitada, di **"palmiche"** en cualquier momento para que Jarvis abra la ventana y comience a escuchar.

---

### Backend Google ADK + Claude

```bash
pip install "palmiche-jarvis[adk]"
# equivale a: pip install google-adk litellm
```

`.env`:

```ini
JARVIS_BACKEND=adk
ANTHROPIC_API_KEY=sk-ant-...
```

---

### Backend Google ADK + Gemini

```bash
pip install "palmiche-jarvis[gemini]"
# equivale a: pip install google-adk
```

`.env`:

```ini
JARVIS_BACKEND=gemini
GOOGLE_API_KEY=AIza...
JARVIS_GEMINI_MODEL=gemini-2.0-flash
```

---

### Backend Ollama (modelo local, sin API key)

```bash
# 1. Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh    # Linux
brew install ollama                               # macOS

# 2. Descargar un modelo
ollama pull llama3.2        # ~2 GB, recomendado
# alternativas:
ollama pull llama3.2:1b     # ~0.8 GB, más rápido
ollama pull qwen2.5:3b      # ~2 GB, excelente tool-use
ollama pull llama3.1:8b     # ~5 GB, más capaz

# 3. Iniciar servidor (si no arranca automáticamente)
ollama serve
```

`.env`:

```ini
JARVIS_BACKEND=ollama
JARVIS_OLLAMA_HOST=http://localhost:11434
JARVIS_OLLAMA_MODEL=llama3.2
```

---

### Extracción de assets (ícono y audio desde YouTube)

```bash
# Dependencias del sistema
sudo apt install ffmpeg     # Linux
brew install ffmpeg         # macOS

# Paquete Python
pip install "palmiche-jarvis[assets]"
# equivale a: pip install yt-dlp

# Ejecutar el extractor
python extract_assets.py
```

El script descarga la miniatura del video como `jarvis/assets/icon.png` y los primeros 6 segundos de audio como `jarvis/assets/welcome.mp3`. Al finalizar imprime las líneas que debes agregar al `.env`.

---

### Instalación completa (todos los componentes)

```bash
# Ubuntu / Debian — dependencias del sistema primero
sudo apt install \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
    libxcb-keysyms1 libxcb-render-util0 \
    python3-dev portaudio19-dev \
    ffmpeg mpg123 \
    playerctl scrot brightnessctl

# macOS
brew install portaudio ffmpeg

# Paquetes Python
pip install "palmiche-jarvis[all]"
# equivale a: voice + tray + adk + assets
```

---

## Dependencias del sistema por funcionalidad

| Funcionalidad | Linux (apt) | macOS (brew) |
|---|---|---|
| Interfaz gráfica (XCB) | `libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0` | — |
| Reconocimiento de voz | `python3-dev portaudio19-dev` | `portaudio` |
| Reproducción MP3 (gTTS) | `mpg123` | Incluido con `ffmpeg` |
| Extracción de assets | `ffmpeg` | `ffmpeg` |
| Control de medios | `playerctl` | Integrado |
| Capturas de pantalla | `scrot` | Integrado (`screencapture`) |
| Control de brillo | `brightnessctl` | — |
| Info de red / WiFi | `network-manager` (nmcli) | Integrado |
| Notificaciones de escritorio | `libnotify-bin` (notify-send) | Integrado (osascript) |

---

## Acciones de energía sin contraseña (Linux)

`power_action` (apagar / reiniciar / suspender) usa `systemctl`, que en muchos sistemas pide autenticación de polkit. Para permitirlas sin contraseña al usuario activo:

```bash
sudo jarvis/scripts/install-power-rules.sh
```

El script copia la regla polkit a `/etc/polkit-1/rules.d/` y reinicia polkit.
Para instalar con un usuario distinto: `JARVIS_USER=otro sudo jarvis/scripts/install-power-rules.sh`.

---

## Inicio rápido tras la instalación

```bash
# Terminal interactivo (backend Anthropic)
python -m jarvis

# Backend local sin API key
python -m jarvis --backend ollama

# Modo bandeja del sistema
python -m jarvis --tray

# Bandeja + backend Gemini + nombre personalizado
python -m jarvis --tray --backend gemini --name "Viernes"

# Consulta única y salir
python -m jarvis -q "¿cuánta RAM tengo?"
```

---

## Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ModuleNotFoundError: PyQt6` | Extras de bandeja no instalados | `pip install "palmiche-jarvis[tray]"` |
| `qt.qpa.xcb: could not connect to display` | Sin servidor gráfico | Verifica que `DISPLAY` esté definido o usa modo CLI |
| `OSError: PortAudio library not found` | portaudio no instalado | `sudo apt install portaudio19-dev` |
| `ANTHROPIC_API_KEY not set` | Falta la API key | Edita `jarvis/.env` y agrega la key |
| `ollama: command not found` | Ollama no instalado | Sigue los pasos del backend Ollama |
| Mic no disponible al abrir la bandeja | `pyaudio`/`SpeechRecognition` no instalados | `pip install "palmiche-jarvis[voice]"` |
