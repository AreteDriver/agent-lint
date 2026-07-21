"""Backward-compatible CLI entry-point shim.

Subcommands have been moved to `agent_lint.cli.*` modules.
This file re-exports ``app`` so the console-script entry point
``agent-lint = "agent_lint.cli:app"`` continues to work.
"""

from __future__ import annotations

from agent_lint.cli import app  # noqa: F401
