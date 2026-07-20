"""Tests for agent_lint.sarif_formatter."""

from __future__ import annotations

import json

# Trigger rule registration so get_all_rules() returns populated list.
import agent_lint.rules.budget  # noqa: F401
import agent_lint.rules.efficiency  # noqa: F401
import agent_lint.rules.resilience  # noqa: F401
import agent_lint.rules.security  # noqa: F401
from agent_lint.models import (
    LintFinding,
    LintReport,
    RuleCategory,
    Severity,
)
from agent_lint.sarif_formatter import format_sarif


def _make_report(findings: list[LintFinding]) -> LintReport:
    return LintReport(
        workflow_name="test-workflow.yaml",
        score=85,
        findings=findings,
        error_count=sum(1 for f in findings if f.severity == Severity.ERROR),
        warning_count=sum(1 for f in findings if f.severity == Severity.WARNING),
        info_count=sum(1 for f in findings if f.severity == Severity.INFO),
    )


class TestFormatSarif:
    def test_basic_structure(self) -> None:
        report = _make_report([])
        raw = format_sarif(report)
        data = json.loads(raw)

        assert data["version"] == "2.1.0"
        assert "$schema" in data
        runs = data["runs"]
        assert len(runs) == 1

        run = runs[0]
        assert "tool" in run
        assert "results" in run
        assert run["results"] == []
        assert run["invocations"][0]["executionSuccessful"] is True
        assert run["properties"]["agent-lint-score"] == 85

    def test_with_findings(self) -> None:
        findings = [
            LintFinding(
                rule_id="B001",
                category=RuleCategory.BUDGET,
                severity=Severity.WARNING,
                message="No token budget",
                step_id="plan",
                suggestion="Add token_budget",
            ),
            LintFinding(
                rule_id="S001",
                category=RuleCategory.SECURITY,
                severity=Severity.ERROR,
                message="Shell injection risk",
                step_id="deploy",
            ),
        ]
        report = _make_report(findings)
        raw = format_sarif(report)
        data = json.loads(raw)

        results = data["runs"][0]["results"]
        assert len(results) == 2

        # Check first result.
        r0 = results[0]
        assert r0["ruleId"] == "B001"
        assert r0["level"] == "warning"
        assert r0["message"]["text"] == "No token budget"
        assert r0["relatedLocations"][0]["message"]["text"] == "Suggestion: Add token_budget"

        # Check second result.
        r1 = results[1]
        assert r1["ruleId"] == "S001"
        assert r1["level"] == "error"
        assert "relatedLocations" not in r1

    def test_tool_driver_has_rules(self) -> None:
        report = _make_report([])
        raw = format_sarif(report)
        data = json.loads(raw)

        driver = data["runs"][0]["tool"]["driver"]
        assert driver["name"] == "agent-lint"
        assert "version" in driver
        assert len(driver["rules"]) > 0

    def test_exit_code_on_errors(self) -> None:
        report = _make_report(
            [
                LintFinding(
                    rule_id="S001",
                    category=RuleCategory.SECURITY,
                    severity=Severity.ERROR,
                    message="error",
                )
            ]
        )
        raw = format_sarif(report)
        data = json.loads(raw)
        assert data["runs"][0]["invocations"][0]["exitCode"] == 1
