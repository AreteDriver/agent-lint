#!/usr/bin/env python3
"""Validate provider pricing YAML and update the last_updated timestamp.

NOTE: OpenAI and Anthropic do NOT expose pricing via their public APIs.
This script validates the existing providers.yaml file and bumps the
last_updated timestamp when changes are detected. Manual price updates
are required when providers announce new rates.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRICING_FILE = PROJECT_ROOT / "src" / "agent_lint" / "data" / "providers.yaml"


def validate_providers_yaml(path: Path) -> bool:
    """Validate that providers.yaml is well-formed."""
    if not path.exists():
        print(f"ERROR: Pricing file not found: {path}")
        return False

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"ERROR: Invalid YAML in {path}: {exc}")
        return False

    if not isinstance(raw, dict):
        print("ERROR: Expected top-level mapping in providers.yaml")
        return False

    meta = raw.get("meta")
    if not isinstance(meta, dict):
        print("WARNING: Missing 'meta' section in providers.yaml")
        print("  Add: meta:\n        last_updated: 'YYYY-MM-DD'")

    providers = raw.get("providers")
    if not isinstance(providers, dict) or not providers:
        print("ERROR: Missing or empty 'providers' section")
        return False

    for provider_name, provider_data in providers.items():
        if not isinstance(provider_data, dict):
            print(f"ERROR: Provider '{provider_name}' is not a mapping")
            return False

        models = provider_data.get("models")
        if not isinstance(models, dict):
            print(f"ERROR: Provider '{provider_name}' missing 'models' mapping")
            return False

        for model_name, model_data in models.items():
            if not isinstance(model_data, dict):
                print(f"ERROR: Model '{provider_name}/{model_name}' is not a mapping")
                return False
            for key in ("input", "output"):
                if key not in model_data:
                    print(f"WARNING: Model '{provider_name}/{model_name}' missing '{key}' price")

    print(f"OK: {len(providers)} provider(s) validated")
    return True


def bump_last_updated(path: Path) -> None:
    """Bump the meta.last_updated field to today."""
    from datetime import UTC, datetime

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    content = path.read_text(encoding="utf-8")

    # Simple regex replacement to preserve formatting
    import re

    new_content = re.sub(
        r'(last_updated:\s*")[^"]+("\s*)',
        rf'\g<1>{today}\g<2>',
        content,
        count=1,
    )
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        print(f"Updated last_updated to {today}")
    else:
        print("last_updated already current")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate provider pricing YAML")
    parser.add_argument(
        "--bump",
        action="store_true",
        help="Bump the last_updated timestamp (use when prices actually change)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("agent-lint pricing validator")
    print("=" * 60)
    print()
    print("NOTE: OpenAI and Anthropic do not expose pricing via API.")
    print("This script validates the existing providers.yaml file.")
    print("Manual updates are required when prices change.")
    print()

    ok = validate_providers_yaml(PRICING_FILE)
    if not ok:
        sys.exit(1)

    if args.bump:
        bump_last_updated(PRICING_FILE)
    else:
        print("Run with --bump to update the last_updated timestamp.")

    sys.exit(0)
