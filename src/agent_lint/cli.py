"""CLI entry point for agent-lint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agent_lint import __version__
from agent_lint.exceptions import AgentAuditError
from agent_lint.formatters import (
    format_compare_json,
    format_compare_table,
    format_estimate_json,
    format_estimate_markdown,
    format_estimate_table,
    format_lint_json,
    format_lint_markdown,
    format_lint_table,
)
from agent_lint.licensing import get_upgrade_message, has_feature
from agent_lint.telemetry import track_command, track_pro_gate

app = typer.Typer(
    name="agent-lint",
    help="Analyze agent workflow configs for cost estimation and anti-patterns.",
)
console = Console()


# ---------------------------------------------------------------------------
# Root callback
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Analyze agent workflow configs for cost estimation and anti-patterns."""
    if version:
        console.print(f"agent-lint {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# ---------------------------------------------------------------------------
# estimate
# ---------------------------------------------------------------------------


@app.command()
def estimate(
    workflow_file: Path = typer.Argument(..., help="Workflow YAML file to analyze."),
    provider: str | None = typer.Option(
        None, "--provider", "-p", help="Provider (anthropic, openai, ollama)."
    ),
    model: str | None = typer.Option(None, "--model", "-m", help="Model name."),
    json: bool = typer.Option(False, "--json", help="Output as JSON."),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format (table|json|markdown)."),
) -> None:
    """Estimate token usage and cost for a workflow."""
    track_command("estimate")
    from agent_lint.estimator import estimate_workflow
    from agent_lint.parsers import parse_workflow

    try:
        wf = parse_workflow(workflow_file)
        result = estimate_workflow(wf, provider=provider, model=model)
    except AgentAuditError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    if json or fmt == "json":
        format_estimate_json(result, console)
    elif fmt == "markdown":
        format_estimate_markdown(result, console)
    else:
        format_estimate_table(result, console)


# ---------------------------------------------------------------------------
# lint
# ---------------------------------------------------------------------------


@app.command()
def lint(
    workflow_file: Path = typer.Argument(..., help="Workflow YAML file to lint."),
    category: str | None = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category (budget|resilience|efficiency|security).",
    ),
    severity: str | None = typer.Option(
        None,
        "--severity",
        "-s",
        help="Filter by severity (error|warning|info).",
    ),
    fail_under: int | None = typer.Option(
        None, "--fail-under", help="Exit 1 if score is below this threshold."
    ),
    json: bool = typer.Option(False, "--json", help="Output as JSON."),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format (table|json|markdown)."),
) -> None:
    """Lint a workflow for anti-patterns and best practice violations."""
    track_command("lint")
    from agent_lint.linter import run_lint
    from agent_lint.models import RuleCategory, Severity
    from agent_lint.parsers import parse_workflow

    try:
        wf = parse_workflow(workflow_file)
    except AgentAuditError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    cat = None
    if category:
        try:
            cat = RuleCategory(category.lower())
        except ValueError:
            console.print(f"[red]Unknown category:[/red] {category}")
            raise typer.Exit(1) from None

    sev = None
    if severity:
        try:
            sev = Severity(severity.lower())
        except ValueError:
            console.print(f"[red]Unknown severity:[/red] {severity}")
            raise typer.Exit(1) from None

    report = run_lint(wf, category=cat, severity=sev)

    if json or fmt == "json":
        format_lint_json(report, console)
    elif fmt == "markdown":
        format_lint_markdown(report, console)
    else:
        format_lint_table(report, console)

    if fail_under is not None and report.score < fail_under:
        console.print(f"[red]Score {report.score} is below threshold {fail_under}.[/red]")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------


@app.command()
def status() -> None:
    """Show license status and available features."""
    track_command("status")
    from agent_lint.licensing import TIER_DEFINITIONS, get_license_info

    info = get_license_info()
    tier_config = TIER_DEFINITIONS[info.tier]

    console.print(f"\n[bold]agent-lint {__version__}[/bold]")
    console.print(f"[bold]Tier:[/bold] {tier_config.name} ({tier_config.price_label})")

    if info.license_key:
        masked = info.license_key[:9] + "****-****"
        console.print(f"[bold]Key:[/bold] {masked}")
        valid_str = "[green]valid[/green]" if info.valid else "[red]invalid[/red]"
        console.print(f"[bold]Valid:[/bold] {valid_str}")

    console.print(f"\n[bold]Features:[/bold] {', '.join(tier_config.features)}")
    console.print()


# ---------------------------------------------------------------------------
# compare (Pro)
# ---------------------------------------------------------------------------


@app.command()
def compare(
    workflow_file: Path = typer.Argument(..., help="Workflow YAML file to analyze."),
    providers: list[str] | None = typer.Option(
        None, "--provider", "-p", help="Providers to compare (repeat for each)."
    ),
    json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Compare workflow costs across providers (Pro feature)."""
    track_command("compare")
    from agent_lint.comparator import compare_providers
    from agent_lint.parsers import parse_workflow

    # Gate check.
    if not has_feature("compare"):
        track_pro_gate("compare")
        console.print(f"[yellow]{get_upgrade_message('compare')}[/yellow]")
        raise typer.Exit(1)

    try:
        wf = parse_workflow(workflow_file)
        result = compare_providers(wf, providers=providers)
    except AgentAuditError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    if json:
        format_compare_json(result, console)
    else:
        format_compare_table(result, console)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------


@app.command()
def stats(
    json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show local usage telemetry (requires AGENT_LINT_TELEMETRY=1)."""
    from agent_lint.telemetry import TelemetryStore, _telemetry_dir, is_enabled

    if not is_enabled():
        console.print(
            "[dim]Telemetry is disabled. "
            "Set AGENT_LINT_TELEMETRY=1 to enable local usage tracking.[/dim]"
        )
        return

    db_file = _telemetry_dir() / "telemetry.db"
    if not db_file.exists():
        console.print("[dim]No telemetry data yet.[/dim]")
        return

    from rich.table import Table

    ts = TelemetryStore(db_file)
    try:
        commands = ts.get_command_counts()
        pro_gates = ts.get_pro_gate_counts()
        total = ts.get_total_events()
        first = ts.get_first_event_time()
        last = ts.get_last_event_time()
        activity = ts.get_daily_activity()

        if json:
            import json as json_mod

            data = {
                "total_events": total,
                "first_event": first,
                "last_event": last,
                "commands": commands,
                "pro_gate_hits": pro_gates,
                "daily_activity": [{"date": d, "count": c} for d, c in activity],
            }
            console.print(json_mod.dumps(data, indent=2))
        else:
            overview = Table(title="Telemetry Overview")
            overview.add_column("Metric", style="cyan")
            overview.add_column("Value", style="green")
            overview.add_row("Total Events", str(total))
            overview.add_row("First Event", first or "n/a")
            overview.add_row("Last Event", last or "n/a")
            console.print(overview)

            if commands:
                cmd_table = Table(title="Command Usage")
                cmd_table.add_column("Command", style="cyan")
                cmd_table.add_column("Count", style="green", justify="right")
                for name, count in commands.items():
                    cmd_table.add_row(name, str(count))
                console.print(cmd_table)

            if pro_gates:
                gate_table = Table(title="Pro Feature Gate Hits")
                gate_table.add_column("Feature", style="cyan")
                gate_table.add_column("Attempts", style="yellow", justify="right")
                for name, count in pro_gates.items():
                    gate_table.add_row(name, str(count))
                console.print(gate_table)

            if activity:
                act_table = Table(title="Daily Activity (Last 7 Days)")
                act_table.add_column("Date", style="cyan")
                act_table.add_column("Events", style="green", justify="right")
                for day, count in activity:
                    act_table.add_row(day, str(count))
                console.print(act_table)
    finally:
        ts.close()
