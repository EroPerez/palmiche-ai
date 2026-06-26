"""Built-in guardrail rules that ship with Jarvis.

These provide a sensible security baseline. Users can override or disable any
of them via ``~/.jarvis_guardrails.json``.
"""

from .models import GuardrailAction, GuardrailPhase, GuardrailRule

DEFAULT_RULES: list[GuardrailRule] = [
    # ── Input guardrails ──────────────────────────────────────────────
    GuardrailRule(
        id="input-max-length",
        name="Input length limit",
        description="Prevents excessively long inputs that could abuse token limits.",
        phase=GuardrailPhase.INPUT,
        action=GuardrailAction.BLOCK,
        max_length=50_000,
        message="Input exceeds the maximum allowed length (50,000 characters).",
        priority=10,
    ),
    GuardrailRule(
        id="input-prompt-injection",
        name="Prompt injection detection",
        description="Blocks common prompt injection patterns.",
        phase=GuardrailPhase.INPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
            r"(?i)you\s+are\s+now\s+(DAN|jailbr[eo]aken|unrestricted|unfiltered)",
            r"(?i)disregard\s+(all\s+)?(your\s+)?(instructions?|guidelines?|rules?|programming)",
            r"(?i)override\s+(your\s+)?(safety|system|core)\s*(prompt|instructions?|rules?)",
            r"(?i)pretend\s+(you\s+)?(are|have)\s+no\s+(restrictions?|rules?|limits?|guidelines?)",
            r"(?i)enter\s+(developer|god|admin|sudo|root)\s*mode",
        ],
        message="The message appears to contain a prompt injection attempt.",
        priority=20,
    ),

    # ── Output guardrails ─────────────────────────────────────────────
    GuardrailRule(
        id="output-no-credentials",
        name="Credential leak prevention",
        description="Redacts patterns that look like secrets in model output.",
        phase=GuardrailPhase.OUTPUT,
        action=GuardrailAction.REDACT,
        patterns=[
            r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}",
            r"sk-[A-Za-z0-9]{20,}",
            r"ghp_[A-Za-z0-9]{36,}",
            r"AKIA[A-Z0-9]{16}",
            r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
        ],
        message="Potential credentials detected in output and redacted.",
        priority=10,
    ),
    GuardrailRule(
        id="output-no-harmful-instructions",
        name="Harmful content filter",
        description="Blocks output that contains instructions for dangerous activities.",
        phase=GuardrailPhase.OUTPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)how\s+to\s+(make|build|create|construct)\s+(a\s+)?(bomb|explosive|weapon)",
            r"(?i)step[- ]by[- ]step\s+(guide|instructions?)\s+(to|for)\s+(hack|exploit|attack)",
        ],
        message="The response was blocked because it may contain harmful content.",
        priority=10,
    ),
    GuardrailRule(
        id="output-max-length",
        name="Output length limit",
        description="Prevents runaway generation from consuming excessive resources.",
        phase=GuardrailPhase.OUTPUT,
        action=GuardrailAction.BLOCK,
        max_length=100_000,
        message="Model output exceeds the maximum allowed length.",
        priority=50,
    ),

    # ── Tool call guardrails ──────────────────────────────────────────
    GuardrailRule(
        id="tool-block-dangerous-shell",
        name="Dangerous shell command blocker",
        description="Blocks shell commands that could cause irreversible damage.",
        phase=GuardrailPhase.TOOL_CALL,
        blocked_tools=[],
        tool_arg_rules={
            "run_shell_command": {
                "command": {
                    "denied_patterns": [
                        r"rm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+/\s*$",
                        r"rm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+/\s*$",
                        r"mkfs\.",
                        r"dd\s+.*of=/dev/[sh]d[a-z]",
                        r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;",
                        r"chmod\s+-R\s+777\s+/\s*$",
                        r">\s*/dev/[sh]d[a-z]",
                    ],
                },
            },
        },
        message="This shell command was blocked because it could cause irreversible damage.",
        priority=10,
    ),
    GuardrailRule(
        id="tool-require-confirmation",
        name="Destructive tool confirmation enforcer",
        description="Ensures destructive tools always receive explicit confirmation.",
        phase=GuardrailPhase.TOOL_CALL,
        tool_arg_rules={
            "power_action": {
                "confirmed": {"required_value": True},
            },
            "delete_file": {
                "confirmed": {"required_value": True},
            },
        },
        message="Destructive action attempted without explicit confirmation.",
        priority=20,
    ),

    # ── Tool result guardrails ────────────────────────────────────────
    GuardrailRule(
        id="tool-result-no-secrets",
        name="Tool result secret redaction",
        description="Redacts secrets that appear in tool execution results.",
        phase=GuardrailPhase.TOOL_RESULT,
        action=GuardrailAction.REDACT,
        patterns=[
            r"(?i)(password|passwd|secret|token|api_key)\s*[:=]\s*\S+",
            r"sk-[A-Za-z0-9]{20,}",
            r"ghp_[A-Za-z0-9]{36,}",
            r"AKIA[A-Z0-9]{16}",
        ],
        message="Sensitive data redacted from tool result.",
        priority=10,
    ),
]
