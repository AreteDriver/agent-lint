"""GitHub annotation formatter for CI integration.

Emits workflow commands that create inline PR annotations:
  https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions

Usage in GitHub Actions:
  agent-lint lint workflows/ --format github

This outputs lines like:
  ::error file=workflows/deploy.yaml,line=15,title=B001::No token_budget declared

GitHub Actions picks these up automatically and surfaces them as PR annotations.
"""

from __future__ import annotations

from agent_lint.models import LintReport, Severity


def _severity_to_annotation_level(severity: Severity) -> str:
    """Map internal severity to GitHub annotation level.

    GitHub levels: error, warning, notice.
    """
    mapping = {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.INFO: "notice",
    }
    return mapping.get(severity, "warning")


def _escape_command_value(value: str) -> str:
    """Escape special characters in GitHub workflow command values.

    See: https://github.com/actions/toolkit/blob/main/docs/commands.md#special-characters
    """
    replacements = [
        ("%", "%25"),
        ("\r", "%0D"),
        ("\n", "%0A"),
    ]
    result = value
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def format_github_annotations(report: LintReport) -> str:
    """Format lint report as GitHub workflow command annotations.

    Returns a multi-line string where each line is a workflow command.
    """
    lines: list[str] = []
    for finding in report.findings:
        level = _severity_to_annotation_level(finding.severity)
        title = _escape_command_value(finding.rule_id)
        message = _escape_command_value(finding.message)
        suggestion = _escape_command_value(finding.suggestion or "")

        # Build file path — best-effort from workflow_name.
        file_path = report.workflow_name or "workflow.yaml"

        # Include suggestion as part of message if present.
        full_message = message
        if suggestion:
            full_message += f" ({suggestion})"

        line = f"::{level} file={file_path},title={title}::{full_message}"
        lines.append(line)

    # Add a summary notice.
    summary = (
        f"::notice::agent-lint score: {report.score}/100 "
        f"({report.error_count} errors, {report.warning_count} warnings, "
        f"{report.info_count} info)"
    )
    lines.append(summary)

    return "\n".join(lines)
