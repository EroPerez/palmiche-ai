# Configuración del Front-End (Palmiche JARVIS Web UI)

Esta guía documenta los pasos necesarios para instalar, configurar e iniciar la interfaz web de Palmiche JARVIS.

El front-end está construido utilizando **Vue 3**, **Vite** y **Tailwind CSS**, y reside dentro del paquete principal en `jarvis/www/`.

## Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:

- **Python** (versión 3.10 o superior) con las dependencias web instaladas:

  ```bash
  pip install 'palmiche-jarvis[web]'
  ```

- **Node.js** (versión 18.0 o superior) — solo para desarrollo del frontend.
- **pnpm** (recomendado como gestor de paquetes):

  ```bash
  npm install -g pnpm
  ```

## Modo Producción

Compila el frontend y sirve todo desde FastAPI:

```bash
cd jarvis/www
pnpm install
pnpm run build
cd ../..
python -m jarvis --web
```

La interfaz estará disponible en `http://127.0.0.1:8000`.

## Modo Desarrollo (Hot-Reload)

Inicia el backend FastAPI y el dev server de Vite en paralelo:

```bash
cd jarvis/www && pnpm install && cd ../..
python -m jarvis --web-dev
```

- Backend API: `http://127.0.0.1:8000`
- Frontend Vite: `http://localhost:3000` (con HMR)

También puedes iniciar el frontend manualmente:

```bash
cd jarvis/www
pnpm run dev
```

## Conexión con el Backend (Jarvis Core)

La interfaz se comunica en tiempo real con el backend de Python a través de WebSockets.
Por defecto, se conecta a:

```
ws://localhost:8000/ws/chat
```

Asegúrate de que el backend esté ejecutándose (`python -m jarvis --web`) para que la interfaz pase del estado *Offline* a *Online*.

## Modos de UI disponibles

| Modo | Comando | Descripción |
|------|---------|-------------|
| CLI | `python -m jarvis` | Terminal interactivo (Rich) |
| Tray | `python -m jarvis --tray` | Bandeja del sistema (PyQt6/PyQt5) |
| Web | `python -m jarvis --web` | Navegador (FastAPI + Vue 3) |
| Web Dev | `python -m jarvis --web-dev` | Desarrollo con hot-reload |
