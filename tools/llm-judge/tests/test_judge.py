"""
Tests for llm-judge core logic and providers.

All LLM calls are mocked — no API key required.
Run with: pytest tests/ -v
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from llm_judge.core import (
    JudgmentResult,
    LLMJudge,
    Verdict,
    _build_judge_prompt,
    _parse_judge_response,
)
from llm_judge.providers import (
    ALL_PROVIDERS,
    DEFAULT_MODELS,
    LLMProvider,
    PROVIDER_ANTHROPIC,
    PROVIDER_CUSTOM,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    CompletionResult,
    get_provider,
)


# ── Mock provider ──────────────────────────────────────────────────────────────

class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, response_text: str = "Mock response.", tokens: int = 100):
        self.response_text = response_text
        self.tokens = tokens
        self.calls: list[dict] = []

    def complete(self, *, system: str, user: str, model: str, max_tokens: int = 1024) -> CompletionResult:
        self.calls.append({"system": system, "user": user, "model": model})
        return CompletionResult(text=self.response_text, tokens_used=self.tokens)


def _make_judge(
    model_response: str = "Water boils at 100°C.",
    judge_response: str | None = None,
    model_tokens: int = 100,
    judge_tokens: int = 150,
) -> tuple[LLMJudge, MockProvider, MockProvider]:
    if judge_response is None:
        judge_response = json.dumps({
            "verdicts": [{"criterion": "test", "pass": True, "reasoning": "Looks good."}],
            "overall_pass": True,
            "confidence": 0.95,
        })
    model_prov = MockProvider(response_text=model_response, tokens=model_tokens)
    judge_prov = MockProvider(response_text=judge_response, tokens=judge_tokens)
    judge = LLMJudge(
        model_provider=model_prov,
        judge_provider=judge_prov,
        model="test-model",
        judge_model="test-judge",
    )
    return judge, model_prov, judge_prov


# ── Verdict dataclass ──────────────────────────────────────────────────────────

class TestVerdict:
    def test_fields_stored_correctly(self):
        v = Verdict(criterion="Must be concise", passed=True, reasoning="Short response.")
        assert v.criterion == "Must be concise"
        assert v.passed is True
        assert v.reasoning == "Short response."

    def test_failed_verdict(self):
        v = Verdict(criterion="Must mention Paris", passed=False, reasoning="Paris not mentioned.")
        assert v.passed is False


# ── JudgmentResult ─────────────────────────────────────────────────────────────

class TestJudgmentResult:
    def _make_result(self, verdicts: list[Verdict]) -> JudgmentResult:
        return JudgmentResult(
            prompt="Test prompt",
            response="Test response",
            model="test-model",
            model_provider="mock",
            judge_model="test-judge",
            judge_provider="mock",
            verdicts=verdicts,
            overall_pass=all(v.passed for v in verdicts),
            confidence=0.9,
            tokens_used=200,
            elapsed_seconds=1.5,
        )

    def test_passed_count_all_pass(self):
        verdicts = [Verdict("c1", True, "ok"), Verdict("c2", True, "ok")]
        result = self._make_result(verdicts)
        assert result.passed_count == 2

    def test_passed_count_mixed(self):
        verdicts = [Verdict("c1", True, "ok"), Verdict("c2", False, "fail")]
        result = self._make_result(verdicts)
        assert result.passed_count == 1

    def test_total_count(self):
        verdicts = [Verdict("c1", True, "ok"), Verdict("c2", True, "ok"), Verdict("c3", False, "x")]
        result = self._make_result(verdicts)
        assert result.total_count == 3

    def test_overall_pass_false_when_any_fails(self):
        verdicts = [Verdict("c1", True, "ok"), Verdict("c2", False, "nope")]
        result = self._make_result(verdicts)
        assert result.overall_pass is False

    def test_overall_pass_true_when_all_pass(self):
        verdicts = [Verdict("c1", True, "ok"), Verdict("c2", True, "ok")]
        result = self._make_result(verdicts)
        assert result.overall_pass is True


# ── Judge prompt builder ───────────────────────────────────────────────────────

class TestBuildJudgePrompt:
    def test_contains_prompt(self):
        msg = _build_judge_prompt("What is 2+2?", "4", ["Must be correct"])
        assert "What is 2+2?" in msg

    def test_contains_response(self):
        msg = _build_judge_prompt("What is 2+2?", "The answer is four.", ["Must be correct"])
        assert "The answer is four." in msg

    def test_contains_all_criteria(self):
        criteria = ["Must be correct", "Must be under 10 words", "Must not hedge"]
        msg = _build_judge_prompt("p", "r", criteria)
        for c in criteria:
            assert c in msg

    def test_criteria_numbered(self):
        msg = _build_judge_prompt("p", "r", ["First", "Second"])
        assert "1. First" in msg
        assert "2. Second" in msg

    def test_requests_json_output(self):
        msg = _build_judge_prompt("p", "r", ["c1"])
        assert "JSON" in msg or "json" in msg.lower()


# ── JSON parsing ───────────────────────────────────────────────────────────────

class TestParseJudgeResponse:
    def test_all_pass(self):
        raw = json.dumps({
            "verdicts": [
                {"criterion": "c1", "pass": True, "reasoning": "Good."},
                {"criterion": "c2", "pass": True, "reasoning": "Fine."},
            ],
            "overall_pass": True,
            "confidence": 0.9,
        })
        verdicts, overall, confidence = _parse_judge_response(raw, ["c1", "c2"])
        assert len(verdicts) == 2
        assert all(v.passed for v in verdicts)
        assert overall is True
        assert confidence == 0.9

    def test_mixed_verdicts(self):
        raw = json.dumps({
            "verdicts": [
                {"criterion": "c1", "pass": True, "reasoning": "ok"},
                {"criterion": "c2", "pass": False, "reasoning": "missing"},
            ],
            "overall_pass": False,
            "confidence": 0.7,
        })
        verdicts, overall, _ = _parse_judge_response(raw, ["c1", "c2"])
        assert verdicts[0].passed is True
        assert verdicts[1].passed is False
        assert overall is False

    def test_malformed_json_fallback(self):
        verdicts, overall, confidence = _parse_judge_response("not json at all {{}}", ["c1", "c2"])
        assert len(verdicts) == 2
        assert all(not v.passed for v in verdicts)
        assert overall is False
        assert confidence == 0.0

    def test_strips_markdown_code_fences(self):
        raw = "```json\n" + json.dumps({
            "verdicts": [{"criterion": "c1", "pass": True, "reasoning": "ok"}],
            "overall_pass": True,
            "confidence": 0.85,
        }) + "\n```"
        verdicts, overall, _ = _parse_judge_response(raw, ["c1"])
        assert verdicts[0].passed is True

    def test_reasoning_preserved(self):
        raw = json.dumps({
            "verdicts": [{"criterion": "c1", "pass": True, "reasoning": "Specific reason here."}],
            "overall_pass": True,
            "confidence": 0.9,
        })
        verdicts, _, _ = _parse_judge_response(raw, ["c1"])
        assert verdicts[0].reasoning == "Specific reason here."


# ── LLMJudge.run ──────────────────────────────────────────────────────────────

class TestLLMJudgeRun:
    def test_returns_judgment_result(self):
        judge, _, _ = _make_judge()
        result = judge.run("What is 2+2?", ["Must answer 4"])
        assert isinstance(result, JudgmentResult)

    def test_prompt_stored_in_result(self):
        judge, _, _ = _make_judge()
        result = judge.run("My specific prompt.", ["c1"])
        assert result.prompt == "My specific prompt."

    def test_model_response_stored(self):
        judge, _, _ = _make_judge(model_response="The answer is 4.")
        result = judge.run("What is 2+2?", ["c1"])
        assert result.response == "The answer is 4."

    def test_token_count_is_sum_of_both_calls(self):
        judge, _, _ = _make_judge(model_tokens=100, judge_tokens=150)
        result = judge.run("prompt", ["c1"])
        assert result.tokens_used == 250

    def test_elapsed_seconds_non_negative(self):
        judge, _, _ = _make_judge()
        result = judge.run("prompt", ["c1"])
        assert result.elapsed_seconds >= 0

    def test_model_called_with_correct_model_id(self):
        judge, model_prov, _ = _make_judge()
        judge.run("prompt", ["c1"])
        assert model_prov.calls[0]["model"] == "test-model"

    def test_judge_called_with_judge_model_id(self):
        judge, _, judge_prov = _make_judge()
        judge.run("prompt", ["c1"])
        assert judge_prov.calls[0]["model"] == "test-judge"

    def test_judge_prompt_contains_model_response(self):
        judge, _, judge_prov = _make_judge(model_response="Paris is the capital.")
        judge.run("What is the capital of France?", ["c1"])
        assert "Paris is the capital." in judge_prov.calls[0]["user"]

    def test_empty_prompt_raises(self):
        judge, _, _ = _make_judge()
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            judge.run("   ", ["c1"])

    def test_empty_criteria_raises(self):
        judge, _, _ = _make_judge()
        with pytest.raises(ValueError, match="At least one criterion"):
            judge.run("Some prompt", [])

    def test_provider_names_stored(self):
        judge, _, _ = _make_judge()
        result = judge.run("prompt", ["c1"])
        assert result.model_provider == "mock"
        assert result.judge_provider == "mock"


# ── Provider factory ───────────────────────────────────────────────────────────

class TestGetProvider:
    def test_all_providers_listed(self):
        for p in [PROVIDER_ANTHROPIC, PROVIDER_OPENAI, PROVIDER_GEMINI, PROVIDER_CUSTOM]:
            assert p in ALL_PROVIDERS

    def test_default_models_exist_for_all(self):
        for p in ALL_PROVIDERS:
            assert p in DEFAULT_MODELS
            assert DEFAULT_MODELS[p]

    def test_get_anthropic_with_key(self):
        from llm_judge.providers import AnthropicProvider
        with patch.object(AnthropicProvider, "__init__", return_value=None):
            provider = get_provider(PROVIDER_ANTHROPIC, api_key="sk-ant-test")
            assert isinstance(provider, AnthropicProvider)

    def test_get_gemini_with_key(self):
        from llm_judge.providers import GeminiProvider
        with patch.object(GeminiProvider, "__init__", return_value=None):
            provider = get_provider(PROVIDER_GEMINI, api_key="AI-test")
            assert isinstance(provider, GeminiProvider)

    def test_get_openai_with_key(self):
        from llm_judge.providers import OpenAIProvider
        with patch.object(OpenAIProvider, "__init__", return_value=None):
            provider = get_provider(PROVIDER_OPENAI, api_key="sk-test")
            assert isinstance(provider, OpenAIProvider)

    def test_anthropic_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Anthropic API key required"):
            get_provider(PROVIDER_ANTHROPIC)

    def test_gemini_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Google API key required"):
            get_provider(PROVIDER_GEMINI)

    def test_openai_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key required"):
            get_provider(PROVIDER_OPENAI)

    def test_custom_raises_without_url(self, monkeypatch):
        monkeypatch.delenv("CUSTOM_BASE_URL", raising=False)
        with pytest.raises(ValueError, match="Custom provider base URL required"):
            get_provider(PROVIDER_CUSTOM, api_key="key")

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("grok")

    def test_provider_name_case_insensitive(self):
        from llm_judge.providers import GeminiProvider
        with patch.object(GeminiProvider, "__init__", return_value=None):
            provider = get_provider("GEMINI", api_key="AI-test")
            assert isinstance(provider, GeminiProvider)
