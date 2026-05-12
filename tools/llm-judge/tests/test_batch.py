"""
Tests for llm-judge batch mode.

All LLM calls are mocked — no API key required.
Run with: pytest tests/ -v
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from llm_judge.batch import (
    BatchItem,
    BatchReport,
    load_batch,
    render_markdown_report,
    run_batch,
)
from llm_judge.core import JudgmentResult, LLMJudge, Verdict
from llm_judge.providers import CompletionResult, LLMProvider


# ── Fixtures ───────────────────────────────────────────────────────────────────

class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, response: str = "Mock.", tokens: int = 50):
        self._response = response
        self._tokens = tokens

    def complete(self, *, system, user, model, max_tokens=1024) -> CompletionResult:
        return CompletionResult(text=self._response, tokens_used=self._tokens)


def _make_judge_response(criteria: list[str], all_pass: bool = True) -> str:
    verdicts = [
        {"criterion": c, "pass": all_pass, "reasoning": "Satisfied." if all_pass else "Not satisfied."}
        for c in criteria
    ]
    return json.dumps({"verdicts": verdicts, "overall_pass": all_pass, "confidence": 0.9})


def _make_judge(all_pass: bool = True, criteria: list[str] | None = None) -> LLMJudge:
    criteria = criteria or ["c1"]
    model_prov = MockProvider(response="Model answer here.")
    judge_prov = MockProvider(response=_make_judge_response(criteria, all_pass=all_pass))
    return LLMJudge(
        model_provider=model_prov,
        judge_provider=judge_prov,
        model="test-model",
        judge_model="test-judge",
    )


# ── load_batch — JSON ──────────────────────────────────────────────────────────

class TestLoadBatchJson:
    def test_parses_items_correctly(self, tmp_path):
        data = [{"id": "q1", "prompt": "Hello?", "criteria": ["Must greet"]}]
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        items = load_batch(str(f))
        assert len(items) == 1
        assert items[0].id == "q1"
        assert items[0].prompt == "Hello?"
        assert items[0].criteria == ["Must greet"]

    def test_auto_generates_id_when_absent(self, tmp_path):
        data = [{"prompt": "Hi?", "criteria": ["c1"]}, {"prompt": "Bye?", "criteria": ["c2"]}]
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        items = load_batch(str(f))
        assert items[0].id == "item-1"
        assert items[1].id == "item-2"

    def test_multiple_items(self, tmp_path):
        data = [
            {"id": f"q{i}", "prompt": f"Prompt {i}", "criteria": ["c1"]}
            for i in range(5)
        ]
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        items = load_batch(str(f))
        assert len(items) == 5

    def test_empty_file_raises(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text("[]")
        with pytest.raises(ValueError, match="empty"):
            load_batch(str(f))

    def test_missing_prompt_raises(self, tmp_path):
        data = [{"id": "q1", "criteria": ["c1"]}]
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        with pytest.raises(ValueError, match="prompt"):
            load_batch(str(f))

    def test_missing_criteria_raises(self, tmp_path):
        data = [{"id": "q1", "prompt": "Hi?", "criteria": []}]
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        with pytest.raises(ValueError, match="criteria"):
            load_batch(str(f))

    def test_invalid_json_raises(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text("{not valid json")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_batch(str(f))

    def test_non_list_json_raises(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"prompt": "hi", "criteria": ["c1"]}')
        with pytest.raises(ValueError, match="list"):
            load_batch(str(f))


# ── load_batch — CSV ───────────────────────────────────────────────────────────

class TestLoadBatchCsv:
    def test_parses_items_correctly(self, tmp_path):
        content = 'id,prompt,criteria\nq1,"What is 2+2?","Must answer 4|Must be short"\n'
        f = tmp_path / "test.csv"
        f.write_text(content)
        items = load_batch(str(f))
        assert len(items) == 1
        assert items[0].id == "q1"
        assert items[0].prompt == "What is 2+2?"
        assert items[0].criteria == ["Must answer 4", "Must be short"]

    def test_pipe_separated_criteria_split_correctly(self, tmp_path):
        content = 'id,prompt,criteria\nq1,"P","c1|c2|c3"\n'
        f = tmp_path / "test.csv"
        f.write_text(content)
        items = load_batch(str(f))
        assert items[0].criteria == ["c1", "c2", "c3"]

    def test_auto_generates_id_when_absent(self, tmp_path):
        content = 'prompt,criteria\n"Hello?","Must greet"\n'
        f = tmp_path / "test.csv"
        f.write_text(content)
        items = load_batch(str(f))
        assert items[0].id == "item-1"

    def test_empty_csv_raises(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("id,prompt,criteria\n")
        with pytest.raises(ValueError, match="empty"):
            load_batch(str(f))

    def test_missing_prompt_column_raises(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("id,criteria\nq1,c1\n")
        with pytest.raises(ValueError, match="prompt"):
            load_batch(str(f))

    def test_missing_criteria_column_raises(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_text("id,prompt\nq1,hello\n")
        with pytest.raises(ValueError, match="criteria"):
            load_batch(str(f))


# ── load_batch — format detection ─────────────────────────────────────────────

class TestLoadBatchFormat:
    def test_unsupported_extension_raises(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("something")
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_batch(str(f))

    def test_nonexistent_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_batch(str(tmp_path / "missing.json"))


# ── run_batch ──────────────────────────────────────────────────────────────────

class TestRunBatch:
    def _make_items(self, n: int = 3) -> list[BatchItem]:
        return [BatchItem(id=f"q{i}", prompt=f"Prompt {i}", criteria=["c1"]) for i in range(n)]

    def test_returns_batch_report(self):
        items = self._make_items(2)
        judge = _make_judge(criteria=["c1"])
        report = run_batch(judge, items)
        assert isinstance(report, BatchReport)

    def test_result_count_matches_items(self):
        items = self._make_items(4)
        judge = _make_judge(criteria=["c1"])
        report = run_batch(judge, items)
        assert len(report.results) == 4

    def test_total_tokens_accumulated(self):
        items = self._make_items(3)
        model_prov = MockProvider(response="Answer.", tokens=100)
        judge_prov = MockProvider(
            response=_make_judge_response(["c1"], all_pass=True),
            tokens=150,
        )
        judge = LLMJudge(
            model_provider=model_prov,
            judge_provider=judge_prov,
            model="m", judge_model="j",
        )
        report = run_batch(judge, items)
        assert report.total_tokens == 3 * (100 + 150)

    def test_pass_rate_all_pass(self):
        items = self._make_items(3)
        judge = _make_judge(all_pass=True, criteria=["c1"])
        report = run_batch(judge, items)
        assert report.pass_rate == 1.0

    def test_pass_rate_none_pass(self):
        items = self._make_items(3)
        judge = _make_judge(all_pass=False, criteria=["c1"])
        report = run_batch(judge, items)
        assert report.pass_rate == 0.0

    def test_pass_rate_mixed(self):
        items = self._make_items(4)
        results_toggle = [True, False, True, False]
        call_count = [0]

        class ToggleProvider(LLMProvider):
            name = "mock"
            def complete(self, *, system, user, model, max_tokens=1024):
                idx = call_count[0] // 2
                is_judge_call = call_count[0] % 2 == 1
                call_count[0] += 1
                if is_judge_call:
                    return CompletionResult(
                        text=_make_judge_response(["c1"], all_pass=results_toggle[min(idx, 3)]),
                        tokens_used=50,
                    )
                return CompletionResult(text="Answer.", tokens_used=50)

        p = ToggleProvider()
        judge = LLMJudge(model_provider=p, judge_provider=p, model="m", judge_model="j")
        report = run_batch(judge, items)
        assert report.pass_rate == 0.5

    def test_on_item_callbacks_called(self):
        items = self._make_items(3)
        judge = _make_judge(criteria=["c1"])
        started, finished = [], []
        run_batch(
            judge, items,
            on_item_start=lambda i, item: started.append(i),
            on_item_done=lambda i, item, result: finished.append(i),
        )
        assert started == [0, 1, 2]
        assert finished == [0, 1, 2]

    def test_total_elapsed_non_negative(self):
        items = self._make_items(2)
        judge = _make_judge(criteria=["c1"])
        report = run_batch(judge, items)
        assert report.total_elapsed >= 0


# ── render_markdown_report ────────────────────────────────────────────────────

class TestRenderMarkdownReport:
    def _make_report(self, n: int = 2, all_pass: bool = True) -> BatchReport:
        items = [BatchItem(id=f"q{i}", prompt=f"Prompt {i}", criteria=["c1"]) for i in range(n)]
        verdicts = [Verdict(criterion="c1", passed=all_pass, reasoning="ok")]
        results = [
            JudgmentResult(
                prompt=item.prompt,
                response="A response.",
                model="test-model",
                model_provider="gemini",
                judge_model="test-judge",
                judge_provider="gemini",
                verdicts=verdicts,
                overall_pass=all_pass,
                confidence=0.9,
                tokens_used=200,
                elapsed_seconds=1.0,
            )
            for item in items
        ]
        return BatchReport(
            source_file="test.json",
            model="test-model",
            model_provider="gemini",
            judge_model="test-judge",
            judge_provider="gemini",
            items=items,
            results=results,
            total_tokens=n * 200,
            total_elapsed=float(n),
        )

    def test_contains_summary_section(self):
        report = self._make_report()
        md = render_markdown_report(report)
        assert "## Summary" in md

    def test_contains_all_item_ids(self):
        report = self._make_report(n=3)
        md = render_markdown_report(report)
        for i in range(3):
            assert f"q{i}" in md

    def test_contains_pass_rate(self):
        report = self._make_report(n=2, all_pass=True)
        md = render_markdown_report(report)
        assert "100.0%" in md

    def test_contains_model_info(self):
        report = self._make_report()
        md = render_markdown_report(report)
        assert "test-model" in md
        assert "gemini" in md

    def test_pass_verdict_shows_checkmark(self):
        report = self._make_report(all_pass=True)
        md = render_markdown_report(report)
        assert "✅" in md

    def test_fail_verdict_shows_cross(self):
        report = self._make_report(all_pass=False)
        md = render_markdown_report(report)
        assert "❌" in md

    def test_contains_token_count(self):
        report = self._make_report(n=2)
        md = render_markdown_report(report)
        assert "400" in md  # 2 × 200 tokens
