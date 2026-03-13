"""Tests for Pro-gated features and uncovered code paths.

Targets: cli.py (178-181, 211-221, 234-304), formatters.py (161, 172-197, 202).
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from agent_lint.cli import app
from agent_lint.formatters import (
    format_compare_json,
    format_compare_table,
    format_lint_markdown,
)
from agent_lint.models import (
    CompareResult,
    LintReport,
    StepEstimate,
    StepType,
    WorkflowEstimate,
)
from agent_lint.telemetry import TelemetryStore

runner = CliRunner()


def _make_console() -> tuple[Console, StringIO]:
    buf = StringIO()
    return Console(file=buf, force_terminal=False), buf


def _sample_compare_result(savings: float = 25.0) -> CompareResult:
    return CompareResult(
        workflow_name="Test Compare",
        estimates=[
            WorkflowEstimate(
                workflow_name="Test Compare",
                total_tokens=10000,
                total_cost_usd=0.10,
                steps=[
                    StepEstimate(
                        step_id="s1",
                        step_type=StepType.LLM,
                        provider="anthropic",
                        model="claude-sonnet-4",
                        estimated_tokens=10000,
                        input_tokens=3000,
                        output_tokens=7000,
                        cost_usd=0.10,
                        source="declared",
                    )
                ],
                provider="anthropic",
                model="claude-sonnet-4",
            ),
            WorkflowEstimate(
                workflow_name="Test Compare",
                total_tokens=10000,
                total_cost_usd=0.00,
                steps=[
                    StepEstimate(
                        step_id="s1",
                        step_type=StepType.LLM,
                        provider="ollama",
                        model="llama3",
                        estimated_tokens=10000,
                        input_tokens=3000,
                        output_tokens=7000,
                        cost_usd=0.00,
                        source="declared",
                    )
                ],
                provider="ollama",
                model="llama3",
            ),
        ],
        cheapest="ollama",
        most_expensive="anthropic",
        savings_pct=savings,
    )


# ---------------------------------------------------------------------------
# formatters.py — compare formatters (lines 172-197, 202)
# ---------------------------------------------------------------------------


class TestFormatCompareTable:
    def test_renders_workflow_name(self) -> None:
        c, buf = _make_console()
        format_compare_table(_sample_compare_result(), c)
        assert "Test Compare" in buf.getvalue()

    def test_renders_provider_names(self) -> None:
        c, buf = _make_console()
        format_compare_table(_sample_compare_result(), c)
        output = buf.getvalue()
        assert "anthropic" in output
        assert "ollama" in output

    def test_renders_savings_message(self) -> None:
        c, buf = _make_console()
        format_compare_table(_sample_compare_result(savings=25.0), c)
        assert "25.0% savings" in buf.getvalue()

    def test_no_savings_message_when_zero(self) -> None:
        c, buf = _make_console()
        format_compare_table(_sample_compare_result(savings=0.0), c)
        assert "savings" not in buf.getvalue()


class TestFormatCompareJson:
    def test_valid_json_output(self) -> None:
        c, buf = _make_console()
        format_compare_json(_sample_compare_result(), c)
        output = buf.getvalue()
        assert "cheapest" in output
        assert "ollama" in output


# ---------------------------------------------------------------------------
# formatters.py — lint markdown empty findings (line 161)
# ---------------------------------------------------------------------------


class TestLintMarkdownEmpty:
    def test_no_findings_message(self) -> None:
        report = LintReport(workflow_name="Clean", score=100, findings=[])
        c, buf = _make_console()
        format_lint_markdown(report, c)
        assert "No findings" in buf.getvalue()


# ---------------------------------------------------------------------------
# cli.py — status command with license key (lines 178-181)
# ---------------------------------------------------------------------------


class TestStatusWithLicense:
    @patch("agent_lint.licensing.get_license_info")
    def test_status_shows_masked_key(self, mock_info: MagicMock) -> None:
        from agent_lint.licensing import LicenseInfo, Tier

        mock_info.return_value = LicenseInfo(
            tier=Tier.PRO,
            license_key="ALNT-ABCD-EFGH-IJKL",
            valid=True,
        )
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "ALNT-ABCD" in result.output
        assert "****" in result.output

    @patch("agent_lint.licensing.get_license_info")
    def test_status_shows_invalid(self, mock_info: MagicMock) -> None:
        from agent_lint.licensing import LicenseInfo, Tier

        mock_info.return_value = LicenseInfo(
            tier=Tier.FREE,
            license_key="ALNT-XXXX-YYYY-ZZZZ",
            valid=False,
        )
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "invalid" in result.output


# ---------------------------------------------------------------------------
# cli.py — compare command through gate (lines 211-221)
# ---------------------------------------------------------------------------


class TestCompareCommand:
    @patch("agent_lint.cli.has_feature", return_value=True)
    def test_compare_with_pro(self, _feat: MagicMock, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["compare", str(gorgon_workflow_path)])
        assert result.exit_code == 0
        # Should render table output with provider names
        assert "anthropic" in result.output or "ollama" in result.output

    @patch("agent_lint.cli.has_feature", return_value=True)
    def test_compare_json(self, _feat: MagicMock, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["compare", str(gorgon_workflow_path), "--json"])
        assert result.exit_code == 0
        assert "cheapest" in result.output

    @patch("agent_lint.cli.has_feature", return_value=True)
    def test_compare_missing_file(self, _feat: MagicMock) -> None:
        result = runner.invoke(app, ["compare", "/nonexistent/workflow.yaml"])
        assert result.exit_code == 1
        assert "Error" in result.output


# ---------------------------------------------------------------------------
# cli.py — stats command (lines 234-304)
# ---------------------------------------------------------------------------


class TestStatsCommand:
    def test_stats_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AGENT_LINT_TELEMETRY", raising=False)
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "disabled" in result.output.lower()

    def test_stats_no_data(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LINT_TELEMETRY", "1")
        monkeypatch.setenv("AGENT_LINT_DIR", str(tmp_path))
        # No db file exists
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "No telemetry data" in result.output

    def test_stats_table_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LINT_TELEMETRY", "1")
        monkeypatch.setenv("AGENT_LINT_DIR", str(tmp_path))
        # Seed telemetry data
        store = TelemetryStore(tmp_path / "telemetry.db")
        store.record("command", "estimate")
        store.record("command", "lint")
        store.record("pro_gate", "compare")
        store.close()
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Total Events" in result.output
        assert "estimate" in result.output
        assert "compare" in result.output

    def test_stats_json_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AGENT_LINT_TELEMETRY", "1")
        monkeypatch.setenv("AGENT_LINT_DIR", str(tmp_path))
        store = TelemetryStore(tmp_path / "telemetry.db")
        store.record("command", "lint")
        store.close()
        result = runner.invoke(app, ["stats", "--json"])
        assert result.exit_code == 0
        assert "total_events" in result.output
        assert "commands" in result.output
