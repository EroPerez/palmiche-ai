# Herramientas externas: MCP y agentes A2A — Palmiche J.A.R.V.I.S.

> Guía paso a paso para conectar Jarvis a servidores MCP externos y agentes A2A remotos.

---

## ¿Puede Jarvis consumir herramientas de MCP externos?

**Sí.** Jarvis incluye un cliente MCP (`jarvis/mcp_support/client.py`) que se conecta a cualquier servidor MCP externo (local o remoto) y registra todas sus herramientas como herramientas nativas del agente. El modelo ve esas herramientas exactamente igual que las 59 integradas y las usa automáticamente durante el bucle agéntico.

Lo mismo aplica al protocolo A2A (Agent-to-Agent): Jarvis puede conectarse a agentes remotos y delegarles tareas como si fueran herramientas locales.

---

## Índice

1. [Prerrequisitos](#1-prerrequisitos)
2. [Servidores MCP externos](#2-servidores-mcp-externos)
   - [Transporte stdio (proceso local)](#21-transporte-stdio-proceso-local)
   - [Transporte SSE / HTTP](#22-transporte-sse--http)
   - [Método 1 — flag de línea de comandos](#23-método-1--flag-de-línea-de-comandos)
   - [Método 2 — variable de entorno](#24-método-2--variable-de-entorno)
   - [Método 3 — API Python](#25-método-3--api-python)
   - [Ejemplos concretos](#26-ejemplos-concretos)
   - [Cómo se nombran las herramientas](#27-cómo-se-nombran-las-herramientas)
3. [Agentes A2A remotos](#3-agentes-a2a-remotos)
   - [Método 1 — flag de línea de comandos](#31-método-1--flag-de-línea-de-comandos)
   - [Método 2 — variable de entorno](#32-método-2--variable-de-entorno)
   - [Método 3 — API Python](#33-método-3--api-python)
   - [Ejemplos concretos](#34-ejemplos-concretos)
   - [Cómo se nombran las herramientas](#35-cómo-se-nombran-las-herramientas)
4. [Combinar MCP + A2A](#4-combinar-mcp--a2a)
5. [Jarvis como servidor](#5-jarvis-como-servidor)
6. [Referencia de variables de entorno](#6-referencia-de-variables-de-entorno)
7. [Solución de problemas](#7-solución-de-problemas)

---

## 1. Prerrequisitos

### Para MCP

El cliente MCP requiere el paquete `mcp`:

```bash
pip install 'palmiche-jarvis[mcp]'
# equivale a: pip install 'mcp>=1.0.0'
```

Para servidores MCP basados en Node.js (como los del ecosistema `@modelcontextprotocol`):

```bash
node --version   # requiere Node.js >= 18
npm --version
```

### Para A2A

No requiere dependencias adicionales para el **cliente** A2A. Para ejecutar Jarvis como **servidor** A2A:

```bash
pip install 'palmiche-jarvis[a2a]'
# equivale a: pip install fastapi>=0.110.0 uvicorn>=0.29.0
```

---

## 2. Servidores MCP externos

### 2.1 Transporte stdio (proceso local)

El cliente lanza el servidor como subproceso y se comunica por stdin/stdout. Es el transporte más común para servidores MCP distribuidos como paquetes npm o Python.

```
Jarvis ←→ [subprocess: npx -y @modelcontextprotocol/server-filesystem /tmp]
```

**Formato del spec:** comando seguido de sus argumentos, en una sola cadena.

```
"npx -y @modelcontextprotocol/server-filesystem /tmp"
"uvx mcp-server-git --repository /home/usuario/proyecto"
"python /ruta/mi_servidor_mcp.py"
```

### 2.2 Transporte SSE / HTTP

El cliente se conecta a un servidor MCP que ya está corriendo y expone un endpoint HTTP con Server-Sent Events.

```
Jarvis ←→ http://localhost:3000   (SSE)
```

**Formato del spec:** URL que comienza con `http://` o `https://`.

```
"http://localhost:3000"
"https://mi-servidor-mcp.ejemplo.com"
```

---

### 2.3 Método 1 — flag de línea de comandos

La forma más rápida. El flag `--connect-mcp` es **repetible**: úsalo varias veces para conectar múltiples servidores.

```bash
# Un servidor MCP (stdio)
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"

# Un servidor MCP (SSE)
python -m jarvis --connect-mcp "http://localhost:3000"

# Múltiples servidores simultáneamente
python -m jarvis \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /home/usuario" \
  --connect-mcp "npx -y @modelcontextprotocol/server-github" \
  --connect-mcp "http://localhost:3001"
```

Al arrancar, Jarvis mostrará las herramientas descubiertas:

```
[MCP] Conectado a 'npx -y @modelcontextprotocol/server-filesystem /home/usuario'
  Herramientas registradas: mcp_read_file, mcp_write_file, mcp_list_directory, ...
```

---

### 2.4 Método 2 — variable de entorno

Define `JARVIS_MCP_SERVERS` en el archivo `.env`. Usa `;` como separador entre specs.

```ini
# jarvis/.env

# Un servidor
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem /home/usuario

# Múltiples servidores (separados por ;)
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem /home/usuario;http://localhost:3001
```

Con esta configuración, Jarvis carga los servidores automáticamente en cada arranque sin necesidad de flags adicionales:

```bash
python -m jarvis   # los MCP servers se conectan automáticamente
```

---

### 2.5 Método 3 — API Python

Para integraciones programáticas, usa `DynamicToolRegistry` y `load_mcp_server` directamente:

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.mcp_support.client import load_mcp_server
from jarvis.brain.agent import JarvisAgent

# Crear el registro dinámico
registry = DynamicToolRegistry()

# Conectar a un servidor MCP stdio
names_stdio = load_mcp_server(
    registry,
    "npx -y @modelcontextprotocol/server-filesystem /tmp"
)
print("Herramientas stdio:", names_stdio)
# → ['mcp_read_file', 'mcp_write_file', 'mcp_list_directory', ...]

# Conectar a un servidor MCP SSE
names_sse = load_mcp_server(registry, "http://localhost:3000")
print("Herramientas SSE:", names_sse)

# Instanciar el agente con el registro extendido
agent = JarvisAgent(name="Jarvis", registry=registry)
response = agent.chat("Lee el archivo /tmp/notas.txt")
print(response)
```

`load_mcp_server` devuelve la lista de nombres registrados, con el prefijo `mcp_`.

---

### 2.6 Ejemplos concretos

#### Ejemplo A — MCP Filesystem (acceso a archivos del sistema)

Este servidor MCP oficial permite leer, escribir y gestionar archivos en una ruta raíz.

```bash
# Instalar (solo la primera vez)
npm install -g @modelcontextprotocol/server-filesystem
# o dejar que npx lo instale automáticamente con -y

# Conectar Jarvis al servidor con raíz en ~/Documentos
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/Documentos"
```

Herramientas disponibles tras la conexión (con prefijo `mcp_`):

| Herramienta | Descripción |
|---|---|
| `mcp_read_file` | Lee el contenido de un archivo |
| `mcp_write_file` | Escribe contenido en un archivo |
| `mcp_list_directory` | Lista el contenido de un directorio |
| `mcp_create_directory` | Crea un directorio |
| `mcp_move_file` | Mueve o renombra archivo |
| `mcp_search_files` | Busca archivos por patrón |
| `mcp_get_file_info` | Metadatos de un archivo |

Prueba en el chat:

```
Tú: Lee el archivo ~/Documentos/notas.txt usando las herramientas MCP
Jarvis: [usa mcp_read_file] El contenido del archivo es: ...
```

---

#### Ejemplo B — MCP GitHub (gestión de repositorios)

```bash
# Requiere token de GitHub en GITHUB_PERSONAL_ACCESS_TOKEN
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_tutoken...

python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-github"
```

En `.env`:

```ini
# Para que el token esté disponible siempre
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_tutoken...
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-github
```

Prueba en el chat:

```
Tú: Lista mis repositorios de GitHub
Tú: Crea un issue en el repositorio mi-usuario/mi-repo con título "Bug en el login"
Tú: Muéstrame los pull requests abiertos de mi-usuario/mi-repo
```

---

#### Ejemplo C — MCP SQLite (base de datos local)

```bash
pip install mcp-server-sqlite
# o con uvx:
python -m jarvis --connect-mcp "uvx mcp-server-sqlite --db-path ~/datos.db"
```

Prueba en el chat:

```
Tú: ¿Qué tablas tiene la base de datos?
Tú: Muéstrame los últimos 10 registros de la tabla usuarios
```

---

#### Ejemplo D — Servidor MCP propio (SSE/HTTP)

Si tienes tu propio servidor MCP corriendo en HTTP/SSE:

```bash
# El servidor ya corre en http://localhost:4000
python -m jarvis --connect-mcp "http://localhost:4000"
```

En `.env` para que se conecte siempre:

```ini
JARVIS_MCP_SERVERS=http://localhost:4000
```

---

### 2.7 Cómo se nombran las herramientas

Todas las herramientas de servidores MCP externos reciben el **prefijo `mcp_`** para evitar colisiones con las 59 herramientas integradas de Jarvis:

| Nombre original en el servidor MCP | Nombre en Jarvis |
|---|---|
| `read_file` | `mcp_read_file` |
| `list_directory` | `mcp_list_directory` |
| `create_issue` | `mcp_create_issue` |
| `query` | `mcp_query` |

La descripción de cada herramienta también incluye la etiqueta `[MCP:spec]` para identificar su origen:

```
[MCP:npx -y @modelcontextprotocol/server-filesystem /tmp] Read a file...
```

El modelo decide automáticamente cuándo usar una herramienta `mcp_*` vs una herramienta local según el contexto de la petición.

---

## 3. Agentes A2A remotos

El protocolo **Agent-to-Agent (A2A)** de Google permite que agentes de IA se comuniquen entre sí sobre HTTP/JSON-RPC 2.0. Jarvis puede conectarse a cualquier agente compatible con A2A y usarlo como herramienta.

### 3.1 Método 1 — flag de línea de comandos

El flag `--connect-a2a` es **repetible**.

```bash
# Conectar a otro agente Jarvis
python -m jarvis --connect-a2a http://localhost:8080

# Conectar a múltiples agentes especializados
python -m jarvis \
  --connect-a2a http://agente-analisis:8080 \
  --connect-a2a http://agente-escritura:9090 \
  --connect-a2a http://agente-codigo:7070
```

---

### 3.2 Método 2 — variable de entorno

```ini
# jarvis/.env

# Un agente
JARVIS_A2A_AGENTS=http://agente-remoto:8080

# Múltiples agentes (separados por coma)
JARVIS_A2A_AGENTS=http://agente-analisis:8080,http://agente-escritura:9090
```

---

### 3.3 Método 3 — API Python

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.a2a.client import load_a2a_agent
from jarvis.brain.agent import JarvisAgent

registry = DynamicToolRegistry()

# Conectar a un agente A2A remoto
load_a2a_agent(registry, "http://specialist-agent:8080")
# → registra: delegate_to_specialist_agent(message: str)

# Conectar a otro agente Jarvis corriendo en el puerto 9090
load_a2a_agent(registry, "http://localhost:9090")
# → registra: delegate_to_jarvis(message: str)

agent = JarvisAgent(name="Orquestador", registry=registry)
response = agent.chat("Analiza este texto y redacta un informe basado en el análisis")
print(response)
```

---

### 3.4 Ejemplos concretos

#### Ejemplo A — Dos instancias de Jarvis colaborando

**Terminal 1 — instancia especializada en análisis:**

```bash
python -m jarvis --serve-a2a --a2a-port 8081 --name "Analista"
```

**Terminal 2 — instancia principal que delega al analista:**

```bash
python -m jarvis --connect-a2a http://localhost:8081
```

Ahora en el chat de la instancia principal:

```
Tú: Analiza el archivo ~/datos.csv y dame un resumen
Jarvis: [usa delegate_to_analista("Analiza el archivo ~/datos.csv y dame un resumen")]
        El Analista responde: He revisado el archivo. Contiene 1.200 filas...
```

---

#### Ejemplo B — Jarvis + agente especializado externo

Supón que tienes un agente A2A especializado en búsqueda de documentos legales corriendo en tu red:

```bash
# En .env
JARVIS_A2A_AGENTS=http://192.168.1.50:8080

python -m jarvis
```

```
Tú: Busca jurisprudencia sobre contratos de arrendamiento en 2024
Jarvis: [usa delegate_to_legal_agent("Busca jurisprudencia...")]
        El agente legal responde: Encontré 3 sentencias relevantes...
```

---

### 3.5 Cómo se nombran las herramientas

Los agentes A2A se registran como herramientas con el prefijo **`delegate_to_`** seguido del nombre del agente (tomado de su Agent Card):

| URL del agente | Nombre del agente (Agent Card) | Herramienta en Jarvis |
|---|---|---|
| `http://localhost:8081` | `Analista` | `delegate_to_analista` |
| `http://agente.example.com:8080` | `Specialist` | `delegate_to_specialist` |
| `http://localhost:9090` | `Jarvis` | `delegate_to_jarvis` |

Cada herramienta acepta un único parámetro `message: str` con la tarea en lenguaje natural que se delega al agente remoto.

---

## 4. Combinar MCP + A2A

Puedes conectar simultáneamente servidores MCP y agentes A2A. El modelo tiene acceso a todas las herramientas y decide la mejor combinación para cada tarea.

```bash
python -m jarvis \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/proyectos" \
  --connect-mcp "npx -y @modelcontextprotocol/server-github" \
  --connect-a2a http://agente-revisor:8080 \
  --connect-a2a http://agente-documentacion:9090
```

Con esta configuración, Jarvis puede en una sola conversación:

```
Tú: Lee el archivo ~/proyectos/src/main.py, pídele al revisor que lo revise
    y al documentador que genere el docstring, y luego actualiza el archivo

Jarvis:
  1. [mcp_read_file] Lee main.py
  2. [delegate_to_revisor] "Revisa este código: ..." → feedback del revisor
  3. [delegate_to_documentador] "Genera docstring para: ..." → docstring
  4. [mcp_write_file] Actualiza main.py con el docstring
  ✓ Archivo actualizado con el docstring generado.
```

En `.env` para que la configuración sea persistente:

```ini
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem ~/proyectos;npx -y @modelcontextprotocol/server-github
JARVIS_A2A_AGENTS=http://agente-revisor:8080,http://agente-documentacion:9090
```

---

## 5. Jarvis como servidor

Jarvis puede actuar **simultáneamente** como cliente (consumiendo herramientas externas) y como servidor (exponiendo sus herramientas a otros).

### Servidor MCP (para Claude Desktop, Cursor, Zed)

```bash
python -m jarvis --serve-mcp
```

Configura en Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` en macOS, `%APPDATA%\Claude\claude_desktop_config.json` en Windows):

```json
{
  "mcpServers": {
    "palmiche": {
      "command": "python",
      "args": ["-m", "jarvis", "--serve-mcp"],
      "cwd": "/ruta/a/palmiche-ai"
    }
  }
}
```

Expone las 59 herramientas de Jarvis a Claude Desktop.

### Servidor A2A (para otros agentes)

```bash
python -m jarvis --serve-a2a --a2a-port 8080
```

Otros agentes pueden descubrir Jarvis en `http://tu-host:8080/.well-known/agent.json`.

### Modo combinado: servidor + cliente

```bash
# Jarvis actúa como servidor A2A Y consume un servidor MCP externo
python -m jarvis \
  --serve-a2a --a2a-port 8080 \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /datos"
```

---

## 6. Referencia de variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `JARVIS_MCP_SERVERS` | — | Specs de servidores MCP separados por `;`. Cada spec es un comando stdio o una URL SSE |
| `JARVIS_A2A_AGENTS` | — | URLs de agentes A2A separadas por `,` |
| `JARVIS_A2A_HOST` | `0.0.0.0` | Host del servidor A2A propio (modo `--serve-a2a`) |
| `JARVIS_A2A_PORT` | `8080` | Puerto del servidor A2A propio |

---

## 7. Solución de problemas

### "mcp package required"

```
ImportError: 'mcp' package required. Install with: pip install 'palmiche-jarvis[mcp]'
```

**Solución:**

```bash
pip install 'palmiche-jarvis[mcp]'
```

---

### El servidor MCP no se conecta al arrancar

```
[MCP] Advertencia: no se pudo conectar a 'npx -y @mcp/server-filesystem /tmp': ...
```

Causas comunes:

1. **Node.js no instalado:** `node --version` debe ser >= 18
2. **npx no disponible:** `npm --version`
3. **La ruta no existe:** verifica que el directorio que pasas al servidor existe
4. **Timeout en la primera ejecución:** `npx -y` descarga el paquete; puede tardar en la primera vez. Jarvis reintenta la conexión cada sesión, no persiste las herramientas entre sesiones.

Para depurar, prueba el servidor directamente:

```bash
npx -y @modelcontextprotocol/server-filesystem /tmp
# Debe arrancar sin errores y quedarse esperando en stdin
```

---

### Las herramientas `mcp_*` no aparecen en la respuesta

El modelo elige herramientas según el contexto. Pide explícitamente:

```
Usa la herramienta mcp_read_file para leer /tmp/archivo.txt
```

O verifica que el servidor se conectó revisando la salida de inicio:

```bash
python -m jarvis --connect-mcp "..." 2>&1 | head -20
```

---

### El agente A2A no responde

1. Verifica que el agente remoto esté corriendo: `curl http://host:8080/health`
2. Verifica la Agent Card: `curl http://host:8080/.well-known/agent.json`
3. Comprueba conectividad de red entre las máquinas

---

### Conflicto de nombres de herramientas

Si dos servidores MCP exponen una herramienta con el mismo nombre (p. ej. `read_file`), ambas recibirán el prefijo `mcp_read_file` y la segunda sobrescribirá a la primera en el registro. Solución: conecta los servidores en orden de prioridad (el último prevalece).

---

## Ver también

- [ARCHITECTURE.md](ARCHITECTURE.md) — Arquitectura completa, flujo de datos y protocolos
- [README.md](../README.md) — Guía general de instalación y uso
- [TOOLS.md](TOOLS.md) — Referencia de las 59 herramientas integradas
