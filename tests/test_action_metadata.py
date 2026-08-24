"""Contract tests for the distributable root GitHub Action."""

from __future__ import annotations

from pathlib import Path

import yaml


def _metadata() -> dict[str, object]:
    return yaml.safe_load(Path("action.yml").read_text(encoding="utf-8"))


def test_root_action_is_marketplace_discoverable() -> None:
    metadata = _metadata()

    assert metadata["name"] == "agent-lint"
    assert metadata["description"]
    assert metadata["branding"] == {"icon": "shield", "color": "blue"}


def test_root_action_installs_its_tagged_source() -> None:
    metadata = _metadata()
    steps = metadata["runs"]["steps"]  # type: ignore[index]
    install_step = next(
        step for step in steps if step["name"] == "Install agent-lint from this release"
    )

    assert '"$GITHUB_ACTION_PATH"' in install_step["run"]


def test_root_action_passes_inputs_via_environment() -> None:
    metadata = _metadata()
    steps = metadata["runs"]["steps"]  # type: ignore[index]
    lint_step = next(step for step in steps if step["name"] == "Lint agent workflows")

    assert "${{ inputs." not in lint_step["run"]
    assert set(lint_step["env"]) == {
        "AGENT_LINT_PATH",
        "AGENT_LINT_FAIL_UNDER",
        "AGENT_LINT_FORMAT",
        "AGENT_LINT_CATEGORY",
        "AGENT_LINT_SEVERITY",
    }
