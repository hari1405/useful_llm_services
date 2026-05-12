#!/usr/bin/env python3
"""
llm-judge — CLI entry point.

Usage:
    python judge.py --prompt "..." --criteria "..." --model gemini
    python judge.py --help
"""

from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.rule import Rule
from rich.text import Text

from llm_judge.batch import (
    BatchReport,
    load_batch,
    render_markdown_report,
    run_batch,
)
from llm_judge.core import JudgmentResult, LLMJudge
from llm_judge.providers import (
    ALL_PROVIDERS,
    DEFAULT_MODELS,
    get_provider,
)

app = typer.Typer(
    name="llm-judge",
    help="Run a prompt through any LLM. Judge the response against your criteria.",
    add_completion=False,
)
console = Console()

# Approximate cost per 1K tokens (input+output blended)
_TOKEN_COST = {
    "anthropic": 0.003,
    "openai":    0.002,
    "gemini":    0.00015,
    "custom":    0.001,
}


def _estimate_cost(tokens: int, provider: str) -> str:
    rate = _TOKEN_COST.get(provider, 0.001)
    cost = (tokens / 1000) * rate
    return f"~${cost:.5f}"


def _print_result(result: JudgmentResult) -> None:
    console.print()
    console.print(Rule("[bold]⚖️  LLM Judge[/bold]"))

    console.print(f"[dim]Prompt:[/dim]   {result.prompt}")
    console.print(f"[dim]Model:[/dim]    [cyan]{result.model}[/cyan]  ({result.model_provider})")
    console.print(f"[dim]Judge:[/dim]    [cyan]{result.judge_model}[/cyan]  ({result.judge_provider})")
    console.print()

    console.print("[bold]Model response:[/bold]")
    for line in result.response.strip().splitlines():
        console.print(f"  {line}")
    console.print()

    console.print(Rule("[dim]Evaluation[/dim]"))
    for v in result.verdicts:
        icon = "✅" if v.passed else "❌"
        status_color = "green" if v.passed else "red"
        console.print(f"[{status_color}]{icon}  {v.criterion}[/{status_color}]")
        console.print(f'    [dim]"{v.reasoning}"[/dim]')
        console.print()

    console.print(Rule())
    verdict_text = Text()
    if result.overall_pass:
        verdict_text.append("✅ PASS", style="bold green")
    else:
        verdict_text.append("❌ FAIL", style="bold red")
    verdict_text.append(f"  ({result.passed_count}/{result.total_count} criteria met)", style="dim")

    console.print(f"[bold]Verdict:[/bold]     ", end="")
    console.print(verdict_text)
    console.print(f"[bold]Confidence:[/bold]  {result.confidence:.2f}")
    console.print(
        f"[bold]Tokens:[/bold]     {result.tokens_used:,}  "
        f"([dim]{_estimate_cost(result.tokens_used, result.model_provider)}[/dim])"
    )
    console.print(f"[bold]Time:[/bold]        {result.elapsed_seconds}s")
    console.print()


@app.command()
def main(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="The prompt to evaluate."),
    criteria: list[str] = typer.Option(
        [], "--criteria", "-c",
        help="A criterion the response must satisfy. Repeat for multiple. "
             'Example: --criteria "Must be under 50 words" --criteria "Must mention Paris"',
    ),
    model: str = typer.Option("gemini", "--model", "-m", help=f"Provider for the model being evaluated. One of: {', '.join(ALL_PROVIDERS)}"),
    judge: str = typer.Option("gemini", "--judge", "-j", help="Provider for the judge. Defaults to same as --model."),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="Override the model ID (e.g. gemini-3.1-flash-lite)."),
    judge_name: Optional[str] = typer.Option(None, "--judge-name", help="Override the judge model ID."),
    model_key: Optional[str] = typer.Option(None, "--model-key", help="API key for the model provider (overrides env var)."),
    judge_key: Optional[str] = typer.Option(None, "--judge-key", help="API key for the judge provider (overrides env var)."),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for custom provider."),
    max_tokens: int = typer.Option(512, "--max-tokens", help="Max tokens for model response."),
) -> None:
    """
    Run a prompt through an LLM and judge the response against your criteria.

    Examples:

      python judge.py --prompt "What is the capital of France?" \\
                      --criteria "Must answer Paris" \\
                      --criteria "Must be under 20 words" \\
                      --model gemini

      python judge.py --prompt "Explain transformers" \\
                      --criteria "Must mention attention mechanism" \\
                      --model anthropic --judge gemini
    """
    # ── Interactive prompt input if not provided ───────────────────────────────
    if not prompt:
        console.print("[bold]⚖️  LLM Judge[/bold] — interactive mode")
        console.print("[dim]Press Ctrl+C to exit.[/dim]")
        console.print()
        prompt = typer.prompt("Prompt")

    if not criteria:
        console.print()
        console.print("[dim]Enter criteria one at a time. Press Enter on an empty line when done.[/dim]")
        while True:
            c = typer.prompt("Criterion (or Enter to finish)", default="", show_default=False)
            if not c.strip():
                break
            criteria.append(c.strip())

    if not criteria:
        console.print("[red]At least one criterion is required.[/red]")
        raise typer.Exit(1)

    # ── Resolve models ─────────────────────────────────────────────────────────
    resolved_model = model_name or DEFAULT_MODELS.get(model.lower(), DEFAULT_MODELS["gemini"])
    resolved_judge_model = judge_name or DEFAULT_MODELS.get(judge.lower(), DEFAULT_MODELS["gemini"])

    # ── Build providers ────────────────────────────────────────────────────────
    try:
        model_provider = get_provider(model, api_key=model_key, base_url=base_url)
        # Reuse model key for judge if same provider and no separate judge key given
        effective_judge_key = judge_key or (model_key if judge.lower() == model.lower() else None)
        judge_provider = get_provider(judge, api_key=effective_judge_key, base_url=base_url)
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    # ── Run ────────────────────────────────────────────────────────────────────
    console.print()
    console.print(
        f"[dim]Running prompt through [cyan]{resolved_model}[/cyan] "
        f"→ judging with [cyan]{resolved_judge_model}[/cyan]...[/dim]"
    )

    try:
        judge_instance = LLMJudge(
            model_provider=model_provider,
            judge_provider=judge_provider,
            model=resolved_model,
            judge_model=resolved_judge_model,
            max_tokens=max_tokens,
        )
        result = judge_instance.run(prompt=prompt, criteria=list(criteria))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    _print_result(result)

    # Exit code reflects verdict
    raise typer.Exit(0 if result.overall_pass else 1)


@app.command("batch")
def batch_cmd(
    file: str = typer.Argument(..., help="Path to .json or .csv batch file."),
    model: str = typer.Option("gemini", "--model", "-m", help=f"Provider for model. One of: {', '.join(ALL_PROVIDERS)}"),
    judge: str = typer.Option("gemini", "--judge", "-j", help="Provider for the judge."),
    model_name: Optional[str] = typer.Option(None, "--model-name", help="Override model ID."),
    judge_name: Optional[str] = typer.Option(None, "--judge-name", help="Override judge model ID."),
    model_key: Optional[str] = typer.Option(None, "--model-key", help="API key for model provider."),
    judge_key: Optional[str] = typer.Option(None, "--judge-key", help="API key for judge provider."),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for custom provider."),
    max_tokens: int = typer.Option(512, "--max-tokens", help="Max tokens for model response."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save Markdown report to this path."),
) -> None:
    """
    Run a batch of prompts from a JSON or CSV file.

    JSON format:
      [{"id": "q1", "prompt": "...", "criteria": ["...", "..."]}]

    CSV format (criteria pipe-separated):
      id,prompt,criteria
      q1,"What is X?","Criterion one|Criterion two"

    Examples:

      python judge.py batch examples/sample_prompts.json --model gemini

      python judge.py batch examples/sample_prompts.csv --model anthropic --judge gemini --output report.md
    """
    # ── Load file ──────────────────────────────────────────────────────────────
    try:
        items = load_batch(file)
    except (ValueError, FileNotFoundError) as e:
        console.print(f"[red]File error:[/red] {e}")
        raise typer.Exit(1)

    console.print()
    console.print(Rule("[bold]⚖️  LLM Judge — Batch Mode[/bold]"))
    console.print(f"[dim]File:[/dim]   {file}")
    console.print(f"[dim]Items:[/dim]  {len(items)}")

    # ── Resolve models & providers ─────────────────────────────────────────────
    resolved_model = model_name or DEFAULT_MODELS.get(model.lower(), DEFAULT_MODELS["gemini"])
    resolved_judge_model = judge_name or DEFAULT_MODELS.get(judge.lower(), DEFAULT_MODELS["gemini"])

    console.print(f"[dim]Model:[/dim]  [cyan]{resolved_model}[/cyan]  ({model})")
    console.print(f"[dim]Judge:[/dim]  [cyan]{resolved_judge_model}[/cyan]  ({judge})")
    console.print()

    try:
        model_provider = get_provider(model, api_key=model_key, base_url=base_url)
        effective_judge_key = judge_key or (model_key if judge.lower() == model.lower() else None)
        judge_provider = get_provider(judge, api_key=effective_judge_key, base_url=base_url)
    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)

    judge_instance = LLMJudge(
        model_provider=model_provider,
        judge_provider=judge_provider,
        model=resolved_model,
        judge_model=resolved_judge_model,
        max_tokens=max_tokens,
    )

    # ── Run with progress ──────────────────────────────────────────────────────
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

    results = []
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(items))

        def on_start(i: int, item) -> None:
            progress.update(task, description=f"[{i + 1}/{len(items)}] {item.id[:30]}")

        def on_done(i: int, item, result) -> None:
            results.append(result)
            progress.advance(task)

        try:
            report = run_batch(judge_instance, items, on_item_start=on_start, on_item_done=on_done)
            report.source_file = file
        except Exception as e:
            console.print(f"[red]Error during batch run:[/red] {e}")
            raise typer.Exit(1)

    # ── Terminal summary table ─────────────────────────────────────────────────
    from rich.table import Table

    console.print()
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Prompt", max_width=40)
    table.add_column("Verdict", justify="center")
    table.add_column("Criteria", justify="center")
    table.add_column("Confidence", justify="right")

    for item, result in zip(report.items, report.results):
        verdict_str = "[green]✅ PASS[/green]" if result.overall_pass else "[red]❌ FAIL[/red]"
        table.add_row(
            item.id,
            item.prompt[:40] + ("…" if len(item.prompt) > 40 else ""),
            verdict_str,
            f"{result.passed_count}/{result.total_count}",
            f"{result.confidence:.2f}",
        )

    console.print(table)
    console.print()
    console.print(Rule())

    pass_pct = report.pass_rate * 100
    rate_color = "green" if pass_pct >= 80 else ("yellow" if pass_pct >= 50 else "red")
    console.print(
        f"[bold]Pass rate:[/bold]  [{rate_color}]{report.pass_count}/{len(report.results)} "
        f"({pass_pct:.1f}%)[/{rate_color}]"
    )
    console.print(f"[bold]Tokens:[/bold]    {report.total_tokens:,}  "
                  f"([dim]{_estimate_cost(report.total_tokens, model)}[/dim])")
    console.print(f"[bold]Time:[/bold]      {report.total_elapsed}s")
    console.print()

    # ── Save report ────────────────────────────────────────────────────────────
    if output:
        md = render_markdown_report(report)
        with open(output, "w", encoding="utf-8") as f:
            f.write(md)
        console.print(f"[dim]Report saved → {output}[/dim]")
        console.print()

    raise typer.Exit(0 if report.pass_rate == 1.0 else 1)


if __name__ == "__main__":
    app()
