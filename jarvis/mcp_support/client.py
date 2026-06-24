"""MCP client — connects to external MCP servers and injects their tools into the agent.

Supports two transports:
  - stdio: spawns a local subprocess (e.g. "npx -y @modelcontextprotocol/server-filesystem /tmp")
  - SSE:   connects to an HTTP server  (e.g. "http://localhost:3000")

Usage:
    from jarvis.mcp_support.client import load_mcp_server
    from jarvis.tools.dynamic import DynamicToolRegistry
    registry = DynamicToolRegistry()
    load_mcp_server(registry, "npx -y @modelcontextprotocol/server-filesystem /tmp")
    load_mcp_server(registry, "http://localhost:3000")
"""
from __future__ import annotations

import asyncio
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Run an async coroutine in a fresh event loop (sync bridge)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _is_url(spec: str) -> bool:
    return spec.startswith("http://") or spec.startswith("https://")


def _parse_stdio_spec(spec: str) -> tuple[str, list[str]]:
    """Split 'command arg1 arg2' into (command, [args])."""
    parts = spec.split()
    return parts[0], parts[1:]


# ---------------------------------------------------------------------------
# Async tool listing
# ---------------------------------------------------------------------------

async def _async_list_stdio_tools(command: str, args: list[str]) -> list[dict]:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        raise ImportError(
            "'mcp' package required. Install with: pip install 'palmiche-jarvis[mcp]'"
        )

    params = StdioServerParameters(command=command, args=args, env=None)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return _convert_tools(result.tools)


async def _async_list_sse_tools(url: str) -> list[dict]:
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
    except ImportError:
        raise ImportError(
            "'mcp' package required. Install with: pip install 'palmiche-jarvis[mcp]'"
        )

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return _convert_tools(result.tools)


# ---------------------------------------------------------------------------
# Async tool execution
# ---------------------------------------------------------------------------

async def _async_call_stdio_tool(
    command: str, args: list[str], tool_name: str, tool_args: dict
) -> str:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        raise ImportError(
            "'mcp' package required. Install with: pip install 'palmiche-jarvis[mcp]'"
        )

    params = StdioServerParameters(command=command, args=args, env=None)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return _extract_text(result.content)


async def _async_call_sse_tool(url: str, tool_name: str, tool_args: dict) -> str:
    try:
        from mcp import ClientSession
        from mcp.client.sse import sse_client
    except ImportError:
        raise ImportError(
            "'mcp' package required. Install with: pip install 'palmiche-jarvis[mcp]'"
        )

    async with sse_client(url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            return _extract_text(result.content)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _convert_tools(mcp_tools) -> list[dict]:
    tools = []
    for t in mcp_tools:
        tools.append(
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema or {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            }
        )
    return tools


def _extract_text(content_list) -> str:
    parts = []
    for item in content_list:
        if hasattr(item, "text"):
            parts.append(item.text)
        elif isinstance(item, dict) and "text" in item:
            parts.append(item["text"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_mcp_server(registry, spec: str) -> list[str]:
    """Discover an MCP server and register all its tools in the DynamicToolRegistry.

    Args:
        registry: DynamicToolRegistry instance.
        spec:  Either:
               - A command string "command arg1 arg2" (stdio transport)
               - An HTTP URL "http://..." (SSE transport)

    Returns:
        List of registered tool names.
    """
    try:
        if _is_url(spec):
            tools = _run_async(_async_list_sse_tools(spec))
        else:
            cmd, args = _parse_stdio_spec(spec)
            tools = _run_async(_async_list_stdio_tools(cmd, args))
    except Exception as exc:
        print(f"  [MCP] Advertencia: no se pudo conectar a '{spec}': {exc}", file=sys.stderr)
        return []

    registered = []
    for tool_def in tools:
        original_name = tool_def["name"]
        # Prefix to avoid collisions with local tools
        prefixed_name = f"mcp_{original_name}"

        prefixed_def = dict(tool_def)
        prefixed_def["name"] = prefixed_name
        prefixed_def["description"] = (
            f"[MCP:{spec}] {tool_def.get('description', '')}"
        ).strip()

        if _is_url(spec):
            _url = spec

            def _make_sse_handler(url: str, name: str):
                def _handler(inputs: dict) -> str:
                    return _run_async(_async_call_sse_tool(url, name, inputs))
                return _handler

            registry.register(prefixed_def, _make_sse_handler(_url, original_name))
        else:
            _cmd, _args = _parse_stdio_spec(spec)

            def _make_stdio_handler(command: str, args: list[str], name: str):
                def _handler(inputs: dict) -> str:
                    return _run_async(_async_call_stdio_tool(command, args, name, inputs))
                return _handler

            registry.register(prefixed_def, _make_stdio_handler(_cmd, _args, original_name))

        registered.append(prefixed_name)

    return registered
