# Plan de Dockerización para Palmiche J.A.R.V.I.S.

Este plan detalla los pasos para crear un entorno Docker completo para Palmiche J.A.R.V.I.S. basado en las dependencias y opciones detalladas en `docs/INSTALL.md`. El objetivo es dockerizar **todos** los componentes opcionales (incluyendo la bandeja de sistema gráfica, uso de micrófono/audio, playwright para computer-use y un backend local de Ollama).

## User Review Required

> [!WARNING]
> **Interfaz Gráfica y Audio en Docker**: Ejecutar aplicaciones gráficas (PyQt6) y utilizar el micrófono o reproducir audio (`portaudio`, `pyaudio`, `mpg123`) desde un contenedor Docker en Linux requiere mapear el socket de X11 (`/tmp/.X11-unix`) y los dispositivos de sonido (`/dev/snd`). Esto puede requerir configuración adicional en el host (como ejecutar `xhost +local:docker`). ¿Estás de acuerdo con este enfoque o prefieres omitir la UI gráfica/audio en la versión de Docker y dejarlo solo como un servidor backend headless (A2A/MCP/CLI)?

> [!IMPORTANT]
> **Tamaño de la imagen**: Al incluir Playwright, Chromium, Ollama y todos los paquetes de soporte para X11, la imagen de Docker generada será bastante pesada. 

## Open Questions

- ¿Quieres que el contenedor arranque el servicio web (A2A/MCP) por defecto, o que sirva principalmente para ejecutar el agente en la terminal de forma interactiva (`python -m jarvis`)?
- ¿Te gustaría incluir un script `docker-entrypoint.sh` para gestionar permisos o arrancar el servidor `ollama` antes de iniciar la aplicación principal?

## Proposed Changes

### Archivos de Configuración de Docker

#### [NEW] [Dockerfile](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/Dockerfile)
- Basado en `python:3.10-slim` o `ubuntu:22.04`.
- Instalación de dependencias del sistema operativo (basado en `INSTALL.md` para Ubuntu/Debian):
  - UI: `libxcb-cursor0`, `libxcb-icccm4`, `libxcb-image0`, `libxcb-keysyms1`, `libxcb-render-util0`
  - Audio/Voz: `python3-dev`, `portaudio19-dev`, `ffmpeg`, `mpg123`
  - Utilidades: `playerctl`, `scrot`, `brightnessctl`
  - Playwright/Computer-Use: `libnss3`, `libatk1.0-0`, `libatk-bridge2.0-0`, `libgbm1`, etc.
- Copiado del código fuente al contenedor.
- Instalación de todas las dependencias de Python con: `pip install ".[all]"`.
- Instalación del navegador para Computer Use con: `playwright install chromium --with-deps`.

#### [NEW] [docker-compose.yml](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/docker-compose.yml)
- Definición del servicio `palmiche-ai`:
  - Construido a partir del nuevo `Dockerfile`.
  - Mapeo de volumen para el archivo `.env` y el directorio `jarvis/assets`.
  - Variables de entorno para habilitar GUI (e.g., `DISPLAY=${DISPLAY}`).
  - Mapeo de volumen de `/tmp/.X11-unix:/tmp/.X11-unix` para la interfaz gráfica.
  - Privilegios/dispositivos para el micrófono/audio (`--device /dev/snd`).
  - Mapeo de puertos para A2A (8080) y MCP.
  - Red conectada al contenedor de Ollama.
- Definición del servicio `ollama`:
  - Imagen oficial de `ollama/ollama`.
  - Volumen local para cachear los modelos descargados y no tener que bajarlos de nuevo.
  - Expuesto en el puerto 11434.

#### [NEW] [.dockerignore](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/.dockerignore)
- Archivo para excluir directorios locales del contexto de construcción (ej. `.venv`, `__pycache__`, `.git`, `.env`).

## Verification Plan

### Manual Verification
1. Hacer un build inicial: `docker-compose build`.
2. Levantar el stack: `docker-compose up -d`.
3. Probar conexión a la terminal interactivamente: `docker exec -it <contenedor> python -m jarvis`.
4. Verificar si la interfaz gráfica abre y el audio funciona correctamente en el host Linux (sujeto a la configuración de X11 y pulseaudio/alsa).
5. Probar que Jarvis puede conectarse con el contenedor de Ollama asignando `JARVIS_OLLAMA_HOST=http://ollama:11434` en el `.env`.
