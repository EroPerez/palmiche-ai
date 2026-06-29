# Documentación de la API (Web UI)

Esta API permite conectar clientes web (Frontend) de forma desacoplada al motor de Inteligencia Artificial de Palmiche J.A.R.V.I.S. utilizando FastAPI.

## Endpoints REST

### `GET /api/v1/health`

Retorna el estado de salud del servidor y la versión de la API.

**Respuesta (200 OK):**

```json
{
  "status": "ok",
  "agent": "Jarvis",
  "version": "1.0.0"
}
```

### `GET /api/v1/history`

Obtiene el historial de mensajes de la sesión actual.

**Respuesta (200 OK):**

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hola Jarvis"
    },
    {
      "role": "assistant",
      "content": "¡Hola! ¿En qué te puedo ayudar?"
    }
  ]
}
```

## Endpoints WebSockets

### `WS /ws/chat`

Canal bidireccional de comunicación en tiempo real para el chat interactivo.

#### Flujo de datos

**1. Envío desde el Cliente (Frontend):**
El cliente debe enviar un JSON con el siguiente formato `ChatRequest`:

```json
{
  "message": "Abre el navegador y busca 'Noticias'",
  "type": "text"
}
```

*(Futuro: `type` podría ser `"audio"` para enviar buffers de micrófono).*

**2. Recepción en el Cliente (Backend -> Frontend):**
El servidor procesará la consulta y responderá con eventos de tipo `ChatResponse`. Como la IA transmite el texto progresivamente (streaming), el cliente recibirá múltiples mensajes para una misma respuesta.

```json
{
  "type": "start",
  "content": ""
}
```

```json
{
  "type": "stream",
  "content": "Abriendo"
}
```

```json
{
  "type": "stream",
  "content": " el navegador..."
}
```

```json
{
  "type": "end",
  "content": "Abriendo el navegador..."
}
```

```json
{
  "type": "error",
  "content": "Mensaje de error si algo falla."
}
```

## Protocolo A2A (opcional)

Cuando se inicia con `--serve-a2a` (o `--web --serve-a2a`), el mismo servidor FastAPI monta las rutas del protocolo A2A:

### `GET /.well-known/agent.json`

Agent Card de descubrimiento para el protocolo A2A de Google.

### `POST /a2a`

Endpoint JSON-RPC 2.0 para el protocolo A2A. Métodos disponibles:
- `tasks/send` — tarea síncrona
- `tasks/sendSubscribe` — tarea con streaming SSE
- `tasks/get` — consultar estado de tarea
- `tasks/cancel` — cancelar tarea

> **Nota:** El endpoint A2A está en `POST /a2a` (no en `POST /`) para evitar conflicto con el catch-all del frontend SPA.

## Arquitectura y Buenas Prácticas

- **Servidor unificado**: Web UI y A2A comparten un solo proceso FastAPI (`jarvis/api/server.py`). La función `create_app()` monta las rutas de chat/system siempre, y las de A2A solo cuando se provee `agent_factory`.
- **Escalabilidad**: La API utiliza el sistema de Routers de FastAPI (`APIRouter`) separando las rutas por dominios (ej: `chat.py`, `system.py`, `a2a.py`).
- **Esquemas**: Todas las validaciones de datos (JSON) están tipadas estáticamente con Pydantic (`schemas.py`), lo que previene errores y autogenera documentación de Swagger en `/docs`.
- **Inyección de Dependencias**: El motor de IA (Agente) se inyecta en las rutas de forma desacoplada para evitar dependencias circulares.
