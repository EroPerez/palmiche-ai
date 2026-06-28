# Migración a Progressive Web App (PWA) para Jarvis

El objetivo es convertir la interfaz web actual de Jarvis, desarrollada en Vue 3 con Vite, en una Progressive Web App (PWA). Esto permitirá instalar Jarvis como una aplicación nativa en el sistema (escritorio y móvil), trabajar en modo offline o con caché, y mejorar el rendimiento de carga.

## User Review Required

> [!IMPORTANT]
> **Íconos de la aplicación:** Para que la PWA sea instalable, se requieren íconos de la aplicación en dimensiones específicas (típicamente 192x192 y 512x512). Actualmente no tenemos íconos en el proyecto. Puedo generar un ícono base con IA (estilo Jarvis) y redimensionarlo, o puedes proporcionar uno propio más adelante. ¿Estás de acuerdo con generar un ícono base con IA?

> [!NOTE]
> **Estrategia de Actualización:** El plan propone usar `autoUpdate`, lo cual actualizará el Service Worker automáticamente en segundo plano cuando detecte cambios, sin que el usuario tenga que recargar la página explícitamente para obtener la nueva versión de inmediato. Esto es ideal para un asistente de IA.

## Open Questions

1. ¿Te gustaría añadir algún prompt visual en la interfaz de usuario (por ejemplo, un botón "Instalar Jarvis") en caso de que el usuario no lo instale directamente desde el navegador, o prefieres dejarlo solo como opción nativa del navegador?

## Proposed Changes

### Dependencias y Configuración

#### [MODIFY] [package.json](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/package.json)
Se instalará la dependencia `@vite-pwa/vite-plugin` (como `devDependencies`) usando `pnpm`.

#### [MODIFY] [vite.config.js](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/vite.config.js)
Se configurará el plugin `VitePWA` con los datos del manifiesto de la aplicación (nombre "Palmiche JARVIS", descripción, colores del tema `theme_color` que hagan juego con la UI actual, etc.).

---

### Recursos (Assets)

#### [NEW] [pwa-192x192.png](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/public/pwa-192x192.png)
#### [NEW] [pwa-512x512.png](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/public/pwa-512x512.png)
Se crearán estos íconos generados para cumplir con los requisitos del manifiesto de la PWA y permitir la instalación.

---

### Registro del Service Worker

Al configurar el plugin en modo `registerType: 'autoUpdate'`, el service worker se registrará e inyectará automáticamente en el `index.html`. No se requerirá código extra en el entrypoint de Vue (a menos que implementemos prompts personalizados de instalación/actualización).

## Verification Plan

### Manual Verification
1. Abrir la aplicación web en Chrome/Edge.
2. Verificar que en la barra de direcciones o en el menú aparece la opción "Instalar aplicación".
3. Revisar la pestaña "Application" -> "Manifest" en las Chrome DevTools para confirmar que el manifiesto carga correctamente sin errores y que el Service Worker se registra y activa.
4. Simular modo "Offline" en DevTools y verificar que la interfaz de la aplicación carga gracias a la caché local.
