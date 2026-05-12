"""
Batch evaluation for llm-judge.

Loads a JSON or CSV file of prompts + criteria, runs each through LLMJudge,
and produces a terminal table + optional Markdown report.

JSON format:
    [
      {
        "id": "q1",
        "prompt": "What is the boiling point of water?",
        "criteria": ["Must state 100°C or 212°F", "Must be under 30 words"]
      }
    ]
    ("id" is optional — auto-generated as "item-1", "item-2", ... if absent)

CSV format:
    id,prompt,criteria
    q1,"What is the boiling point of water?","Must state 100°C or 212°F|Must be under 30 words"

    Criteria are pipe-separated (|) within the criteria column.
    The "id" column is optional.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .core import JudgmentResult, LLMJudge


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class BatchItem:
    id: str
    prompt: str
    criteria: list[str]


@dataclass
class BatchReport:
    source_file: str
    model: str
    model_provider: str
    judge_model: str
    judge_provider: str
    items: list[BatchItem]
    results: list[JudgmentResult]
    total_tokens: int
    total_elapsed: float

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.overall_pass)

    @property
    def fail_count(self) -> int:
        return len(self.results) - self.pass_count

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return self.pass_count / len(self.results)


# ── File loading ───────────────────────────────────────────────────────────────

def load_batch(file_path: str) -> list[BatchItem]:
    """
    Load a JSON or CSV file and return a list of BatchItems.
    Raises ValueError on unsupported format or empty file.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        return _load_json(path)
    elif suffix == ".csv":
        return _load_csv(path)
    else:
        raise ValueError(
            f"Unsupported file format: '{suffix}'.\n"
            "Supported formats: .json, .csv\n"
            "Run 'python judge.py batch --help' for file format details."
        )


def _load_json(path: Path) -> list[BatchItem]:
    """Parse a JSON batch file."""
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in '{path}': {e}") from e

    if not isinstance(data, list):
        raise ValueError(f"JSON file must contain a list of objects. Got: {type(data).__name__}")

    if not data:
        raise ValueError(f"Batch file '{path}' is empty — no items to evaluate.")

    items = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValueError(f"Item {i + 1} in JSON must be an object, got: {type(entry).__name__}")

        prompt = entry.get("prompt", "").strip()
        if not prompt:
            raise ValueError(f"Item {i + 1} is missing a 'prompt' field.")

        criteria = entry.get("criteria", [])
        if not isinstance(criteria, list) or not criteria:
            raise ValueError(f"Item {i + 1} 'criteria' must be a non-empty list of strings.")

        item_id = str(entry.get("id", f"item-{i + 1}")).strip() or f"item-{i + 1}"
        items.append(BatchItem(id=item_id, prompt=prompt, criteria=[str(c) for c in criteria]))

    return items


def _load_csv(path: Path) -> list[BatchItem]:
    """Parse a CSV batch file. Criteria column is pipe-separated (|)."""
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Batch file '{path}' is empty — no items to evaluate.")

    fieldnames = reader.fieldnames or []
    if "prompt" not in fieldnames:
        raise ValueError("CSV file must have a 'prompt' column.")
    if "criteria" not in fieldnames:
        raise ValueError("CSV file must have a 'criteria' column (pipe-separated values).")

    items = []
    for i, row in enumerate(rows):
        prompt = row.get("prompt", "").strip()
        if not prompt:
            raise ValueError(f"Row {i + 1} has an empty 'prompt' field.")

        raw_criteria = row.get("criteria", "").strip()
        criteria = [c.strip() for c in raw_criteria.split("|") if c.strip()]
        if not criteria:
            raise ValueError(f"Row {i + 1} has no criteria. Use pipe (|) to separate multiple criteria.")

        item_id = row.get("id", "").strip() or f"item-{i + 1}"
        items.append(BatchItem(id=item_id, prompt=prompt, criteria=criteria))

    return items


# ── Batch runner ───────────────────────────────────────────────────────────────

def run_batch(
    judge: LLMJudge,
    items: list[BatchItem],
    on_item_start: callable = None,
    on_item_done: callable = None,
) -> BatchReport:
    """
    Run all items through the judge and return a BatchReport.

    Args:
        judge:          configured LLMJudge instance
        items:          list of BatchItems to evaluate
        on_item_start:  called with (index, item) before each evaluation
        on_item_done:   called with (index, item, result) after each evaluation
    """
    results: list[JudgmentResult] = []
    total_tokens = 0
    total_elapsed = 0.0

    for i, item in enumerate(items):
        if on_item_start:
            on_item_start(i, item)

        result = judge.run(prompt=item.prompt, criteria=item.criteria)
        results.append(result)
        total_tokens += result.tokens_used
        total_elapsed += result.elapsed_seconds

        if on_item_done:
            on_item_done(i, item, result)

    return BatchReport(
        source_file="",
        model=judge.model,
        model_provider=judge.model_provider.name,
        judge_model=judge.judge_model,
        judge_provider=judge.judge_provider.name,
        items=items,
        results=results,
        total_tokens=total_tokens,
        total_elapsed=round(total_elapsed, 2),
    )


# ── Markdown report ────────────────────────────────────────────────────────────

# Approximate cost per 1K tokens
_TOKEN_COST = {
    "anthropic": 0.003,
    "openai":    0.002,
    "gemini":    0.00015,
    "custom":    0.001,
}


def _estimate_cost(tokens: int, provider: str) -> str:
    rate = _TOKEN_COST.get(provider, 0.001)
    return f"~${(tokens / 1000) * rate:.5f}"


def render_markdown_report(report: BatchReport) -> str:
    """Generate a full Markdown report from a BatchReport."""
    lines: list[str] = []

    lines.append("# ⚖️ llm-judge Batch Report")
    lines.append("")
    if report.source_file:
        lines.append(f"**File:** `{report.source_file}`  ")
    lines.append(f"**Model:** `{report.model}` ({report.model_provider})  ")
    lines.append(f"**Judge:** `{report.judge_model}` ({report.judge_provider})  ")
    lines.append(f"**Date:** {date.today().isoformat()}  ")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total prompts | {len(report.results)} |")
    lines.append(f"| Passed | {report.pass_count} |")
    lines.append(f"| Failed | {report.fail_count} |")
    lines.append(f"| Pass rate | {report.pass_rate * 100:.1f}% |")
    lines.append(f"| Total tokens | {report.total_tokens:,} |")
    lines.append(f"| Estimated cost | {_estimate_cost(report.total_tokens, report.model_provider)} |")
    lines.append(f"| Total time | {report.total_elapsed}s |")
    lines.append("")

    # Per-item results
    lines.append("## Results")
    lines.append("")

    for item, result in zip(report.items, report.results):
        icon = "✅" if result.overall_pass else "❌"
        verdict_label = "PASS" if result.overall_pass else "FAIL"
        lines.append(f"### {icon} `{item.id}` — {verdict_label}")
        lines.append("")
        lines.append(f"**Prompt:** {item.prompt}")
        lines.append("")
        lines.append(f"**Response:**")
        lines.append(f"> {result.response.strip().replace(chr(10), '  ')}")
        lines.append("")
        lines.append("| Criterion | Result | Reasoning |")
        lines.append("|-----------|--------|-----------|")
        for v in result.verdicts:
            v_icon = "✅" if v.passed else "❌"
            reasoning = v.reasoning.replace("|", "\\|")
            lines.append(f"| {v.criterion} | {v_icon} | {reasoning} |")
        lines.append("")
        lines.append(
            f"*Confidence: {result.confidence:.2f} · "
            f"Tokens: {result.tokens_used:,} · "
            f"Time: {result.elapsed_seconds}s*"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append(
        f"*Generated by [llm-judge](https://github.com/hari1405/useful_llm_services) · "
        f"Pass rate: {report.pass_rate * 100:.1f}%*"
    )

    return "\n".join(lines)
