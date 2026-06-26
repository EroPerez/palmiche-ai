#!/usr/bin/env python3
"""Verify dynamic tools (A2A / MCP / plain-text custom) reach every brain.

Covers the registry accessor, the ADK callable synthesis (the trickiest part,
since ADK builds schemas from Python signatures), and the Ollama routing — all
without needing google-adk, a running Ollama, or any API key.

Run directly::

    python tests/test_dynamic_tools_all_brains.py
"""
import inspect
import sys
import tempfile
from pathlib import Path
from typing import get_args, get_origin

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jarvis.tools.dynamic import DynamicToolRegistry
from jarvis.brain.adk_dynamic import make_adk_callable, adk_tools_from_registry
from jarvis.brain.ollama_agent import JarvisOllamaAgent, _to_ollama_tools


def _sample_def():
    return {
        "name": "lookup_weather",
        "description": "Look up the weather for a city",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "Unit system",
                },
            },
            "required": ["city"],
        },
    }


def _registry_with_one_dynamic_tool(calls):
    registry = DynamicToolRegistry()

    def handler(inputs):
        calls.append(inputs)
        return f"weather for {inputs.get('city')}"

    registry.register(_sample_def(), handler)
    return registry


def test_registry_returns_only_dynamic_tools():
    registry = _registry_with_one_dynamic_tool([])
    dyn = registry.dynamic_tools()
    assert len(dyn) == 1
    assert dyn[0][0]["name"] == "lookup_weather"
    # Static built-ins are NOT included among dynamic tools.
    dyn_names = {d["name"] for d, _ in dyn}
    assert "get_system_info" not in dyn_names
    # But they ARE present in the full definitions list.
    assert "get_system_info" in {d["name"] for d in registry.definitions}


def test_adk_callable_signature_matches_schema():
    fn = make_adk_callable(_sample_def(), lambda i: "x")
    assert fn.__name__ == "lookup_weather"
    assert fn.__doc__ == "Look up the weather for a city"

    sig = inspect.signature(fn)
    params = list(sig.parameters)
    assert params == ["city", "units"], params  # required first
    assert sig.parameters["city"].default is inspect.Parameter.empty
    assert sig.parameters["units"].default is None

    # 'units' is an Optional[Literal['metric','imperial']]
    units_ann = sig.parameters["units"].annotation
    literal = next((a for a in get_args(units_ann) if get_origin(a) is not None), None) or units_ann
    assert "metric" in get_args(literal) and "imperial" in get_args(literal)


def test_adk_callable_forwards_to_handler():
    calls = []
    fn = make_adk_callable(_sample_def(), lambda i: calls.append(i) or "ok")

    assert fn(city="Havana") == "ok"
    assert calls[-1] == {"city": "Havana"}  # None optional dropped

    fn(city="Lima", units="metric")
    assert calls[-1] == {"city": "Lima", "units": "metric"}


def test_adk_tools_from_registry():
    registry = _registry_with_one_dynamic_tool([])
    tools = adk_tools_from_registry(registry)
    assert [t.__name__ for t in tools] == ["lookup_weather"]
    assert adk_tools_from_registry(None) == []


def test_ollama_routes_execution_through_registry():
    calls = []
    registry = _registry_with_one_dynamic_tool(calls)

    # Build an instance without touching the network (__init__ pings Ollama).
    agent = object.__new__(JarvisOllamaAgent)
    agent._registry = registry
    assert agent._execute_tool("lookup_weather", {"city": "Quito"}) == "weather for Quito"
    assert calls[-1] == {"city": "Quito"}

    # Without a registry it falls back to the static executor.
    agent._registry = None
    out = agent._execute_tool("generate_uuid", {"count": 1})
    assert isinstance(out, str) and out  # produced a real result, no crash


def test_ollama_tool_list_includes_dynamic_tools():
    registry = _registry_with_one_dynamic_tool([])
    tools = _to_ollama_tools(registry.definitions)
    names = {t["function"]["name"] for t in tools}
    assert "lookup_weather" in names          # custom tool exposed to Ollama
    assert "get_system_info" in names          # built-ins still present


def test_custom_tool_reaches_all_brain_surfaces():
    """End-to-end: a plain-text custom tool shows up in the Ollama and ADK surfaces."""
    from jarvis.tools.custom import load_custom_tools

    registry = DynamicToolRegistry()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("[tool: ping_demo]\ndescription: demo\ncommand: echo demo\n")
        path = f.name
    try:
        assert load_custom_tools(registry, path) == ["ping_demo"]
    finally:
        Path(path).unlink(missing_ok=True)

    # Anthropic surface: registry.definitions (used directly by JarvisAgent)
    assert "ping_demo" in {d["name"] for d in registry.definitions}
    # Ollama surface
    assert "ping_demo" in {t["function"]["name"] for t in _to_ollama_tools(registry.definitions)}
    # ADK surface
    assert "ping_demo" in {t.__name__ for t in adk_tools_from_registry(registry)}


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
