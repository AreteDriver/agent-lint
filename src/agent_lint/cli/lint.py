"""Lint command: analyze workflow configs for anti-patterns."""

from __future__ import annotations

import json as json_mod
from pathlib import Path

import typer

from agent_lint.autofix import apply_autofixes, generate_patch, get_fixable_findings
from agent_lint.cli import app, console
from agent_lint.exceptions import AgentAuditError
from agent_lint.formatters import format_lint_json, format_lint_markdown, format_lint_table
from agent_lint.github_formatter import format_github_annotations
from agent_lint.models import LintReport
from agent_lint.sarif_formatter import format_sarif
from agent_lint.telemetry import track_command

_WORKFLOW_SUFFIXES = {".yaml", ".yml"}
_OUTPUT_FORMATS = {"table", "json", "markdown", "github", "sarif"}


def _discover_workflows(path: Path) -> list[Path]:
    """Return a stable list of YAML workflow files for a file or directory input."""
    if path.is_file():
        if path.suffix.lower() not in _WORKFLOW_SUFFIXES:
            raise AgentAuditError(f"Workflow must be a YAML file: {path}")
        return [path]
    if not path.is_dir():
        raise AgentAuditError(f"Workflow path not found: {path}")

    workflows = sorted(
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file()
        and candidate.suffix.lower() in _WORKFLOW_SUFFIXES
        and not any(part.startswith(".") for part in candidate.relative_to(path).parts)
    )
    if not workflows:
        raise AgentAuditError(f"No YAML workflow files found in: {path}")
    return workflows


def _format_reports(reports: list[LintReport], fmt: str) -> None:
    """Render one or more reports while preserving valid machine-readable output."""
    if fmt == "json" and len(reports) > 1:
        console.print_json(
            json_mod.dumps([report.model_dump(mode="json") for report in reports], indent=2)
        )
        return
    if fmt == "sarif":
        runs = []
        for report in reports:
            runs.extend(json_mod.loads(format_sarif(report))["runs"])
        print(
            json_mod.dumps(
                {
                    "$schema": "https://raw.githubusercontent.com/oasis-tcs/"
                    "sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
                    "version": "2.1.0",
                    "runs": runs,
                },
                indent=2,
            )
        )
        return

    for report in reports:
        if fmt == "json":
            format_lint_json(report, console)
        elif fmt == "markdown":
            format_lint_markdown(report, console)
        elif fmt == "github":
            print(format_github_annotations(report))
        else:
            format_lint_table(report, console)


@app.command()
def lint(
    workflow_file: Path = typer.Argument(..., help="Workflow YAML file or directory to lint."),
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
    fmt: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format (table|json|markdown|github|sarif).",
    ),
    fix: bool = typer.Option(False, "--fix", help="Suggest autofixes as a diff patch."),
) -> None:
    """Lint a workflow for anti-patterns and best practice violations."""
    track_command("lint")
    from agent_lint.linter import run_lint
    from agent_lint.models import RuleCategory, Severity
    from agent_lint.parsers import load_yaml, parse_workflow

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

    output_format = "json" if json else fmt.lower()
    if output_format not in _OUTPUT_FORMATS:
        console.print(f"[red]Unknown format:[/red] {fmt}")
        raise typer.Exit(1)

    try:
        workflow_paths = _discover_workflows(workflow_file)
        reports = [
            run_lint(parse_workflow(path), category=cat, severity=sev) for path in workflow_paths
        ]
    except AgentAuditError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    if fix:
        for path, report in zip(workflow_paths, reports, strict=True):
            fixable = get_fixable_findings(report.findings)
            if not fixable:
                continue
            console.print(f"\n[bold]{path}: {len(fixable)} fixable finding(s):[/bold]")
            for finding in fixable:
                console.print(f"  [dim]{finding.rule_id}[/dim]: {finding.message}")
            try:
                raw = load_yaml(path)
                fixed = apply_autofixes(raw, fixable)
                patch = generate_patch(raw, fixed)
                if patch:
                    console.print("\n[bold]Proposed patch:[/bold]")
                    console.print(patch)
            except Exception as exc:
                console.print(f"\n[yellow]Could not generate patch for {path}: {exc}[/yellow]")
    else:
        _format_reports(reports, output_format)

    failed = [report for report in reports if fail_under is not None and report.score < fail_under]
    if failed:
        summary = ", ".join(f"{report.workflow_name} ({report.score})" for report in failed)
        if output_format in {"json", "sarif"}:
            typer.echo(f"Below threshold {fail_under}: {summary}", err=True)
        else:
            console.print(f"[red]Below threshold {fail_under}:[/red] {summary}")
        raise typer.Exit(1)
