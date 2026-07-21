"""CLI entry point for agent-lint.

Subcommands are split into modules under cli/ for maintainability.
"""

from __future__ import annotations

import typer
from rich.console import Console

from agent_lint import __version__

app = typer.Typer(
    name="agent-lint",
    help="Analyze agent workflow configs for cost estimation and anti-patterns.",
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Analyze agent workflow configs for cost estimation and anti-patterns."""
    if version:
        console.print(f"agent-lint {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


# Import subcommands so they self-register on the app.
# Order does not matter; Typer registers them by name.
from agent_lint.cli import compare, estimate, lint, stats, status  # noqa: E402, F401
