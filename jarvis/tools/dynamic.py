"""DynamicToolRegistry — extends the static tool registry with runtime-registered tools.

Used by A2A client and MCP client integrations to inject remote tools into the agent loop.
"""
from __future__ import annotations

from .registry import TOOL_DEFINITIONS, execute_tool as _static_execute


class DynamicToolRegistry:
    """Tool registry that combines static tools with dynamically registered remote tools."""

    def __init__(self) -> None:
        self._definitions: list[dict] = list(TOOL_DEFINITIONS)
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

    def execute(self, name: str, inputs: dict) -> str:
        """Dispatch a tool call to the appropriate handler."""
        if name in self._handlers:
            try:
                return str(self._handlers[name](inputs))
            except Exception as exc:
                return f"Error ejecutando herramienta remota '{name}': {exc}"
        return str(_static_execute(name, inputs))
