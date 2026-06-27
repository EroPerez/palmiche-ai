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

### Arquitectura y Buenas Prácticas

- **Escalabilidad**: La API utiliza el sistema de Routers de FastAPI (`APIRouter`) separando las rutas por dominios (ej: `chat.py`, `system.py`).
- **Esquemas**: Todas las validaciones de datos (JSON) están tipadas estáticamente con Pydantic (`schemas.py`), lo que previene errores y autogenera documentación de Swagger en `/docs`.
- **Inyección de Dependencias**: El motor de IA (Agente) se inyecta en las rutas de forma desacoplada para evitar dependencias circulares.
