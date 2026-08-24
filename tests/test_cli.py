"""Tests for agent_lint.cli."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from agent_lint import __version__
from agent_lint.cli import app

runner = CliRunner()


class TestVersion:
    def test_version_flag(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_short_version_flag(self) -> None:
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0


class TestNoArgs:
    def test_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert result.exit_code == 0


class TestEstimateCommand:
    def test_estimate_gorgon_workflow(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["estimate", str(gorgon_workflow_path)])
        assert result.exit_code == 0
        assert "Feature Build" in result.output
        assert "TOTAL" in result.output

    def test_estimate_json(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["estimate", str(gorgon_workflow_path), "--json"])
        assert result.exit_code == 0
        assert "total_tokens" in result.output

    def test_estimate_markdown(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["estimate", str(gorgon_workflow_path), "--format", "markdown"])
        assert result.exit_code == 0
        assert "| Step |" in result.output

    def test_estimate_with_provider(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["estimate", str(gorgon_workflow_path), "--provider", "ollama"])
        assert result.exit_code == 0
        assert "$0.0000" in result.output

    def test_estimate_missing_file(self) -> None:
        result = runner.invoke(app, ["estimate", "/nonexistent/workflow.yaml"])
        assert result.exit_code == 1
        assert "Error" in result.output


class TestLintCommand:
    def test_clean_process_registers_builtin_rules(self, gorgon_no_budget_path: Path) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_lint",
                "lint",
                str(gorgon_no_budget_path),
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        report = json.loads(result.stdout)
        assert report["score"] < 100
        assert report["findings"]

    def test_lint_gorgon_workflow(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path)])
        assert result.exit_code == 0
        assert "Score" in result.output

    def test_lint_json(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--json"])
        assert result.exit_code == 0
        assert "score" in result.output

    def test_lint_filter_category(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--category", "budget"])
        assert result.exit_code == 0

    def test_lint_invalid_category(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(
            app, ["lint", str(gorgon_workflow_path), "--category", "nonexistent"]
        )
        assert result.exit_code == 1
        assert "Unknown category" in result.output

    def test_lint_fail_under(self, gorgon_no_budget_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_no_budget_path), "--fail-under", "100"])
        # No-budget workflow will have findings, score < 100.
        assert result.exit_code == 1
        assert "Below threshold" in result.output

    def test_lint_fail_under_passes(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--fail-under", "1"])
        assert result.exit_code == 0

    def test_lint_json_remains_valid_when_threshold_fails(
        self, gorgon_no_budget_path: Path
    ) -> None:
        result = runner.invoke(
            app,
            ["lint", str(gorgon_no_budget_path), "--format", "json", "--fail-under", "100"],
        )

        assert result.exit_code == 1
        assert json.loads(result.stdout)["score"] < 100
        assert "Below threshold 100" in result.stderr

    def test_lint_missing_file(self) -> None:
        result = runner.invoke(app, ["lint", "/nonexistent/workflow.yaml"])
        assert result.exit_code == 1

    def test_lint_directory_as_valid_json(
        self, tmp_path: Path, gorgon_workflow_path: Path, langchain_path: Path
    ) -> None:
        workflows = tmp_path / "workflows"
        workflows.mkdir()
        (workflows / "one.yaml").write_text(gorgon_workflow_path.read_text())
        (workflows / "two.yml").write_text(langchain_path.read_text())

        result = runner.invoke(app, ["lint", str(workflows), "--format", "json"])

        assert result.exit_code == 0
        reports = json.loads(result.output)
        assert len(reports) == 2

    def test_lint_directory_fails_when_any_report_is_below_threshold(
        self, tmp_path: Path, gorgon_workflow_path: Path, gorgon_no_budget_path: Path
    ) -> None:
        workflows = tmp_path / "workflows"
        workflows.mkdir()
        (workflows / "clean.yaml").write_text(gorgon_workflow_path.read_text())
        (workflows / "risky.yaml").write_text(gorgon_no_budget_path.read_text())

        result = runner.invoke(app, ["lint", str(workflows), "--fail-under", "100"])

        assert result.exit_code == 1
        assert "Below threshold 100" in result.output

    def test_lint_directory_ignores_hidden_yaml(
        self, tmp_path: Path, gorgon_workflow_path: Path
    ) -> None:
        workflows = tmp_path / "workflows"
        workflows.mkdir()
        (workflows / "workflow.yaml").write_text(gorgon_workflow_path.read_text())
        hidden = workflows / ".github"
        hidden.mkdir()
        (hidden / "ci.yml").write_text("not: an agent workflow\n")

        result = runner.invoke(app, ["lint", str(workflows), "--format", "json"])

        assert result.exit_code == 0
        assert isinstance(json.loads(result.output), dict)

    def test_lint_github_format_is_wired(self, gorgon_no_budget_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_no_budget_path), "--format", "github"])
        assert result.exit_code == 0
        assert "::warning" in result.output

    def test_lint_sarif_format_is_wired(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--format", "sarif"])
        assert result.exit_code == 0
        assert json.loads(result.output)["version"] == "2.1.0"

    def test_lint_rejects_unknown_format(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--format", "xml"])
        assert result.exit_code == 1
        assert "Unknown format" in result.output


class TestStatusCommand:
    def test_status_free(self) -> None:
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Free" in result.output
        assert "agent-lint" in result.output
