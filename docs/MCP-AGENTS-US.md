# External Tools: MCP and A2A Agents — Palmiche J.A.R.V.I.S.

> Step-by-step guide for connecting Jarvis to external MCP servers and remote A2A agents.

---

## Can Jarvis consume tools from external MCP servers?

**Yes.** Jarvis includes an MCP client (`jarvis/mcp_support/client.py`) that connects to any external MCP server (local or remote) and registers all its tools as native agent tools. The model sees those tools exactly like the 59 built-in ones and uses them automatically during the agentic loop.

The same applies to the A2A (Agent-to-Agent) protocol: Jarvis can connect to remote agents and delegate tasks to them as if they were local tools.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [External MCP Servers](#2-external-mcp-servers)
   - [stdio transport (local process)](#21-stdio-transport-local-process)
   - [SSE / HTTP transport](#22-sse--http-transport)
   - [Method 1 — command-line flag](#23-method-1--command-line-flag)
   - [Method 2 — environment variable](#24-method-2--environment-variable)
   - [Method 3 — Python API](#25-method-3--python-api)
   - [Concrete examples](#26-concrete-examples)
   - [How tools are named](#27-how-tools-are-named)
3. [Remote A2A Agents](#3-remote-a2a-agents)
   - [Method 1 — command-line flag](#31-method-1--command-line-flag)
   - [Method 2 — environment variable](#32-method-2--environment-variable)
   - [Method 3 — Python API](#33-method-3--python-api)
   - [Concrete examples](#34-concrete-examples)
   - [How tools are named](#35-how-tools-are-named)
4. [Combining MCP + A2A](#4-combining-mcp--a2a)
5. [Jarvis as a Server](#5-jarvis-as-a-server)
6. [Environment Variable Reference](#6-environment-variable-reference)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Prerequisites

### For MCP

The MCP client requires the `mcp` package:

```bash
pip install 'palmiche-jarvis[mcp]'
# equivalent to: pip install 'mcp>=1.0.0'
```

For Node.js-based MCP servers (such as those from the `@modelcontextprotocol` ecosystem):

```bash
node --version   # requires Node.js >= 18
npm --version
```

### For A2A

No additional dependencies are required for the A2A **client**. To run Jarvis as an A2A **server**:

```bash
pip install 'palmiche-jarvis[a2a]'
# equivalent to: pip install fastapi>=0.110.0 uvicorn>=0.29.0
```

---

## 2. External MCP Servers

### 2.1 stdio transport (local process)

The client launches the server as a subprocess and communicates via stdin/stdout. This is the most common transport for MCP servers distributed as npm or Python packages.

```
Jarvis ←→ [subprocess: npx -y @modelcontextprotocol/server-filesystem /tmp]
```

**Spec format:** command followed by its arguments, as a single string.

```
"npx -y @modelcontextprotocol/server-filesystem /tmp"
"uvx mcp-server-git --repository /home/user/project"
"python /path/to/my_mcp_server.py"
```

### 2.2 SSE / HTTP transport

The client connects to an already-running MCP server that exposes an HTTP endpoint with Server-Sent Events.

```
Jarvis ←→ http://localhost:3000   (SSE)
```

**Spec format:** URL starting with `http://` or `https://`.

```
"http://localhost:3000"
"https://my-mcp-server.example.com"
```

---

### 2.3 Method 1 — command-line flag

The fastest approach. The `--connect-mcp` flag is **repeatable**: use it multiple times to connect several servers simultaneously.

```bash
# One MCP server (stdio)
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /tmp"

# One MCP server (SSE)
python -m jarvis --connect-mcp "http://localhost:3000"

# Multiple servers at once
python -m jarvis \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /home/user" \
  --connect-mcp "npx -y @modelcontextprotocol/server-github" \
  --connect-mcp "http://localhost:3001"
```

On startup, Jarvis will display the discovered tools:

```
[MCP] Connected to 'npx -y @modelcontextprotocol/server-filesystem /home/user'
  Registered tools: mcp_read_file, mcp_write_file, mcp_list_directory, ...
```

---

### 2.4 Method 2 — environment variable

Define `JARVIS_MCP_SERVERS` in the `.env` file. Use `;` as the separator between specs.

```ini
# jarvis/.env

# One server
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem /home/user

# Multiple servers (separated by ;)
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem /home/user;http://localhost:3001
```

With this configuration, Jarvis loads the servers automatically on every startup without additional flags:

```bash
python -m jarvis   # MCP servers connect automatically
```

---

### 2.5 Method 3 — Python API

For programmatic integrations, use `DynamicToolRegistry` and `load_mcp_server` directly:

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.mcp_support.client import load_mcp_server
from jarvis.brain.agent import JarvisAgent

# Create the dynamic registry
registry = DynamicToolRegistry()

# Connect to a stdio MCP server
names_stdio = load_mcp_server(
    registry,
    "npx -y @modelcontextprotocol/server-filesystem /tmp"
)
print("stdio tools:", names_stdio)
# → ['mcp_read_file', 'mcp_write_file', 'mcp_list_directory', ...]

# Connect to an SSE MCP server
names_sse = load_mcp_server(registry, "http://localhost:3000")
print("SSE tools:", names_sse)

# Instantiate the agent with the extended registry
agent = JarvisAgent(name="Jarvis", registry=registry)
response = agent.chat("Read the file /tmp/notes.txt")
print(response)
```

`load_mcp_server` returns the list of registered tool names, with the `mcp_` prefix.

---

### 2.6 Concrete examples

#### Example A — MCP Filesystem (file system access)

This official MCP server allows reading, writing and managing files under a root path.

```bash
# Install (first time only)
npm install -g @modelcontextprotocol/server-filesystem
# or let npx install it automatically with -y

# Connect Jarvis with root at ~/Documents
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/Documents"
```

Tools available after connecting (with `mcp_` prefix):

| Tool | Description |
|---|---|
| `mcp_read_file` | Read file contents |
| `mcp_write_file` | Write content to a file |
| `mcp_list_directory` | List directory contents |
| `mcp_create_directory` | Create a directory |
| `mcp_move_file` | Move or rename a file |
| `mcp_search_files` | Search files by pattern |
| `mcp_get_file_info` | File metadata |

Test in chat:

```
You: Read the file ~/Documents/notes.txt using the MCP tools
Jarvis: [uses mcp_read_file] The file contents are: ...
```

---

#### Example B — MCP GitHub (repository management)

```bash
# Requires GitHub token in GITHUB_PERSONAL_ACCESS_TOKEN
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_yourtoken...

python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-github"
```

In `.env`:

```ini
# So the token is always available
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_yourtoken...
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-github
```

Test in chat:

```
You: List my GitHub repositories
You: Create an issue in the repository my-user/my-repo with the title "Login bug"
You: Show me the open pull requests in my-user/my-repo
```

---

#### Example C — MCP SQLite (local database)

```bash
pip install mcp-server-sqlite
# or with uvx:
python -m jarvis --connect-mcp "uvx mcp-server-sqlite --db-path ~/data.db"
```

Test in chat:

```
You: What tables does the database have?
You: Show me the last 10 records from the users table
```

---

#### Example D — Custom MCP server (SSE/HTTP)

If you have your own MCP server running over HTTP/SSE:

```bash
# The server is already running at http://localhost:4000
python -m jarvis --connect-mcp "http://localhost:4000"
```

In `.env` for persistent connection:

```ini
JARVIS_MCP_SERVERS=http://localhost:4000
```

---

### 2.7 How tools are named

All tools from external MCP servers receive the **`mcp_` prefix** to avoid collisions with Jarvis's 59 built-in tools:

| Original name in the MCP server | Name in Jarvis |
|---|---|
| `read_file` | `mcp_read_file` |
| `list_directory` | `mcp_list_directory` |
| `create_issue` | `mcp_create_issue` |
| `query` | `mcp_query` |

Each tool's description also includes the `[MCP:spec]` tag to identify its origin:

```
[MCP:npx -y @modelcontextprotocol/server-filesystem /tmp] Read a file...
```

The model automatically decides when to use an `mcp_*` tool vs a local tool based on the request context.

---

## 3. Remote A2A Agents

The **Agent-to-Agent (A2A)** protocol by Google allows AI agents to communicate with each other over HTTP/JSON-RPC 2.0. Jarvis can connect to any A2A-compatible agent and use it as a tool.

### 3.1 Method 1 — command-line flag

The `--connect-a2a` flag is **repeatable**.

```bash
# Connect to another Jarvis instance
python -m jarvis --connect-a2a http://localhost:8080

# Connect to multiple specialized agents
python -m jarvis \
  --connect-a2a http://analysis-agent:8080 \
  --connect-a2a http://writing-agent:9090 \
  --connect-a2a http://code-agent:7070
```

---

### 3.2 Method 2 — environment variable

```ini
# jarvis/.env

# One agent
JARVIS_A2A_AGENTS=http://remote-agent:8080

# Multiple agents (comma-separated)
JARVIS_A2A_AGENTS=http://analysis-agent:8080,http://writing-agent:9090
```

---

### 3.3 Method 3 — Python API

```python
from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.a2a.client import load_a2a_agent
from jarvis.brain.agent import JarvisAgent

registry = DynamicToolRegistry()

# Connect to a remote A2A agent
load_a2a_agent(registry, "http://specialist-agent:8080")
# → registers: delegate_to_specialist_agent(message: str)

# Connect to another Jarvis running on port 9090
load_a2a_agent(registry, "http://localhost:9090")
# → registers: delegate_to_jarvis(message: str)

agent = JarvisAgent(name="Orchestrator", registry=registry)
response = agent.chat("Analyze this text and write a report based on the analysis")
print(response)
```

---

### 3.4 Concrete examples

#### Example A — Two Jarvis instances collaborating

**Terminal 1 — analysis-specialized instance:**

```bash
python -m jarvis --serve-a2a --a2a-port 8081 --name "Analyst"
```

**Terminal 2 — main instance that delegates to the analyst:**

```bash
python -m jarvis --connect-a2a http://localhost:8081
```

Now in the main instance's chat:

```
You: Analyze the file ~/data.csv and give me a summary
Jarvis: [uses delegate_to_analyst("Analyze the file ~/data.csv and give me a summary")]
        The Analyst responds: I reviewed the file. It contains 1,200 rows...
```

---

#### Example B — Jarvis + specialized external agent

Suppose you have an A2A-compatible agent specialized in legal document search running on your network:

```bash
# In .env
JARVIS_A2A_AGENTS=http://192.168.1.50:8080

python -m jarvis
```

```
You: Search for case law on rental contracts in 2024
Jarvis: [uses delegate_to_legal_agent("Search for case law...")]
        The legal agent responds: I found 3 relevant rulings...
```

---

### 3.5 How tools are named

A2A agents are registered as tools with the **`delegate_to_`** prefix followed by the agent name (taken from its Agent Card):

| Agent URL | Agent name (Agent Card) | Tool in Jarvis |
|---|---|---|
| `http://localhost:8081` | `Analyst` | `delegate_to_analyst` |
| `http://agent.example.com:8080` | `Specialist` | `delegate_to_specialist` |
| `http://localhost:9090` | `Jarvis` | `delegate_to_jarvis` |

Each tool accepts a single `message: str` parameter with the natural language task to delegate to the remote agent.

---

## 4. Combining MCP + A2A

You can connect MCP servers and A2A agents simultaneously. The model has access to all tools and decides the best combination for each task.

```bash
python -m jarvis \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/projects" \
  --connect-mcp "npx -y @modelcontextprotocol/server-github" \
  --connect-a2a http://reviewer-agent:8080 \
  --connect-a2a http://docs-agent:9090
```

With this setup, Jarvis can in a single conversation:

```
You: Read the file ~/projects/src/main.py, ask the reviewer to review it,
     ask the docs agent to generate the docstring, then update the file

Jarvis:
  1. [mcp_read_file] Reads main.py
  2. [delegate_to_reviewer] "Review this code: ..." → reviewer feedback
  3. [delegate_to_docs_agent] "Generate docstring for: ..." → docstring
  4. [mcp_write_file] Updates main.py with the docstring
  ✓ File updated with the generated docstring.
```

In `.env` for persistent configuration:

```ini
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem ~/projects;npx -y @modelcontextprotocol/server-github
JARVIS_A2A_AGENTS=http://reviewer-agent:8080,http://docs-agent:9090
```

---

## 5. Jarvis as a Server

Jarvis can act **simultaneously** as a client (consuming external tools) and as a server (exposing its tools to others).

### MCP server (for Claude Desktop, Cursor, Zed)

```bash
python -m jarvis --serve-mcp
```

Configure in Claude Desktop (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "palmiche": {
      "command": "python",
      "args": ["-m", "jarvis", "--serve-mcp"],
      "cwd": "/path/to/palmiche-ai"
    }
  }
}
```

Exposes all 59 Jarvis tools to Claude Desktop.

### A2A server (for other agents)

```bash
python -m jarvis --serve-a2a --a2a-port 8080
```

Other agents can discover Jarvis at `http://your-host:8080/.well-known/agent.json`.

### Combined mode: server + client

```bash
# Jarvis acts as A2A server AND consumes an external MCP server
python -m jarvis \
  --serve-a2a --a2a-port 8080 \
  --connect-mcp "npx -y @modelcontextprotocol/server-filesystem /data"
```

---

## 6. Environment Variable Reference

| Variable | Default | Description |
|---|---|---|
| `JARVIS_MCP_SERVERS` | — | MCP server specs separated by `;`. Each spec is a stdio command or an SSE URL |
| `JARVIS_A2A_AGENTS` | — | A2A agent URLs separated by `,` |
| `JARVIS_A2A_HOST` | `0.0.0.0` | Host for Jarvis's own A2A server (`--serve-a2a` mode) |
| `JARVIS_A2A_PORT` | `8080` | Port for Jarvis's own A2A server |

---

## 7. Troubleshooting

### "mcp package required"

```
ImportError: 'mcp' package required. Install with: pip install 'palmiche-jarvis[mcp]'
```

**Solution:**

```bash
pip install 'palmiche-jarvis[mcp]'
```

---

### MCP server fails to connect on startup

```
[MCP] Warning: could not connect to 'npx -y @mcp/server-filesystem /tmp': ...
```

Common causes:

1. **Node.js not installed:** `node --version` must be >= 18
2. **npx not available:** `npm --version`
3. **Path doesn't exist:** verify the directory you pass to the server exists
4. **First-run timeout:** `npx -y` downloads the package; it may take time the first time. Jarvis retries the connection each session — tools are not persisted between sessions.

To debug, test the server directly:

```bash
npx -y @modelcontextprotocol/server-filesystem /tmp
# Should start without errors and wait on stdin
```

---

### `mcp_*` tools don't appear in responses

The model chooses tools based on context. Ask explicitly:

```
Use the mcp_read_file tool to read /tmp/file.txt
```

Or verify the server connected by checking startup output:

```bash
python -m jarvis --connect-mcp "..." 2>&1 | head -20
```

---

### A2A agent not responding

1. Verify the remote agent is running: `curl http://host:8080/health`
2. Check the Agent Card: `curl http://host:8080/.well-known/agent.json`
3. Check network connectivity between machines

---

### Tool name collision

If two MCP servers expose a tool with the same name (e.g. `read_file`), both will be prefixed as `mcp_read_file` and the second one will overwrite the first in the registry. Solution: connect servers in priority order (last one wins).

---

## See also

- [ARCHITECTURE-US.md](ARCHITECTURE-US.md) — Full architecture, data flow and protocols
- [README-US.md](../README-US.md) — General installation and usage guide
- [TOOLS-US.md](TOOLS-US.md) — Reference for the 59 built-in tools
