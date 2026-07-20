"""SARIF v2.1.0 formatter for GitHub Advanced Security integration.

This module produces SARIF JSON output compatible with:
- GitHub Advanced Security (code scanning alerts)
- VS Code SARIF Viewer extension
- Azure DevOps SARIF ingestion

Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from __future__ import annotations

import json as json_mod
from pathlib import Path
from typing import Any

from agent_lint.models import LintReport, Severity


def _severity_to_sarif_level(severity: Severity) -> str:
    """Map internal severity to SARIF level.

    SARIF levels: error, warning, note, none.
    """
    mapping = {
        Severity.ERROR: "error",
        Severity.WARNING: "warning",
        Severity.INFO: "note",
    }
    return mapping.get(severity, "warning")


def _build_tool_driver(report: LintReport) -> dict[str, Any]:
    """Build the tool.driver object with rule metadata."""
    from agent_lint import __version__
    from agent_lint.rules import get_all_rules

    rules = get_all_rules()
    rule_index: dict[str, int] = {}
    driver_rules: list[dict[str, Any]] = []

    for idx, rule in enumerate(rules):
        rule_index[rule.rule_id] = idx
        driver_rules.append(
            {
                "id": rule.rule_id,
                "name": rule.description,
                "shortDescription": {"text": rule.description},
                "defaultConfiguration": {
                    "level": _severity_to_sarif_level(rule.severity),
                },
                "properties": {
                    "category": rule.category.value,
                },
            }
        )

    return {
        "name": "agent-lint",
        "informationUri": "https://github.com/AreteDriver/agent-lint",
        "version": __version__,
        "rules": driver_rules,
    }


def _build_results(report: LintReport) -> list[dict[str, Any]]:
    """Map LintFindings to SARIF Result objects."""
    from agent_lint.rules import get_all_rules

    rules = get_all_rules()
    rule_index = {r.rule_id: i for i, r in enumerate(rules)}

    results: list[dict[str, Any]] = []
    for finding in report.findings:
        result: dict[str, Any] = {
            "ruleId": finding.rule_id,
            "ruleIndex": rule_index.get(finding.rule_id, -1),
            "level": _severity_to_sarif_level(finding.severity),
            "message": {
                "text": finding.message,
            },
        }

        # Include suggestion as a related location if present.
        if finding.suggestion:
            result["relatedLocations"] = [
                {
                    "id": 1,
                    "message": {"text": f"Suggestion: {finding.suggestion}"},
                }
            ]

        # Physical location — source_path from report if available.
        # Note: agent-lint currently operates on normalized models without
        # line/column info. We emit the file URI only.
        if report.workflow_name:
            # Best-effort: assume workflow_name is a path or use it as artifact.
            artifact_uri = _resolve_artifact_uri(report.workflow_name)
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": artifact_uri},
                        "region": {
                            "startLine": 1,  # Placeholder until parser adds line info.
                        },
                    }
                }
            ]

        results.append(result)

    return results


def _resolve_artifact_uri(workflow_name: str) -> str:
    """Convert workflow name or path into a relative URI.

    If the name looks like a path (contains / or \\), use it directly.
    Otherwise, assume it's a basename and prefix with ./workflows/.
    """
    if "/" in workflow_name or "\\" in workflow_name:
        return workflow_name
    return f"./workflows/{workflow_name}"


def format_sarif(report: LintReport) -> str:
    """Return a SARIF v2.1.0 JSON string from a LintReport."""
    tool_driver = _build_tool_driver(report)
    results = _build_results(report)

    sarif: dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": tool_driver},
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "exitCode": 0 if report.error_count == 0 else 1,
                    }
                ],
                "properties": {
                    "agent-lint-score": report.score,
                    "agent-lint-error-count": report.error_count,
                    "agent-lint-warning-count": report.warning_count,
                    "agent-lint-info-count": report.info_count,
                },
            }
        ],
    }

    return json_mod.dumps(sarif, indent=2)


def write_sarif_file(report: LintReport, output_path: Path) -> None:
    """Write SARIF output to disk for upload to GitHub Advanced Security."""
    output_path.write_text(format_sarif(report), encoding="utf-8")
