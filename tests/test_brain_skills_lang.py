#!/usr/bin/env python3
"""Verify each brain can present its skills/tools in English or Spanish.

This exercises the bilingual skill catalog without needing any API key or
external service (Anthropic, Ollama, ADK/Gemini). It checks that:

  * the English overlay covers every tool and every parameter,
  * switching language only changes human text — never the schema structure
    (tool names, parameter names, enums, required lists),
  * the system prompt and the per-brain skill surfaces resolve in both
    languages (Anthropic/Ollama via the registry, ADK via docstrings).

Run directly::

    python tests/test_brain_skills_lang.py

or under pytest if available::

    pytest tests/test_brain_skills_lang.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jarvis.tools.registry import TOOL_DEFINITIONS, get_tool_definitions
from jarvis.tools.translations import TOOL_TEXT_EN, localize_definitions
from jarvis.brain.prompts import get_system_prompt
from jarvis.brain.adk_tools import ADK_TOOLS, ADK_TOOL_DOCS_ES, get_adk_tools


def _schema_skeleton(defs):
    """Reduce definitions to language-independent structure for equality checks."""
    skeleton = {}
    for d in defs:
        schema = d.get("input_schema", {})
        props = schema.get("properties", {})
        skeleton[d["name"]] = {
            "params": {
                p: {"type": info.get("type"), "enum": info.get("enum")}
                for p, info in props.items()
            },
            "required": sorted(schema.get("required", [])),
        }
    return skeleton


def test_english_overlay_is_complete():
    """Every tool and every parameter has an English translation (no silent gaps)."""
    missing_tools = []
    missing_params = []
    for d in TOOL_DEFINITIONS:
        name = d["name"]
        entry = TOOL_TEXT_EN.get(name)
        if entry is None:
            missing_tools.append(name)
            continue
        if "_" not in entry:
            missing_params.append(f"{name}._ (tool description)")
        for param in d.get("input_schema", {}).get("properties", {}):
            if param not in entry:
                missing_params.append(f"{name}.{param}")
    assert not missing_tools, f"Tools with no English overlay: {missing_tools}"
    assert not missing_params, f"Parameters with no English overlay: {missing_params}"


def test_language_switch_preserves_schema():
    """English and Spanish definitions differ only in text, never in structure."""
    es = get_tool_definitions("es")
    en = get_tool_definitions("en")

    assert [d["name"] for d in es] == [d["name"] for d in en], "tool set changed across languages"
    assert _schema_skeleton(es) == _schema_skeleton(en), "schema structure changed across languages"

    # And the descriptions actually changed for at least the bulk of tools.
    changed = sum(1 for a, b in zip(es, en) if a["description"] != b["description"])
    assert changed >= len(es) - 1, f"too few descriptions changed: {changed}/{len(es)}"


def test_english_is_default_and_non_mutating():
    """The default matches config and overlaying does not mutate the canonical defs."""
    before = TOOL_DEFINITIONS[0]["description"]
    en = localize_definitions(TOOL_DEFINITIONS, "en")
    after = TOOL_DEFINITIONS[0]["description"]
    assert before == after, "localize_definitions mutated the canonical Spanish defs"
    # First tool's English description comes from the catalog.
    assert en[0]["description"] == TOOL_TEXT_EN[en[0]["name"]]["_"]


def test_system_prompt_both_languages():
    """The shared system prompt resolves in both languages with the assistant name."""
    es = get_system_prompt("Palmiche", "es")
    en = get_system_prompt("Palmiche", "en")
    assert "Palmiche" in es and "Palmiche" in en
    assert "Eres" in es, "Spanish prompt missing expected Spanish wording"
    assert "You are" in en, "English prompt missing expected English wording"
    assert es != en


def test_system_prompt_covers_all_tool_categories():
    """Both prompts must mention every tool category (guards against drift)."""
    es = get_system_prompt("Palmiche", "es")
    en = get_system_prompt("Palmiche", "en")

    # Keyword that must appear in each prompt for every capability group.
    required = [
        ("Sistema", "System"),
        ("Aplicaciones", "Applications"),
        ("Archivos", "Files"),
        ("RSS", "RSS"),                       # fetch_webpage / get_rss_feed
        ("Portapapeles", "Clipboard"),
        ("Notificaciones", "Notifications"),
        ("Shell", "Shell"),
        ("Red", "Network"),
        ("Medios", "Media"),
        ("Capturas", "Screenshots"),
        ("Calendario", "Calendar"),
        ("Clima", "Weather"),                 # get_weather / get_forecast
        ("Notas", "Notes"),                   # *_note tools
        ("Temporizadores", "Timers"),         # timers / alarms
        ("Calculadora", "Calculator"),        # calculate / convert_units
        ("Texto", "Text"),                    # text_stats / text_transform
        ("Desarrollo", "Development"),
        ("Computer Use", "Computer Use"),     # computer_use_task
        ("personalizadas", "Custom tools"),   # plain-text custom tools
    ]
    missing_es = [es_kw for es_kw, _ in required if es_kw not in es]
    missing_en = [en_kw for _, en_kw in required if en_kw not in en]
    assert not missing_es, f"Spanish prompt missing categories: {missing_es}"
    assert not missing_en, f"English prompt missing categories: {missing_en}"


def test_ollama_brain_tool_conversion():
    """The Ollama brain converts the localized skills into OpenAI function format."""
    from jarvis.brain.ollama_agent import _to_ollama_tools

    en_tools = _to_ollama_tools(get_tool_definitions("en"))
    names = {t["function"]["name"] for t in en_tools}
    assert names == {d["name"] for d in TOOL_DEFINITIONS}
    # A representative description is English.
    by_name = {t["function"]["name"]: t["function"]["description"] for t in en_tools}
    assert by_name["get_system_info"] == TOOL_TEXT_EN["get_system_info"]["_"]


def test_adk_brain_docstrings_localized():
    """The ADK brain exposes the same callables with language-specific docstrings."""
    en_tools = get_adk_tools("en")
    es_tools = get_adk_tools("es")

    assert [f.__name__ for f in en_tools] == [f.__name__ for f in ADK_TOOLS]
    assert [f.__name__ for f in es_tools] == [f.__name__ for f in ADK_TOOLS]

    en_by_name = {f.__name__: f for f in en_tools}
    es_by_name = {f.__name__: f for f in es_tools}

    # English is canonical (same objects), Spanish are clones with swapped docs.
    assert en_by_name["get_system_info"].__doc__.startswith("Get system information")
    assert es_by_name["get_system_info"].__doc__ == ADK_TOOL_DOCS_ES["get_system_info"]

    # Clones keep the signature/annotations so ADK still builds a valid schema.
    for name, fn in es_by_name.items():
        assert fn.__annotations__ == en_by_name[name].__annotations__, f"annotations lost for {name}"


def test_config_language_validation():
    """Invalid language env values fall back to the default instead of breaking."""
    from jarvis.config import _get_lang

    assert _get_lang("JARVIS_TOOL_LANG", "en") in ("en", "es")
    import os
    os.environ["JARVIS_TOOL_LANG_TEST"] = "fr"
    assert _get_lang("JARVIS_TOOL_LANG_TEST", "en") == "en"
    os.environ["JARVIS_TOOL_LANG_TEST"] = "ES"
    assert _get_lang("JARVIS_TOOL_LANG_TEST", "en") == "es"
    del os.environ["JARVIS_TOOL_LANG_TEST"]


def _run():
    """Tiny runner so the suite works without pytest installed."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {t.__name__}: {exc}")
        except Exception as exc:  # pragma: no cover - unexpected import/runtime errors
            failures += 1
            print(f"  ERROR {t.__name__}: {type(exc).__name__}: {exc}")
    total = len(tests)
    print(f"\n{total - failures}/{total} checks passed.")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
