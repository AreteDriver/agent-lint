#!/usr/bin/env python3
"""Fetch real-world agent workflow YAMLs from GitHub and run linter.

Usage:
    python scripts/fetch-corpus.py

Requires GITHUB_TOKEN env var for authenticated Search API (higher rate limit).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = PROJECT_ROOT / ".corpus"

QUERIES = [
    "language:yaml agent workflow steps",
    "language:yaml langchain workflow",
    "language:yaml crewai workflow",
]


def fetch_files(query: str, limit: int = 20) -> list[dict]:
    """Search GitHub for YAML files matching query."""
    import requests

    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = "https://api.github.com/search/code"
    params = {"q": query, "per_page": limit}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        print(f"  '{query}' \u2192 {len(items)} files")
        return items
    except Exception as exc:
        print(f"Search failed for '{query}': {exc}")
        return []


def download_raw(url: str) -> str | None:
    """Download raw file content from GitHub."""
    import requests

    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.raw+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def run_lint_on_text(text: str) -> dict:
    """Lint a workflow string and return summary."""
    from agent_lint.linter import run_lint
    from agent_lint.parsers import parse_workflow

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as fh:
        fh.write(text)
        path = fh.name

    try:
        wf = parse_workflow(Path(path))
        report = run_lint(wf)
        return {
            "findings": len(report.findings),
            "score": report.score,
            "rules": [f.rule_id for f in report.findings],
        }
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        os.unlink(path)


def main() -> int:
    CORPUS_DIR.mkdir(exist_ok=True)
    total_files = 0
    total_findings = 0
    errors = 0

    for query in QUERIES:
        items = fetch_files(query, limit=10)
        for item in items:
            raw_url = item["html_url"].replace(
                "github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            text = download_raw(raw_url)
            if text is None:
                continue
            total_files += 1
            result = run_lint_on_text(text)
            if "error" in result:
                errors += 1
                continue
            total_findings += result["findings"]

    summary = {
        "total_files": total_files,
        "parse_errors": errors,
        "total_findings": total_findings,
        "avg_findings_per_file": round(total_findings / total_files, 2) if total_files else 0,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
