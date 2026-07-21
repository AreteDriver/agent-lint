"""Lint command: analyze workflow configs for anti-patterns."""

from __future__ import annotations

from pathlib import Path

import typer

from agent_lint.autofix import apply_autofixes, generate_patch, get_fixable_findings
from agent_lint.cli import app, console
from agent_lint.exceptions import AgentAuditError
from agent_lint.formatters import format_lint_json, format_lint_markdown, format_lint_table
from agent_lint.telemetry import track_command


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
    fix: bool = typer.Option(False, "--fix", help="Suggest autofixes as a diff patch."),
) -> None:
    """Lint a workflow for anti-patterns and best practice violations."""
    track_command("lint")
    from agent_lint.linter import run_lint
    from agent_lint.models import RuleCategory, Severity
    from agent_lint.parsers import load_yaml, parse_workflow

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

    if fix and report.findings:
        fixable = get_fixable_findings(report.findings)
        if fixable:
            console.print(f"\n[bold]{len(fixable)} fixable finding(s):[/bold]")
            for f in fixable:
                console.print(f"  [dim]{f.rule_id}[/dim]: {f.message}")
            try:
                raw = load_yaml(workflow_file)
                fixed = apply_autofixes(raw, fixable)
                patch = generate_patch(raw, fixed)
                if patch:
                    console.print("\n[bold]Proposed patch:[/bold]")
                    console.print(patch)
                else:
                    console.print(
                        "\n[yellow]No patch generated (fixes did not change structure).[/yellow]"
                    )
            except Exception as exc:
                console.print(f"\n[yellow]Could not generate patch: {exc}[/yellow]")
        else:
            console.print("\n[dim]No autofixes available for current findings.[/dim]")
    else:
        if json or fmt == "json":
            format_lint_json(report, console)
        elif fmt == "markdown":
            format_lint_markdown(report, console)
        else:
            format_lint_table(report, console)

    if fail_under is not None and report.score < fail_under:
        console.print(f"[red]Score {report.score} is below threshold {fail_under}.[/red]")
        raise typer.Exit(1)
