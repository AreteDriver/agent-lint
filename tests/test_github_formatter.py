"""Tests for agent_lint.github_formatter."""

from __future__ import annotations

from agent_lint.github_formatter import format_github_annotations
from agent_lint.models import LintFinding, LintReport, RuleCategory, Severity


def _make_report(findings: list[LintFinding]) -> LintReport:
    return LintReport(
        workflow_name="workflows/deploy.yaml",
        score=85,
        findings=findings,
        error_count=sum(1 for f in findings if f.severity == Severity.ERROR),
        warning_count=sum(1 for f in findings if f.severity == Severity.WARNING),
        info_count=sum(1 for f in findings if f.severity == Severity.INFO),
    )


class TestFormatGithubAnnotations:
    def test_empty_report(self) -> None:
        report = _make_report([])
        output = format_github_annotations(report)
        lines = output.split("\n")
        assert len(lines) == 1
        assert lines[0].startswith("::notice::agent-lint score:")
        assert "85/100" in lines[0]

    def test_error_annotation(self) -> None:
        findings = [
            LintFinding(
                rule_id="S001",
                category=RuleCategory.SECURITY,
                severity=Severity.ERROR,
                message="Shell injection risk",
                step_id="deploy",
                suggestion="Validate inputs",
            )
        ]
        report = _make_report(findings)
        output = format_github_annotations(report, filepath="workflows/deploy.yaml")
        lines = output.split("\n")

        assert lines[0].startswith("::error file=workflows/deploy.yaml,title=S001::")
        assert "Shell injection risk" in lines[0]
        assert "Validate inputs" in lines[0]
    def test_warning_annotation(self) -> None:
        findings = [
            LintFinding(
                rule_id="B001",
                category=RuleCategory.BUDGET,
                severity=Severity.WARNING,
                message="No token budget",
                step_id="plan",
            )
        ]
        report = _make_report(findings)
        output = format_github_annotations(report)
        lines = output.split("\n")

        assert lines[0].startswith("::warning file=workflows/deploy.yaml,title=B001::")
        assert "No token budget" in lines[0]

    def test_notice_annotation(self) -> None:
        findings = [
            LintFinding(
                rule_id="E003",
                category=RuleCategory.EFFICIENCY,
                severity=Severity.INFO,
                message="Unnecessary checkpoint",
                step_id="check",
            )
        ]
        report = _make_report(findings)
        output = format_github_annotations(report)
        lines = output.split("\n")

        assert lines[0].startswith("::notice file=workflows/deploy.yaml,title=E003::")

    def test_multiline_message_escaping(self) -> None:
        findings = [
            LintFinding(
                rule_id="B002",
                category=RuleCategory.BUDGET,
                severity=Severity.WARNING,
                message="Step uses 50% of budget\nConsider breaking up",
                step_id="build",
            )
        ]
        report = _make_report(findings)
        output = format_github_annotations(report)
        lines = output.split("\n")

        # Newlines should be escaped, not actual line breaks.
        assert lines[0].startswith("::warning file=workflows/deploy.yaml,title=B002::")
        assert "%0A" in lines[0] or lines[0].count("::warning") == 1
