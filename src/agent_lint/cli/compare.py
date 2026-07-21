"""Compare command: compare workflow costs across providers (Pro feature)."""

from __future__ import annotations

from pathlib import Path

import typer

from agent_lint.cli import app, console
from agent_lint.exceptions import AgentAuditError
from agent_lint.formatters import format_compare_json, format_compare_table
from agent_lint.licensing import get_upgrade_message, has_feature
from agent_lint.telemetry import track_command, track_pro_gate


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
