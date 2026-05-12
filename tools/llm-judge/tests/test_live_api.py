#!/usr/bin/env python3
"""
Live API smoke test for llm-judge.

Uses Gemini for both model and judge — only GOOGLE_API_KEY needed.

Usage:
    GOOGLE_API_KEY=your-key-here python3 tests/test_live_api.py

Expected output:
    ✅ Live API test passed — llm-judge is working.
    Model:  gemini-3.1-flash-lite  (gemini)
    Judge:  gemini-3.1-flash-lite  (gemini)
    Verdict: PASS | Confidence: 0.xx | Tokens: NNN | Time: N.Ns
    --- Verdicts ---
    ✅  <criterion> — <reasoning>
    ...
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_judge.core import LLMJudge
from llm_judge.providers import DEFAULT_MODELS, get_provider


def main() -> None:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set.")
        print("   Run:  GOOGLE_API_KEY=your-key python3 tests/test_live_api.py")
        sys.exit(1)

    model_id = DEFAULT_MODELS["gemini"]

    prompt = "What is the boiling point of water at sea level?"
    criteria = [
        "Answer must state 100 degrees Celsius or 212 degrees Fahrenheit",
        "Answer must be under 50 words",
    ]

    print(f"🔄 Running prompt through {model_id} (gemini)...")
    print(f"   Prompt: \"{prompt}\"")
    print(f"   Criteria: {criteria}")
    print()

    try:
        provider = get_provider("gemini", api_key=api_key)
        judge_instance = LLMJudge(
            model_provider=provider,
            judge_provider=provider,
            model=model_id,
            judge_model=model_id,
            max_tokens=256,
        )
        result = judge_instance.run(prompt=prompt, criteria=criteria)

        print("✅ Live API test passed — llm-judge is working.")
        print(f"   Model:  {result.model}  ({result.model_provider})")
        print(f"   Judge:  {result.judge_model}  ({result.judge_provider})")
        overall = "PASS" if result.overall_pass else "FAIL"
        print(f"   Verdict: {overall} | Confidence: {result.confidence:.2f} | Tokens: {result.tokens_used} | Time: {result.elapsed_seconds}s")
        print()
        print("--- Model response ---")
        print(f"  {result.response[:300]}")
        print()
        print("--- Verdicts ---")
        for v in result.verdicts:
            icon = "✅" if v.passed else "❌"
            print(f"  {icon}  {v.criterion}")
            print(f"      \"{v.reasoning}\"")

    except Exception as e:
        print(f"❌ API call failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
