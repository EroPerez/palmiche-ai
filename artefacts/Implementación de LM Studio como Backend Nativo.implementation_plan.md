# Implementación de LM Studio como Backend Nativo

El objetivo es crear un nuevo backend `lmstudio` para Jarvis que se conecte directamente a la API local de LM Studio, la cual es 100% compatible con el estándar de OpenAI. Esto permitirá usar modelos GGUF descargados desde LM Studio con soporte completo de "Llamada a Herramientas" (Tool Calling) sin depender de librerías externas pesadas.

## Cambios Propuestos

### Componente: Configuración

#### [MODIFY] [config.py](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/jarvis/config.py)
- Añadir las variables de entorno `JARVIS_LMSTUDIO_HOST` (por defecto `http://localhost:1234/v1`) y `JARVIS_LMSTUDIO_MODEL` (por defecto `local-model`).
- Esto permitirá al usuario cambiar el host/puerto si lo necesita.

#### [MODIFY] [.env](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/jarvis/.env)
- Documentar las variables de entorno para LM Studio en la sección de backends.
- Proveer instrucciones breves de cómo configurarlo.

### Componente: Backend (Cerebro)

#### [NEW] [lmstudio_agent.py](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/jarvis/brain/lmstudio_agent.py)
- Crear el agente `JarvisLMStudioAgent` usando la librería estándar `requests` para mantener el código ligero (igual que `ollama_agent.py`).
- Implementar la traducción de schemas de herramientas al formato estándar de OpenAI (`type: "function"`, `function: {...}`).
- Implementar el bucle de herramientas (Tool Loop) llamando a `POST /chat/completions` de LM Studio.
- Asegurar que el formato de respuesta del historial y de los resultados de herramientas cumplan estrictamente con la especificación de OpenAI (usando `tool_call_id`).

### Componente: Punto de Entrada

#### [MODIFY] [__main__.py](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/jarvis/__main__.py)
- En la función `_build_agent`, añadir la lógica para instanciar `JarvisLMStudioAgent` cuando `JARVIS_BACKEND == "lmstudio"`.

## Plan de Verificación

### Verificación Manual
1. Iniciar LM Studio con un modelo que soporte herramientas (ej. Qwen2.5 o Llama3).
2. Configurar el `.env` con `JARVIS_BACKEND=lmstudio`.
3. Ejecutar el servidor de desarrollo web (`bash run_web_dev.sh`) o el modo bandeja (`./run_jarvis.sh --tray`).
4. Pedir a Jarvis que ejecute una herramienta del sistema (ej. "¿qué hora es?" o "abre el navegador") y verificar que la herramienta se invoca y el modelo responde correctamente.

## Preguntas Abiertas (User Review Required)

> [!IMPORTANT]
> LM Studio expone su API de forma idéntica a OpenAI. Construiré el módulo usando `requests` (peticiones HTTP puras) en lugar de importar la librería oficial `openai` en Python para no añadir nuevas dependencias al proyecto de las que ya tienes. ¿Estás de acuerdo con este enfoque liviano?
