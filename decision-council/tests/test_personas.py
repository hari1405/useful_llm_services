"""Tests for the persona library — no API key required."""

import pytest

from council.personas import (
    DEFAULT_PERSONAS,
    Persona,
    build_custom_persona,
    get_persona,
    list_personas,
)


class TestDefaultPersonas:
    def test_default_personas_not_empty(self):
        assert len(DEFAULT_PERSONAS) > 0

    def test_all_personas_have_required_fields(self):
        for p in DEFAULT_PERSONAS:
            assert p.name, f"Persona missing name: {p}"
            assert p.role, f"Persona missing role: {p.name}"
            assert p.emoji, f"Persona missing emoji: {p.name}"
            assert p.system_prompt, f"Persona missing system_prompt: {p.name}"
            assert p.focus, f"Persona missing focus: {p.name}"
            assert p.color, f"Persona missing color: {p.name}"

    def test_system_prompts_are_substantive(self):
        """Each system prompt should be meaningful — not just a sentence."""
        for p in DEFAULT_PERSONAS:
            assert len(p.system_prompt) > 100, (
                f"System prompt for {p.name} is too short ({len(p.system_prompt)} chars). "
                "Prompts should be detailed enough to shape LLM behaviour."
            )

    def test_no_duplicate_names(self):
        names = [p.name for p in DEFAULT_PERSONAS]
        assert len(names) == len(set(names)), "Duplicate persona names found"

    def test_personas_include_key_roles(self):
        """Ensure critical business perspectives are covered."""
        names = {p.name for p in DEFAULT_PERSONAS}
        assert "The CFO" in names
        assert "The Skeptical Eng" in names
        assert "The PM Devil" in names
        assert "The Compliance Lead" in names

    def test_at_least_six_personas(self):
        """A useful council needs meaningful diversity."""
        assert len(DEFAULT_PERSONAS) >= 6


class TestGetPersona:
    def test_get_existing_persona(self):
        p = get_persona("The CFO")
        assert p is not None
        assert p.name == "The CFO"

    def test_get_nonexistent_persona_returns_none(self):
        p = get_persona("The Unicorn")
        assert p is None

    def test_get_all_defaults_by_name(self):
        for p in DEFAULT_PERSONAS:
            retrieved = get_persona(p.name)
            assert retrieved is not None
            assert retrieved.name == p.name


class TestListPersonas:
    def test_list_returns_tuples(self):
        result = list_personas()
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 3 for item in result)

    def test_list_length_matches_defaults(self):
        assert len(list_personas()) == len(DEFAULT_PERSONAS)

    def test_list_contains_name_role_emoji(self):
        for name, role, emoji in list_personas():
            assert name
            assert role
            assert emoji


class TestBuildCustomPersona:
    def test_builds_valid_persona(self):
        p = build_custom_persona(
            name="The Investor",
            role="Series B VC Partner",
            emoji="📈",
            focus="Market size, defensibility, founder-market fit",
        )
        assert isinstance(p, Persona)
        assert p.name == "The Investor"
        assert p.role == "Series B VC Partner"
        assert p.emoji == "📈"
        assert "Series B VC Partner" in p.system_prompt
        assert len(p.system_prompt) > 50

    def test_custom_persona_with_extra_context(self):
        p = build_custom_persona(
            name="The Board Member",
            role="Independent Board Director",
            emoji="🎩",
            focus="Governance, fiduciary duty, long-term shareholder value",
            extra_context="You have seen three IPOs and two acquisitions.",
        )
        assert "three IPOs" in p.system_prompt

    def test_custom_persona_has_default_color(self):
        p = build_custom_persona(
            name="X", role="Y", emoji="🔥", focus="Z"
        )
        assert p.color == "white"

    def test_multiple_custom_personas_are_independent(self):
        p1 = build_custom_persona("A", "Role A", "🅰️", "Focus A")
        p2 = build_custom_persona("B", "Role B", "🅱️", "Focus B")
        assert p1.name != p2.name
        assert "Role A" not in p2.system_prompt
        assert "Role B" not in p1.system_prompt
