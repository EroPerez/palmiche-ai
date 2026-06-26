#!/usr/bin/env python3
"""Verify plain-text custom tools parse, build schemas, and run safely.

No API keys needed; the only external dependency is a shell (uses `echo`).

Run directly::

    python tests/test_custom_tools.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jarvis.tools.custom import (
    parse_custom_tools,
    make_handler,
    load_custom_tools,
    CustomTool,
)

SAMPLE = """
# A comment line, ignored
[tool: clima_casa]
description: Clima en La Habana
command: echo Havana

[tool: saludar]
description: Saluda por nombre
param *nombre: Nombre de la persona
param idioma: Idioma opcional
confirm: true
command: echo hola {nombre} {idioma}

[tool: sin_comando]
description: Esta no tiene command y debe omitirse

[tool: 9invalido]
description: Nombre inválido, se omite
command: echo no
"""


def test_parse_skips_malformed_blocks():
    tools, warnings = parse_custom_tools(SAMPLE)
    names = [t.name for t in tools]
    assert names == ["clima_casa", "saludar"], names
    # Two bad blocks → at least two warnings (missing command, invalid name).
    assert len(warnings) >= 2, warnings


def test_required_and_optional_params():
    tools, _ = parse_custom_tools(SAMPLE)
    saludar = next(t for t in tools if t.name == "saludar")
    by_name = {p.name: p for p in saludar.params}
    assert by_name["nombre"].required is True
    assert by_name["idioma"].required is False
    assert saludar.confirm is True


def test_definition_schema():
    tools, _ = parse_custom_tools(SAMPLE)
    saludar = next(t for t in tools if t.name == "saludar")
    d = saludar.to_definition()
    assert d["name"] == "saludar"
    props = d["input_schema"]["properties"]
    assert set(props) == {"nombre", "idioma", "confirmed"}  # confirmed added by confirm:true
    assert d["input_schema"]["required"] == ["nombre"]


def test_render_command_quotes_and_is_injection_safe():
    tool = CustomTool(
        name="t",
        description="d",
        command="echo {msg} {missing} done",
        params=[type("P", (), {"name": "msg", "description": "", "required": False})()],
    )
    # A value trying to inject extra shell gets quoted into a single argument.
    rendered = tool.render_command({"msg": "hi; rm -rf /"})
    assert "'hi; rm -rf /'" in rendered
    assert "rm -rf / done" not in rendered  # the ; is neutralized inside quotes
    # Unknown placeholder for an undeclared param is left literal.
    assert "{missing}" in rendered


def test_handler_validates_required():
    tool = CustomTool(
        name="t",
        description="d",
        command="echo {nombre}",
        params=[type("P", (), {"name": "nombre", "description": "", "required": True})()],
    )
    out = make_handler(tool)({})
    assert "requeridos" in out.lower(), out


def test_handler_requires_confirmation():
    tool = CustomTool(name="t", description="d", command="echo hi", confirm=True)
    out = make_handler(tool)({})
    assert "confirm" in out.lower(), out
    # With confirmation it actually runs.
    out2 = make_handler(tool)({"confirmed": True})
    assert "hi" in out2, out2


def test_handler_runs_command():
    tool = CustomTool(
        name="t",
        description="d",
        command="echo hola {nombre}",
        params=[type("P", (), {"name": "nombre", "description": "", "required": True})()],
    )
    out = make_handler(tool)({"nombre": "mundo"})
    assert "hola mundo" in out, out


def test_load_custom_tools_into_registry():
    from jarvis.tools.dynamic import DynamicToolRegistry

    registry = DynamicToolRegistry()
    base = len(registry.definitions)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(SAMPLE)
        path = f.name
    try:
        names = load_custom_tools(registry, path)
        assert set(names) == {"clima_casa", "saludar"}, names
        assert len(registry.definitions) == base + 2
        # The registered custom tool actually executes through the registry.
        assert "Havana" in registry.execute("clima_casa", {})
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_missing_file_is_noop():
    from jarvis.tools.dynamic import DynamicToolRegistry

    registry = DynamicToolRegistry()
    assert load_custom_tools(registry, "/nonexistent/path/xyz.txt") == []


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {t.__name__}: {exc}")
        except Exception as exc:  # pragma: no cover
            failures += 1
            print(f"  ERROR {t.__name__}: {type(exc).__name__}: {exc}")
    total = len(tests)
    print(f"\n{total - failures}/{total} checks passed.")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
