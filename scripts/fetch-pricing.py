#!/usr/bin/env python3
"""Fetch latest model pricing from OpenAI and Anthropic APIs.

Updates src/agent_lint/pricing.py in-place with current rates.
This is a best-effort script; manual review of the generated PR is required.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRICING_FILE = PROJECT_ROOT / "src" / "agent_lint" / "pricing.py"


def fetch_openai() -> dict[str, float]:
    """Return OpenAI model prices (USD per 1K tokens)."""
    import requests

    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"OpenAI fetch failed: {exc}")
        return {}

    data = resp.json()
    prices: dict[str, float] = {}
    for _model in data.get("data", []):
        # OpenAI does not expose pricing via API; placeholder for manual override
        pass
    return prices


def fetch_anthropic() -> dict[str, float]:
    """Return Anthropic model prices (USD per 1K tokens)."""
    import requests

    url = "https://api.anthropic.com/v1/models"
    headers = {"x-api-key": os.environ.get("ANTHROPIC_API_KEY", "")}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Anthropic fetch failed: {exc}")
        return {}

    data = resp.json()
    prices: dict[str, float] = {}
    for _model in data.get("data", []):
        # Anthropic API does not expose pricing either; placeholder
        pass
    return prices


def update_pricing_file(updates: dict[str, float]) -> bool:
    """Patch pricing.py with new values. Returns True if changed."""
    if not PRICING_FILE.exists():
        print(f"Pricing file not found: {PRICING_FILE}")
        return False

    content = PRICING_FILE.read_text()
    changed = False
    for model, price in updates.items():
        # Naive regex replacement; assumes MODEL_PRICES dict literal
        pattern = rf'("{re.escape(model)}":\s*)\d+\.?\d*'
        replacement = rf"\g<1>{price}"
        new_content, count = re.subn(pattern, replacement, content)
        if count:
            content = new_content
            changed = True
            print(f"Updated {model} = {price}")

    if changed:
        PRICING_FILE.write_text(content)
    return changed


if __name__ == "__main__":
    updates: dict[str, float] = {}
    updates.update(fetch_openai())
    updates.update(fetch_anthropic())

    if not updates:
        print("No pricing updates fetched.")
    else:
        changed = update_pricing_file(updates)
        print(f"Pricing file modified: {changed}")
