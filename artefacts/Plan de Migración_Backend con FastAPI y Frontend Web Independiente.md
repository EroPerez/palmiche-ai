# Plan de Migración: Backend con FastAPI y Frontend Web Independiente

El objetivo de este plan es modernizar y desacoplar la arquitectura de Jarvis. Mantendremos el potente motor de IA en Python (para conservar la compatibilidad perfecta con LiteLLM, Ollama, herramientas locales y procesamiento de audio) y construiremos un servidor FastAPI que exponga toda esta funcionalidad a un Frontend Web independiente.

## 1. Arquitectura Propuesta

- **Backend (Python + FastAPI):** Jarvis se ejecutará como un servicio o demonio. Expondrá una API REST para configuraciones/historial y un endpoint de **WebSockets** para la comunicación en tiempo real (streaming de texto y, eventualmente, audio).
- **Frontend (Web - HTML/JS/CSS o Framework JS):** Una interfaz de usuario moderna que corre en el navegador (o en un contenedor tipo Electron/Tauri si queremos mantenerlo como app de escritorio más adelante). Se conectará al backend de Python mediante WebSockets.

---

## 2. Cambios en el Código (Backend)

Vamos a aprovechar el ecosistema que ya tienes en el proyecto (ya usas `fastapi` y `uvicorn` para la característica `a2a`).

### [NEW] `jarvis/api/server.py`
Crearemos un nuevo servidor dedicado para clientes UI (a diferencia de `a2a/server.py` que es para comunicación entre agentes vía JSON-RPC).
- Endpoint REST `/api/v1/health`: Estado del agente.
- Endpoint REST `/api/v1/history`: Obtener el historial de la sesión.
- **Endpoint WebSocket `/ws/chat`**: La joya de la corona. Permitirá al frontend enviar mensajes y recibir la respuesta del LLM (agente) en tiempo real, palabra por palabra (streaming).

### [MODIFY] `jarvis/__main__.py`
Agregaremos un nuevo flag `--serve-api` (o `--serve-web`) que inicie el servidor FastAPI en lugar de la CLI o la bandeja (tray) del sistema.
- Se instanciará el Agente (`_build_agent`) y se pasará al servidor FastAPI.

---

## 3. Cambios en el Código (Frontend)

### [NEW] Directorio `web/` (o `frontend/`)
Crearemos un proyecto Frontend completamente independiente en la raíz del repositorio. Aquí hay dos opciones que debemos decidir (ver sección de "Preguntas Abiertas").
- **Opción A (Vanilla):** Un simple archivo `index.html`, `style.css` y `app.js`. No requiere Node.js instalado obligatoriamente (FastAPI puede servir estos archivos directamente estáticos).
- **Opción B (Modern Web App):** Crear un proyecto con Vite (ej: React + Tailwind CSS o Vue). Da resultados visualmente más impresionantes y mantenibles, pero requiere que ejecutes `npm run dev` junto con tu servidor de Python, y saber algo de Node.js.

---

## 4. Plan de Ejecución (Paso a Paso)

1. **Fase 1: El Backend FastAPI**
   - Crear `jarvis/api/server.py` con el WebSocket.
   - Modificar `__main__.py` para soportar el flag `--serve-api`.
   - Modificar las clases de `jarvis.brain` para asegurar que expongan funciones de *streaming* (rendir generadores o usar colas asíncronas) si queremos respuestas fluidas.
2. **Fase 2: El Frontend Base**
   - Crear la carpeta del frontend y configurar el proyecto básico.
   - Implementar la lógica del cliente WebSocket para conectar con FastAPI.
3. **Fase 3: UI / UX**
   - Diseñar la interfaz de chat (estilo ChatGPT o Claude).
   - Aplicar estilos modernos, animaciones suaves y un tema oscuro.
4. **Fase 4: Pruebas**
   - Levantar el servidor FastAPI.
   - Abrir el Frontend en el navegador y probar la comunicación.

---

> [!IMPORTANT]
> **Revisión del Usuario Requerida**
> 
> Esta migración cambiará la forma en que interactúas con Jarvis si decides abandonar el modo `--tray` en favor del modo web. La bandeja del sistema nativa de PyQt6 y las herramientas nativas de control de pantalla/ratón (PyAutoGUI) desde el navegador tendrán limitaciones o requerirán permisos especiales que el servidor backend deberá manejar de forma segura.

## 5. Preguntas Abiertas

Por favor, ayúdame a decidir sobre los siguientes puntos antes de comenzar a escribir código:

1. **El Frontend (Stack Tecnológico):** ¿Prefieres que usemos **HTML/JS puro** (para mantener las cosas simples sin necesidad de Node.js) o prefieres que armemos un proyecto moderno usando un framework como **React, Next.js o Vite** para que quede espectacular visualmente?
2. **Distribución del Frontend:** Si elegimos una UI web, ¿quieres que FastAPI sirva estos archivos estáticos (todo arranca con un solo comando de Python) o prefieres correr dos comandos separados (`python -m jarvis --serve-api` y `npm run dev`)?
