"""
Decision Council CLI — terminal entry point.

Run:
    python -m council             # interactive mode
    python -m council run         # run with flags
    python -m council list        # list all personas
    python -m council providers   # list supported LLM providers
"""

import os
import sys
from pathlib import Path

import typer
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .council import DecisionCouncil
from .personas import DEFAULT_PERSONAS, Persona, build_custom_persona, get_persona
from .providers import (
    ALL_PROVIDERS,
    DEFAULT_MODELS,
    PROVIDER_ANTHROPIC,
    PROVIDER_CUSTOM,
    PROVIDER_GEMINI,
    PROVIDER_OPENAI,
    env_var_for_provider,
)

app = typer.Typer(
    name="council",
    help="🧠 Decision Council — stress-test your ideas before the meeting.",
    add_completion=False,
)
console = Console()


# ── Provider info ──────────────────────────────────────────────────────────────

PROVIDER_INFO = {
    PROVIDER_ANTHROPIC: {
        "label": "Anthropic (Claude)",
        "env":   "ANTHROPIC_API_KEY",
        "url":   "https://console.anthropic.com/",
        "color": "bright_blue",
    },
    PROVIDER_OPENAI: {
        "label": "OpenAI (GPT)",
        "env":   "OPENAI_API_KEY",
        "url":   "https://platform.openai.com/api-keys",
        "color": "bright_green",
    },
    PROVIDER_GEMINI: {
        "label": "Google Gemini",
        "env":   "GOOGLE_API_KEY",
        "url":   "https://aistudio.google.com/app/apikey",
        "color": "bright_yellow",
    },
    PROVIDER_CUSTOM: {
        "label": "Custom (any OpenAI-compatible endpoint)",
        "env":   "CUSTOM_API_KEY + CUSTOM_BASE_URL",
        "url":   "your endpoint docs",
        "color": "bright_magenta",
    },
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _header():
    console.print()
    console.rule("[bold bright_white]🏛️  Decision Council[/]", style="bright_white")
    console.print(
        "[dim]Stress-test your decisions before the room does.[/dim]",
        justify="center",
    )
    console.print()


def _get_api_key(provider: str, api_key: str | None, base_url: str | None) -> tuple[str, str | None]:
    """
    Resolve the API key for the given provider.
    Returns (key, base_url). Exits with a helpful message if key is missing.
    """
    info = PROVIDER_INFO.get(provider, {})
    env_var = env_var_for_provider(provider)
    key = api_key or os.environ.get(env_var, "")

    # For custom provider, also need base_url
    resolved_base_url = base_url or os.environ.get("CUSTOM_BASE_URL", "") or None

    if not key:
        get_url = info.get("url", "your provider's docs")
        env_hint = info.get("env", env_var)
        console.print(
            Panel(
                f"[yellow]No API key found for provider:[/] [bold]{provider}[/]\n\n"
                f"Set [bold]{env_hint}[/] in your environment:\n"
                f"  [dim]export {env_hint.split('+')[0].strip()}=your-key-here[/]\n\n"
                f"Or pass it directly:\n"
                f"  [dim]python -m council run --provider {provider} --api-key your-key[/]\n\n"
                f"Get your key at: [link={get_url}]{get_url}[/link]",
                title=f"[red]⚠ BYOK Required — {provider}[/]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    if provider == PROVIDER_CUSTOM and not resolved_base_url:
        console.print(
            Panel(
                "[yellow]Custom provider requires a base URL.[/]\n\n"
                "Set [bold]CUSTOM_BASE_URL[/] in your environment:\n"
                "  [dim]export CUSTOM_BASE_URL=https://your-endpoint/v1[/]\n\n"
                "Or pass it directly:\n"
                "  [dim]python -m council run --provider custom --base-url https://...[/]",
                title="[red]⚠ CUSTOM_BASE_URL Required[/]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    return key, resolved_base_url


def _select_provider_interactive() -> str:
    """Let the user pick a provider interactively."""
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Provider", style="bold")
    table.add_column("Env Var", style="dim")
    table.add_column("Default Model", style="dim")

    for i, p in enumerate(ALL_PROVIDERS, 1):
        info = PROVIDER_INFO[p]
        table.add_row(
            str(i),
            f"[{info['color']}]{info['label']}[/]",
            info["env"],
            DEFAULT_MODELS.get(p, "—"),
        )

    console.print("\n[bold]Choose your LLM provider:[/]\n")
    console.print(table)
    console.print()

    raw = Prompt.ask(
        "[bold]Provider[/] (number or name)",
        default="1",
    )

    # Try numeric
    try:
        idx = int(raw.strip()) - 1
        if 0 <= idx < len(ALL_PROVIDERS):
            return ALL_PROVIDERS[idx]
    except ValueError:
        pass

    # Try name
    lower = raw.strip().lower()
    for p in ALL_PROVIDERS:
        if p.startswith(lower):
            return p

    console.print("[yellow]Unrecognised — defaulting to anthropic.[/]")
    return PROVIDER_ANTHROPIC


def _select_personas_interactive() -> list[Persona]:
    """Let the user pick personas interactively."""
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("#", style="dim", width=3)
    table.add_column("Persona", style="bold")
    table.add_column("Role", style="dim")

    for i, p in enumerate(DEFAULT_PERSONAS, 1):
        table.add_row(str(i), f"{p.emoji} {p.name}", p.role)

    console.print(table)
    console.print()

    raw = Prompt.ask(
        "[bold]Select council members[/] (comma-separated numbers, or [bold]all[/])",
        default="all",
    )

    if raw.strip().lower() == "all":
        return list(DEFAULT_PERSONAS)

    selected = []
    for part in raw.split(","):
        part = part.strip()
        try:
            idx = int(part) - 1
            if 0 <= idx < len(DEFAULT_PERSONAS):
                selected.append(DEFAULT_PERSONAS[idx])
            else:
                console.print(f"[yellow]Skipping invalid index: {part}[/]")
        except ValueError:
            console.print(f"[yellow]Skipping invalid input: {part}[/]")

    if not selected:
        console.print("[red]No valid personas selected. Using all.[/]")
        return list(DEFAULT_PERSONAS)

    return selected


def _render_response(response, index: int, total: int):
    p = response.persona
    content = Text()
    content.append(response.critique)

    console.print(
        Panel(
            content,
            title=f"[bold {p.color}]{p.emoji} {p.name}[/]  [dim]{p.role}[/]",
            subtitle=f"[dim]{index}/{total} · {response.elapsed_seconds}s · {response.tokens_used:,} tokens[/]",
            border_style=p.color,
            padding=(1, 2),
        )
    )
    console.print()


# ── Commands ───────────────────────────────────────────────────────────────────

@app.command("run")
def run_council(
    proposal:     str  = typer.Option(None,  "--proposal",  "-p",  help="The decision or proposal text"),
    context:      str  = typer.Option("",    "--context",   "-c",  help="Additional background context"),
    personas:     list[str] = typer.Option(
        None, "--persona", help="Persona names to include (repeat for multiple). Omit for interactive."
    ),
    provider:     str  = typer.Option(None,  "--provider",         help=f"LLM provider: {', '.join(ALL_PROVIDERS)}"),
    api_key:      str  = typer.Option(None,  "--api-key",          help="API key for the chosen provider (BYOK)"),
    base_url:     str  = typer.Option(None,  "--base-url",         help="Base URL for custom provider"),
    model:        str  = typer.Option(None,  "--model",            help="Override the model for the chosen provider"),
    output:       Path = typer.Option(None,  "--output",    "-o",  help="Save report to a Markdown file"),
    all_personas: bool = typer.Option(False, "--all",              help="Use all default personas"),
):
    """Run your proposal through the Decision Council."""
    _header()

    # ── Provider selection ─────────────────────────────────────────────────────
    chosen_provider = provider
    if not chosen_provider:
        # Check if any known env var is set — use that provider by default
        if os.environ.get("ANTHROPIC_API_KEY"):
            chosen_provider = PROVIDER_ANTHROPIC
        elif os.environ.get("OPENAI_API_KEY"):
            chosen_provider = PROVIDER_OPENAI
        elif os.environ.get("GOOGLE_API_KEY"):
            chosen_provider = PROVIDER_GEMINI
        elif os.environ.get("CUSTOM_API_KEY"):
            chosen_provider = PROVIDER_CUSTOM
        else:
            chosen_provider = _select_provider_interactive()

    key, resolved_base_url = _get_api_key(chosen_provider, api_key, base_url)

    info = PROVIDER_INFO.get(chosen_provider, {})
    console.print(
        f"[dim]Provider:[/] [{info.get('color', 'white')}]{info.get('label', chosen_provider)}[/]  "
        f"[dim]Model:[/] [bold]{model or DEFAULT_MODELS.get(chosen_provider, '—')}[/]"
    )
    console.print()

    # ── Get proposal ───────────────────────────────────────────────────────────
    if not proposal:
        console.print("[bold]What decision or proposal should the council review?[/]")
        console.print("[dim](Tip: paste a paragraph — more detail = sharper critique)[/]\n")
        proposal = Prompt.ask("[bold yellow]Your proposal")

    if not proposal.strip():
        console.print("[red]Proposal cannot be empty.[/]")
        raise typer.Exit(1)

    # ── Optional context ───────────────────────────────────────────────────────
    if not context:
        add_ctx = Confirm.ask("\nAdd background context? (audience, constraints, goals)", default=False)
        if add_ctx:
            context = Prompt.ask("[dim]Context")

    # ── Select personas ────────────────────────────────────────────────────────
    council_members: list[Persona] = []

    if all_personas:
        council_members = list(DEFAULT_PERSONAS)
    elif personas:
        for name in personas:
            p = get_persona(name)
            if p:
                council_members.append(p)
            else:
                console.print(f"[yellow]Unknown persona: '{name}' — skipping.[/]")
        if not council_members:
            console.print("[red]No valid personas found. Run 'council list' to see options.[/]")
            raise typer.Exit(1)
    else:
        console.print("\n[bold]Choose your council:[/]\n")
        council_members = _select_personas_interactive()

    console.print()
    console.rule(f"[dim]Running {len(council_members)} council members[/]", style="dim")
    console.print()

    # ── Run council ────────────────────────────────────────────────────────────
    council = DecisionCouncil(
        provider=chosen_provider,
        api_key=key,
        model=model,
        base_url=resolved_base_url,
    )
    completed: list = []

    def on_start(persona: Persona):
        console.print(f"  [dim]→ Consulting {persona.emoji} {persona.name}...[/]")

    def on_done(response):
        completed.append(response)
        _render_response(response, len(completed), len(council_members))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        task = progress.add_task("Convening council...", total=None)
        session = council.run(
            proposal=proposal,
            personas=council_members,
            context=context,
            on_persona_start=on_start,
            on_persona_done=on_done,
        )
        progress.update(task, description="Synthesising...", completed=True)

    # ── Synthesis ──────────────────────────────────────────────────────────────
    console.rule("[bold bright_white]🧠 Battle Brief[/]", style="bright_white")
    console.print()
    console.print(Markdown(session.synthesis))
    console.print()
    console.rule(
        f"[dim]Total: {session.total_tokens:,} tokens · {session.total_elapsed}s · "
        f"{session.provider_name}/{session.model}[/]",
        style="dim",
    )

    # ── Save output ────────────────────────────────────────────────────────────
    if output is None:
        save = Confirm.ask("\nSave report to Markdown file?", default=False)
        if save:
            output = Path(Prompt.ask("Output file path", default="council_report.md"))

    if output:
        md = DecisionCouncil.to_markdown(session)
        output.write_text(md, encoding="utf-8")
        console.print(f"\n[green]✓ Report saved to:[/] {output.resolve()}")


@app.command("list")
def list_personas():
    """List all available default personas."""
    _header()
    table = Table(
        show_header=True,
        header_style="bold",
        title="[bold]Available Council Members[/]",
        title_style="bright_white",
    )
    table.add_column("Persona", style="bold")
    table.add_column("Role", style="dim")
    table.add_column("Focus")

    for p in DEFAULT_PERSONAS:
        table.add_row(
            f"[{p.color}]{p.emoji} {p.name}[/]",
            p.role,
            p.focus,
        )

    console.print(table)
    console.print()
    console.print(
        "[dim]Use[/] [bold]--persona 'The CFO'[/] [dim]to select specific members, "
        "or[/] [bold]--all[/] [dim]for the full council.[/]"
    )


@app.command("providers")
def list_providers():
    """List all supported LLM providers and their configuration."""
    _header()
    table = Table(
        show_header=True,
        header_style="bold",
        title="[bold]Supported LLM Providers[/]",
        title_style="bright_white",
    )
    table.add_column("Provider", style="bold")
    table.add_column("Env Var(s)", style="dim")
    table.add_column("Default Model")
    table.add_column("Get Key")

    for p in ALL_PROVIDERS:
        info = PROVIDER_INFO[p]
        table.add_row(
            f"[{info['color']}]{info['label']}[/]",
            info["env"],
            DEFAULT_MODELS.get(p, "—"),
            info["url"],
        )

    console.print(table)
    console.print()
    console.print(
        "[dim]Use[/] [bold]--provider anthropic[/] [dim](or openai/gemini/custom) to pick your provider.[/]\n"
        "[dim]If a provider's env var is already set, it will be auto-detected.[/]"
    )


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """🏛️ Decision Council — stress-test any decision before the meeting."""
    if ctx.invoked_subcommand is None:
        # Default: run interactive mode
        ctx.invoke(run_council)
