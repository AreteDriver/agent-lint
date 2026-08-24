# CI Integration

## GitHub Actions

### Option 1: Composite Action (Recommended)

Use the official composite action published in this repository:

```yaml
name: Agent Lint
on:
  pull_request:
    paths:
      - "workflows/**"
      - ".agent-lint.toml"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AreteDriver/agent-lint@v0.4.0
        with:
          path: workflows/
          fail-under: 80
          format: github
```

### Option 2: Manual Setup

```yaml
- name: Install agent-lint
  run: pip install agentlinter

- name: Lint workflows
  run: agent-lint lint workflows/ --fail-under 80
```

### Option 3: SARIF Upload to GitHub Advanced Security

```yaml
- name: Generate SARIF
  run: agent-lint lint workflows/ --format sarif > agent-lint.sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: agent-lint.sarif
```

## Pre-commit Hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/AreteDriver/agent-lint
    rev: v0.4.0
    hooks:
      - id: agent-lint
        args: [--fail-under, "80"]
```

Install locally:

```bash
pre-commit install
```
