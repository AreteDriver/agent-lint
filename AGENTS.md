# Repository Guide

## Purpose

`agent-lint` statically analyzes agent workflow YAML for cost exposure,
reliability risks, security issues, and missing governance controls.

## Architecture

- `src/agent_lint/parsers/` normalizes supported workflow dialects.
- `src/agent_lint/rules/` contains registered lint rules by category.
- `estimator.py` combines normalized steps with bundled provider pricing.
- `src/agent_lint/data/providers.yaml` is the canonical pricing database.
- CLI commands belong in `src/agent_lint/cli/`; shared behavior stays outside command modules.

## Pricing Invariants

- Store token prices in USD per 1,000 tokens and context windows in tokens.
- Verify changes against official provider pricing pages and update `meta.last_updated`.
- Add exact rate, alias, context-window, and estimator regression tests.
- Document any unmodeled cached, batch, long-context, or service-tier pricing.

## Safety

- Never print or commit API keys, license keys, or credential values.
- Keep estimates deterministic: pricing lookup must not make runtime network calls.
- Do not silently fall back when a requested provider or model is unknown.

## Verification

```bash
ruff check src tests
ruff format --check src tests
mypy src
pytest
python -m build
mkdocs build --strict
```

Python 3.11+ and strict mypy are required. Coverage must remain at least 90%.
