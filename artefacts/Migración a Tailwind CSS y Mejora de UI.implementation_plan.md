# Migración a Tailwind CSS y Mejora de UI

El objetivo de este plan es migrar el front-end a Tailwind CSS para eliminar el CSS redundante, mejorar la interfaz de usuario con un diseño más moderno y profesional, y asegurar que no se rompa la funcionalidad actual ni el componente `SiriAnimation.vue`.

## User Review Required

> [!IMPORTANT]
> **Instalación Manual Requerida:** Debido a problemas previos de conexión en la terminal integrada, necesitaré que ejecutes algunos comandos manualmente (`npm install tailwindcss postcss autoprefixer`) una vez que apruebes este plan.
> 
> **Estética del Diseño:** El rediseño utilizará la paleta oscura de Tailwind (tonos "zinc" o "slate") con acentos azules/índigo modernos, bordes redondeados suaves, y efectos sutiles de vidrio (glassmorphism) en la cabecera. ¿Estás de acuerdo con este enfoque visual?

## Proposed Changes

### Dependencias y Configuración

#### [MODIFY] [package.json](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/package.json)
- Se agregarán `tailwindcss`, `postcss`, y `autoprefixer` a las `devDependencies`.

#### [NEW] [tailwind.config.js](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/tailwind.config.js)
- Archivo de configuración básico de Tailwind para analizar los archivos `.vue`, `.js` y `.html`.

#### [NEW] [postcss.config.js](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/postcss.config.js)
- Archivo para integrar Tailwind CSS en el pipeline de Vite.

---

### Estilos Globales

#### [MODIFY] [style.scss](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/src/style.scss)
- Se eliminará el CSS básico redundante (resets de body, `#app`, etc.).
- Se añadirán las directivas de Tailwind (`@tailwind base; @tailwind components; @tailwind utilities;`).
- Se mantendrán solo configuraciones esenciales como la tipografía y el fondo global (o se delegará a Tailwind).

---

### Componentes

#### [MODIFY] [App.vue](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/src/App.vue)
- **Eliminación de CSS:** Se borrará por completo el bloque `<style lang="scss" scoped>`.
- **Refactorización de la Plantilla:** Se reemplazarán las clases antiguas por clases utilitarias de Tailwind.
- **Mejora de UI:** 
  - La cabecera tendrá un diseño tipo *glassmorphism* con `backdrop-blur`.
  - El área de chat tendrá mejor espaciado y burbujas de mensaje con diseños asimétricos modernos.
  - Los botones de micrófono y enviar tendrán transiciones suaves, sombras sutiles (drop-shadow), y estados `:hover`/`:disabled` pulidos.

#### [NO CAMBIOS] [SiriAnimation.vue](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/src/components/SiriAnimation.vue)
- Este componente se mantendrá exactamente igual, tal como solicitaste.

## Verification Plan

### Manual Verification
1. Una vez ejecutados los comandos y el código, recargaremos la página.
2. Comprobaremos que la interfaz carga sin CSS roto y que luce más profesional.
3. Probaremos enviar un mensaje para ver que el layout y animaciones siguen funcionando correctamente.
4. Verificaremos que la animación de Siri siga viéndose bien dentro del nuevo diseño general.
