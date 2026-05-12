"""
Tests for the CLI (main.py) — no API key required.

Uses Typer's CliRunner and mocks all LLM calls.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from council.main import app
from council.providers import CompletionResult

runner = CliRunner()


# ── Helper: build a fake CouncilSession ───────────────────────────────────────

def _fake_session(personas=None):
    """Build a minimal fake CouncilSession for CLI tests."""
    from council.council import CouncilSession, PersonaResponse
    from council.personas import DEFAULT_PERSONAS

    personas = personas or [DEFAULT_PERSONAS[0]]
    return CouncilSession(
        proposal="Test proposal",
        context="",
        responses=[
            PersonaResponse(
                persona=p,
                critique="Mock critique.",
                tokens_used=100,
                elapsed_seconds=0.5,
            )
            for p in personas
        ],
        synthesis="**Top 3 Hardest Questions**\n1. Q1\n2. Q2\n3. Q3",
        total_tokens=len(personas) * 100 + 100,
        total_elapsed=1.0,
        provider_name="anthropic",
        model="claude-haiku-4-5-20251001",
    )


# ── List commands ─────────────────────────────────────────────────────────────

class TestListCommand:
    def test_list_shows_all_personas(self):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "The CFO" in result.output
        assert "The Skeptical Eng" in result.output
        assert "The PM Devil" in result.output

    def test_list_shows_roles(self):
        result = runner.invoke(app, ["list"])
        assert "Chief Financial Officer" in result.output
        assert "Principal Engineer" in result.output


class TestProvidersCommand:
    def test_providers_shows_all_providers(self):
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "Anthropic" in result.output
        assert "OpenAI" in result.output
        assert "Gemini" in result.output
        assert "Custom" in result.output

    def test_providers_shows_env_vars(self):
        result = runner.invoke(app, ["providers"])
        assert "ANTHROPIC_API_KEY" in result.output
        assert "OPENAI_API_KEY" in result.output
        assert "GOOGLE_API_KEY" in result.output


# ── Run command — error cases ─────────────────────────────────────────────────

class TestRunErrors:
    def test_empty_proposal_exits(self):
        """An empty --proposal should exit with an error."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            with patch("council.main.DecisionCouncil") as MockCouncil:
                result = runner.invoke(app, ["run", "--proposal", "", "--all"])
                assert result.exit_code == 1

    def test_missing_api_key_exits(self):
        """No API key set and no --api-key flag should exit."""
        env = {k: "" for k in [
            "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
            "GOOGLE_API_KEY", "CUSTOM_API_KEY"
        ]}
        with patch.dict(os.environ, env, clear=False):
            for k in env:
                os.environ.pop(k, None)
            result = runner.invoke(
                app,
                ["run", "--provider", "anthropic", "--proposal", "test"],
                input="1\n",
            )
            assert result.exit_code == 1


# ── Run command — success with mock ───────────────────────────────────────────

class TestRunSuccess:
    def test_run_with_all_personas(self):
        from council.personas import DEFAULT_PERSONAS
        with patch("council.main.DecisionCouncil") as MockCouncil:
            instance = MagicMock()
            MockCouncil.return_value = instance
            instance.run.return_value = _fake_session(DEFAULT_PERSONAS)

            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                # Input: "n" for context prompt, then "n" for save prompt
                result = runner.invoke(
                    app,
                    ["run", "--proposal", "Test proposal", "--all"],
                    input="n\nn\n",
                )
                assert result.exit_code == 0, f"Unexpected exit. Output:\n{result.output}"
                assert "Battle Brief" in result.output

    def test_run_single_persona(self):
        from council.personas import get_persona
        cfo = get_persona("The CFO")
        with patch("council.main.DecisionCouncil") as MockCouncil:
            instance = MagicMock()
            MockCouncil.return_value = instance
            instance.run.return_value = _fake_session([cfo])

            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                result = runner.invoke(
                    app,
                    ["run", "--proposal", "Test", "--persona", "The CFO"],
                    input="n\nn\n",
                )
                assert result.exit_code == 0, f"Unexpected exit. Output:\n{result.output}"


# ── Output file ───────────────────────────────────────────────────────────────

class TestOutputFile:
    def test_output_flag_writes_file(self, tmp_path):
        out_file = tmp_path / "report.md"
        with patch("council.main.DecisionCouncil") as MockCouncil:
            instance = MagicMock()
            MockCouncil.return_value = instance
            MockCouncil.to_markdown = MagicMock(return_value="# Report\nContent here.")

            from council.personas import DEFAULT_PERSONAS
            instance.run.return_value = _fake_session([DEFAULT_PERSONAS[0]])

            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
                result = runner.invoke(
                    app,
                    ["run", "--proposal", "Test", "--all", "--output", str(out_file)],
                    input="n\n",  # "n" for context prompt; --output skips save prompt
                )
                assert result.exit_code == 0, f"Unexpected exit. Output:\n{result.output}"
                assert out_file.exists()
