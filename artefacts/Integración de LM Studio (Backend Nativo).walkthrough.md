# Integración de LM Studio (Backend Nativo)

El backend de Jarvis ha sido extendido exitosamente para soportar **LM Studio** de forma nativa a través del estándar de la API de OpenAI. Esta solución es completamente "liviana" (Dependency-Free), utilizando solo la librería estándar `requests`.

## Cambios Realizados

- **Nuevo Cerebro (Brain)**: Se creó `jarvis/brain/lmstudio_agent.py`, el cual incluye:
  - Traducción automática de esquemas de herramientas al formato oficial de *Function Calling* de OpenAI (`type: "function"`, `function: {...}`).
  - Loop de ejecución de herramientas iterativo idéntico al de Ollama pero adaptado a la estructura de respuesta anidada (`data["choices"][0]["message"]`) de OpenAI.
  - Generación estricta de validación `tool_call_id` en las respuestas de herramientas enviadas de vuelta a LM Studio.
- **Registro del Entrypoint**: Se modificó la fábrica de inicialización `_build_agent()` en `jarvis/__main__.py` para inicializar el agente correctamente al detectar el backend `lmstudio`.
- **Configuración (`config.py` y `.env`)**:
  - Se añadieron `JARVIS_LMSTUDIO_HOST` (por defecto el estándar de LM Studio: `http://localhost:1234/v1`).
  - Se añadió `JARVIS_LMSTUDIO_MODEL` (por defecto `local-model`, que LM Studio mapea automáticamente al modelo GGUF actualmente cargado en su interfaz).
  - Se actualizaron los `.env` y `.env.example` con la nueva sección de LM Studio.

## Cómo Utilizarlo

1. Abre la aplicación de escritorio de **LM Studio**.
2. Descarga un modelo con buenas capacidades de *Tool Calling* (ej. `Qwen 2.5` o `Llama 3.1/3.2`).
3. Ve a la pestaña de **Developer** (Servidor Local) y presiona "Start Server".
4. En tu archivo `.env`, asegúrate de tener:
   ```env
   JARVIS_BACKEND=lmstudio
   ```
5. ¡Inicia Jarvis y pruébalo!
