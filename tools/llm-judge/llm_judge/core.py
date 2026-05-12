"""
Core judgment logic for llm-judge.

Flow:
  1. Run the user's prompt through the model provider → get response
  2. Send prompt + response + criteria to the judge provider → get scored verdict
  3. Return JudgmentResult with per-criterion verdicts, overall pass/fail, confidence
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from .providers import LLMProvider


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class Verdict:
    criterion: str
    passed: bool
    reasoning: str


@dataclass
class JudgmentResult:
    prompt: str
    response: str
    model: str
    model_provider: str
    judge_model: str
    judge_provider: str
    verdicts: list[Verdict]
    overall_pass: bool
    confidence: float
    tokens_used: int
    elapsed_seconds: float

    @property
    def passed_count(self) -> int:
        return sum(1 for v in self.verdicts if v.passed)

    @property
    def total_count(self) -> int:
        return len(self.verdicts)


# ── Judge prompt ───────────────────────────────────────────────────────────────

_JUDGE_SYSTEM = """You are a ruthless, impartial evaluator. Your only job is to determine \
whether an LLM response satisfies each criterion. You do not give partial credit. \
You do not assume positive intent. You do not reward effort or style.

Rules you enforce without exception:
1. A criterion passes ONLY if the response explicitly and completely satisfies it.
2. Vague or hedged answers fail. "Around 100°C" when the criterion requires "100°C" is a fail.
3. Word and length limits are hard limits. Count the words. One word over is a fail.
4. If a criterion requires a specific term, name, or value, it must appear clearly — \
implied presence does not count.
5. If the response contradicts itself anywhere, every related criterion fails.
6. Incomplete answers fail. "Partially addresses the question" is a fail.
7. Verbose answers that bury the correct answer in irrelevant content fail any brevity criterion.
8. Answers that hedge with "it depends", "generally", or "in most cases" when a direct \
answer is possible fail any directness criterion.

Your reasoning for each verdict must be ONE sentence. Quote the specific part of the \
response that caused the pass or fail. Never write "the response is good" or "seems correct". \
State exactly what is present or what is missing.

Return only valid JSON. No markdown fences. No text outside the JSON object."""


def _build_judge_prompt(prompt: str, response: str, criteria: list[str]) -> str:
    """Build the user message sent to the judge model."""
    criteria_block = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(criteria))
    return (
        f"PROMPT GIVEN TO THE MODEL:\n{prompt}\n\n"
        f"MODEL RESPONSE:\n{response}\n\n"
        f"CRITERIA (evaluate each independently):\n{criteria_block}\n\n"
        "Return exactly this JSON structure — one verdict per criterion, in order:\n"
        '{\n'
        '  "verdicts": [\n'
        '    {"criterion": "...", "pass": true, "reasoning": "one sentence"}\n'
        '  ],\n'
        '  "overall_pass": true,\n'
        '  "confidence": 0.95\n'
        '}'
    )


# ── JSON parsing ───────────────────────────────────────────────────────────────

def _parse_judge_response(raw: str, criteria: list[str]) -> tuple[list[Verdict], bool, float]:
    """
    Parse the judge's JSON response into verdicts.
    Falls back gracefully if JSON is malformed — marks all criteria as failed.
    """
    try:
        # Strip markdown code fences if present
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(clean)

        verdicts = [
            Verdict(
                criterion=v.get("criterion", criteria[i] if i < len(criteria) else "unknown"),
                passed=bool(v.get("pass", False)),
                reasoning=v.get("reasoning", "No reasoning provided."),
            )
            for i, v in enumerate(data.get("verdicts", []))
        ]
        overall_pass = bool(data.get("overall_pass", all(v.passed for v in verdicts)))
        confidence = float(data.get("confidence", 0.5))
        return verdicts, overall_pass, confidence

    except (json.JSONDecodeError, KeyError, TypeError):
        verdicts = [
            Verdict(criterion=c, passed=False, reasoning="Judge returned unparseable response.")
            for c in criteria
        ]
        return verdicts, False, 0.0


# ── Core class ─────────────────────────────────────────────────────────────────

class LLMJudge:
    """
    Runs a prompt through a model, then judges the response against criteria.

    Args:
        model_provider:  provider instance for generating the response
        judge_provider:  provider instance for judging the response
        model:           model ID for the response generation
        judge_model:     model ID for the judge
        max_tokens:      max tokens for the model response
        judge_max_tokens: max tokens for the judge response (needs enough for JSON)
    """

    def __init__(
        self,
        model_provider: LLMProvider,
        judge_provider: LLMProvider,
        model: str,
        judge_model: str,
        max_tokens: int = 512,
        judge_max_tokens: int = 1024,
    ):
        self.model_provider = model_provider
        self.judge_provider = judge_provider
        self.model = model
        self.judge_model = judge_model
        self.max_tokens = max_tokens
        self.judge_max_tokens = judge_max_tokens

    def run(self, prompt: str, criteria: list[str]) -> JudgmentResult:
        """Run prompt through model, judge response against criteria."""
        if not criteria:
            raise ValueError("At least one criterion is required.")
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        start = time.time()
        total_tokens = 0

        # Step 1: get model response
        model_result = self.model_provider.complete(
            system="You are a helpful assistant. Answer clearly and directly.",
            user=prompt,
            model=self.model,
            max_tokens=self.max_tokens,
        )
        total_tokens += model_result.tokens_used

        # Step 2: judge the response
        judge_prompt = _build_judge_prompt(prompt, model_result.text, criteria)
        judge_result = self.judge_provider.complete(
            system=_JUDGE_SYSTEM,
            user=judge_prompt,
            model=self.judge_model,
            max_tokens=self.judge_max_tokens,
        )
        total_tokens += judge_result.tokens_used

        verdicts, overall_pass, confidence = _parse_judge_response(judge_result.text, criteria)

        return JudgmentResult(
            prompt=prompt,
            response=model_result.text,
            model=self.model,
            model_provider=self.model_provider.name,
            judge_model=self.judge_model,
            judge_provider=self.judge_provider.name,
            verdicts=verdicts,
            overall_pass=overall_pass,
            confidence=confidence,
            tokens_used=total_tokens,
            elapsed_seconds=round(time.time() - start, 2),
        )
