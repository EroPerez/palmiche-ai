# Plan de Implementación: Waveform de Voz de Jarvis (Versión 2)

El objetivo es añadir una indicación visual animada circular tipo "Waveform Líquido" que se mostrará en el centro inferior de la pantalla cuando Jarvis esté hablando.

## Cambios Propuestos

### 1. El Reto del Análisis de Audio (Importante)
Actualmente utilizamos `window.speechSynthesis` (la voz nativa del navegador) para reproducir la voz de Jarvis. 
**Limitación técnica del navegador:** La API de `speechSynthesis` es ejecutada por el sistema operativo y *no permite* interceptar el flujo de audio puro para analizar las frecuencias (bajos, agudos) con un `AnalyserNode`. 

**Solución Propuesta:** Para lograr la fluidez "líquida" sin tener que reescribir todo el motor de voz al backend, crearé un algoritmo matemático/CSS que **simule** la reactividad de la voz. El componente generará pulsos orgánicos y fluidos aleatorios pero rítmicos mientras `isSpeaking` sea verdadero, dando la ilusión perfecta de que está reaccionando a las sílabas y los bajos.

### 2. Nuevo Componente Visual: `LiquidWaveform.vue`
#### [NEW] [LiquidWaveform.vue](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/src/components/LiquidWaveform.vue)
- Se creará un componente aislado que renderice un "Blob Líquido" (Liquid Waveform).
- Usaremos múltiples capas (divs superpuestos) con `border-radius` variables y animaciones CSS que rotan e interactúan para crear un efecto de "esfera de agua" o "plasma" que palpita.
- Color base: Colores neón (Cyan/Indigo) heredados del diseño actual.

### 3. Ubicación y Estado Reactivo
#### [MODIFY] [App.vue](file:///home/maochoa/Projects/Palmiche_JARVIS/palmiche-ai/www/src/App.vue)
- Añadir la variable reactiva `const isSpeaking = ref(false)`.
- Modificar `speakText` para usar los eventos `onstart` y `onend` para alternar este estado.
- Importar `<LiquidWaveform />` y colocarlo con posición absoluta en la parte **inferior central** (`bottom-10 left-1/2 -translate-x-1/2`), usando la transición suave.

## User Review Required

> [!WARNING]
> No he podido recibir la imagen adjunta que mencionaste (los canales del chat a veces filtran archivos multimedia), pero entiendo perfectamente la referencia de "Waveform líquido y circular".
> 
> **Pregunta Crítica:** ¿Estás de acuerdo con **simular** orgánicamente las ondas de voz (con animaciones muy fluidas y pulsos artificiales) debido a la limitación nativa del navegador, o prefieres que iniciemos un rediseño mayor moviendo la síntesis de voz al backend de Python para extraer las frecuencias reales? (Recomiendo la simulación, ¡queda sorprendentemente realista y fluida!).
