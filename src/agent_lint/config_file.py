"""Project-level configuration loader.

Supports:
  1. pyproject.toml — [tool.agent-lint] section
  2. .agent-lint.toml — standalone TOML file
  3. Environment variables — AGENT_LINT_* prefix

Precedence (highest first):
  CLI flags > environment variables > .agent-lint.toml > pyproject.toml > defaults
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from agent_lint.models import Severity


def _find_pyproject_toml(start: Path | None = None) -> Path | None:
    """Walk upward from start (or cwd) looking for pyproject.toml."""
    cwd = start or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.exists():
            return candidate
    return None


def _find_agent_lint_toml(start: Path | None = None) -> Path | None:
    """Walk upward from start (or cwd) looking for .agent-lint.toml."""
    cwd = start or Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".agent-lint.toml"
        if candidate.exists():
            return candidate
    return None


def _read_toml_section(path: Path, section: str) -> dict[str, Any] | None:
    """Parse a TOML file and return the requested table section."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[import-not-found,no-redef]
        except ImportError:
            return None

    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except OSError:
        return None

    keys = section.split(".")
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current if isinstance(current, dict) else None


def _load_env_overrides() -> dict[str, Any]:
    """Read AGENT_LINT_* environment variables."""
    overrides: dict[str, Any] = {}
    if os.getenv("AGENT_LINT_FAIL_UNDER"):
        overrides["fail_under"] = int(os.getenv("AGENT_LINT_FAIL_UNDER", ""))
    if os.getenv("AGENT_LINT_EXCLUDE_RULES"):
        overrides["exclude_rules"] = [
            r.strip() for r in os.getenv("AGENT_LINT_EXCLUDE_RULES", "").split(",") if r.strip()
        ]
    if os.getenv("AGENT_LINT_FORMAT"):
        overrides["format"] = os.getenv("AGENT_LINT_FORMAT")
    return overrides


class AgentLintConfig:
    """Resolved project configuration for agent-lint.

    Attributes are sourced from config files / env vars and can be overridden
    by CLI flags at invocation time.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.fail_under: int | None = kwargs.get("fail_under")
        self.format: str = kwargs.get("format", "table")
        self.exclude_rules: list[str] = kwargs.get("exclude_rules", [])
        self.custom_severities: dict[str, str] = kwargs.get("custom_severities", {})
        self.include_paths: list[str] = kwargs.get("include_paths", ["."])
        self.exclude_paths: list[str] = kwargs.get("exclude_paths", [])
        self.category: str | None = kwargs.get("category")
        self.severity: str | None = kwargs.get("severity")

    @classmethod
    def from_project(cls, start_path: Path | None = None) -> AgentLintConfig:
        """Load config from nearest project files (lowest precedence layer)."""
        merged: dict[str, Any] = {}

        # 1. pyproject.toml [tool.agent-lint]
        pyproject = _find_pyproject_toml(start_path)
        if pyproject:
            section = _read_toml_section(pyproject, "tool.agent-lint")
            if section:
                merged.update(section)

        # 2. .agent-lint.toml overrides pyproject.toml
        standalone = _find_agent_lint_toml(start_path)
        if standalone:
            section = _read_toml_section(standalone, "agent-lint")
            if section is None:
                # Allow top-level keys directly in .agent-lint.toml
                section = _read_toml_section(standalone, "")
            if section:
                merged.update(section)

        # Normalize kebab-case keys from TOML files before env overrides.
        if "exclude-rules" in merged:
            merged["exclude_rules"] = merged.pop("exclude-rules")
        if "custom-severities" in merged:
            merged["custom_severities"] = merged.pop("custom-severities")
        if "include-paths" in merged:
            merged["include_paths"] = merged.pop("include-paths")
        if "exclude-paths" in merged:
            merged["exclude_paths"] = merged.pop("exclude-paths")
        if "fail-under" in merged:
            merged["fail_under"] = merged.pop("fail-under")

        # 3. Environment variables override files
        merged.update(_load_env_overrides())

        return cls(**merged)

    def apply_cli_overrides(
        self,
        *,
        fail_under: int | None = None,
        fmt: str | None = None,
        category: str | None = None,
        severity: str | None = None,
    ) -> None:
        """Apply CLI flag overrides (highest precedence)."""
        if fail_under is not None:
            self.fail_under = fail_under
        if fmt is not None:
            self.format = fmt
        if category is not None:
            self.category = category
        if severity is not None:
            self.severity = severity

    def resolve_severity(self, rule_id: str, default: Severity) -> Severity:
        """Return custom severity for a rule if configured, else the default."""
        if rule_id in self.custom_severities:
            try:
                return Severity(self.custom_severities[rule_id].lower())
            except ValueError:
                pass
        return default


def load_config(start_path: Path | None = None) -> AgentLintConfig:
    """Convenience entry point: load project config from disk."""
    return AgentLintConfig.from_project(start_path)
