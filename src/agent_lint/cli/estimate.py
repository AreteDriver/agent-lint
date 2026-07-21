"""Estimate command: project token usage and cost for a workflow."""

from __future__ import annotations

from pathlib import Path

import typer

from agent_lint.cli import app, console
from agent_lint.exceptions import AgentAuditError
from agent_lint.formatters import (
    format_estimate_json,
    format_estimate_markdown,
    format_estimate_table,
)
from agent_lint.telemetry import track_command


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
