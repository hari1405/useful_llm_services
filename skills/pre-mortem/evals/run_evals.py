"""
pre-mortem skill evaluator

Usage:
    ANTHROPIC_API_KEY=your-key python run_evals.py
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

MODEL = "claude-sonnet-4-6"
PASS_THRESHOLD = 42


def load(path: Path) -> str:
    return path.read_text()


def run_skill(client: anthropic.Anthropic, instructions: str, user_input: str) -> tuple[str, int]:
    """Run pre-mortem skill. Returns (output, total_tokens)."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=instructions,
        messages=[{"role": "user", "content": user_input}],
    )
    tokens = resp.usage.input_tokens + resp.usage.output_tokens
    return resp.content[0].text, tokens


def run_judge(
    client: anthropic.Anthropic,
    rubric: str,
    case_input: str,
    skill_output: str,
    disqualifying: list[str],
) -> dict[str, Any]:
    """Score skill output with LLM judge. Returns parsed score dict."""
    disqualify_block = "\n".join(f"- {b}" for b in disqualifying)
    prompt = rubric.replace("{input}", case_input).replace("{output}", skill_output).replace(
        "{disqualifying_behaviors}", disqualify_block
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip().strip("```json").strip("```").strip()
    return json.loads(raw)


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    instructions = load(SKILL_DRAFT_PATH)
    rubric = load(RUBRIC_PATH)
    cases = json.loads(load(CASES_PATH))

    print(f"pre-mortem eval — {len(cases)} cases | model: {MODEL} | pass: {PASS_THRESHOLD}/60")

    results = []

    for case in cases:
        print(f"\nRunning {case['id']} ...")
        t0 = time.time()

        try:
            output, tokens = run_skill(client, instructions, case["input"])
            elapsed = time.time() - t0
            score = run_judge(client, rubric, case["input"], output, case.get("disqualifying_behaviors", []))

            passed = score.get("pass", False) and score.get("total", 0) >= PASS_THRESHOLD
            results.append({"id": case["id"], "passed": passed, "total": score.get("total", 0)})

            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] total={score.get('total','?')}/60 | tokens={tokens} | {elapsed:.1f}s")

            dims = ["temporal_anchoring", "chain_quality", "kill_shot_specificity",
                    "early_warning_quality", "reversibility_reasoning", "what_to_change_quality"]
            for d in dims:
                s = score.get(d, {})
                flag = " ⚠" if isinstance(s.get("score"), int) and s["score"] < 5 else ""
                print(f"    {d:<30} {s.get('score','?'):>2}/10{flag}  {s.get('rationale','')}")

            print(f"  Summary: {score.get('summary','')}")

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"id": case["id"], "passed": False, "total": 0})

    print("\n" + "=" * 60)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"RESULT: {passed_count}/{len(results)} passed")
    for r in results:
        print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['id']}  {r.get('total','?')}/60")

    if passed_count < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
