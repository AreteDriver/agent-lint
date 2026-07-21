"""Status command: show license status and available features."""

from __future__ import annotations

from agent_lint import __version__
from agent_lint.cli import app, console
from agent_lint.licensing import TIER_DEFINITIONS, get_license_info
from agent_lint.telemetry import track_command


@app.command()
def status() -> None:
    """Show license status and available features."""
    track_command("status")

    info = get_license_info()
    tier_config = TIER_DEFINITIONS[info.tier]

    console.print(f"\n[bold]agent-lint {__version__}[/bold]")
    console.print(f"[bold]Tier:[/bold] {tier_config.name} ({tier_config.price_label})")

    if info.license_key:
        masked = info.license_key[:9] + "****-****"
        console.print(f"[bold]Key:[/bold] {masked}")
        valid_str = "[green]valid[/green]" if info.valid else "[red]invalid[/red]"
        console.print(f"[bold]Valid:[/bold] {valid_str}")

    console.print(f"\n[bold]Features:[/bold] {', '.join(tier_config.features)}")
    console.print()
