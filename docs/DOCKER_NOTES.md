# Consideraciones para Docker (Palmiche J.A.R.V.I.S.)

La contenedorización de agentes de inteligencia artificial interactivos que utilizan capacidades gráficas, de audio y visión de escritorio requiere configuraciones especiales debido a la aislación del sistema operativo anfitrión (host) que proporciona Docker.

A continuación, se detallan los puntos clave a tener en cuenta al usar Palmiche-AI mediante Docker.

## 1. Interfaz Gráfica (X11 / Wayland)

La interfaz de bandeja del sistema (UI) usa PyQt6. Para que el contenedor pueda dibujar ventanas en la pantalla de un sistema Linux host, es necesario compartir el socket X11.

- **Volumen necesario:** `-v /tmp/.X11-unix:/tmp/.X11-unix`
- **Variable de entorno:** `-e DISPLAY=$DISPLAY`
- **Permisos X11 en el host:** Es posible que Docker reciba errores del tipo `qt.qpa.xcb: could not connect to display`. Para solucionarlo temporalmente (y permitir que cualquier usuario local conecte al display X11), ejecuta en la terminal de tu host:
  ```bash
  xhost +local:docker
  ```
  *(Nota: en sistemas estrictos basados en Wayland sin XWayland, esto puede requerir configuraciones adicionales o mapeos de `/run/user/1000/wayland-0` y la variable `WAYLAND_DISPLAY`)*.

## 2. Micrófono y Audio

Palmiche-AI utiliza `pyaudio` y `portaudio` para grabar audio, y reproductores (como `mpg123`) para la síntesis de voz (TTS). Docker bloquea el acceso directo a dispositivos de hardware por defecto.

- **Dispositivo de sonido:** Se expone montando el dispositivo de sonido directamente con `--device /dev/snd`.
- **Privilegios de Pulseaudio/ALSA:** En hosts modernos con PipeWire o PulseAudio, puede que no sea suficiente con `/dev/snd`. Como alternativa, podrías mapear el socket de PulseAudio, pero el método de `--device /dev/snd` suele ser el más directo y robusto en entornos Ubuntu/Debian compartiendo el mismo grupo de audio.
- En caso de errores al iniciar la voz: Verifica que el usuario dentro del contenedor pertenezca al grupo `audio` o deshabilita la voz en tu `.env` (`JARVIS_VOICE_ENABLED=false`).

## 3. Tamaño de la Imagen y Playwright

La instalación **completa** de Jarvis incluye dependencias muy pesadas (Navegador Chromium, Playwright, X11 completo), superando a menudo los 1.5 - 2 GB. 

Para mantener la imagen más liviana y ágil, el `Dockerfile` por defecto **no incluye** los extras de `computer-use` (Playwright y Google GenAI).

- **Si necesitas Playwright (Computer Use):**
  Abre el archivo `Dockerfile` y descomenta las secciones que instalan dependencias de X11 extendidas, ajusta la instalación de Python para incluir `[all]` en lugar de las opciones seleccionadas, y descomenta el comando `RUN playwright install chromium --with-deps`.

## 4. Ejecución del Servidor Web por Defecto

El contenedor está configurado para ejecutar un servicio web por defecto al iniciar (`python -m jarvis --serve-a2a`). Esto levanta un endpoint HTTP que permite a otros agentes (o interfaces web) enviar tareas a Jarvis.

- Si prefieres un modo de terminal interactivo (CLI tradicional), puedes sobrescribir el comando predeterminado (entrypoint) usando:
  ```bash
  docker exec -it palmiche_jarvis bash
  # una vez dentro
  python -m jarvis
  ```
- O modificar el bloque `command` dentro de `docker-compose.yml`.

## 5. El Contenedor Ollama

El archivo `docker-compose.yml` incluye un servicio separado para `ollama` (que ejecuta modelos LLM localmente). Para mantener la integridad de los modelos descargados (y no tener que descargar Gb de pesos neuronales cada vez que se levanta el entorno), se usa un mapeo local hacia la carpeta `./.ollama-models`.

Jarvis está preconfigurado (mediante el `.env`) para conectarse a `http://ollama:11434`. Antes de usarlo con un modelo, recuerda descargar un modelo dentro del contenedor de ollama:
```bash
docker exec -it ollama_server ollama pull llama3.2
```

### Aceleración por GPU (NVIDIA)

Por defecto, Ollama en Docker se ejecuta utilizando la CPU, lo cual es significativamente más lento que usar una tarjeta de video dedicada. Si tienes una GPU NVIDIA y al menos 6 GB de VRAM (suficiente para correr cómodamente el modelo `llama3.2` de 3B), puedes habilitar la aceleración por hardware:

1. Instala el [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) en tu sistema anfitrión.
2. Abre el archivo `docker-compose.yml` y descomenta el bloque `deploy` dentro del servicio `ollama`:
   ```yaml
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ```
3. Reinicia tu stack con `docker compose down` y `docker compose up -d`.

*(Si cuentas con una gráfica AMD Radeon, necesitarás usar la imagen `ollama/ollama:rocm` y mapear `/dev/kfd` y `/dev/dri` en lugar de usar el bloque deploy de NVIDIA).*
