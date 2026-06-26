"""Bridge dynamic tools (A2A / MCP / plain-text custom tools) into Google ADK.

ADK builds each tool's schema from a Python callable's signature and docstring
and then calls that callable directly. Dynamic tools, however, are described by
an Anthropic-style JSON schema plus a ``handler(inputs: dict) -> str``. This
module synthesizes, for each dynamic tool, a real Python function whose
signature mirrors the JSON schema and whose body forwards to the handler — so
the ADK/Gemini backend can use the same A2A/MCP/custom tools as the other brains.
"""
from __future__ import annotations

import inspect
from typing import Literal, Optional

_JSON_TO_PY = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _annotation_for(info: dict):
    """Map a JSON-schema property to a Python type annotation (Literal for enums)."""
    enum = info.get("enum")
    if enum:
        try:
            return Literal[tuple(enum)]  # type: ignore[valid-type]
        except TypeError:
            return str
    return _JSON_TO_PY.get(info.get("type", "string"), str)


def make_adk_callable(definition: dict, handler):
    """Synthesize an ADK-compatible callable for a dynamic tool.

    The returned function exposes a signature derived from
    ``definition['input_schema']`` (required params first, optionals defaulting
    to None) and forwards all received keyword arguments to *handler*.
    """
    name = definition["name"]
    schema = definition.get("input_schema", {}) or {}
    props: dict = schema.get("properties", {}) or {}
    required = set(schema.get("required", []) or [])

    parameters: list[inspect.Parameter] = []
    annotations: dict[str, object] = {}
    # Required parameters first so the synthesized signature is valid
    # (no non-default parameter after a defaulted one).
    ordered = list(required) + [p for p in props if p not in required]
    for pname in ordered:
        info = props.get(pname, {})
        ann = _annotation_for(info)
        if pname in required:
            annotations[pname] = ann
            parameters.append(
                inspect.Parameter(pname, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=ann)
            )
        else:
            annotations[pname] = Optional[ann]
            parameters.append(
                inspect.Parameter(
                    pname,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=Optional[ann],
                    default=None,
                )
            )
    annotations["return"] = str

    def impl(**kwargs) -> str:
        # Drop None values so absent optionals are not forwarded as nulls.
        inputs = {k: v for k, v in kwargs.items() if v is not None}
        return str(handler(inputs))

    impl.__name__ = name
    impl.__qualname__ = name
    impl.__doc__ = definition.get("description", "") or name
    impl.__signature__ = inspect.Signature(parameters)
    impl.__annotations__ = annotations
    return impl


def adk_tools_from_registry(registry) -> list:
    """Return ADK callables for every dynamically registered tool in *registry*."""
    if registry is None:
        return []
    return [make_adk_callable(defn, handler) for defn, handler in registry.dynamic_tools()]
