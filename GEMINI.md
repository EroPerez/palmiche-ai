# Palmiche JARVIS - AI Agent Context

Este archivo (`GEMINI.md`) provee contexto esencial sobre la arquitectura, stack tecnológico y convenciones de desarrollo de **Palmiche JARVIS** para cualquier agente de inteligencia artificial que colabore en el proyecto.

## 📌 Visión General del Proyecto

**J.A.R.V.I.S** (Just A Rather Very Intelligent System) es un asistente personal de IA para escritorio. Está compuesto por un núcleo (backend) robusto en Python y una interfaz web moderna construida con Vue 3.

El sistema soporta múltiples integraciones: LLMs (Anthropic, Gemini, LiteLLM), reconocimiento y síntesis de voz, WebSockets para comunicación en tiempo real, Model Context Protocol (MCP) y herramientas de control de sistema operativo (computer-use).

## 🛠️ Stack Tecnológico

### Backend (Python)

- **Lenguaje:** Python >= 3.10
- **Dependencias Base:** `anthropic`, `rich`, `python-dotenv`, `psutil`.
- **Módulos Opcionales (Features):**
  - **Voz:** `SpeechRecognition`, `pyttsx3`, `gtts`.
  - **Servidor / WebSockets:** `fastapi`, `uvicorn` (A2A).
  - **Agentes / MCP:** `mcp`, `google-adk`, `litellm`.
  - **Computer Use:** `playwright`, `pyautogui`, `mss`.
- **Gestión de Paquetes:** `hatchling` (vía `pyproject.toml`).
- **Linting:** `ruff`.

### Frontend (`jarvis/www/`)

- **Framework:** Vue 3 (Composition API / `<script setup>`).
- **Build Tool:** Vite.
- **Gestor de Paquetes:** `pnpm`.
- **Estilos:** Tailwind CSS v3.
- **Tipografía:** Google Sans Flex (variable font).
- **Animaciones:** `animejs`.

## 📁 Estructura del Proyecto

- `/jarvis/`: Código fuente del backend en Python (modelos, integraciones, API, utilidades).
  - `/jarvis/interface/`: Implementaciones de UI (CLI, tray, web).
  - `/jarvis/api/`: Backend FastAPI (routers, schemas) para la Web UI.
  - `/jarvis/www/`: Código fuente del frontend (aplicación web Vue 3).
    - `/jarvis/www/src/components/`: Componentes Vue modulares (ej. `ChatMessage.vue`, `TypingIndicator.vue`, `SiriAnimation.vue`).
- `run_jarvis.sh` / `run_jarvis.py`: Scripts de inicio del backend.
- `pyproject.toml`: Configuración principal de dependencias Python.

## 🎨 Convenciones de Desarrollo (Frontend)

1. **Tailwind CSS Primero:** No utilices bloques `<style scoped>` de CSS/SCSS a menos que sea estrictamente necesario para animaciones complejas (como `SiriAnimation.vue`). Utiliza las clases utilitarias de Tailwind.
2. **Componentización:** Mantén `App.vue` limpio. Si un bloque de la interfaz (como los mensajes o los indicadores) crece demasiado, extráelo a un componente independiente en `/jarvis/www/src/components/`.
3. **Diseño Visual:** El proyecto sigue un estilo corporativo/moderno ("Professional UI"): paletas oscuras (`zinc`), bordes redondeados (`rounded-2xl`), efectos de vidrio translucido (`backdrop-blur-md`, `bg-opacity`), y uso intensivo de la fuente *Google Sans Flex*.
4. **Interactividad:** Los elementos deben tener estados claros de `:hover` y `:disabled` (opacidad reducida o cursor bloqueado) con transiciones suaves (`transition-all duration-300`).

## ⚙️ Notas Técnicas para Agentes IA

- Si vas a ejecutar comandos de instalación para el frontend, recuerda usar `pnpm` en lugar de `npm`.
- La comunicación entre el frontend y el backend se realiza mediante WebSockets en `ws://localhost:8000/ws/chat`. Cualquier cambio en la estructura de los payloads (`data.type === 'start' | 'stream' | 'end' | 'error'`) requiere sincronización entre el cliente Vue y el servidor FastAPI.
