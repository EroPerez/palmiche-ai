"""DynamicToolRegistry — extends the static tool registry with runtime-registered tools.

Used by A2A client and MCP client integrations to inject remote tools into the agent loop.
"""
from __future__ import annotations

from .registry import get_tool_definitions, execute_tool as _static_execute, _log_tool_call


class DynamicToolRegistry:
    """Tool registry that combines static tools with dynamically registered remote tools."""

    def __init__(self) -> None:
        self._definitions: list[dict] = list(get_tool_definitions())
        self._handlers: dict[str, object] = {}

    def register(self, definition: dict, handler) -> None:
        """Add a dynamic tool.

        Args:
            definition: Anthropic-format tool schema dict (name, description, input_schema).
            handler: Callable(inputs: dict) -> str that executes the tool.
        """
        self._definitions.append(definition)
        self._handlers[definition["name"]] = handler

    @property
    def definitions(self) -> list[dict]:
        """All tool definitions (static + dynamic)."""
        return self._definitions

    def dynamic_tools(self) -> list[tuple[dict, object]]:
        """Return (definition, handler) pairs for the dynamically registered tools only.

        Excludes the static built-in tools (which brains load via their own
        path, e.g. ADK python wrappers). Used to inject A2A/MCP/custom tools into
        backends that don't execute through ``execute``.
        """
        return [
            (d, self._handlers[d["name"]])
            for d in self._definitions
            if d["name"] in self._handlers
        ]

    def execute(self, name: str, inputs: dict) -> str:
        """Dispatch a tool call to the appropriate handler."""
        if name in self._handlers:
            try:
                result = str(self._handlers[name](inputs))
                _log_tool_call(name, inputs, result)
                return result
            except Exception as exc:
                msg = f"Error ejecutando herramienta remota '{name}': {exc}"
                _log_tool_call(name, inputs, msg, error=True)
                return msg
        return str(_static_execute(name, inputs))
