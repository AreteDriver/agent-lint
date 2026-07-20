"""Tests for agent_lint.autofix."""

from __future__ import annotations

from agent_lint.autofix import (
    apply_autofixes,
    generate_patch,
    get_fixable_findings,
)
from agent_lint.models import LintFinding, RuleCategory, Severity


def _make_finding(rule_id: str, message: str, step_id: str | None = None) -> LintFinding:
    return LintFinding(
        rule_id=rule_id,
        category=RuleCategory.BUDGET,
        severity=Severity.WARNING,
        message=message,
        step_id=step_id,
    )


class TestGetFixableFindings:
    def test_returns_only_fixable(self) -> None:
        findings = [
            _make_finding("B001", "No budget"),
            _make_finding("B002", "Step exceeds budget", step_id="build"),
            _make_finding("R003", "No max_retries", step_id="deploy"),
        ]
        fixable = get_fixable_findings(findings)
        ids = [f.rule_id for f in fixable]
        assert "B001" in ids
        assert "R003" in ids
        assert "B002" not in ids


class TestApplyAutofixes:
    def test_b001_adds_token_budget(self) -> None:
        raw = {"name": "test", "steps": []}
        findings = [_make_finding("B001", "No token budget")]
        fixed = apply_autofixes(raw, findings)
        assert fixed["token_budget"] == 50000

    def test_b001_preserves_existing(self) -> None:
        raw = {"name": "test", "token_budget": 100000, "steps": []}
        findings = [_make_finding("B001", "No token budget")]
        fixed = apply_autofixes(raw, findings)
        assert fixed["token_budget"] == 100000

    def test_r003_adds_max_retries(self) -> None:
        raw = {
            "steps": [
                {"id": "deploy", "type": "claude_code", "on_failure": "retry"},
            ]
        }
        findings = [_make_finding("R003", "retry without max_retries", step_id="deploy")]
        fixed = apply_autofixes(raw, findings)
        assert fixed["steps"][0]["max_retries"] == 3

    def test_r004_adds_shell_timeout(self) -> None:
        raw = {
            "steps": [
                {"id": "test", "type": "shell", "command": "pytest"},
            ]
        }
        findings = [_make_finding("R004", "No timeout", step_id="test")]
        fixed = apply_autofixes(raw, findings)
        assert fixed["steps"][0]["timeout_seconds"] == 300

    def test_s003_adds_input_type(self) -> None:
        raw = {
            "inputs": {"feature_request": {"required": True, "description": "Feature"}},
            "steps": [],
        }
        findings = [
            _make_finding("S003", "Required input 'feature_request' has no type constraint.")
        ]
        fixed = apply_autofixes(raw, findings)
        assert fixed["inputs"]["feature_request"]["type"] == "string"

    def test_e004_adds_max_concurrent(self) -> None:
        raw = {
            "steps": [
                {"id": "parallel", "type": "fan_out"},
            ]
        }
        findings = [_make_finding("E004", "No max_concurrent", step_id="parallel")]
        fixed = apply_autofixes(raw, findings)
        assert fixed["steps"][0]["max_concurrent"] == 4

    def test_multiple_fixes(self) -> None:
        raw = {
            "steps": [
                {"id": "deploy", "type": "claude_code", "on_failure": "retry"},
                {"id": "test", "type": "shell", "command": "pytest"},
            ]
        }
        findings = [
            _make_finding("R003", "retry without max_retries", step_id="deploy"),
            _make_finding("R004", "No timeout", step_id="test"),
        ]
        fixed = apply_autofixes(raw, findings)
        assert fixed["steps"][0]["max_retries"] == 3
        assert fixed["steps"][1]["timeout_seconds"] == 300

    def test_no_mutation_of_original(self) -> None:
        raw = {"name": "test", "steps": []}
        findings = [_make_finding("B001", "No token budget")]
        apply_autofixes(raw, findings)
        assert "token_budget" not in raw


class TestGeneratePatch:
    def test_generates_diff(self) -> None:
        original = {"name": "test", "steps": []}
        fixed = {"name": "test", "token_budget": 50000, "steps": []}
        patch = generate_patch(original, fixed)
        assert "--- a/workflow.yaml" in patch
        assert "+++ b/workflow.yaml" in patch
        assert "token_budget" in patch
