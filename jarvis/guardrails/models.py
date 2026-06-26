"""Data models for guardrail rules and evaluation results."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class GuardrailPhase(str, enum.Enum):
    """When in the request lifecycle a guardrail is evaluated."""

    INPUT = "input"
    OUTPUT = "output"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class GuardrailAction(str, enum.Enum):
    """What happens when a guardrail rule matches."""

    BLOCK = "block"
    WARN = "warn"
    REDACT = "redact"
    LOG = "log"


@dataclass
class GuardrailRule:
    """A single guardrail rule definition.

    Attributes:
        id: Unique identifier (e.g. ``"no-credentials-leak"``).
        name: Human-readable name shown in logs/warnings.
        description: Explains *why* this rule exists.
        phase: When the rule is evaluated (input, output, tool_call, tool_result).
        action: What to do when the rule triggers.
        enabled: Toggle individual rules without removing them.
        priority: Lower numbers run first (default 100).
        patterns: Regex patterns that trigger the rule when matched.
        keywords: Case-insensitive keyword list — any match triggers the rule.
        blocked_tools: Tool names that are forbidden (tool_call phase only).
        allowed_tools: Allowlist — if non-empty, only these tools may be called.
        tool_arg_rules: Per-tool argument constraints (tool_call phase only).
            Format: ``{"tool_name": {"arg_name": {"denied_patterns": [...]}}}``
        max_length: Maximum character length (0 = unlimited).
        custom_validator: Dotted path to a callable ``(text, rule) -> str|None``.
            Returns an error message on violation, or None if OK.
        message: Custom message returned when the rule triggers.
        redact_replacement: Replacement text when action is REDACT (default ``"[REDACTED]"``).
    """

    id: str
    name: str
    description: str = ""
    phase: GuardrailPhase = GuardrailPhase.INPUT
    action: GuardrailAction = GuardrailAction.BLOCK
    enabled: bool = True
    priority: int = 100
    patterns: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    tool_arg_rules: dict = field(default_factory=dict)
    max_length: int = 0
    custom_validator: str = ""
    message: str = ""
    redact_replacement: str = "[REDACTED]"

    @classmethod
    def from_dict(cls, data: dict) -> GuardrailRule:
        """Create a rule from a JSON-compatible dictionary."""
        data = dict(data)
        if "phase" in data:
            data["phase"] = GuardrailPhase(data["phase"])
        if "action" in data:
            data["action"] = GuardrailAction(data["action"])
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        d: dict = {}
        for f in self.__dataclass_fields__:
            val = getattr(self, f)
            if isinstance(val, enum.Enum):
                val = val.value
            d[f] = val
        return d


@dataclass
class GuardrailVerdict:
    """Result of evaluating guardrails against a piece of content.

    Attributes:
        blocked: Whether the content was blocked entirely.
        warnings: Warning messages from rules with action=WARN.
        triggered_rules: IDs of all rules that fired.
        message: The primary user-facing message (from the first blocking rule).
        transformed_text: The (possibly redacted) version of the original text.
            None means the text was not modified.
    """

    blocked: bool = False
    warnings: list[str] = field(default_factory=list)
    triggered_rules: list[str] = field(default_factory=list)
    message: str = ""
    transformed_text: str | None = None

    @property
    def passed(self) -> bool:
        return not self.blocked
