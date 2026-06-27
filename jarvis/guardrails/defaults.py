"""Built-in guardrail rules that ship with Jarvis.

These provide a sensible security baseline. Users can override or disable any
of them via ``~/.jarvis_guardrails.json``.
"""

from .models import GuardrailAction, GuardrailPhase, GuardrailRule

_SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd)\s*[:=]\s*['\"]?[^'\"\s]+['\"]?",
    r"sk-[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{36,}",
    r"AKIA[A-Z0-9]{16}",
    r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
]

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
    GuardrailRule(
        id="input-jailbreak",
        name="Jailbreak attempt detection",
        description="Blocks jailbreak attempts that try to bypass safety controls.",
        phase=GuardrailPhase.INPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)act\s+as\s+(an?\s+)?(evil|malicious|unethical|unrestricted|uncensored)",
            r"(?i)(jailbreak|jail\s*break|bypass)\s+(the\s+)?(filter|safety|restriction|guard|censor)",
            r"(?i)from\s+now\s+on\s+you\s+(will|must|should|can)\s+(not\s+)?(follow|obey|ignore)",
            r"(?i)respond\s+(without|with\s+no)\s+(any\s+)?(filter|restriction|censor|limit|moral|ethic)",
            r"(?i)(do\s+not|don'?t|never)\s+(refuse|decline|reject|censor|filter|limit)",
            r"(?i)you\s+(must|have\s+to|should)\s+answer\s+(any|every|all)\s+(question|request|prompt)",
            r"(?i)(simulate|emulate|roleplay|role[- ]play)\s+(as\s+)?(an?\s+)?(evil|malicious|unrestricted|unfiltered|uncensored)",
            r"(?i)forget\s+(all\s+)?(your\s+)?(training|rules?|restrictions?|guidelines?|programming|safety)",
        ],
        message="The message appears to contain a jailbreak attempt. This is not allowed.",
        priority=15,
    ),
    GuardrailRule(
        id="input-system-prompt-extraction",
        name="System prompt extraction prevention",
        description="Blocks attempts to extract the internal system prompt or configuration.",
        phase=GuardrailPhase.INPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)(show|reveal|display|print|output|give|tell|share|repeat|write)\s+(me\s+)?(your|the)\s+(system\s*prompt|initial\s*prompt|instructions?|programming|configuration|internal\s*(rules?|prompt))",
            r"(?i)what\s+(is|are)\s+your\s+(system\s*prompt|initial\s*(instructions?|prompt)|internal\s*(rules?|instructions?)|programming|hidden\s*instructions?)",
            r"(?i)(copy|paste|dump|leak|expose|extract|tell)\s+(me\s+)?(the\s+)?(your\s+)?(system\s*prompt|internal\s*(prompt|instructions?)|hidden\s*(prompt|instructions?))",
            r"(?i)repeat\s+(everything|all|the\s+text)\s+(above|before|from\s+the\s+(beginning|start|top))",
            r"(?i)(start|begin)\s+(your\s+)?(response|answer|reply)\s+with\s+(the|your)\s+(system|initial|internal)",
        ],
        message="Requests to reveal internal system prompts or instructions are not allowed.",
        priority=15,
    ),
    GuardrailRule(
        id="input-offensive-language",
        name="Offensive and discriminatory language filter",
        description="Blocks messages containing slurs, hate speech, or discriminatory language.",
        phase=GuardrailPhase.INPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)\b(nigger|nigga|faggot|tranny|retard|spic|kike|chink|wetback|gook|coon|darkie|raghead|towelhead|beaner)\b",
            r"(?i)\b(negro de mierda|sudaca|indio de mierda|maric[oó]n de mierda|put[oa] de mierda)\b",
            r"(?i)(heil\s+hitler|white\s+power|white\s+supremac|sieg\s+heil|death\s+to\s+(all\s+)?(jews?|muslims?|blacks?|gays?|immigrants?))",
            r"(?i)\b(kill\s+(all|every)\s+(jews?|muslims?|blacks?|whites?|gays?|trans|immigrants?|women|men))\b",
            r"(?i)\b(matar\s+(a\s+)?(todos?\s+)?(los\s+)?(negros?|jud[ií]os?|mujeres|gays?|trans|inmigrantes?))\b",
        ],
        message="The message contains offensive or discriminatory language and has been blocked.",
        priority=5,
    ),

    # ── Output guardrails ─────────────────────────────────────────────
    GuardrailRule(
        id="output-no-credentials",
        name="Credential leak prevention",
        description="Redacts patterns that look like secrets in model output.",
        phase=GuardrailPhase.OUTPUT,
        action=GuardrailAction.REDACT,
        patterns=_SECRET_PATTERNS,
        message="Potential credentials detected in output and redacted.",
        priority=10,
    ),
    GuardrailRule(
        id="output-no-system-prompt-leak",
        name="System prompt leak prevention",
        description="Blocks output that reveals the internal system prompt or configuration.",
        phase=GuardrailPhase.OUTPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)(my|the)\s+(system\s*prompt|initial\s*instructions?|internal\s*prompt|hidden\s*instructions?)\s+(is|are|says?|reads?|states?)\s*:",
            r"(?i)(here\s+is|here'?s|this\s+is)\s+(my|the)\s+(system\s*prompt|internal\s*prompt|initial\s*instructions?|programming|hidden\s*instructions?)",
            r"REGLA CR[ÍI]TICA.*NUNCA INVENTES",
            r"CRITICAL RULE.*NEVER INVENT",
            r"Eres \{name\}, un asistente de IA personal",
            r"You are \{name\}, a personal AI assistant",
        ],
        message="The response was blocked because it may reveal internal system configuration.",
        priority=5,
    ),
    GuardrailRule(
        id="output-no-offensive-language",
        name="Offensive output filter",
        description="Blocks model output containing slurs, hate speech, or discriminatory language.",
        phase=GuardrailPhase.OUTPUT,
        action=GuardrailAction.BLOCK,
        patterns=[
            r"(?i)\b(nigger|nigga|faggot|tranny|retard|spic|kike|chink|wetback|gook|coon|darkie|raghead|towelhead|beaner)\b",
            r"(?i)(heil\s+hitler|white\s+power|white\s+supremac|sieg\s+heil)",
        ],
        message="The response was blocked because it contains offensive or discriminatory language.",
        priority=5,
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
                        r"rm\s[^\n]*--no-preserve-root",
                        r"rm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\s+/(?=\s|$|[;&|])",
                        r"rm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\s+/(?=\s|$|[;&|])",
                        r"mkfs\.",
                        r"dd\s+.*of=/dev/(?:[sh]d[a-z]|nvme\d+n\d+|mapper/\S+)",
                        r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;",
                        r"chmod\s+-R\s+777\s+/\s*$",
                        r">\s*/dev/(?:[sh]d[a-z]|nvme\d+n\d+|mapper/\S+)",
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
        patterns=_SECRET_PATTERNS,
        message="Sensitive data redacted from tool result.",
        priority=10,
    ),
]
