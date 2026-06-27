FROM ubuntu:22.04

# Evitar prompts interactivos de apt
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema operativo (basadas en docs/INSTALL.md)
# Priorizando compatibilidad y herramientas necesarias (sin Playwright/chromium por defecto)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Herramientas base
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    nano \
    # Dependencias de Interfaz Gráfica (XCB)
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libx11-xcb1 \
    libxrender1 \
    libxext6 \
    libglib2.0-0 \
    # Dependencias de Audio y Voz
    portaudio19-dev \
    ffmpeg \
    mpg123 \
    alsa-utils \
    # Utilidades varias
    playerctl \
    scrot \
    # Limpieza
    && rm -rf /var/lib/apt/lists/*

# Configurar Python por defecto
RUN ln -s /usr/bin/python3 /usr/bin/python

# (Opcional) Si necesitas habilitar Computer Use, descomenta las siguientes líneas para instalar dependencias de Playwright
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxfixes3 \
#     libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 \
#     && rm -rf /var/lib/apt/lists/*

# Copiar el código de la aplicación
COPY . /app

# Instalar los paquetes Python (omitiendo 'computer-use' y 'tray' para mantener la imagen ligera)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir ".[voice,adk,assets,a2a,mcp]"

# (Opcional) Si descomentaste las dependencias arriba, cambia la línea anterior por:
# RUN pip install --no-cache-dir ".[all]" && playwright install chromium --with-deps

# Copiar y configurar el entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# El entrypoint configurará cosas básicas antes de ceder control
ENTRYPOINT ["docker-entrypoint.sh"]

# Comando por defecto (modo servidor A2A). Se puede sobrescribir en docker-compose
CMD ["python", "-m", "jarvis", "--serve-a2a", "--a2a-port", "8080", "--a2a-host", "0.0.0.0"]
