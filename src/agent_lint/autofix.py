"""Autofix engine: generate patchable fixes for fixable lint findings.

Each fixable rule has a corresponding autofix function that receives the
raw YAML dict and the LintFinding, and returns a modified dict.

Usage:
    report = run_lint(wf)
    raw = load_yaml(path)
    fixed = apply_autofixes(raw, report.findings)
    print(yaml.dump(fixed))
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent_lint.models import LintFinding

FixFunc = Callable[[dict[str, Any], LintFinding], dict[str, Any]]

_FIX_REGISTRY: dict[str, FixFunc] = {}


def autofix(rule_id: str) -> Callable[[FixFunc], FixFunc]:
    """Decorator to register an autofix function for a rule."""

    def decorator(func: FixFunc) -> FixFunc:
        _FIX_REGISTRY[rule_id] = func
        return func

    return decorator


def get_fixable_findings(findings: list[LintFinding]) -> list[LintFinding]:
    """Return only findings that have a registered autofix."""
    return [f for f in findings if f.rule_id in _FIX_REGISTRY]


def apply_autofixes(raw: dict[str, Any], findings: list[LintFinding]) -> dict[str, Any]:
    """Apply all registered autofixes to the raw YAML dict.

    Fixes are applied in order. The dict is deep-copied before mutation.
    """
    import copy

    fixed = copy.deepcopy(raw)
    fixable = get_fixable_findings(findings)
    for finding in fixable:
        func = _FIX_REGISTRY[finding.rule_id]
        fixed = func(fixed, finding)
    return fixed


def _find_step_by_id(raw: dict[str, Any], step_id: str) -> dict[str, Any] | None:
    """Locate a step dict by its 'id' within the raw YAML, searching recursively."""
    steps = raw.get("steps")
    if not isinstance(steps, list):
        return None

    def search(step_list: list[Any]) -> dict[str, Any] | None:
        for step in step_list:
            if isinstance(step, dict):
                if step.get("id") == step_id:
                    return step
                for key in ("steps", "nested_steps"):
                    nested = step.get(key)
                    if isinstance(nested, list):
                        found = search(nested)
                        if found is not None:
                            return found
        return None

    return search(steps)


# ---------------------------------------------------------------------------
# Budget fixes (B)
# ---------------------------------------------------------------------------


@autofix("B001")
def fix_b001_add_token_budget(raw: dict[str, Any], _finding: LintFinding) -> dict[str, Any]:
    """Add a default token_budget at workflow level."""
    if raw.get("token_budget") is None:
        raw["token_budget"] = 50000
    return raw
    return raw


# ---------------------------------------------------------------------------
# Resilience fixes (R)
# ---------------------------------------------------------------------------


@autofix("R003")
def fix_r003_add_max_retries(raw: dict[str, Any], finding: LintFinding) -> dict[str, Any]:
    """Add max_retries: 3 to a step that has on_failure: retry but no max_retries."""
    step = _find_step_by_id(raw, finding.step_id or "")
    if step and step.get("on_failure") == "retry":
        step["max_retries"] = 3
    return raw


@autofix("R004")
def fix_r004_add_shell_timeout(raw: dict[str, Any], finding: LintFinding) -> dict[str, Any]:
    """Add timeout_seconds: 300 to a shell step with no timeout."""
    step = _find_step_by_id(raw, finding.step_id or "")
    if step and step.get("type") == "shell":
        step["timeout_seconds"] = 300
    return raw


# ---------------------------------------------------------------------------
# Security fixes (S)
# ---------------------------------------------------------------------------


@autofix("S003")
def fix_s003_add_input_type(raw: dict[str, Any], finding: LintFinding) -> dict[str, Any]:
    """Add type: string to a required input that has no type constraint."""
    if not finding.message:
        return raw
    # Extract input name from message: "Required input 'foo' has no type constraint."
    import re

    match = re.search(r"Required input '([^']+)'", finding.message)
    if not match:
        return raw
    input_name = match.group(1)
    inputs = raw.get("inputs", {})
    if isinstance(inputs, dict) and input_name in inputs:
        config = inputs[input_name]
        if isinstance(config, dict) and "type" not in config:
            config["type"] = "string"
    return raw


# ---------------------------------------------------------------------------
# Efficiency fixes (E)
# ---------------------------------------------------------------------------


@autofix("E004")
def fix_e004_add_max_concurrent(raw: dict[str, Any], finding: LintFinding) -> dict[str, Any]:
    """Add max_concurrent: 4 to a fan_out step with no limit."""
    step = _find_step_by_id(raw, finding.step_id or "")
    if step and step.get("type") == "fan_out":
        step["max_concurrent"] = 4
    return raw


# ---------------------------------------------------------------------------
# Diff generation
# ---------------------------------------------------------------------------


def generate_patch(original: dict[str, Any], fixed: dict[str, Any]) -> str:
    """Generate a unified-diff-style patch between two YAML dicts.

    This is a best-effort textual diff, not a true unified diff.
    """
    import difflib

    import yaml

    orig_lines = yaml.dump(original, default_flow_style=False, sort_keys=False).splitlines(
        keepends=True
    )
    fixed_lines = yaml.dump(fixed, default_flow_style=False, sort_keys=False).splitlines(
        keepends=True
    )

    diff = difflib.unified_diff(
        orig_lines,
        fixed_lines,
        fromfile="a/workflow.yaml",
        tofile="b/workflow.yaml",
    )
    return "".join(diff)
