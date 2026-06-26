"""MCP stdio server — exposes all Jarvis tools via Model Context Protocol.

Start with:
    python -m jarvis --serve-mcp

Any MCP client (Claude Desktop, Cursor, etc.) can then connect to this
server as a stdio subprocess and use all 58 Jarvis tools.

Example entry in Claude Desktop config:
    {
      "mcpServers": {
        "palmiche": {
          "command": "python",
          "args": ["-m", "jarvis", "--serve-mcp"]
        }
      }
    }
"""
from __future__ import annotations

import asyncio
import sys


def run_mcp_server(registry=None) -> None:
    """Start the MCP stdio server (blocking).

    Args:
        registry: Optional DynamicToolRegistry. If None, uses static tools only.
    """
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp import types as mcp_types
    except ImportError:
        print(
            "[ERROR] El paquete 'mcp' no está instalado.\n"
            "  Instálalo con:  pip install 'palmiche-jarvis[mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)

    from ..tools.registry import get_tool_definitions, execute_tool

    app = Server("palmiche-jarvis")

    def _get_definitions() -> list[dict]:
        return registry.definitions if registry is not None else get_tool_definitions()

    def _execute(name: str, inputs: dict) -> str:
        if registry is not None:
            return registry.execute(name, inputs)
        return str(execute_tool(name, inputs))

    @app.list_tools()
    async def list_tools() -> list[mcp_types.Tool]:
        tools = []
        for t in _get_definitions():
            schema = dict(t.get("input_schema", {}))
            tools.append(
                mcp_types.Tool(
                    name=t["name"],
                    description=t.get("description", ""),
                    inputSchema=schema,
                )
            )
        return tools

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[mcp_types.TextContent | mcp_types.ImageContent | mcp_types.EmbeddedResource]:
        try:
            result = await asyncio.to_thread(_execute, name, arguments or {})
            return [mcp_types.TextContent(type="text", text=str(result))]
        except Exception as exc:
            return [mcp_types.TextContent(type="text", text=f"Error: {exc}")]

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            init_options = app.create_initialization_options()
            await app.run(read_stream, write_stream, init_options)

    asyncio.run(_run())
