"""Verify API key priority and fallback behaviour across all backends.

Rules under test:
  1. JARVIS_API_KEY takes priority over any provider-specific key.
  2. When JARVIS_API_KEY is absent, provider-specific keys are used as fallback:
       anthropic/* → ANTHROPIC_API_KEY
       gemini/*    → GOOGLE_API_KEY  (via LiteLLM)
       gemini-*    → GOOGLE_API_KEY  (ADK native, sets os.environ)
       openai/*, groq/*, etc. → LiteLLM reads the right env var automatically
  3. An explicit api_key_override (internal, from legacy-alias backends) wins over
     everything else.
  4. JARVIS_BASE_URL is used as the provider base URL; base_url_override takes
     priority (e.g. JARVIS_OLLAMA_HOST).
  5. JarvisAgent (anthropic SDK loop) also respects JARVIS_API_KEY over
     ANTHROPIC_API_KEY.

Run with:
    python -m pytest tests/test_api_key_resolution.py -v
"""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jarvis.brain.adk_universal as universal
from jarvis.brain.adk_universal import _effective_api_key, _normalize_model_str


# ---------------------------------------------------------------------------
# _effective_api_key — priority table
# ---------------------------------------------------------------------------

class TestEffectiveApiKey:
    """Priority: api_key_override > JARVIS_API_KEY > provider fallback."""

    def _patch(self, jarvis_key="", anthropic_key="", google_key=""):
        return patch.multiple(
            "jarvis.brain.adk_universal",
            JARVIS_API_KEY=jarvis_key,
            ANTHROPIC_API_KEY=anthropic_key,
            GOOGLE_API_KEY=google_key,
        )

    def test_api_key_override_wins_over_all(self):
        with self._patch(jarvis_key="jarvis-key", anthropic_key="ant-key"):
            result = _effective_api_key("anthropic", api_key_override="override-key")
        assert result == "override-key"

    def test_jarvis_api_key_wins_over_anthropic_fallback(self):
        with self._patch(jarvis_key="jarvis-key", anthropic_key="ant-key"):
            result = _effective_api_key("anthropic")
        assert result == "jarvis-key"

    def test_jarvis_api_key_wins_over_google_fallback(self):
        with self._patch(jarvis_key="jarvis-key", google_key="google-key"):
            result = _effective_api_key("gemini")
        assert result == "jarvis-key"

    def test_jarvis_api_key_wins_for_openai_provider(self):
        with self._patch(jarvis_key="jarvis-key"):
            result = _effective_api_key("openai")
        assert result == "jarvis-key"

    def test_anthropic_fallback_when_jarvis_absent(self):
        with self._patch(jarvis_key="", anthropic_key="ant-key"):
            result = _effective_api_key("anthropic")
        assert result == "ant-key"

    def test_google_fallback_when_jarvis_absent(self):
        with self._patch(jarvis_key="", google_key="google-key"):
            result = _effective_api_key("gemini")
        assert result == "google-key"

    def test_google_fallback_for_vertex_ai(self):
        with self._patch(jarvis_key="", google_key="google-key"):
            result = _effective_api_key("vertex_ai")
        assert result == "google-key"

    def test_no_key_returns_empty_for_openai(self):
        """openai/* falls back to OPENAI_API_KEY via LiteLLM — returns '' here."""
        with self._patch(jarvis_key="", anthropic_key="", google_key=""):
            result = _effective_api_key("openai")
        assert result == ""

    def test_both_keys_absent_returns_empty(self):
        with self._patch(jarvis_key="", anthropic_key="", google_key=""):
            result = _effective_api_key("anthropic")
        assert result == ""


# ---------------------------------------------------------------------------
# _resolve_model — LiteLlm kwargs correctness
# ---------------------------------------------------------------------------

class TestResolveModel:
    """_resolve_model must pass the right api_key and api_base to LiteLlm."""

    def _run(self, model_str, *, jarvis_key="", anthropic_key="",
             google_key="", base_url="", api_key_override=None, base_url_override=None):
        mock_litellm_cls = MagicMock()
        mock_litellm_cls.return_value = MagicMock()

        with patch.multiple(
            "jarvis.brain.adk_universal",
            JARVIS_API_KEY=jarvis_key,
            ANTHROPIC_API_KEY=anthropic_key,
            GOOGLE_API_KEY=google_key,
            JARVIS_BASE_URL=base_url,
        ), patch("jarvis.brain.adk_universal.LiteLlm", mock_litellm_cls, create=True):
            # Patch the lazy import inside _resolve_model
            import importlib
            with patch.dict("sys.modules", {
                "google.adk.models.lite_llm": MagicMock(LiteLlm=mock_litellm_cls)
            }):
                from jarvis.brain.adk_universal import _resolve_model
                _resolve_model(
                    model_str,
                    api_key_override=api_key_override,
                    base_url_override=base_url_override,
                )

        return mock_litellm_cls.call_args

    def test_jarvis_api_key_passed_to_litellm_for_anthropic(self):
        call = self._run(
            "anthropic/claude-haiku-4-5-20251001",
            jarvis_key="jarvis-key",
            anthropic_key="ant-key",
        )
        assert call is not None
        kwargs = call.kwargs if call.kwargs else call[1]
        assert kwargs.get("api_key") == "jarvis-key"

    def test_fallback_anthropic_key_used_when_jarvis_absent(self):
        call = self._run(
            "anthropic/claude-haiku-4-5-20251001",
            jarvis_key="",
            anthropic_key="ant-fallback",
        )
        assert call is not None
        kwargs = call.kwargs if call.kwargs else call[1]
        assert kwargs.get("api_key") == "ant-fallback"

    def test_no_api_key_kwarg_when_both_absent(self):
        call = self._run(
            "anthropic/claude-haiku-4-5-20251001",
            jarvis_key="",
            anthropic_key="",
        )
        assert call is not None
        kwargs = call.kwargs if call.kwargs else call[1]
        assert "api_key" not in kwargs

    def test_base_url_passed_to_litellm(self):
        call = self._run(
            "ollama_chat/llama3.2",
            base_url="http://localhost:11434",
        )
        assert call is not None
        kwargs = call.kwargs if call.kwargs else call[1]
        assert kwargs.get("api_base") == "http://localhost:11434"

    def test_base_url_override_wins_over_jarvis_base_url(self):
        call = self._run(
            "ollama_chat/llama3.2",
            base_url="http://default:11434",
            base_url_override="http://override:11434",
        )
        assert call is not None
        kwargs = call.kwargs if call.kwargs else call[1]
        assert kwargs.get("api_base") == "http://override:11434"

    def test_api_key_override_wins_over_jarvis_api_key(self):
        call = self._run(
            "anthropic/claude-haiku-4-5-20251001",
            jarvis_key="jarvis-key",
            anthropic_key="ant-key",
            api_key_override="override-key",
        )
        assert call is not None
        kwargs = call.kwargs if call.kwargs else call[1]
        assert kwargs.get("api_key") == "override-key"


# ---------------------------------------------------------------------------
# Native Gemini path — sets os.environ["GOOGLE_API_KEY"]
# ---------------------------------------------------------------------------

class TestNativeGeminiKeyResolution:
    """Bare gemini names go through ADK natively; key is set in os.environ."""

    def _patch(self, jarvis_key="", google_key=""):
        return patch.multiple(
            "jarvis.brain.adk_universal",
            JARVIS_API_KEY=jarvis_key,
            GOOGLE_API_KEY=google_key,
        )

    def test_jarvis_api_key_written_to_env_for_native_gemini(self):
        env_before = os.environ.get("GOOGLE_API_KEY", "")
        try:
            with self._patch(jarvis_key="jarvis-google-key", google_key="old-google-key"):
                from jarvis.brain.adk_universal import _resolve_model
                result = _resolve_model("gemini-2.0-flash")
            assert os.environ["GOOGLE_API_KEY"] == "jarvis-google-key"
            assert result == "gemini-2.0-flash"  # bare name returned as-is for ADK
        finally:
            # Restore
            if env_before:
                os.environ["GOOGLE_API_KEY"] = env_before
            else:
                os.environ.pop("GOOGLE_API_KEY", None)

    def test_google_fallback_written_when_jarvis_absent(self):
        env_before = os.environ.get("GOOGLE_API_KEY", "")
        try:
            with self._patch(jarvis_key="", google_key="google-fallback"):
                from jarvis.brain.adk_universal import _resolve_model
                _resolve_model("gemini-2.0-flash")
            assert os.environ["GOOGLE_API_KEY"] == "google-fallback"
        finally:
            if env_before:
                os.environ["GOOGLE_API_KEY"] = env_before
            else:
                os.environ.pop("GOOGLE_API_KEY", None)

    def test_jarvis_key_overwrites_existing_env_var(self):
        """JARVIS_API_KEY must overwrite (not setdefault) an existing GOOGLE_API_KEY."""
        os.environ["GOOGLE_API_KEY"] = "pre-existing"
        try:
            with self._patch(jarvis_key="jarvis-wins", google_key="google-key"):
                from jarvis.brain.adk_universal import _resolve_model
                _resolve_model("gemini-2.0-flash")
            assert os.environ["GOOGLE_API_KEY"] == "jarvis-wins"
        finally:
            os.environ.pop("GOOGLE_API_KEY", None)


# ---------------------------------------------------------------------------
# JarvisAgent (anthropic SDK backend) — respects JARVIS_API_KEY
# ---------------------------------------------------------------------------

class TestJarvisAgentApiKeyPriority:
    """JarvisAgent must prefer JARVIS_API_KEY over ANTHROPIC_API_KEY."""

    def _build_agent_kwargs(self, jarvis_key="", anthropic_key="", model="claude-haiku-4-5-20251001"):
        """Instantiate JarvisAgent via object.__new__ (no network call) and return
        the api_key that was passed to the Anthropic client constructor."""
        captured = {}

        class FakeAnthropic:
            def __init__(self, api_key=None):
                captured["api_key"] = api_key

        with patch.multiple(
            "jarvis.brain.agent",
            JARVIS_API_KEY=jarvis_key,
            ANTHROPIC_API_KEY=anthropic_key,
            JARVIS_MODEL=model,
            JARVIS_GUARDRAILS_ENABLED=False,
        ), patch("jarvis.brain.agent.anthropic.Anthropic", FakeAnthropic):
            from jarvis.brain.agent import JarvisAgent
            agent = JarvisAgent.__new__(JarvisAgent)
            JarvisAgent.__init__(agent)

        return captured["api_key"]

    def test_jarvis_api_key_wins_over_anthropic_api_key(self):
        key = self._build_agent_kwargs(
            jarvis_key="jarvis-unified-key",
            anthropic_key="ant-specific-key",
        )
        assert key == "jarvis-unified-key"

    def test_anthropic_fallback_when_jarvis_absent(self):
        key = self._build_agent_kwargs(
            jarvis_key="",
            anthropic_key="ant-fallback-key",
        )
        assert key == "ant-fallback-key"

    def test_model_prefix_stripped(self):
        """JarvisAgent strips 'anthropic/' so the SDK gets a bare model name."""
        from jarvis.brain.agent import JarvisAgent

        class FakeAnthropic:
            def __init__(self, api_key=None):
                pass

        with patch.multiple(
            "jarvis.brain.agent",
            JARVIS_API_KEY="",
            ANTHROPIC_API_KEY="key",
            JARVIS_MODEL="anthropic/claude-haiku-4-5-20251001",
            JARVIS_GUARDRAILS_ENABLED=False,
        ), patch("jarvis.brain.agent.anthropic.Anthropic", FakeAnthropic):
            agent = JarvisAgent.__new__(JarvisAgent)
            JarvisAgent.__init__(agent)

        assert agent._model == "claude-haiku-4-5-20251001"

    def test_bare_model_name_unchanged(self):
        """If the model has no prefix, it passes through unchanged."""
        from jarvis.brain.agent import JarvisAgent

        class FakeAnthropic:
            def __init__(self, api_key=None):
                pass

        with patch.multiple(
            "jarvis.brain.agent",
            JARVIS_API_KEY="",
            ANTHROPIC_API_KEY="key",
            JARVIS_MODEL="claude-haiku-4-5-20251001",
            JARVIS_GUARDRAILS_ENABLED=False,
        ), patch("jarvis.brain.agent.anthropic.Anthropic", FakeAnthropic):
            agent = JarvisAgent.__new__(JarvisAgent)
            JarvisAgent.__init__(agent)

        assert agent._model == "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# JARVIS_BASE_URL fallback chain
# ---------------------------------------------------------------------------

class TestBaseUrlResolution:
    """JARVIS_BASE_URL applies globally; base_url_override (ollama alias) wins."""

    def _patch_base_url(self, base_url=""):
        return patch("jarvis.brain.adk_universal.JARVIS_BASE_URL", base_url)

    def test_jarvis_base_url_applied_when_set(self):
        mock_cls = MagicMock()
        with self._patch_base_url("http://custom:8000/v1"), \
             patch.dict("sys.modules", {
                 "google.adk.models.lite_llm": MagicMock(LiteLlm=mock_cls)
             }), \
             patch("jarvis.brain.adk_universal.JARVIS_API_KEY", "key"), \
             patch("jarvis.brain.adk_universal.ANTHROPIC_API_KEY", ""), \
             patch("jarvis.brain.adk_universal.GOOGLE_API_KEY", ""):
            from jarvis.brain.adk_universal import _resolve_model
            _resolve_model("anthropic/claude-haiku-4-5-20251001")

        kwargs = mock_cls.call_args[1] if mock_cls.call_args else {}
        assert kwargs.get("api_base") == "http://custom:8000/v1"

    def test_no_api_base_kwarg_when_base_url_empty(self):
        mock_cls = MagicMock()
        with self._patch_base_url(""), \
             patch.dict("sys.modules", {
                 "google.adk.models.lite_llm": MagicMock(LiteLlm=mock_cls)
             }), \
             patch("jarvis.brain.adk_universal.JARVIS_API_KEY", "key"), \
             patch("jarvis.brain.adk_universal.ANTHROPIC_API_KEY", ""), \
             patch("jarvis.brain.adk_universal.GOOGLE_API_KEY", ""):
            from jarvis.brain.adk_universal import _resolve_model
            _resolve_model("anthropic/claude-haiku-4-5-20251001")

        kwargs = mock_cls.call_args[1] if mock_cls.call_args else {}
        assert "api_base" not in kwargs
