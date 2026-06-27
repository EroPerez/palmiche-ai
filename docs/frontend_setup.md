# Configuración del Front-End (Palmiche JARVIS UI)

Esta guía documenta los pasos necesarios para instalar, configurar e iniciar la interfaz web de Palmiche JARVIS.

El front-end está construido utilizando **Vue 3**, **Vite** y **Tailwind CSS**.

## 📌 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:

- **Node.js** (versión 18.0 o superior).
- **pnpm** (recomendado como gestor de paquetes para este proyecto). Si no lo tienes instalado, puedes hacerlo ejecutando:

  ```bash
  npm install -g pnpm
  ```

## 🛠️ Instalación de Dependencias

Todo el código de la interfaz de usuario reside dentro del directorio `www/`. Para instalar las dependencias, navega a este directorio e instala los paquetes:

```bash
cd www
pnpm install
```

## 🚀 Inicio en Entorno de Desarrollo

Para iniciar el entorno de desarrollo con Hot Module Replacement (HMR) y Vite, tienes dos opciones:

### Opción 1: Usar el script de ayuda (Recomendado desde la raíz)

Desde el directorio raíz del proyecto (`palmiche-ai`), puedes ejecutar directamente el script Bash destinado a levantar el frontend:

```bash
./run_web_dev.sh
```

### Opción 2: Usar pnpm (Desde el directorio `www/`)

```bash
cd www
pnpm run dev
```

Esto iniciará el servidor de desarrollo, y la interfaz estará disponible por defecto en `http://localhost:5173`.

## 📦 Compilación para Producción

Si necesitas generar la compilación de producción estática de la interfaz (los archivos minificados y optimizados se generarán en `www/dist/`):

### Opción 1: Usar el script de ayuda

Desde el directorio raíz:

```bash
./run_web_prod.sh
```

### Opción 2: Usar pnpm

```bash
cd www
pnpm run build
```

## 🔌 Conexión con el Backend (Jarvis Core)

La interfaz se comunica de forma bidireccional y en tiempo real con el backend de Python a través de WebSockets.
Por defecto, la interfaz intenta conectarse a la siguiente dirección:

```
ws://localhost:8000/ws/chat
```

Asegúrate de que el núcleo de Jarvis (Backend) esté ejecutándose (`./run_jarvis.sh` o `python run_jarvis.py`) en el puerto 8000 para que la interfaz pase del estado *Offline* a *Online* y puedas interactuar, ver animaciones y enviar/recibir comandos de voz.
