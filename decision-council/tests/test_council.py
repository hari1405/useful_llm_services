"""
Tests for council.py and providers.py

All LLM-dependent tests use a mock provider — no API key required.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from council.council import CouncilSession, DecisionCouncil, PersonaResponse
from council.personas import DEFAULT_PERSONAS, build_custom_persona
from council.providers import (
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


# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_PROPOSAL = (
    "I want to build a multi-agent system that automates our EMEA regulatory "
    "compliance review process. The system will use Claude to parse regulatory "
    "documents, identify requirements, and generate a structured compliance report. "
    "Estimated savings: $2.5M annually in manual review costs."
)

SAMPLE_CONTEXT = "Team size: 3 engineers. Timeline: 6 months. Stack: Python + Anthropic API."


class MockProvider(LLMProvider):
    """
    In-memory mock LLM provider.
    Returns a configurable response for all complete() calls.
    """
    name = "mock"

    def __init__(self, response_text: str = "Mock critique.", tokens: int = 300):
        self.response_text = response_text
        self.tokens = tokens
        self.calls: list[dict] = []

    def complete(self, *, system: str, user: str, model: str, max_tokens: int = 1024) -> CompletionResult:
        self.calls.append({"system": system, "user": user, "model": model})
        return CompletionResult(text=self.response_text, tokens_used=self.tokens)


def make_council(response_text: str = "Mock critique.", tokens: int = 300) -> tuple[DecisionCouncil, MockProvider]:
    mock = MockProvider(response_text=response_text, tokens=tokens)
    council = DecisionCouncil(_provider_instance=mock)
    return council, mock


# ── Provider tests ─────────────────────────────────────────────────────────────

class TestGetProvider:
    def test_all_providers_listed(self):
        assert PROVIDER_ANTHROPIC in ALL_PROVIDERS
        assert PROVIDER_OPENAI in ALL_PROVIDERS
        assert PROVIDER_GEMINI in ALL_PROVIDERS
        assert PROVIDER_CUSTOM in ALL_PROVIDERS

    def test_default_models_exist_for_all_providers(self):
        for p in ALL_PROVIDERS:
            assert p in DEFAULT_MODELS
            assert DEFAULT_MODELS[p]  # non-empty string

    def test_get_anthropic_with_key(self):
        from council.providers import AnthropicProvider
        with patch.object(AnthropicProvider, "__init__", return_value=None):
            provider = get_provider(PROVIDER_ANTHROPIC, api_key="sk-ant-test")
            assert isinstance(provider, AnthropicProvider)

    def test_get_anthropic_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env")
        from council.providers import AnthropicProvider
        with patch.object(AnthropicProvider, "__init__", return_value=None):
            provider = get_provider(PROVIDER_ANTHROPIC)
            assert isinstance(provider, AnthropicProvider)

    def test_get_anthropic_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Anthropic API key required"):
            get_provider(PROVIDER_ANTHROPIC)

    def test_get_openai_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OpenAI API key required"):
            get_provider(PROVIDER_OPENAI)

    def test_get_gemini_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Google API key required"):
            get_provider(PROVIDER_GEMINI)

    def test_get_custom_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("CUSTOM_API_KEY", raising=False)
        monkeypatch.delenv("CUSTOM_BASE_URL", raising=False)
        with pytest.raises(ValueError, match="Custom provider API key required"):
            get_provider(PROVIDER_CUSTOM)

    def test_get_custom_raises_without_base_url(self, monkeypatch):
        monkeypatch.delenv("CUSTOM_BASE_URL", raising=False)
        with pytest.raises(ValueError, match="Custom provider base URL required"):
            get_provider(PROVIDER_CUSTOM, api_key="my-key")

    def test_get_custom_with_key_and_url(self):
        from council.providers import CustomProvider
        with patch.object(CustomProvider, "__init__", return_value=None):
            provider = get_provider(PROVIDER_CUSTOM, api_key="key", base_url="https://api.example.com/v1")
            assert isinstance(provider, CustomProvider)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("grok")

    def test_provider_name_case_insensitive(self):
        from council.providers import AnthropicProvider
        with patch.object(AnthropicProvider, "__init__", return_value=None):
            provider = get_provider("ANTHROPIC", api_key="sk-ant-test")
            assert isinstance(provider, AnthropicProvider)


# ── DecisionCouncil initialisation ────────────────────────────────────────────

class TestDecisionCouncilInit:
    def test_init_with_mock_provider(self):
        council, _ = make_council()
        assert council is not None

    def test_init_with_explicit_anthropic_key(self):
        from council.providers import AnthropicProvider
        with patch.object(AnthropicProvider, "__init__", return_value=None):
            council = DecisionCouncil(provider="anthropic", api_key="sk-ant-test")
            assert council is not None

    def test_init_from_env_var(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
        from council.providers import AnthropicProvider
        with patch.object(AnthropicProvider, "__init__", return_value=None):
            council = DecisionCouncil(provider="anthropic")
            assert council is not None

    def test_init_raises_without_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(ValueError):
            DecisionCouncil(provider="anthropic")

    def test_default_model_from_provider(self):
        council, _ = make_council()
        # Mock provider doesn't have a key in DEFAULT_MODELS, so falls back to gpt-4o-mini
        assert council.model is not None

    def test_custom_model_override(self):
        mock = MockProvider()
        council = DecisionCouncil(_provider_instance=mock, model="my-custom-model")
        assert council.model == "my-custom-model"

    def test_default_max_tokens(self):
        council, _ = make_council()
        assert council.max_tokens == 1024

    def test_custom_max_tokens(self):
        mock = MockProvider()
        council = DecisionCouncil(_provider_instance=mock, max_tokens=512)
        assert council.max_tokens == 512

    def test_provider_name_stored(self):
        council, _ = make_council()
        assert council.provider_name == "mock"


# ── Single critique ────────────────────────────────────────────────────────────

class TestCritique:
    def test_critique_returns_persona_response(self):
        council, mock = make_council("This has serious flaws.")
        persona = DEFAULT_PERSONAS[0]
        response = council.critique(SAMPLE_PROPOSAL, persona)

        assert isinstance(response, PersonaResponse)
        assert response.persona == persona
        assert response.critique == "This has serious flaws."
        assert response.tokens_used == 300
        assert response.elapsed_seconds >= 0

    def test_critique_includes_context_in_message(self):
        council, mock = make_council()
        council.critique(SAMPLE_PROPOSAL, DEFAULT_PERSONAS[0], context=SAMPLE_CONTEXT)

        last_call = mock.calls[-1]
        assert "Additional Context" in last_call["user"]
        assert SAMPLE_CONTEXT in last_call["user"]

    def test_critique_passes_persona_system_prompt(self):
        council, mock = make_council()
        persona = DEFAULT_PERSONAS[0]
        council.critique(SAMPLE_PROPOSAL, persona)

        last_call = mock.calls[-1]
        assert last_call["system"] == persona.system_prompt

    def test_critique_no_context(self):
        council, mock = make_council()
        council.critique(SAMPLE_PROPOSAL, DEFAULT_PERSONAS[0])

        last_call = mock.calls[-1]
        assert "Additional Context" not in last_call["user"]

    def test_critique_passes_model_to_provider(self):
        mock = MockProvider()
        council = DecisionCouncil(_provider_instance=mock, model="test-model-x")
        council.critique(SAMPLE_PROPOSAL, DEFAULT_PERSONAS[0])

        assert mock.calls[-1]["model"] == "test-model-x"


# ── Full council run ───────────────────────────────────────────────────────────

class TestCouncilRun:
    def test_run_returns_council_session(self):
        council, _ = make_council()
        session = council.run(SAMPLE_PROPOSAL, DEFAULT_PERSONAS[:2])

        assert isinstance(session, CouncilSession)
        assert len(session.responses) == 2
        assert session.proposal == SAMPLE_PROPOSAL
        assert session.synthesis

    def test_run_stores_provider_info(self):
        council, _ = make_council()
        session = council.run(SAMPLE_PROPOSAL, DEFAULT_PERSONAS[:1])

        assert session.provider_name == "mock"
        assert session.model is not None

    def test_run_calls_on_persona_callbacks(self):
        council, _ = make_council()
        started = []
        finished = []

        personas = DEFAULT_PERSONAS[:3]
        council.run(
            SAMPLE_PROPOSAL,
            personas,
            on_persona_start=lambda p: started.append(p.name),
            on_persona_done=lambda r: finished.append(r.persona.name),
        )

        assert len(started) == 3
        assert len(finished) == 3
        assert started == [p.name for p in personas]

    def test_run_accumulates_tokens(self):
        council, _ = make_council(tokens=300)
        personas = DEFAULT_PERSONAS[:2]
        session = council.run(SAMPLE_PROPOSAL, personas)

        # 2 personas × 300 + 1 synthesis × 300 = 900
        assert session.total_tokens == 900

    def test_run_with_single_custom_persona(self):
        council, _ = make_council("Custom critique.")
        custom = build_custom_persona(
            name="The Customer",
            role="Enterprise Buyer",
            emoji="🛒",
            focus="Price, vendor reliability, integration complexity",
        )
        session = council.run(SAMPLE_PROPOSAL, [custom])
        assert session.responses[0].persona.name == "The Customer"
        assert "Custom critique." in session.responses[0].critique

    def test_run_with_context(self):
        council, mock = make_council()
        council.run(SAMPLE_PROPOSAL, DEFAULT_PERSONAS[:1], context=SAMPLE_CONTEXT)

        # Verify context was included in user messages
        user_messages = [c["user"] for c in mock.calls]
        assert any(SAMPLE_CONTEXT in msg for msg in user_messages)


# ── Markdown export ────────────────────────────────────────────────────────────

class TestMarkdownExport:
    def test_to_markdown_contains_proposal(self):
        council, _ = make_council("Some critique.")
        session = council.run(SAMPLE_PROPOSAL, [DEFAULT_PERSONAS[0]])
        md = DecisionCouncil.to_markdown(session)

        assert "Decision Council Report" in md
        assert "Battle Brief" in md
        assert DEFAULT_PERSONAS[0].name in md

    def test_to_markdown_contains_provider_info(self):
        council, _ = make_council()
        session = council.run(SAMPLE_PROPOSAL, [DEFAULT_PERSONAS[0]])
        md = DecisionCouncil.to_markdown(session)

        assert "mock" in md  # provider name appears in footer

    def test_to_markdown_truncates_long_proposals(self):
        council, _ = make_council()
        long_proposal = "X" * 500
        session = council.run(long_proposal, [DEFAULT_PERSONAS[0]])
        md = DecisionCouncil.to_markdown(session)

        assert "..." in md

    def test_to_markdown_contains_all_personas(self):
        council, _ = make_council()
        personas = DEFAULT_PERSONAS[:3]
        session = council.run(SAMPLE_PROPOSAL, personas)
        md = DecisionCouncil.to_markdown(session)

        for p in personas:
            assert p.name in md


# ── Message builder ────────────────────────────────────────────────────────────

class TestBuildUserMessage:
    def test_message_contains_proposal(self):
        msg = DecisionCouncil._build_user_message(SAMPLE_PROPOSAL, "")
        assert SAMPLE_PROPOSAL in msg

    def test_message_with_context(self):
        msg = DecisionCouncil._build_user_message(SAMPLE_PROPOSAL, SAMPLE_CONTEXT)
        assert "Additional Context" in msg
        assert SAMPLE_CONTEXT in msg

    def test_message_without_context_has_no_context_header(self):
        msg = DecisionCouncil._build_user_message(SAMPLE_PROPOSAL, "")
        assert "Additional Context" not in msg

    def test_message_strips_whitespace(self):
        msg = DecisionCouncil._build_user_message("  " + SAMPLE_PROPOSAL + "  ", "  ")
        assert not msg.startswith(" ")


# ── MockProvider sanity check ──────────────────────────────────────────────────

class TestMockProvider:
    def test_mock_provider_returns_completion(self):
        mock = MockProvider("hello world", tokens=42)
        result = mock.complete(system="sys", user="usr", model="x")
        assert result.text == "hello world"
        assert result.tokens_used == 42

    def test_mock_provider_records_calls(self):
        mock = MockProvider()
        mock.complete(system="sys1", user="usr1", model="m1")
        mock.complete(system="sys2", user="usr2", model="m2")
        assert len(mock.calls) == 2
        assert mock.calls[0]["system"] == "sys1"
        assert mock.calls[1]["model"] == "m2"
