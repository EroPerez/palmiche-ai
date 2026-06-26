"""AI Guardrails — safety mechanisms and rule-based controls between users and AI models.

Guardrails ensure the assistant behaves reliably, ethically, and securely by
validating inputs (user messages), outputs (model responses), and tool calls
before they take effect.

Quick start::

    from jarvis.guardrails import GuardrailsEngine

    engine = GuardrailsEngine.from_config()      # loads ~/.jarvis_guardrails.json
    verdict = engine.check_input("user message")
    if verdict.blocked:
        print(verdict.message)

See ``jarvis/guardrails/README.md`` for the full rule specification.
"""

from .models import (
    GuardrailAction,
    GuardrailPhase,
    GuardrailRule,
    GuardrailVerdict,
)
from .engine import GuardrailsEngine

__all__ = [
    "GuardrailAction",
    "GuardrailPhase",
    "GuardrailRule",
    "GuardrailVerdict",
    "GuardrailsEngine",
]
