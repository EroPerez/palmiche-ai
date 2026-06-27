# Dockerización de Palmiche J.A.R.V.I.S. Completada

He finalizado la creación de los archivos necesarios para ejecutar Palmiche J.A.R.V.I.S. en Docker, tomando en cuenta todas tus observaciones.

## Archivos Creados

### [DOCKER_NOTES.md](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/docs/DOCKER_NOTES.md)
Se creó un documento detallado en `docs/DOCKER_NOTES.md` con consideraciones clave sobre:
- Configuración y mapeo del servidor X11 para la interfaz gráfica.
- Mapeo del dispositivo de audio para micrófono y altavoces.
- Recomendaciones para reducir el tamaño de la imagen excluyendo Playwright por defecto, y cómo activarlo si fuera necesario.

### [Dockerfile](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/Dockerfile)
- Basado en `ubuntu:22.04` para garantizar la compatibilidad con las dependencias del sistema (apt) especificadas en la guía original.
- Instala las herramientas base, XCB y paquetes de Audio.
- Instala los extras Python `[voice,tray,adk,assets,a2a,mcp]`, omitiendo `[computer-use]` de forma intencionada para reducir el tamaño final de la imagen.

### [docker-entrypoint.sh](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/docker-entrypoint.sh)
- Un script de arranque que copia `jarvis/.env.example` a `jarvis/.env` si este no existe.
- Ejecuta la aplicación. El archivo de Docker ya le asigna permisos de ejecución durante el `build`.

### [docker-compose.yml](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/docker-compose.yml)
Define dos servicios:
1. `palmiche-ai`: Se mapea `/tmp/.X11-unix` y `/dev/snd`. Se expone el puerto `8080` (A2A). Por defecto, arranca el servidor web (`--serve-a2a`).
2. `ollama`: Se expone el puerto `11434` con persistencia mediante un volumen local para no perder los modelos entre reinicios.

### [.dockerignore](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/.dockerignore)
Evita la copia accidental de directorios pesados (`.venv`, `.git`) y protege tu archivo `.env` local para evitar sobreescribir el del volumen montado si realizaras un build posteriormente.

---

> [!TIP]
> Para construir y levantar el entorno, ejecuta en tu terminal:
> ```bash
> docker-compose up -d --build
> ```
> Recuerda ejecutar `xhost +local:docker` en tu anfitrión si usas un escritorio con X11 y deseas usar la interfaz gráfica desde el contenedor.
