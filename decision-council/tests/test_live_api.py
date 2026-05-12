#!/usr/bin/env python3
"""
Live API smoke test for Decision Council.

Sends a single, minimal proposal to ONE persona (The CFO) using the Gemini provider.
Uses the smallest possible input to minimise token usage.

Usage:
    GOOGLE_API_KEY=your-key-here python3 tests/test_live_api.py

Expected output:
    ✅ Live API test passed — Gemini is working.
    Provider: gemini | Model: gemini-2.0-flash
    Tokens used: <number> | Time: <seconds>s
    --- CFO critique (first 200 chars) ---
    <critique text>

If your quota is exceeded you will see:
    ❌ API call failed: <error message>
"""

import os
import sys

# Add parent dir so `council` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from council.council import DecisionCouncil
from council.personas import get_persona


def main():
    api_key = os.environ.get("GOOGLE_API_KEY", "")

    if not api_key:
        print("❌ GOOGLE_API_KEY not set.")
        print("   Run:  GOOGLE_API_KEY=your-key python3 tests/test_live_api.py")
        sys.exit(1)

    # Minimal proposal — keeps token count low
    proposal = "Should we use AI to automate code reviews?"
    persona = get_persona("The CFO")

    print(f"🔄 Sending 1 proposal to {persona.emoji} {persona.name} via Gemini...")
    print(f"   Proposal: \"{proposal}\"")
    print()

    try:
        council = DecisionCouncil(
            provider="gemini",
            api_key=api_key,
            model="gemini-2.0-flash",
            max_tokens=256,  # Keep response short to save quota
        )

        response = council.critique(proposal, persona)

        print(f"✅ Live API test passed — Gemini is working.")
        print(f"   Provider: gemini | Model: gemini-2.0-flash")
        print(f"   Tokens used: {response.tokens_used} | Time: {response.elapsed_seconds}s")
        print()
        print(f"--- {persona.emoji} {persona.name} critique (first 300 chars) ---")
        print(response.critique[:300])
        print("---")

    except Exception as e:
        print(f"❌ API call failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
