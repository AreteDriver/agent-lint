#!/usr/bin/env python3
"""Generate CHANGELOG.md from conventional commits.

Usage:
    OUTPUT=CHANGELOG.md python scripts/generate-changelog.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = {
    "feat": "### Added",
    "fix": "### Fixed",
    "docs": "### Documentation",
    "perf": "### Performance",
    "refactor": "### Refactored",
    "test": "### Testing",
    "ci": "### CI/CD",
    "chore": "### Chore",
    "security": "### Security",
}


def get_tags() -> list[str]:
    """Return list of version tags sorted oldest first."""
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    tags = result.stdout.strip().splitlines()
    # Sort by semver
    return sorted(tags, key=lambda t: [int(x) for x in t[1:].split(".")])


def get_commits_between(from_ref: str, to_ref: str) -> list[dict]:
    """Get conventional commits between two refs."""
    range_spec = f"{from_ref}..{to_ref}" if from_ref else to_ref
    result = subprocess.run(
        ["git", "log", range_spec, "--format=%H|%s|%b"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    commits = []
    for raw in result.stdout.strip().split("\n\n"):
        if "|" not in raw:
            continue
        parts = raw.split("|", 2)
        if len(parts) < 2:
            continue
        sha, subject = parts[0], parts[1]
        match = re.match(r"^(\w+)(?:\([^)]+\))?:\s*(.+)", subject)
        if match:
            commits.append({
                "sha": sha[:7],
                "type": match.group(1),
                "message": match.group(2),
            })
    return commits


def get_tag_date(tag: str) -> str:
    """Return ISO date for a tag."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ci", tag],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    date_str = result.stdout.strip().split()[0]
    return date_str


def generate_changelog() -> str:
    """Build CHANGELOG.md content."""
    tags = get_tags()
    if not tags:
        return "# Changelog\n\nNo releases yet.\n"

    lines = ["# Changelog", ""]

    # Process newest to oldest
    for i in range(len(tags) - 1, -1, -1):
        tag = tags[i]
        prev_tag = tags[i - 1] if i > 0 else ""
        date = get_tag_date(tag)
        lines.append(f"## [{tag[1:]}] - {date}")
        lines.append("")

        commits = get_commits_between(prev_tag, tag)
        if not commits:
            lines.append("_No notable changes._")
            lines.append("")
            continue

        # Group by type
        grouped: dict[str, list[str]] = {}
        for commit in commits:
            cat = CATEGORIES.get(commit["type"], "### Other")
            entry = f"- {commit['message']} ({commit['sha']})"
            grouped.setdefault(cat, []).append(entry)

        for heading in CATEGORIES.values():
            if heading in grouped:
                lines.append(heading)
                lines.append("")
                for entry in grouped[heading]:
                    lines.append(entry)
                lines.append("")

        if "### Other" in grouped:
            lines.append("### Other")
            lines.append("")
            for entry in grouped["### Other"]:
                lines.append(entry)
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    output = os.environ.get("OUTPUT", "CHANGELOG.md")
    content = generate_changelog()
    path = PROJECT_ROOT / output
    path.write_text(content)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
