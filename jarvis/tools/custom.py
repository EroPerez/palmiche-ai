"""Plain-text custom tools (skills) for Jarvis.

Lets a user define their own tools without writing Python: each tool is a block
of plain text that maps a name + description + parameters to a shell command
template. The tools are loaded into a :class:`DynamicToolRegistry`, so every
brain sees them in its tool list exactly like the built-in ones.

File format (default: ``~/.jarvis_custom_tools.txt``)::

    # Lines starting with '#' are comments. Blank lines separate nothing —
    # a block runs from one [tool: ...] header to the next.

    [tool: clima_casa]
    description: Clima actual en mi ciudad (La Habana)
    command: curl -s "wttr.in/Havana?format=3"

    [tool: saludar]
    description: Saluda a alguien por su nombre
    param *nombre: Nombre de la persona (el * marca el parámetro como requerido)
    param idioma: Idioma del saludo (opcional)
    confirm: false
    command: echo "Hola {nombre} ({idioma})"

Rules:
  * ``[tool: name]`` starts a block; *name* must match ``[a-zA-Z_][a-zA-Z0-9_]*``.
  * ``description:`` is required.
  * ``param name: desc`` declares an optional string parameter; prefix the name
    with ``*`` (``param *name: ...``) to make it required.
  * ``command:`` is the shell template; ``{name}`` placeholders are replaced with
    the shell-quoted parameter value (absent optional params become empty).
  * ``confirm: true`` makes the tool ask for explicit confirmation before running
    (handled like the built-in destructive tools).

Parameter values are quoted with :func:`shlex.quote` before substitution, so a
user-supplied value cannot break out of the intended command.
"""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

from .shell import run_shell_command

_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
_HEADER_RE = re.compile(r"^\[tool:\s*([^\]]+)\]\s*$")


@dataclass
class CustomParam:
    name: str
    description: str
    required: bool = False


@dataclass
class CustomTool:
    name: str
    description: str
    command: str
    params: list[CustomParam] = field(default_factory=list)
    confirm: bool = False

    def to_definition(self) -> dict:
        """Build the Anthropic-format tool schema for this custom tool."""
        properties: dict[str, dict] = {}
        required: list[str] = []
        for p in self.params:
            properties[p.name] = {"type": "string", "description": p.description}
            if p.required:
                required.append(p.name)
        if self.confirm:
            properties["confirmed"] = {
                "type": "boolean",
                "description": "El usuario confirmó explícitamente ejecutar esta herramienta personalizada.",
            }
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def render_command(self, inputs: dict) -> str:
        """Substitute ``{param}`` placeholders with shell-quoted input values."""
        declared = {p.name for p in self.params}

        def _replace(match: re.Match) -> str:
            key = match.group(1)
            if key not in declared:
                return match.group(0)  # leave unknown braces untouched
            value = inputs.get(key, "")
            text = "" if value is None else str(value)
            return shlex.quote(text) if text != "" else ""

        return _PLACEHOLDER_RE.sub(_replace, self.command)


def parse_custom_tools(text: str) -> tuple[list[CustomTool], list[str]]:
    """Parse plain-text tool definitions.

    Returns a tuple of (tools, warnings). Malformed blocks are skipped with a
    warning rather than aborting the whole file.
    """
    tools: list[CustomTool] = []
    warnings: list[str] = []

    # Split into blocks on [tool: ...] headers, keeping track of line numbers.
    current_name: str | None = None
    current_lineno = 0
    buffer: list[str] = []

    def _flush():
        if current_name is None:
            return
        tool, warn = _build_tool(current_name, current_lineno, buffer)
        if tool is not None:
            tools.append(tool)
        warnings.extend(warn)

    for lineno, raw in enumerate(text.splitlines(), start=1):
        header = _HEADER_RE.match(raw.strip())
        if header:
            _flush()
            current_name = header.group(1).strip()
            current_lineno = lineno
            buffer = []
        elif current_name is not None:
            buffer.append(raw)
    _flush()

    # Reject duplicate names (first wins).
    seen: set[str] = set()
    unique: list[CustomTool] = []
    for t in tools:
        if t.name in seen:
            warnings.append(f"Herramienta duplicada '{t.name}' ignorada.")
            continue
        seen.add(t.name)
        unique.append(t)
    return unique, warnings


def _build_tool(name: str, lineno: int, lines: list[str]) -> tuple[CustomTool | None, list[str]]:
    """Build a single CustomTool from its header name and body lines."""
    warnings: list[str] = []
    if not _NAME_RE.match(name):
        return None, [f"Línea {lineno}: nombre de herramienta inválido '{name}' (omitida)."]

    description = ""
    command = ""
    confirm = False
    params: list[CustomParam] = []

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip().lower()
        value = value.strip()

        if key == "description":
            description = value
        elif key == "command":
            command = value
        elif key == "confirm":
            confirm = value.lower() in ("true", "1", "yes", "si", "sí")
        elif key.startswith("param"):
            # "param name" or "param *name"
            pname = key[len("param"):].strip()
            required = pname.startswith("*")
            pname = pname.lstrip("*").strip()
            if not _NAME_RE.match(pname):
                warnings.append(f"Herramienta '{name}': parámetro inválido '{pname}' (omitido).")
                continue
            params.append(CustomParam(name=pname, description=value or pname, required=required))

    if not description:
        return None, warnings + [f"Herramienta '{name}': falta 'description' (omitida)."]
    if not command:
        return None, warnings + [f"Herramienta '{name}': falta 'command' (omitida)."]

    return CustomTool(name=name, description=description, command=command, params=params, confirm=confirm), warnings


def make_handler(tool: CustomTool):
    """Return a registry handler(inputs) -> str that runs the tool's command."""

    def _handler(inputs: dict) -> str:
        missing = [
            p.name for p in tool.params
            if p.required and not str(inputs.get(p.name, "")).strip()
        ]
        if missing:
            return f"Faltan parámetros requeridos para '{tool.name}': {', '.join(missing)}"

        if tool.confirm and not inputs.get("confirmed", False):
            return (
                f"Confirmación requerida para la herramienta personalizada '{tool.name}'. "
                "Informa al usuario qué se va a ejecutar y vuelve a llamar con confirmed=true."
            )

        command = tool.render_command(inputs)
        return run_shell_command(command)

    return _handler


def load_custom_tools(registry, path: str | Path | None = None) -> list[str]:
    """Load plain-text custom tools from *path* into *registry*.

    When *path* is None, ``JARVIS_CUSTOM_TOOLS_FILE`` from config is used. Missing
    or empty files are a no-op. Returns the list of registered tool names.
    """
    import sys

    if path is None:
        from ..config import JARVIS_CUSTOM_TOOLS_FILE
        path = JARVIS_CUSTOM_TOOLS_FILE
    path = Path(path).expanduser()

    if not path.is_file():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"  [tools] No se pudo leer {path}: {exc}", file=sys.stderr)
        return []

    tools, warnings = parse_custom_tools(text)
    for w in warnings:
        print(f"  [tools] {w}", file=sys.stderr)

    registered: list[str] = []
    existing = {d["name"] for d in registry.definitions}
    for tool in tools:
        if tool.name in existing:
            print(
                f"  [tools] '{tool.name}' choca con una herramienta existente (omitida).",
                file=sys.stderr,
            )
            continue
        registry.register(tool.to_definition(), make_handler(tool))
        registered.append(tool.name)
    return registered
