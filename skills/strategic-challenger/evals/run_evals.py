"""
strategic-challenger skill evaluator

Usage:
    ANTHROPIC_API_KEY=your-key python run_evals.py

Runs all 3 eval cases through the skill, scores each with an LLM judge,
and prints a pass/fail report.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import anthropic

_EVALS_DIR = Path(__file__).parent
_SKILL_DIR = _EVALS_DIR.parent

CASES_PATH = _EVALS_DIR / "eval_cases.json"
RUBRIC_PATH = _EVALS_DIR / "eval_rubric.md"
SKILL_DRAFT_PATH = _SKILL_DIR / "SKILL-draft.md"

CHALLENGER_MODEL = "claude-sonnet-4-6"
JUDGE_MODEL = "claude-sonnet-4-6"

PASS_THRESHOLD = 49


def load_skill_instructions() -> str:
    """Load skill instructions from SKILL-draft.md."""
    return SKILL_DRAFT_PATH.read_text()


def load_rubric() -> str:
    """Load judge rubric from eval_rubric.md."""
    return RUBRIC_PATH.read_text()


def load_cases() -> list[dict[str, Any]]:
    """Load eval cases from eval_cases.json."""
    return json.loads(CASES_PATH.read_text())


def run_challenger(client: anthropic.Anthropic, skill_instructions: str, user_input: str) -> tuple[str, int]:
    """Run the strategic-challenger skill on a given input. Returns (output, tokens_used)."""
    response = client.messages.create(
        model=CHALLENGER_MODEL,
        max_tokens=2048,
        system=skill_instructions,
        messages=[{"role": "user", "content": user_input}],
    )
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return response.content[0].text, tokens


def run_judge(
    client: anthropic.Anthropic,
    rubric: str,
    case_input: str,
    skill_output: str,
    disqualifying_behaviors: list[str],
) -> dict[str, Any]:
    """Run the LLM judge on a challenger output. Returns parsed score dict."""
    disqualify_block = "\n".join(f"- {b}" for b in disqualifying_behaviors)
    judge_prompt = f"""{rubric}

---

## Input given to the skill
{case_input}

## Skill output to evaluate
{skill_output}

## Disqualifying behaviors — if any present, set "pass" to false regardless of score
{disqualify_block}

Score now. Output only valid JSON, no preamble.
"""
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": judge_prompt}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    return json.loads(raw.strip())


def cost_estimate(tokens: int, model: str = "challenger") -> float:
    """Rough cost in USD. Challenger = Sonnet input+output blended."""
    # claude-sonnet-4-6: ~$0.003/1K input, $0.015/1K output — blended ~$0.009/1K
    return (tokens / 1000) * 0.009


def print_case_result(case: dict, score: dict, challenger_output: str, tokens: int, elapsed: float) -> None:
    """Print formatted result for one case."""
    passed = score.get("pass", False) and score.get("total", 0) >= PASS_THRESHOLD
    status = "PASS" if passed else "FAIL"
    bar = "=" * 60

    print(f"\n{bar}")
    print(f"[{status}] {case['id']} — {case['label']}")
    print(f"  Total: {score.get('total', '?')}/70  |  Threshold: {PASS_THRESHOLD}")
    print(f"  Tokens: {tokens}  |  Cost: ~${cost_estimate(tokens):.4f}  |  Elapsed: {elapsed:.1f}s")
    print()

    dims = [
        "assumption_coverage", "challenge_specificity", "pre_mortem_quality",
        "forcing_question_quality", "trendslop_avoidance", "posture_integrity",
        "what_holds_specificity",
    ]
    for dim in dims:
        d = score.get(dim, {})
        s = d.get("score", "?")
        r = d.get("rationale", "")
        flag = " ⚠" if isinstance(s, int) and s < 5 else ""
        print(f"  {dim:<28} {s:>2}/10{flag}")
        print(f"    {r}")

    print()
    summary = score.get("summary", "")
    if summary:
        print(f"  Summary: {summary}")


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    skill_instructions = load_skill_instructions()
    rubric = load_rubric()
    cases = load_cases()

    print(f"strategic-challenger eval — {len(cases)} cases")
    print(f"Challenger model: {CHALLENGER_MODEL}  |  Judge model: {JUDGE_MODEL}")
    print(f"Pass threshold: {PASS_THRESHOLD}/70")

    results = []

    for case in cases:
        print(f"\nRunning: {case['id']} ...")
        t0 = time.time()

        try:
            challenger_output, tokens = run_challenger(client, skill_instructions, case["input"])
            elapsed = time.time() - t0

            score = run_judge(
                client,
                rubric,
                case["input"],
                challenger_output,
                case.get("disqualifying_behaviors", []),
            )

            passed = score.get("pass", False) and score.get("total", 0) >= PASS_THRESHOLD
            results.append({"case_id": case["id"], "passed": passed, "total": score.get("total", 0)})

            print_case_result(case, score, challenger_output, tokens, elapsed)

        except Exception as e:
            print(f"  ERROR in {case['id']}: {e}")
            results.append({"case_id": case["id"], "passed": False, "total": 0, "error": str(e)})

    # Summary
    passed_count = sum(1 for r in results if r["passed"])
    print("\n" + "=" * 60)
    print(f"RESULT: {passed_count}/{len(results)} cases passed")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['case_id']}  score={r.get('total', '?')}/70")

    if passed_count < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
