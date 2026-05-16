#!/usr/bin/env python3
"""
Live API test for llm-judge — single mode and batch mode.

Uses Gemini for both model and judge. Only GOOGLE_API_KEY required.

Usage:
    GOOGLE_API_KEY=your-key python3 tests/test_llm_live_bulk_api.py

Expected output:
    🔄  [single mode] running...
    ✅  [single mode] PASS  (NNN tokens, N.Ns)
        Verdict: PASS | Confidence: 0.xx
        ✅ Must state 100 degrees Celsius: "Response states..."
        ...

    🔄  [batch mode — 1 row] running...
    ✅  [batch mode — 1 row] PASS  (NNN tokens, N.Ns)
        Pass rate: 100% | Items: 1 | Tokens: NNN
        ...

    ──────────────────────────────────────────────────
    Tool:    llm-judge
    Results: 2/2 cases passed
    ...
"""

import os
import sys

_tool_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_repo_root = os.path.dirname(os.path.dirname(_tool_root))
sys.path.insert(0, _tool_root)                           # tools/llm-judge
sys.path.insert(0, os.path.join(_repo_root, "shared"))  # shared/

from live_harness import LiveTestRunner
from llm_judge.batch import BatchItem, load_batch, run_batch
from llm_judge.core import LLMJudge
from llm_judge.providers import DEFAULT_MODELS, get_provider

# ── Test configuration ─────────────────────────────────────────────────────────

PROVIDER     = "gemini"
MODEL_ID     = DEFAULT_MODELS[PROVIDER]

SINGLE_PROMPT   = "What is the boiling point of water at sea level?"
SINGLE_CRITERIA = [
    "Must state 100 degrees Celsius",
    "Must state 212 degrees Fahrenheit",
    "Must be under 40 words",
]

BATCH_ITEMS = [
    BatchItem(
        id="live-batch-1",
        prompt="How many bits are in a byte?",
        criteria=[
            "Must state exactly 8",
            "Must be a single sentence",
        ],
    )
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _verdict_summary(result) -> str:
    lines = [f"Verdict: {'PASS' if result.overall_pass else 'FAIL'} | Confidence: {result.confidence:.2f}"]
    lines.append(f"Response: {result.response[:120].strip()}")
    for v in result.verdicts:
        icon = "✅" if v.passed else "❌"
        lines.append(f'{icon} {v.criterion}: "{v.reasoning}"')
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    runner = LiveTestRunner("llm-judge")
    api_key = runner.require_env(
        "GOOGLE_API_KEY",
        hint="Get your key at: https://aistudio.google.com/app/apikey",
    )

    # Build shared provider and judge (reused across both cases)
    provider = get_provider(PROVIDER, api_key=api_key)
    judge = LLMJudge(
        model_provider=provider,
        judge_provider=provider,
        model=MODEL_ID,
        judge_model=MODEL_ID,
        max_tokens=256,
    )

    # ── Case 1: single mode ────────────────────────────────────────────────────
    def single_case():
        result = judge.run(prompt=SINGLE_PROMPT, criteria=SINGLE_CRITERIA)
        return result.overall_pass, _verdict_summary(result), result.tokens_used, result.elapsed_seconds

    runner.run_case("single mode", single_case)

    # ── Case 2: batch mode (1 row) ─────────────────────────────────────────────
    def batch_case():
        report = run_batch(judge, BATCH_ITEMS)
        first = report.results[0]
        summary_lines = [
            f"Pass rate: {report.pass_rate * 100:.0f}% | Items: {len(report.results)} | Tokens: {report.total_tokens}",
        ]
        summary_lines.append(f"Response: {first.response[:120].strip()}")
        for v in first.verdicts:
            icon = "✅" if v.passed else "❌"
            summary_lines.append(f'{icon} {v.criterion}: "{v.reasoning}"')
        return report.pass_rate == 1.0, "\n".join(summary_lines), report.total_tokens, report.total_elapsed

    runner.run_case("batch mode — 1 row", batch_case)

    runner.finish()


if __name__ == "__main__":
    main()
