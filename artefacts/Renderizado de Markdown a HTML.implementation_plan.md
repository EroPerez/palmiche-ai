# Renderizado de Markdown a HTML

El objetivo es permitir que la interfaz de usuario interprete correctamente las respuestas de la IA que vienen en formato Markdown (negritas, listas, bloques de código, etc.) y las renderice como HTML estilizado.

## Cambios Propuestos

### 1. Dependencias
Se instalarán dos nuevos paquetes en el directorio `www/`:
- `marked`: Una librería ligera y rápida para parsear el texto Markdown a HTML.
- `@tailwindcss/typography`: Un plugin oficial de Tailwind CSS que proporciona un conjunto de clases (`prose`) para estilizar automáticamente cualquier bloque de HTML puro que no tenga clases utilitarias de Tailwind, dándole un formato hermoso a los encabezados, listas, código y texto.

### 2. Configuración
#### [MODIFY] [tailwind.config.js](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/tailwind.config.js)
- Agregar `require('@tailwindcss/typography')` a la lista de plugins.

### 3. Componentes
#### [MODIFY] [ChatMessage.vue](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/src/components/ChatMessage.vue)
- Importar `marked`.
- En lugar de usar `{{ msg.content }}` para los mensajes del asistente, usaremos la directiva `v-html="parsedContent"`.
- Aplicar las clases `prose prose-invert prose-cyan max-w-none` (o similares) al contenedor del mensaje para que herede todo el estilo moderno de Tailwind. 
- Los mensajes del usuario pueden mantenerse como texto plano para evitar que si el usuario escribe algo parecido a markdown o HTML se renderice incorrectamente.

## User Review Required

> [!IMPORTANT]
> - ¿Estás de acuerdo con usar `marked` y el plugin de tipografía de Tailwind?
> - ¿Te parece bien si el formateo de Markdown se aplica únicamente a los mensajes del Asistente y del Sistema, manteniendo los del usuario como texto plano?
