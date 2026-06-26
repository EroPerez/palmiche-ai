# Guía de herramientas — Palmiche J.A.R.V.I.S.

Referencia completa de las **59 herramientas** disponibles, con ejemplos de uso conversacional y preguntas frecuentes (FAQ) para cada categoría.

---

## Índice

1. [Sistema](#1-sistema)
2. [Aplicaciones y procesos](#2-aplicaciones-y-procesos)
3. [Archivos y directorios](#3-archivos-y-directorios)
4. [Red y conectividad](#4-red-y-conectividad)
5. [Medios](#5-medios)
6. [Capturas de pantalla](#6-capturas-de-pantalla)
7. [Web](#7-web)
8. [Portapapeles y notificaciones](#8-portapapeles-y-notificaciones)
9. [Clima](#9-clima)
10. [Notas](#10-notas)
11. [Temporizadores y alarmas](#11-temporizadores-y-alarmas)
12. [Calculadora y conversión de unidades](#12-calculadora-y-conversión-de-unidades)
13. [Herramientas de texto](#13-herramientas-de-texto)
14. [Calendario y eventos](#14-calendario-y-eventos)
15. [Developer](#15-developer)
16. [Sistema — energía y autoarranque](#16-sistema--energía-y-autoarranque)
17. [Computer Use ★](#17-computer-use-)
18. [Herramientas externas (MCP y agentes A2A)](#18-herramientas-externas-mcp-y-agentes-a2a)

---

## 1. Sistema

### `get_system_info`

Devuelve uso de CPU, RAM, espacio en disco y tiempo de actividad del sistema.

**Ejemplos de uso:**
```
¿Cómo está el sistema?
¿Cuánta RAM estoy usando?
Muéstrame el estado de la CPU y el disco
¿Cuánto tiempo lleva encendido el ordenador?
```

**FAQ:**

**¿Qué datos exactamente devuelve?**
Uso de CPU (porcentaje global), RAM (usada/total/porcentaje), disco de la partición raíz (usado/total/porcentaje) y uptime del sistema.

**¿Puedo ver el uso de una partición distinta a raíz?**
No directamente; usa `run_shell_command` con `df -h /ruta` para particiones específicas.

**¿Con qué frecuencia se actualiza?**
Cada vez que haces la consulta — no hay monitoreo continuo.

---

### `get_battery_info`

Estado de la batería: porcentaje, si está cargando/descargando y tiempo estimado restante.

**Ejemplos de uso:**
```
¿Cuánta batería me queda?
¿Está cargando el portátil?
¿Cuánto tiempo de batería tengo?
```

**FAQ:**

**¿Funciona en ordenadores de escritorio?**
En equipos sin batería devuelve un mensaje indicando que no hay batería detectada.

**¿El tiempo restante es exacto?**
Es una estimación del sistema operativo basada en el consumo actual; puede variar si cambias la carga de trabajo.

---

### `control_volume`

Controla el volumen del sistema: obtener nivel, establecer un valor exacto, subir, bajar, silenciar o desilenciar.

**Acciones disponibles:** `get` `set` `up` `down` `mute` `unmute`

**Ejemplos de uso:**
```
¿A qué volumen está el sistema?
Sube el volumen al 80%
Baja el volumen 10 puntos
Silencia el audio
Quita el silencio
Pon el volumen al 50%
```

**FAQ:**

**¿Requiere algún programa externo?**
En Linux usa `pactl` (PulseAudio/PipeWire). En macOS usa `osascript` (integrado). Si `pactl` no está disponible devuelve un error con instrucciones de instalación.

**¿`up` y `down` reciben un número?**
Sí, puedes especificar el incremento: "sube el volumen 15 puntos" → `action=up, value=15`. Si no indicas valor, el incremento por defecto es 10.

**¿Puedo silenciar solo una aplicación?**
No; esta herramienta controla el volumen maestro del sistema.

---

### `control_brightness`

Controla el brillo de la pantalla (solo Linux con `brightnessctl` instalado).

**Acciones disponibles:** `get` `set` `up` `down`

**Ejemplos de uso:**
```
¿Cuánto brillo tiene la pantalla?
Pon el brillo al 70%
Baja el brillo 20 puntos
Brillo máximo
```

**FAQ:**

**¿Funciona en macOS?**
No actualmente; `brightnessctl` es exclusivo de Linux. En macOS devuelve un mensaje de no compatibilidad.

**¿Por qué no funciona aunque tengo `brightnessctl` instalado?**
El usuario que ejecuta Jarvis necesita permisos de escritura al dispositivo de backlight. Ejecuta `sudo usermod -aG video $USER` y reinicia sesión.

**`set 100` no llega al brillo máximo visual**
Algunos monitores externos tienen su propio control de brillo independiente del sistema operativo. Esta herramienta solo controla el backlight de la pantalla integrada.

---

## 2. Aplicaciones y procesos

### `open_application`

Abre una aplicación o programa por nombre o comando.

**Ejemplos de uso:**
```
Abre Firefox
Inicia el editor de código
Abre la calculadora del sistema
Lanza Spotify
Abre el explorador de archivos
```

**FAQ:**

**¿Cómo sabe Jarvis qué comando usar?**
Lanza el nombre tal como lo escribiste. Si el binario está en el `PATH` del sistema, funciona. Si no, el sistema devuelve un error.

**¿Puedo pasar argumentos?**
Sí, por ejemplo: "abre firefox con la URL google.com". Jarvis incluirá el argumento al lanzar el proceso.

**La app se abre pero Jarvis dice que hubo un error**
Algunos programas escriben en stderr al arrancar (mensajes de Qt, advertencias de GTK…) sin ser un error real. La herramienta usa `Popen` en segundo plano — si el proceso arranca, la app debería aparecer.

---

### `close_application`

Termina un proceso por nombre. Por defecto envía SIGTERM (cierre limpio); con `force=true` envía SIGKILL.

**Ejemplos de uso:**
```
Cierra Firefox
Termina el proceso de Spotify
Fuerza el cierre de vlc
Mata el proceso python
```

**FAQ:**

**¿Cierra todos los procesos con ese nombre?**
Sí, termina todos los procesos cuyo nombre coincida (parcialmente) con el indicado.

**¿Cuándo usar `force`?**
Cuando el proceso no responde a SIGTERM. Úsalo con cuidado ya que no da tiempo a guardar datos.

**¿Puedo cerrar por PID?**
No directamente; usa `run_shell_command` con `kill -9 <PID>` si necesitas precisión por PID.

---

### `list_running_apps`

Lista los procesos en ejecución con su uso de memoria.

**Ejemplos de uso:**
```
¿Qué aplicaciones están corriendo?
¿Qué procesos están consumiendo más memoria?
¿Hay algún proceso de Python activo?
Muéstrame los procesos de Firefox
```

**FAQ:**

**¿Muestra todos los procesos del sistema?**
Muestra los procesos más relevantes ordenados por uso de memoria. Los procesos del kernel y de sistema suelen filtrarse.

**¿Puedo filtrar por nombre?**
Sí: "¿hay algún proceso de python?" → `filter=python`.

---

## 3. Archivos y directorios

### `search_files`

Busca archivos o directorios en el sistema de archivos por nombre o patrón glob.

**Ejemplos de uso:**
```
Busca archivos PDF en ~/Documentos
¿Dónde están los archivos .log del sistema?
Encuentra todos los archivos llamados "config.json"
Busca carpetas llamadas "node_modules" en ~/proyectos
```

**FAQ:**

**¿Qué profundidad de búsqueda tiene?**
Máximo 6 niveles de profundidad para evitar búsquedas lentas en árboles grandes.

**¿Soporta comodines?**
Sí, patrones glob como `*.pdf`, `config*`, `*.{js,ts}`.

**¿Busca en archivos ocultos?**
Sí, incluye directorios y archivos ocultos (que comienzan con `.`).

---

### `read_file`

Lee el contenido de un archivo de texto (hasta N líneas, por defecto 100).

**Ejemplos de uso:**
```
Lee el archivo ~/notas.txt
Muéstrame las primeras 50 líneas de ~/config.py
¿Qué hay en ~/.bashrc?
```

**FAQ:**

**¿Funciona con archivos binarios?**
No; está diseñado para archivos de texto. Los binarios se mostrarán como caracteres ilegibles.

**¿Puedo leer más de 100 líneas?**
Sí, especifica el número: "lee las primeras 500 líneas de archivo.log".

**El archivo tiene miles de líneas, ¿cómo busco algo específico?**
Pide a Jarvis que use `run_shell_command` con `grep "término" archivo.txt`.

---

### `write_file`

Escribe o agrega contenido a un archivo de texto.

**Modos:** `write` (sobrescribe) · `append` (agrega al final)

**Ejemplos de uso:**
```
Escribe "Hola mundo" en ~/prueba.txt
Agrega esta línea al final de ~/diario.txt: "Hoy fue un buen día"
Crea un archivo ~/script.sh con este contenido: ...
```

**FAQ:**

**¿Sobrescribe el archivo si ya existe?**
Con modo `write` sí. Si solo quieres agregar, especifica "agrega" o "append".

**¿Crea los directorios padre si no existen?**
No; usa `create_directory` primero si la ruta no existe.

---

### `list_directory`

Lista el contenido de un directorio (hasta 40 elementos, directorios primero).

**Ejemplos de uso:**
```
Lista los archivos en ~/Documentos
¿Qué hay en el escritorio?
Muéstrame los archivos ocultos de mi home
```

**FAQ:**

**¿Por qué solo veo 40 elementos?**
Para evitar respuestas excesivamente largas. Si necesitas ver más, usa `run_shell_command` con `ls -la ~/ruta | head -100`.

**¿Incluye archivos ocultos?**
Por defecto no. Pide explícitamente "muéstrame los archivos ocultos" para incluirlos.

---

### `delete_file` · `move_file` · `copy_file` · `create_directory` · `open_file`

Operaciones estándar de gestión de archivos.

**Ejemplos de uso:**
```
Elimina ~/Descargas/archivo_viejo.zip
Mueve ~/Descargas/foto.jpg a ~/Imágenes/vacaciones/
Copia el informe.pdf a ~/Backups/
Crea la carpeta ~/proyectos/nuevo-app
Abre el PDF ~/Documentos/manual.pdf
```

**FAQ — `delete_file`:**
¿Puedo recuperar un archivo eliminado? No, la eliminación es permanente (no va a la papelera). Confirma antes de pedir que Jarvis borre algo importante.

**FAQ — `open_file`:**
Usa la aplicación predeterminada del sistema (`xdg-open` en Linux, `open` en macOS). Si no hay app asociada al tipo de archivo, puede no abrirse.

---

## 4. Red y conectividad

### `get_network_info`

Muestra IP local, IP pública, SSID de la red WiFi y nivel de señal.

**Ejemplos de uso:**
```
¿Cuál es mi dirección IP?
¿A qué red WiFi estoy conectado?
¿Cuál es mi IP pública?
Dame información de red
```

**FAQ:**

**¿La IP pública se obtiene de internet?**
Sí, hace una petición a un servicio externo. Puede fallar sin conexión.

**¿Funciona con conexión por cable (Ethernet)?**
Sí; en ese caso el campo SSID aparecerá vacío o como "cable".

---

### `ping_host`

Envía paquetes ICMP a un host y devuelve latencia y pérdida de paquetes.

**Ejemplos de uso:**
```
Haz ping a google.com
¿Responde el servidor 192.168.1.1?
Comprueba la conexión con cloudflare.com con 10 paquetes
```

**FAQ:**

**¿Cuántos paquetes envía por defecto?**
4 paquetes. Puedes cambiarlo: "haz 10 pings a google.com".

**Dice que el host no responde pero la web carga bien**
Algunos servidores bloquean ICMP por firewall. La falta de respuesta al ping no implica que el servicio esté caído.

---

## 5. Medios

### `media_control`

Controla la reproducción de medios del sistema.

**Acciones disponibles:** `play` `pause` `next` `previous` `stop`

**Ejemplos de uso:**
```
Pausa la música
Pon la siguiente canción
Para la reproducción
Reanuda la música
Vuelve a la canción anterior
```

**FAQ:**

**¿Con qué reproductores funciona?**
En Linux usa `playerctl`, que es compatible con Spotify, VLC, Rhythmbox, mpv y cualquier reproductor que implemente MPRIS. En macOS controla Music.app vía AppleScript.

**¿Puedo controlar YouTube en el navegador?**
Solo si el navegador expone controles MPRIS (algunos no lo hacen por defecto).

---

### `get_media_status`

Devuelve el título y artista del track en reproducción.

**Ejemplos de uso:**
```
¿Qué canción está sonando?
¿Qué música estoy escuchando?
```

**FAQ:**

**Devuelve "sin reproducción activa" pero hay música**
Asegúrate de que el reproductor esté activo en el sistema. En Linux, `playerctl status` en terminal debería mostrar `Playing`.

---

## 6. Capturas de pantalla

### `take_screenshot`

Captura la pantalla completa o permite seleccionar un área.

**Ejemplos de uso:**
```
Toma una captura de pantalla
Haz un screenshot del escritorio
Captura solo una zona de la pantalla
Guarda la captura en ~/Imágenes/captura.png
```

**FAQ:**

**¿Dónde guarda el archivo?**
Por defecto en `~/screenshot_YYYYMMDD_HHMMSS.png`. Puedes indicar una ruta diferente.

**¿Requiere algún programa externo?**
En Linux usa `scrot` (`sudo apt install scrot`). En macOS usa `screencapture` (integrado).

**¿Funciona en modo bandeja (sin foco de ventana)?**
Sí, `scrot` captura el escritorio completo independientemente de qué ventana esté activa.

---

## 7. Web

### `open_url`

Abre una URL en el navegador predeterminado del sistema.

**Ejemplos de uso:**
```
Abre github.com
Abre https://news.ycombinator.com
Visita la página de documentación de Python
```

**FAQ:**

**¿Necesita el prefijo `https://`?**
No; si no incluyes esquema, se añade `https://` automáticamente.

---

### `web_search`

Abre una búsqueda en el navegador en modo incógnito/privado.

**Motores disponibles:** `google` (default) · `duckduckgo` · `youtube`

**Ejemplos de uso:**
```
Busca en Google "recetas de pasta"
Busca en YouTube tutoriales de Python
Busca en DuckDuckGo sin rastreo "privacidad en internet"
```

**FAQ:**

**¿Jarvis devuelve los resultados de búsqueda?**
No; abre el navegador con la búsqueda. Para leer resultados directamente, combina con `fetch_webpage`.

**¿Por qué modo incógnito?**
Para no guardar historial de navegación de las búsquedas lanzadas desde Jarvis.

---

### `fetch_webpage` *(nueva)*

Descarga una página web y extrae su texto legible (elimina HTML, scripts, estilos y navegación).

**Ejemplos de uso:**
```
Lee el artículo en https://example.com/noticia
¿Qué dice esta página? https://docs.python.org/3/library/os.html
Extrae el contenido de https://wikipedia.org/wiki/Inteligencia_artificial
Busca en DuckDuckGo y léeme el primer resultado
```

**FAQ:**

**¿Cuánto texto devuelve?**
Hasta 3.000 caracteres por defecto. Puedes pedir más: "lee hasta 8000 caracteres de esa página".

**No devuelve el contenido que espero**
Algunas páginas cargan contenido dinámicamente con JavaScript (React, Vue…). Esta herramienta descarga el HTML estático inicial. Para páginas con contenido dinámico, el resultado puede ser incompleto.

**¿Puede leer páginas detrás de un login?**
No; no gestiona sesiones ni cookies de autenticación.

**¿Funciona con PDFs en línea?**
No; está diseñado para `text/html` y `text/plain`. Para PDFs, descárgalos primero con `http_request` y luego usa `read_file`.

---

### `get_rss_feed` *(nueva)*

Obtiene las últimas entradas de un feed RSS 2.0 o Atom, devolviendo título, enlace y fecha.

**Ejemplos de uso:**
```
Muéstrame las últimas noticias de https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada
Dame las 5 últimas entradas del feed de Hacker News
¿Qué hay nuevo en el blog de Python? https://feeds.feedburner.com/PythonInsider
```

**FAQ:**

**¿Cuántas entradas muestra por defecto?**
10. Puedes cambiarlo: "muéstrame las últimas 20 entradas".

**¿Cuál es la diferencia entre RSS y Atom?**
Son dos formatos de feed. Jarvis detecta y parsea ambos automáticamente.

**¿Puedo suscribirme para recibir actualizaciones automáticas?**
No actualmente; cada consulta hace una petición puntual al feed. Para monitoreo continuo, combina con un temporizador periódico.

---

## 8. Portapapeles y notificaciones

### `get_clipboard` · `set_clipboard`

Lee y escribe en el portapapeles del sistema.

**Ejemplos de uso:**
```
¿Qué tengo en el portapapeles?
Copia esto al portapapeles: npm install palmiche-jarvis
Guarda este texto en el clipboard: [texto largo...]
```

**FAQ:**

**¿Funciona entre aplicaciones?**
Sí, modifica el portapapeles global del sistema (el mismo que usa Ctrl+C / Ctrl+V).

**¿Hay límite de tamaño?**
En la práctica no, aunque portapapeles muy grandes pueden tardar más.

---

### `send_notification`

Envía una notificación de escritorio con título, mensaje y nivel de urgencia.

**Urgencias:** `low` · `normal` (default) · `critical`

**Ejemplos de uso:**
```
Manda una notificación: "Reunión en 5 minutos"
Notifícame con urgencia crítica: "¡Memoria casi llena!"
Envía una notificación baja: "Descarga completada"
```

**FAQ:**

**¿Requiere algún programa en Linux?**
Sí, `notify-send` del paquete `libnotify-bin` (`sudo apt install libnotify-bin`).

**Las notificaciones no aparecen aunque `notify-send` está instalado**
Verifica que el servicio de notificaciones esté activo en tu escritorio. En entornos mínimos puede no haber daemon de notificaciones.

---

## 9. Clima

> No requiere API key. Datos vía [wttr.in](https://wttr.in) (servicio público gratuito).

### `get_weather` *(nueva)*

Clima actual: temperatura (con sensación térmica), humedad, viento, visibilidad, presión y rango del día.

**Ejemplos de uso:**
```
¿Qué tiempo hace hoy?
¿Cómo está el clima en Madrid?
¿Cuántos grados hay en Buenos Aires ahora?
Dame el clima en Tokio en Fahrenheit
¿Está lloviendo en Londres?
```

**FAQ:**

**¿Qué pasa si no indico ciudad?**
Detecta la ubicación automáticamente por IP. La precisión puede ser la de tu proveedor de internet, no tu ubicación exacta.

**¿En qué unidades devuelve la temperatura?**
En Celsius por defecto (sistema métrico). Escribe "en Fahrenheit" o "en imperial" para cambiar.

**¿Funciona sin conexión a internet?**
No; necesita conectarse a `wttr.in` para obtener los datos.

**Los datos no corresponden a mi ciudad exacta**
Prueba con el nombre en inglés o incluye el país: "Madrid, Spain" o "Santiago, Chile".

---

### `get_forecast` *(nueva)*

Pronóstico de 1 a 3 días: descripción del tiempo, temperatura máxima/mínima y precipitación total.

**Ejemplos de uso:**
```
¿Cómo estará el tiempo esta semana?
Dame el pronóstico de 3 días para Barcelona
¿Va a llover mañana en Sevilla?
Pronóstico de 2 días para Nueva York en imperial
```

**FAQ:**

**¿Puede dar más de 3 días?**
No; la API gratuita de wttr.in devuelve máximo 3 días.

**¿Qué significa "lluvia: X mm"?**
Es la precipitación total acumulada para ese día según el pronóstico.

---

## 10. Notas

> Almacenadas en `~/.jarvis_notes.json` (configurable con `JARVIS_NOTES_FILE`). Funcionan sin conexión.

### `create_note` *(nueva)*

Crea una nueva nota o actualiza el contenido de una existente con el mismo título.

**Ejemplos de uso:**
```
Crea una nota titulada "Ideas de proyecto" con el contenido: ...
Guarda esto como nota "Receta de pasta": ingredientes...
Actualiza la nota "Ideas de proyecto" con esto nuevo: ...
Crea una nota "Reunión lunes" con etiquetas: trabajo, urgente
```

**FAQ:**

**¿Qué pasa si ya existe una nota con ese título?**
Se actualiza el contenido y las etiquetas; el id y la fecha de creación se mantienen.

**¿Las etiquetas distinguen mayúsculas?**
No; las búsquedas por etiqueta son insensibles a mayúsculas.

**¿Puedo usar markdown en el contenido?**
Sí, el contenido se almacena como texto plano y Jarvis lo mostrará con formato si el terminal lo soporta.

---

### `list_notes` *(nueva)*

Lista todas las notas ordenadas por fecha de actualización (más recientes primero).

**Ejemplos de uso:**
```
¿Qué notas tengo guardadas?
Muéstrame las notas con etiqueta "trabajo"
Lista mis notas de "recetas"
¿Cuántas notas tengo?
```

**FAQ:**

**¿Cuántas notas muestra?**
Todas las que existan. Si tienes muchas, el resultado puede ser largo; usa filtros por etiqueta o `search_notes` para reducirlo.

---

### `read_note` *(nueva)*

Lee el contenido completo de una nota por título (búsqueda parcial) o id.

**Ejemplos de uso:**
```
Lee la nota "Ideas de proyecto"
Muéstrame la nota sobre la reunión del lunes
Abre la nota con id a1b2c3d4
```

**FAQ:**

**¿La búsqueda es exacta?**
No; busca primero por id exacto, luego por título exacto, y finalmente por coincidencia parcial del título. La primera coincidencia se devuelve.

**¿Puedo ver dos notas a la vez?**
No con un solo comando; haz dos peticiones separadas.

---

### `search_notes` *(nueva)*

Busca en título y contenido de todas las notas (insensible a mayúsculas).

**Ejemplos de uso:**
```
Busca en mis notas "presupuesto"
¿Tengo alguna nota que mencione "API key"?
Busca notas sobre "Python"
```

**FAQ:**

**¿Busca también en las etiquetas?**
No directamente; usa `list_notes` con filtro de etiqueta para eso.

**¿Soporta expresiones regulares?**
No; la búsqueda es texto literal, insensible a mayúsculas.

---

### `delete_note` *(nueva)*

Elimina una nota permanentemente por título o id.

**Ejemplos de uso:**
```
Elimina la nota "Borrador viejo"
Borra la nota con id a1b2c3d4
```

**FAQ:**

**¿Se puede deshacer?**
No; la eliminación es permanente. El archivo JSON se actualiza inmediatamente.

**¿Puedo eliminar todas las notas a la vez?**
No hay un comando masivo; hazlo nota a nota o borra directamente `~/.jarvis_notes.json` desde el terminal.

---

## 11. Temporizadores y alarmas

> Los temporizadores corren en hilos de fondo y disparan notificaciones de escritorio al completarse. Son volátiles: se pierden si el proceso termina.

### `set_timer` *(nueva)*

Inicia un temporizador por duración en segundos.

**Ejemplos de uso:**
```
Pon un temporizador de 25 minutos para el pomodoro
Avísame en 30 segundos
Temporizador de 1 hora para el horno
Pon un temporizador de 90 segundos llamado "pasta al dente"
```

**FAQ:**

**¿Cuál es la duración máxima?**
24 horas (86.400 segundos).

**¿Qué pasa cuando termina?**
Envía una notificación de escritorio con el nombre del temporizador. Si no hay daemon de notificaciones activo, la notificación no aparece (pero el temporizador sí terminó).

**¿Jarvis sigue respondiendo mientras corre el temporizador?**
Sí; el temporizador corre en un hilo de fondo y no bloquea la conversación.

**¿El temporizador sobrevive si cierro Jarvis?**
No; los temporizadores son en memoria. Si el proceso termina, se pierden. Para tareas programadas persistentes, usa `cron` del sistema.

**¿Cuántos temporizadores puedo tener activos simultáneamente?**
No hay límite fijo, pero cada uno ocupa un hilo del sistema.

---

### `set_alarm` *(nueva)*

Programa una alarma para una hora concreta del día en formato HH:MM (24h).

**Ejemplos de uso:**
```
Pon una alarma a las 08:30 para levantarme
Alarma a las 14:00 para la reunión
Recuérdame a las 23:59 que tengo que hacer algo
```

**FAQ:**

**¿Qué pasa si la hora ya pasó hoy?**
La alarma se programa para el mismo horario del día siguiente.

**¿Puedo poner una alarma para una fecha específica?**
No directamente; usa `add_event` en el calendario si necesitas recordatorios en fechas futuras.

**¿Funciona si el portátil está en suspensión?**
No; el proceso de Python debe estar activo. Si el sistema se suspende, el temporizador no disparará en la hora correcta.

---

### `list_timers` *(nueva)*

Muestra todos los temporizadores activos con tiempo restante en formato `HH:MM:SS`.

**Ejemplos de uso:**
```
¿Cuánto tiempo le queda al temporizador?
¿Qué temporizadores tengo activos?
```

**FAQ:**

**¿Por qué no aparece el temporizador que puse?**
Si el proceso de Jarvis se reinició, los temporizadores se perdieron. Crea uno nuevo.

---

### `cancel_timer` *(nueva)*

Cancela un temporizador activo por su id (6 caracteres hexadecimales).

**Ejemplos de uso:**
```
Cancela el temporizador abc123
Para el temporizador del pomodoro [id: f3a9c1]
```

**FAQ:**

**¿Dónde encuentro el id del temporizador?**
Se muestra al crearlo con `set_timer` o `set_alarm`, y también aparece en `list_timers`.

---

## 12. Calculadora y conversión de unidades

### `calculate` *(nueva)*

Evalúa expresiones matemáticas de forma segura usando el módulo `ast` de Python (sin `eval` directo). No puede ejecutar código arbitrario.

**Operadores:** `+` `-` `*` `/` `**` (potencia) `%` `//` (división entera)
**Funciones:** `sqrt` `cbrt` `sin` `cos` `tan` `asin` `acos` `atan` `atan2` `log` `log2` `log10` `exp` `abs` `round` `floor` `ceil` `factorial` `gcd` `hypot` `degrees` `radians` `min` `max`
**Constantes:** `pi` `e` `tau` `inf`
**Alias:** `×` → `*` · `÷` → `/` · `^` → `**`

**Ejemplos de uso:**
```
¿Cuánto es sqrt(144) + 2^10?
Calcula el factorial de 10
¿Cuánto es sin(pi/2)?
¿Cuánto es log(e)?
Calcula 3.14159 × 5²
¿Cuántos segundos hay en una semana? (7 * 24 * 60 * 60)
```

**FAQ:**

**¿Es seguro? ¿Puede ejecutar comandos del sistema?**
Sí, es seguro. El evaluador parsea la expresión como un árbol AST y solo permite nodos de tipo número, operadores aritméticos y las funciones de la lista blanca. Ningún acceso a módulos, importaciones ni llamadas del sistema.

**¿Soporta números complejos?**
No en las funciones, pero `sqrt(-1)` devuelve error; usa `1j` directamente si necesitas números complejos.

**¿Funciona con notación científica?**
Sí: `1.5e3` equivale a `1500`.

**¿Puede resolver ecuaciones?**
No; solo evalúa expresiones numéricas directas. Para álgebra simbólica, pide a Jarvis que use `run_shell_command` con Python y sympy.

---

### `convert_units` *(nueva)*

Convierte entre unidades de medida en las siguientes categorías.

| Categoría | Unidades disponibles |
|---|---|
| Longitud | `m` `km` `cm` `mm` `mi` `yd` `ft` `in` `nm` |
| Masa | `kg` `g` `mg` `lb` `oz` `t` (tonelada) |
| Temperatura | `°C` `celsius` `°F` `fahrenheit` `K` `kelvin` |
| Velocidad | `m/s` `km/h` `mph` `kt` (nudos) |
| Área | `m²` `km²` `ha` `acre` `ft²` `in²` `mi²` |
| Volumen | `l` `ml` `m³` `gal` `qt` `pt` `cup` |
| Almacenamiento digital | `B` `KB` `MB` `GB` `TB` `PB` `KiB` `MiB` `GiB` `TiB` |

**Ejemplos de uso:**
```
Convierte 100 km a millas
¿Cuántos pies son 1,80 metros?
Convierte 37°C a Fahrenheit
¿Cuántos nudos son 100 km/h?
Convierte 2.5 GB a MB
¿Cuántas libras son 75 kg?
Convierte 1 acre a metros cuadrados
```

**FAQ:**

**La unidad que necesito no está en la lista**
Abre un issue en el repositorio o añade el factor de conversión directamente en `jarvis/tools/calculator.py` en el diccionario `_UNITS`.

**¿Por qué temperatura usa fórmulas y no factores?**
Porque la conversión de temperatura es afín (implica suma/resta), no multiplicativa como el resto de unidades.

**¿Puedo encadenar conversiones?**
No directamente, pero puedes hacer dos peticiones: "convierte 5 millas a km, y ese resultado a metros".

---

## 13. Herramientas de texto

### `text_stats` *(nueva)*

Analiza un texto y devuelve estadísticas: palabras, caracteres (total y sin espacios), líneas, párrafos, oraciones y tiempo estimado de lectura.

**Ejemplos de uso:**
```
¿Cuántas palabras tiene este texto? [texto]
Analiza las estadísticas de mi redacción
¿Cuánto tiempo llevaría leer esto?
```

**FAQ:**

**¿Cómo calcula el tiempo de lectura?**
Usa una velocidad media de 200 palabras por minuto, que es la velocidad de lectura adulta estándar.

**¿Cómo cuenta las oraciones?**
Busca signos de puntuación finales (`.` `!` `?`). Puede no ser exacto con abreviaciones o puntos decimales.

---

### `text_transform` *(nueva)*

Aplica una transformación al texto de entrada.

| Operación | Resultado |
|---|---|
| `upper` | MAYÚSCULAS |
| `lower` | minúsculas |
| `title` | Primera Letra De Cada Palabra En Mayúscula |
| `capitalize` | Solo la primera letra en mayúscula |
| `reverse` | otxet le etreivnI |
| `trim` | Elimina espacios al inicio y final |
| `slug` | texto-listo-para-url (elimina acentos, espacios → guiones) |
| `snake` | texto_en_formato_snake_case |
| `camel` | textoEnFormatoCamelCase |
| `pascal` | TextoEnFormatoPascalCase |
| `strip_accents` | Elimina tildes y diacríticos (á→a, ñ→n…) |
| `count_vowels` | Cuenta las vocales del texto |
| `palindrome` | Comprueba si el texto es un palíndromo |

**Ejemplos de uso:**
```
Convierte "Hola Mundo" a snake_case
¿Es "anilina" un palíndromo?
Convierte este título a slug: "Guía de instalación de Ubuntu"
Pasa este nombre de clase a camelCase: "mi_variable_importante"
Elimina los acentos de este texto: "Ángel García Ramírez"
```

**FAQ:**

**`slug` vs `snake`: ¿cuál usar?**
`slug` genera identificadores para URLs (solo letras, números y guiones, sin acentos). `snake_case` usa guiones bajos y mantiene el idioma original.

**¿`palindrome` distingue espacios y signos?**
No; elimina todo excepto letras y números antes de comparar, por lo que "Anita lava la tina" se reconoce como palíndromo correctamente.

**¿`strip_accents` elimina la ñ?**
La ñ se convierte en `n`. Si solo quieres eliminar tildes (á→a) pero mantener caracteres como ñ, deberás post-procesar.

---

## 14. Calendario y eventos

> Almacenado en `~/.jarvis_events.json` (configurable con `JARVIS_EVENTS_FILE`). No requiere conexión ni cuentas externas.

### `add_event`

Crea un evento en el calendario local.

**Parámetros:** título (requerido), fecha `YYYY-MM-DD` o `hoy`/`mañana` (requerido), hora `HH:MM` (opcional), descripción (opcional), lugar (opcional).

**Ejemplos de uso:**
```
Agrega una cita al dentista mañana a las 10:30
Crea un evento "Cumpleaños de Ana" el 2026-07-15
Añade "Reunión de equipo" hoy a las 15:00 en la sala B
```

**FAQ:**

**¿Puedo crear eventos recurrentes?**
No; cada evento es puntual. Para eventos recurrentes, crea uno por cada fecha.

**¿Se sincronizan con Google Calendar?**
No; el calendario es completamente local. Para integración con Google Calendar, contribuye o usa un conector externo.

---

### `list_events` · `upcoming_events` · `delete_event`

**Ejemplos de uso:**
```
¿Qué eventos tengo esta semana?
Muéstrame los próximos 14 días de agenda
¿Tengo algo programado para julio?
Elimina el evento a3f2b1c4
```

**FAQ — `upcoming_events`:**
¿Cuántos días muestra por defecto? 7. Cambia con: "muéstrame los próximos 30 días".

**FAQ — `delete_event`:**
¿Dónde encuentro el id del evento? Aparece entre corchetes al listar eventos: `[a3f2b1c4]`.

---

## 15. Developer

### `format_json`

Valida y formatea JSON con indentación configurable.

**Ejemplos de uso:**
```
Formatea este JSON: {"name":"test","value":42}
Indenta este JSON con 4 espacios: [{"a":1},{"b":2}]
¿Es válido este JSON? {name: "test"}
```

**FAQ:**

**¿Qué pasa si el JSON es inválido?**
Devuelve el error de parsing con la posición del problema.

---

### `hash_text`

Calcula el hash criptográfico de un texto.

**Algoritmos:** `md5` · `sha1` · `sha256` (default) · `sha512`

**Ejemplos de uso:**
```
Calcula el SHA256 de "hola mundo"
¿Cuál es el MD5 de esta cadena?
Hash SHA512 de mi contraseña [texto]
```

**FAQ:**

**¿Puedo hashear archivos?**
No directamente; usa `read_file` para obtener el contenido y luego `hash_text`. Para archivos grandes, usa `run_shell_command` con `sha256sum archivo`.

---

### `encode_decode`

Codifica o decodifica texto en base64, URL-encoding o hexadecimal.

**Ejemplos de uso:**
```
Codifica en base64: "usuario:contraseña"
Decodifica este base64: dXN1YXJpbzpjb250cmFzZcOxYQ==
Codifica en URL: "búsqueda con espacios"
```

---

### `generate_uuid`

Genera uno o más UUID4 aleatorios.

**Ejemplos de uso:**
```
Genera un UUID
Dame 5 UUIDs
Necesito 10 identificadores únicos
```

---

### `convert_timestamp`

Convierte entre epoch Unix y formato ISO-8601, o devuelve la hora actual.

**Ejemplos de uso:**
```
¿Qué hora es ahora en epoch?
Convierte el timestamp 1719187200 a fecha
¿Qué epoch corresponde a 2026-06-24T12:00:00?
```

---

### `http_request`

Realiza peticiones HTTP y devuelve status, headers clave y preview del body. Ideal para probar APIs.

**Métodos:** `GET` (default) · `POST` · `PUT` · `DELETE` · `PATCH` · `HEAD`

**Ejemplos de uso:**
```
Haz un GET a https://api.github.com/zen
Prueba este endpoint: POST https://httpbin.org/post con body {"test": true}
¿Qué devuelve HEAD de https://example.com?
```

**FAQ:**

**¿Cuántos caracteres del body muestra?**
Hasta 1.000 caracteres. Para ver más, usa `fetch_webpage` que está optimizado para contenido HTML.

**¿Soporta autenticación?**
No directamente; añade el header manualmente usando `run_shell_command` con `curl -H "Authorization: Bearer TOKEN" ...`.

---

### `git_status`

Muestra rama actual, cambios en el árbol de trabajo y los últimos 5 commits de un repositorio.

**Ejemplos de uso:**
```
¿Cuál es el estado del repositorio actual?
Estado del repo en ~/proyectos/mi-app
¿En qué rama estoy?
¿Hay cambios sin commitear?
```

**FAQ:**

**¿Por qué path por defecto es "."?**
Usa el directorio de trabajo del proceso de Jarvis. Si lanzaste Jarvis desde tu repo, funcionará directamente.

---

### `find_process_on_port`

Identifica qué proceso está escuchando en un puerto TCP.

**Ejemplos de uso:**
```
¿Qué hay corriendo en el puerto 3000?
¿Qué proceso usa el puerto 8080?
¿Está libre el puerto 5432?
```

**FAQ:**

**¿Necesita permisos especiales?**
Para ver procesos de otros usuarios puede necesitar `sudo`. Los procesos del usuario actual siempre son visibles.

**¿Funciona con UDP?**
No; solo escanea conexiones TCP en estado LISTEN.

---

## 16. Sistema — energía y autoarranque

### `power_action`

Controla el estado de energía del sistema.

**Acciones:** `shutdown` · `restart` · `sleep` · `lock`

**Ejemplos de uso:**
```
Bloquea la pantalla
Pon el ordenador en suspensión
Apaga el sistema
Reinicia el ordenador
```

> **Nota de seguridad:** Las acciones `shutdown`, `restart` y `sleep` requieren confirmación explícita antes de ejecutarse. Jarvis pedirá confirmación y solo procederá cuando respondas afirmativamente.

**FAQ:**

**¿Por qué Jarvis pide confirmación antes de apagar?**
Son acciones destructivas e irreversibles. La confirmación es forzada en código (no solo en el prompt) para evitar ejecuciones accidentales.

**`shutdown` da error de autenticación en Linux**
Es un problema de permisos de polkit. Instala la regla incluida:
```bash
sudo jarvis/scripts/install-power-rules.sh
```

---

### `setup_autostart`

Configura Jarvis para arrancar automáticamente con el sistema operativo.

**Ejemplos de uso:**
```
Activa el arranque automático de Jarvis
Desactiva el autoarranque
Configura Jarvis para que arranque con el backend Ollama
```

**FAQ:**

**¿Dónde instala la entrada de autoarranque?**
En Linux crea un archivo `.desktop` en `~/.config/autostart/`. En macOS usa un LaunchAgent en `~/Library/LaunchAgents/`.

**¿Arranca en modo tray o terminal?**
Por defecto en modo tray (`--tray`). Puedes cambiarlo con el parámetro `tray=false`.

---

---

## 17. Computer Use ★

> Requiere `pip install "palmiche-jarvis[computer-use]"` y `GOOGLE_API_KEY` en `.env`.

### `computer_use_task`

Controla visualmente un **navegador Chromium** (backend `playwright`) o el **escritorio completo** (backend `desktop`) para completar tareas descritas en lenguaje natural. El agente usa Gemini para ver la pantalla y decide qué acciones ejecutar en cada paso.

Inspirado en [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview).

**Parámetros:**

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `task` | string | — | Tarea en lenguaje natural |
| `backend` | string | `"playwright"` | `"playwright"` (browser) o `"desktop"` (escritorio) |
| `initial_url` | string | `"https://www.google.com"` | URL de inicio (solo backend playwright) |
| `max_iterations` | integer | `30` | Límite de pasos del agente visual |

**Acciones que puede ejecutar Gemini:**

| Acción | Descripción |
|---|---|
| `click` / `double_click` / `triple_click` | Clic simple, doble o triple en coordenadas |
| `right_click` / `middle_click` | Clic secundario o con rueda |
| `type` | Escribir texto (con Enter opcional) |
| `scroll` | Desplazamiento en cualquier dirección con magnitud |
| `drag_and_drop` | Arrastrar desde origen a destino |
| `navigate` | Navegar a una URL |
| `go_back` / `go_forward` | Historial del navegador |
| `press_key` / `hotkey` | Tecla individual o combinación (Ctrl+C, Alt+F4…) |
| `take_screenshot` | Captura explícita para ver el estado |
| `wait` | Esperar N segundos |

**Ejemplos de uso:**
```
Busca el precio del Bitcoin hoy en el navegador
Abre YouTube y pon música de jazz
Navega a wikipedia.org y busca "Revolución cubana"
Rellena el formulario de contacto en example.com con nombre "Juan" y email "juan@test.com"
Ve a google.com, busca "mejores restaurantes en La Habana" y dime los 3 primeros resultados
Descarga la imagen de portada de la página https://example.com
```

**FAQ:**

**¿Necesito tener Chromium instalado previamente?**
No. Playwright descarga su propio Chromium al ejecutar `playwright install chromium`. No interfiere con el navegador del sistema.

**¿Funciona en modo headless? ¿Se abre alguna ventana?**
Por defecto sí, funciona en modo headless (sin ventana visible). Para depuración puedes pasar `headless=False` (solo desde Python directamente).

**¿Qué modelos de Gemini soportan computer use?**
El modelo recomendado es `gemini-2.5-flash`. Los modelos que soportan la API `ComputerUse` son los de la familia `gemini-2.5` y versiones específicas con soporte de computer use habilitado.

**¿El backend `desktop` puede controlar cualquier aplicación?**
Sí, puede controlar cualquier aplicación visible en el escritorio: navegadores, editores, apps nativas, etc. Requiere entorno gráfico (Xorg/Wayland).

**¿Es seguro?**
Gemini incluye detección de acciones sensibles y solicita confirmación del usuario antes de ejecutarlas. El agente también tiene un límite configurable de iteraciones (`COMPUTER_USE_MAX_ITERATIONS`) para evitar bucles infinitos.

**¿Qué pasa si el agente no completa la tarea en el límite de iteraciones?**
Devuelve el último razonamiento disponible con un mensaje indicando que se alcanzó el límite. Aumenta `max_iterations` o simplifica la tarea.

**¿Puedo combinar computer use con otros backends (Claude, Gemini nativo)?**
La herramienta `computer_use_task` siempre usa `google-genai` directamente con `GOOGLE_API_KEY`, independientemente del backend principal de Jarvis. Puedes usar `--backend anthropic` para el chat mientras computer use usa Gemini internamente.

---

## 18. Herramientas externas (MCP y agentes A2A)

Las 59 herramientas integradas son solo el punto de partida. Jarvis puede conectarse a **servidores MCP externos** e inyectar sus herramientas dinámicamente, además de delegar tareas a **agentes A2A remotos**. El modelo ve todas estas herramientas exactamente igual que las integradas.

> Guía completa con ejemplos paso a paso: **[MCP-AGENTS.md](MCP-AGENTS.md)**

---

### Herramientas MCP externas (`mcp_*`)

Al conectar un servidor MCP, todas sus herramientas se registran con el prefijo `mcp_`.

**Activar:**

```bash
# Transporte stdio (proceso local — más común)
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/proyectos"

# Transporte SSE/HTTP (servidor ya corriendo)
python -m jarvis --connect-mcp "http://localhost:3000"

# En .env (persistente, separados por ;)
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem ~/proyectos;http://mi-server:3000
```

**Ejemplo de herramientas registradas tras conectar el MCP Filesystem:**

| Herramienta en Jarvis | Descripción |
|---|---|
| `mcp_read_file` | Lee el contenido de un archivo (vía MCP) |
| `mcp_write_file` | Escribe contenido en un archivo (vía MCP) |
| `mcp_list_directory` | Lista el contenido de un directorio (vía MCP) |
| `mcp_search_files` | Busca archivos por patrón (vía MCP) |
| `mcp_create_directory` | Crea un directorio (vía MCP) |
| `mcp_get_file_info` | Devuelve metadatos de un archivo (vía MCP) |

**Ejemplo de uso en el chat:**

```
Tú: Lee el archivo ~/proyectos/main.py y explícame qué hace
Jarvis: [usa mcp_read_file] El archivo contiene una clase...
```

**FAQ:**

**¿Necesito el paquete `mcp`?**
Sí. Instala con `pip install 'palmiche-jarvis[mcp]'`.

**¿Qué servidores MCP puedo usar?**
Cualquier servidor compatible con el protocolo MCP: los del ecosistema oficial `@modelcontextprotocol` (filesystem, GitHub, SQLite, Brave Search, etc.), servidores comunitarios, o los propios.

**¿Cuántos servidores puedo conectar simultáneamente?**
Sin límite técnico. Cada servidor puede aportar múltiples herramientas.

**¿Las herramientas MCP persisten entre sesiones?**
No; se descubren en cada arranque de Jarvis conectándose al servidor.

---

### Agentes A2A remotos (`delegate_to_*`)

Al conectar un agente A2A, se registra como herramienta con el prefijo `delegate_to_` seguido del nombre del agente.

**Activar:**

```bash
# Por flag (repetible)
python -m jarvis --connect-a2a http://agente-especializado:8080

# En .env (persistente, separados por coma)
JARVIS_A2A_AGENTS=http://agente1:8080,http://agente2:9090
```

**Herramienta registrada:**

| Herramienta en Jarvis | Parámetro | Descripción |
|---|---|---|
| `delegate_to_<nombre>` | `message: str` | Delega la tarea al agente remoto y devuelve su respuesta |

**Ejemplo:**

```
Tú: Analiza este código y dime si hay bugs
Jarvis: [usa delegate_to_analista("Analiza este código...")] 
        El analista encontró 2 posibles problemas...
```

**FAQ:**

**¿Qué agentes son compatibles con A2A?**
Cualquier agente que implemente el protocolo A2A de Google (JSON-RPC 2.0 sobre HTTP). Otro Jarvis con `--serve-a2a` también es compatible.

**¿Se puede combinar MCP y A2A en la misma sesión?**
Sí; el modelo tiene acceso a todas las herramientas y decide cuáles usar según el contexto de cada petición.

---

## Añadir nuevas herramientas

Para contribuir con una nueva herramienta integrada:

1. Crea un módulo en `jarvis/tools/nombre_modulo.py` con las funciones
2. Registra la herramienta en `jarvis/tools/registry.py`:
   - Importa las funciones al inicio del archivo
   - Añade la definición JSON al array `TOOL_DEFINITIONS`
   - Añade el handler al diccionario en `execute_tool`
3. Abre un Pull Request describiendo la nueva herramienta

Sigue el patrón de cualquier módulo existente (por ejemplo `jarvis/tools/weather.py`).
