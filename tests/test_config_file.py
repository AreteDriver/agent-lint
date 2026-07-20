"""Tests for agent_lint.config_file."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_lint.config_file import (
    AgentLintConfig,
    _find_agent_lint_toml,
    _find_pyproject_toml,
    load_config,
)


class TestFindPyprojectToml:
    def test_finds_in_cwd(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.agent-lint]\nfail-under = 90\n")
        found = _find_pyproject_toml(tmp_path)
        assert found is not None
        assert found.name == "pyproject.toml"

    def test_finds_in_parent(self, tmp_path: Path) -> None:
        child = tmp_path / "sub"
        child.mkdir()
        (tmp_path / "pyproject.toml").write_text("[tool.agent-lint]\n")
        found = _find_pyproject_toml(child)
        assert found is not None
        assert found.parent == tmp_path

    def test_none_when_missing(self, tmp_path: Path) -> None:
        assert _find_pyproject_toml(tmp_path) is None


class TestFindAgentLintToml:
    def test_finds_in_cwd(self, tmp_path: Path) -> None:
        (tmp_path / ".agent-lint.toml").write_text("[agent-lint]\nfail-under = 90\n")
        found = _find_agent_lint_toml(tmp_path)
        assert found is not None
        assert found.name == ".agent-lint.toml"


class TestAgentLintConfig:
    def test_defaults(self) -> None:
        cfg = AgentLintConfig()
        assert cfg.fail_under is None
        assert cfg.format == "table"
        assert cfg.exclude_rules == []
        assert cfg.custom_severities == {}

    def test_from_kwargs(self) -> None:
        cfg = AgentLintConfig(fail_under=80, format="json")
        assert cfg.fail_under == 80
        assert cfg.format == "json"

    def test_apply_cli_overrides(self) -> None:
        cfg = AgentLintConfig(fail_under=70)
        cfg.apply_cli_overrides(fail_under=90, fmt="sarif")
        assert cfg.fail_under == 90
        assert cfg.format == "sarif"

    def test_cli_none_does_not_override(self) -> None:
        cfg = AgentLintConfig(fail_under=70)
        cfg.apply_cli_overrides(fail_under=None)
        assert cfg.fail_under == 70


class TestLoadConfig:
    def test_from_pyproject_toml(self, tmp_path: Path) -> None:
        text = """
[tool.agent-lint]
fail-under = 85
format = "json"
exclude-rules = ["B001"]
"""
        (tmp_path / "pyproject.toml").write_text(text)
        cfg = load_config(tmp_path)
        assert cfg.fail_under == 85
        assert cfg.format == "json"
        assert cfg.exclude_rules == ["B001"]

    def test_from_agent_lint_toml(self, tmp_path: Path) -> None:
        text = """
[agent-lint]
fail-under = 90
format = "markdown"
"""
        (tmp_path / ".agent-lint.toml").write_text(text)
        cfg = load_config(tmp_path)
        assert cfg.fail_under == 90
        assert cfg.format == "markdown"

    def test_standalone_overrides_pyproject(self, tmp_path: Path) -> None:
        pp = """
[tool.agent-lint]
fail-under = 70
format = "table"
"""
        alt = """
[agent-lint]
fail-under = 95
format = "json"
"""
        (tmp_path / "pyproject.toml").write_text(pp)
        (tmp_path / ".agent-lint.toml").write_text(alt)
        cfg = load_config(tmp_path)
        # .agent-lint.toml takes precedence over pyproject.toml
        assert cfg.fail_under == 95
        assert cfg.format == "json"

    def test_env_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / "pyproject.toml").write_text("[tool.agent-lint]\nfail-under = 70\n")
        monkeypatch.setenv("AGENT_LINT_FAIL_UNDER", "99")
        monkeypatch.setenv("AGENT_LINT_FORMAT", "sarif")
        cfg = load_config(tmp_path)
        assert cfg.fail_under == 99
        assert cfg.format == "sarif"
