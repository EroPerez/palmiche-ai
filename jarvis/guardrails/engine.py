"""Core guardrails evaluation engine."""

from __future__ import annotations

import importlib
import json
import logging
import re
from pathlib import Path

from .defaults import DEFAULT_RULES
from .models import (
    GuardrailAction,
    GuardrailPhase,
    GuardrailRule,
    GuardrailVerdict,
)

logger = logging.getLogger(__name__)


class GuardrailsEngine:
    """Evaluates guardrail rules against text at each lifecycle phase.

    The engine loads built-in defaults and merges them with user-defined rules
    from a JSON config file.  Rules are keyed by ``id`` — a user rule with the
    same ``id`` as a default rule replaces it, allowing full customization.
    """

    def __init__(self, rules: list[GuardrailRule] | None = None):
        self._rules: list[GuardrailRule] = list(rules) if rules else list(DEFAULT_RULES)
        self._rules.sort(key=lambda r: r.priority)

    # ── Factory ───────────────────────────────────────────────────────

    @classmethod
    def from_config(cls, path: str | Path | None = None) -> GuardrailsEngine:
        """Create an engine by merging defaults with an optional JSON config.

        The config file is a JSON object with an optional ``"rules"`` array.
        Each rule object follows the same schema as :class:`GuardrailRule`.
        A rule whose ``id`` matches a default rule *replaces* it entirely;
        new ids are appended.

        To disable a default rule, override it with ``{"id": "...", "enabled": false}``.
        """
        if path is None:
            from ..config import JARVIS_GUARDRAILS_FILE
            path = JARVIS_GUARDRAILS_FILE

        rules_by_id = {r.id: r for r in DEFAULT_RULES}

        config_path = Path(path)
        if config_path.is_file():
            try:
                data = json.loads(config_path.read_text(encoding="utf-8"))
                for raw_rule in data.get("rules", []):
                    rule = GuardrailRule.from_dict(raw_rule)
                    rules_by_id[rule.id] = rule
                logger.info("Loaded %d guardrail rule(s) from %s", len(data.get("rules", [])), path)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("Failed to load guardrails config %s: %s", path, exc)

        return cls(list(rules_by_id.values()))

    # ── Public API ────────────────────────────────────────────────────

    @property
    def rules(self) -> list[GuardrailRule]:
        return list(self._rules)

    def add_rule(self, rule: GuardrailRule) -> None:
        """Add or replace a rule at runtime."""
        self._rules = [r for r in self._rules if r.id != rule.id]
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by id. Returns True if found."""
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.id != rule_id]
        return len(self._rules) < before

    def check_input(self, text: str) -> GuardrailVerdict:
        """Evaluate input-phase rules against user text."""
        return self._evaluate(text, GuardrailPhase.INPUT)

    def check_output(self, text: str) -> GuardrailVerdict:
        """Evaluate output-phase rules against model response text."""
        return self._evaluate(text, GuardrailPhase.OUTPUT)

    def check_tool_call(self, tool_name: str, arguments: dict) -> GuardrailVerdict:
        """Evaluate tool-call-phase rules against a proposed tool invocation."""
        return self._evaluate_tool_call(tool_name, arguments)

    def check_tool_result(self, result: str) -> GuardrailVerdict:
        """Evaluate tool-result-phase rules against a tool's output."""
        return self._evaluate(result, GuardrailPhase.TOOL_RESULT)

    # ── Internal evaluation ───────────────────────────────────────────

    def _evaluate(self, text: str, phase: GuardrailPhase) -> GuardrailVerdict:
        """Run all rules for *phase* against *text*."""
        verdict = GuardrailVerdict()
        current_text = text

        for rule in self._rules:
            if not rule.enabled or rule.phase != phase:
                continue

            violation = self._check_rule(current_text, rule)
            if violation is None:
                continue

            verdict.triggered_rules.append(rule.id)
            msg = rule.message or violation

            if rule.action == GuardrailAction.BLOCK:
                verdict.blocked = True
                if not verdict.message:
                    verdict.message = msg
                logger.warning("Guardrail BLOCK [%s]: %s", rule.id, msg)

            elif rule.action == GuardrailAction.WARN:
                verdict.warnings.append(msg)
                logger.info("Guardrail WARN [%s]: %s", rule.id, msg)

            elif rule.action == GuardrailAction.REDACT:
                current_text = self._apply_redaction(current_text, rule)
                verdict.transformed_text = current_text
                logger.info("Guardrail REDACT [%s]: %s", rule.id, msg)

            elif rule.action == GuardrailAction.LOG:
                logger.info("Guardrail LOG [%s]: %s", rule.id, msg)

        return verdict

    def _check_rule(self, text: str, rule: GuardrailRule) -> str | None:
        """Check a single rule against *text*. Returns a reason string or None."""
        if rule.max_length > 0 and len(text) > rule.max_length:
            return f"Text length {len(text)} exceeds limit {rule.max_length}."

        for pattern in rule.patterns:
            try:
                if re.search(pattern, text):
                    return f"Pattern matched: {pattern}"
            except re.error:
                logger.warning("Invalid regex in rule %s: %s", rule.id, pattern)

        if rule.keywords:
            text_lower = text.lower()
            for kw in rule.keywords:
                if kw.lower() in text_lower:
                    return f"Keyword matched: {kw}"

        if rule.custom_validator:
            result = self._run_custom_validator(rule.custom_validator, text, rule)
            if result:
                return result

        return None

    def _evaluate_tool_call(self, tool_name: str, arguments: dict) -> GuardrailVerdict:
        """Run tool-call-phase rules against a proposed invocation."""
        verdict = GuardrailVerdict()

        for rule in self._rules:
            if not rule.enabled or rule.phase != GuardrailPhase.TOOL_CALL:
                continue

            violation = self._check_tool_rule(tool_name, arguments, rule)
            if violation is None:
                continue

            verdict.triggered_rules.append(rule.id)
            msg = rule.message or violation

            if rule.action == GuardrailAction.BLOCK:
                verdict.blocked = True
                if not verdict.message:
                    verdict.message = msg
                logger.warning("Guardrail BLOCK tool [%s]: %s", rule.id, msg)
            elif rule.action == GuardrailAction.WARN:
                verdict.warnings.append(msg)
                logger.info("Guardrail WARN tool [%s]: %s", rule.id, msg)
            elif rule.action == GuardrailAction.LOG:
                logger.info("Guardrail LOG tool [%s]: %s", rule.id, msg)

        return verdict

    def _check_tool_rule(self, tool_name: str, arguments: dict, rule: GuardrailRule) -> str | None:
        """Check a tool-call rule. Returns a reason or None."""
        if rule.blocked_tools and tool_name in rule.blocked_tools:
            return f"Tool '{tool_name}' is blocked."

        if rule.allowed_tools and tool_name not in rule.allowed_tools:
            return f"Tool '{tool_name}' is not in the allowlist."

        if tool_name in rule.tool_arg_rules:
            arg_rules = rule.tool_arg_rules[tool_name]
            for arg_name, constraints in arg_rules.items():
                arg_value = arguments.get(arg_name)

                if "required_value" in constraints:
                    if arg_value != constraints["required_value"]:
                        return (
                            f"Tool '{tool_name}' argument '{arg_name}' "
                            f"must be {constraints['required_value']!r}."
                        )

                if "denied_patterns" in constraints and isinstance(arg_value, str):
                    for pattern in constraints["denied_patterns"]:
                        try:
                            if re.search(pattern, arg_value):
                                return (
                                    f"Tool '{tool_name}' argument '{arg_name}' "
                                    f"matches blocked pattern."
                                )
                        except re.error:
                            logger.warning(
                                "Invalid regex in tool_arg_rules for %s.%s: %s",
                                tool_name, arg_name, pattern,
                            )

                if "max_length" in constraints and isinstance(arg_value, str):
                    if len(arg_value) > constraints["max_length"]:
                        return (
                            f"Tool '{tool_name}' argument '{arg_name}' exceeds "
                            f"max length {constraints['max_length']}."
                        )

        return None

    def _apply_redaction(self, text: str, rule: GuardrailRule) -> str:
        """Replace all pattern matches in *text* with the redaction string."""
        result = text
        for pattern in rule.patterns:
            try:
                result = re.sub(pattern, rule.redact_replacement, result)
            except re.error:
                pass
        return result

    @staticmethod
    def _run_custom_validator(dotted_path: str, text: str, rule: GuardrailRule) -> str | None:
        """Import and execute a custom validator function."""
        try:
            module_path, func_name = dotted_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            return func(text, rule)
        except Exception as exc:
            logger.warning("Custom validator %s failed: %s", dotted_path, exc)
            return None
