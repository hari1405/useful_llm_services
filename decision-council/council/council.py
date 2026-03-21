"""
Core orchestration logic for Decision Council.

Sends a proposal to each selected persona and collects their critiques
using the configured LLM provider (Anthropic, OpenAI, Gemini, or Custom).
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional

from .personas import Persona
from .providers import (
    DEFAULT_MODELS,
    LLMProvider,
    PROVIDER_ANTHROPIC,
    get_provider,
)


# ── Models ────────────────────────────────────────────────────────────────────

@dataclass
class PersonaResponse:
    persona: Persona
    critique: str
    tokens_used: int
    elapsed_seconds: float


@dataclass
class CouncilSession:
    proposal: str
    context: str
    responses: list[PersonaResponse]
    synthesis: str
    total_tokens: int
    total_elapsed: float
    provider_name: str
    model: str


# ── Council runner ────────────────────────────────────────────────────────────

class DecisionCouncil:
    """
    Orchestrates a set of Persona critics against a proposal.

    Supports any LLM provider — Anthropic, OpenAI, Gemini, or Custom.

    Usage (Anthropic — default):
        council = DecisionCouncil(provider="anthropic", api_key="sk-ant-...")
        session = council.run(proposal="...", personas=[...])

    Usage (OpenAI):
        council = DecisionCouncil(provider="openai", api_key="sk-...")

    Usage (Gemini):
        council = DecisionCouncil(provider="gemini", api_key="AI...")

    Usage (Custom):
        council = DecisionCouncil(
            provider="custom",
            api_key="your-key",
            base_url="https://your-endpoint/v1",
        )
    """

    def __init__(
        self,
        provider: str = PROVIDER_ANTHROPIC,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        max_tokens: int = 1024,
        # Legacy support: if an LLMProvider instance is passed directly
        _provider_instance: Optional[LLMProvider] = None,
    ):
        self.provider_name = provider
        self.max_tokens = max_tokens

        if _provider_instance is not None:
            self._provider = _provider_instance
            self.provider_name = getattr(_provider_instance, "name", provider)
        else:
            self._provider = get_provider(
                provider_name=provider,
                api_key=api_key,
                base_url=base_url,
            )

        self.model = model or DEFAULT_MODELS.get(self.provider_name, "gpt-4o-mini")

    # ── Single persona ────────────────────────────────────────────────────────

    def critique(
        self,
        proposal: str,
        persona: Persona,
        context: str = "",
    ) -> PersonaResponse:
        """Get a single persona's critique of the proposal."""
        user_message = self._build_user_message(proposal, context)

        start = time.time()
        result = self._provider.complete(
            system=persona.system_prompt,
            user=user_message,
            model=self.model,
            max_tokens=self.max_tokens,
        )
        elapsed = time.time() - start

        return PersonaResponse(
            persona=persona,
            critique=result.text,
            tokens_used=result.tokens_used,
            elapsed_seconds=round(elapsed, 2),
        )

    # ── Full council run ──────────────────────────────────────────────────────

    def run(
        self,
        proposal: str,
        personas: list[Persona],
        context: str = "",
        on_persona_start: Optional[Callable] = None,
        on_persona_done: Optional[Callable] = None,
    ) -> CouncilSession:
        """
        Run the full council. Calls each persona sequentially.

        Callbacks:
          on_persona_start(persona) — called before each critique
          on_persona_done(response) — called after each critique
        """
        responses: list[PersonaResponse] = []
        total_tokens = 0
        total_start = time.time()

        for persona in personas:
            if on_persona_start:
                on_persona_start(persona)

            response = self.critique(proposal, persona, context)
            responses.append(response)
            total_tokens += response.tokens_used

            if on_persona_done:
                on_persona_done(response)

        # Synthesise across all critiques
        synthesis_text, synthesis_tokens = self._synthesise(proposal, responses)
        total_tokens += synthesis_tokens

        return CouncilSession(
            proposal=proposal,
            context=context,
            responses=responses,
            synthesis=synthesis_text,
            total_tokens=total_tokens,
            total_elapsed=round(time.time() - total_start, 2),
            provider_name=self.provider_name,
            model=self.model,
        )

    # ── Synthesis ─────────────────────────────────────────────────────────────

    def _synthesise(
        self,
        proposal: str,
        responses: list[PersonaResponse],
    ) -> tuple[str, int]:
        """
        Generate a consolidated "battle brief" from all council critiques.
        Returns (synthesis_text, tokens_used).
        """
        critiques_block = "\n\n".join(
            f"### {r.persona.emoji} {r.persona.name} ({r.persona.role})\n{r.critique}"
            for r in responses
        )

        system = """You are a senior advisor who has just received criticism from a panel of
experts on a proposal. Your job is to produce a concise "Battle Brief" — a tight summary
that helps the proposal owner walk into their next meeting fully prepared.

Structure your response as:
1. **Top 3 Hardest Questions You Will Face** — the questions most likely to kill this in the room
2. **Biggest Assumption to Prove** — the single claim that the whole proposal rests on
3. **Recommended Prep Actions** — 3-5 concrete things to do before the meeting
4. **One Line to Lead With** — the sharpest, most defensible framing of this proposal

Be direct, specific, and actionable. No fluff."""

        user = f"""Proposal:\n{proposal}\n\nCouncil Critiques:\n{critiques_block}"""

        result = self._provider.complete(
            system=system,
            user=user,
            model=self.model,
            max_tokens=1024,
        )
        return result.text, result.tokens_used

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_user_message(proposal: str, context: str) -> str:
        parts = [f"## Proposal / Decision\n\n{proposal.strip()}"]
        if context.strip():
            parts.append(f"## Additional Context\n\n{context.strip()}")
        parts.append(
            "Please provide your critique from your specific perspective. "
            "Be sharp, specific, and helpful. This person needs to be prepared."
        )
        return "\n\n".join(parts)

    # ── Export ────────────────────────────────────────────────────────────────

    @staticmethod
    def to_markdown(session: CouncilSession) -> str:
        """Export a full session to a Markdown string."""
        lines = [
            "# Decision Council Report",
            "",
            f"**Proposal:** {session.proposal[:200]}{'...' if len(session.proposal) > 200 else ''}",
            f"**Provider:** {session.provider_name} · **Model:** {session.model}",
            "",
            "---",
            "",
        ]

        for r in session.responses:
            lines += [
                f"## {r.persona.emoji} {r.persona.name}",
                f"*{r.persona.role}*",
                "",
                r.critique,
                "",
                "---",
                "",
            ]

        lines += [
            "## 🧠 Battle Brief (Synthesis)",
            "",
            session.synthesis,
            "",
            "---",
            "",
            f"*Total tokens used: {session.total_tokens:,} | "
            f"Total time: {session.total_elapsed}s | "
            f"Provider: {session.provider_name} / {session.model}*",
        ]

        return "\n".join(lines)
