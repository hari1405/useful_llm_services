"""
Reusable live test harness for useful-llm-services tools.

Canonical location: shared/live_harness.py (repo root)
Import in any tool's live test file by inserting the repo root into sys.path:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
    from live_harness import LiveTestRunner

Usage pattern:
    runner = LiveTestRunner("my-tool")
    api_key = runner.require_env("GOOGLE_API_KEY")

    def my_single_test():
        # ... run the tool ...
        return passed, "summary string", tokens_used, elapsed_seconds

    def my_batch_test():
        # ... run batch ...
        return passed, "summary string", tokens_used, elapsed_seconds

    runner.run_case("single mode", my_single_test)
    runner.run_case("batch mode",  my_batch_test)
    runner.finish()
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Union


# Return type for test callables — two forms accepted:
#   Full:  (passed, summary, tokens_used, elapsed_seconds)  — direct API / batch mode
#   Short: (passed, summary)                                 — A2A / MCP (tokens unknown)
TestCallable = Callable[[], Union[Tuple[bool, str, int, float], Tuple[bool, str]]]


@dataclass
class CaseResult:
    label: str
    passed: bool
    summary: str
    tokens_used: int
    elapsed_seconds: float
    error: Optional[str] = None


class LiveTestRunner:
    """
    Runs a sequence of live test cases and prints a unified report.

    Each case is a callable that returns (passed, summary, tokens, elapsed).
    Short 2-tuple (passed, summary) is also accepted — tokens/elapsed default to 0.
    The runner accumulates results and exits 0 only if all cases pass.
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self._cases: list[CaseResult] = []

    def require_env(self, var: str, hint: str = "") -> str:
        """Return the value of an env var or exit 1 with a clear message."""
        value = os.environ.get(var, "").strip()
        if not value:
            print(f"❌  {var} not set.")
            if hint:
                print(f"    {hint}")
            else:
                print(f"    Run:  {var}=your-key python3 tests/{self._test_filename()}")
            sys.exit(1)
        return value

    def run_case(self, label: str, fn: TestCallable) -> None:
        """Run one test case and record the result."""
        print(f"🔄  [{label}] running...", flush=True)
        wall_start = time.time()
        try:
            raw = fn()
            if len(raw) == 2:
                passed, summary = raw  # type: ignore[misc]
                tokens, elapsed = 0, 0.0
            else:
                passed, summary, tokens, elapsed = raw  # type: ignore[misc]
            case = CaseResult(
                label=label,
                passed=passed,
                summary=summary,
                tokens_used=tokens,
                elapsed_seconds=elapsed,
            )
        except Exception as e:
            elapsed = round(time.time() - wall_start, 2)
            case = CaseResult(
                label=label,
                passed=False,
                summary="",
                tokens_used=0,
                elapsed_seconds=elapsed,
                error=str(e),
            )

        self._cases.append(case)

        icon = "✅" if case.passed else "❌"
        status = "PASS" if case.passed else "FAIL"
        print(f"{icon}  [{label}] {status}  ({case.tokens_used} tokens, {case.elapsed_seconds}s)")

        if case.error:
            print(f"    Error: {case.error}")
        elif case.summary:
            for line in case.summary.splitlines():
                print(f"    {line}")
        print()

    def finish(self) -> None:
        """Print a final summary and exit 0 if all cases passed, else exit 1."""
        passed_n = sum(1 for c in self._cases if c.passed)
        total_n = len(self._cases)
        total_tokens = sum(c.tokens_used for c in self._cases)
        total_elapsed = sum(c.elapsed_seconds for c in self._cases)

        print("─" * 50)
        print(f"Tool:    {self.tool_name}")
        print(f"Results: {passed_n}/{total_n} cases passed")
        print(f"Tokens:  {total_tokens:,}")
        print(f"Time:    {total_elapsed:.1f}s")
        print("─" * 50)

        if passed_n == total_n:
            print("✅  All live tests passed.")
            sys.exit(0)
        else:
            failed = [c.label for c in self._cases if not c.passed]
            print(f"❌  {total_n - passed_n} case(s) failed: {', '.join(failed)}")
            sys.exit(1)

    def _test_filename(self) -> str:
        return f"test_{self.tool_name.replace('-', '_')}_live_bulk_api.py"
