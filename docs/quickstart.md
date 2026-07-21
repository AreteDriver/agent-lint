# Quick Start

## Lint a Single Workflow

```bash
agent-lint lint workflow.yaml
```

Output is a table by default. Use `--format json` or `--format markdown` for machine-readable output.

## Estimate Cost

```bash
agent-lint estimate workflow.yaml --provider anthropic
```

Supported providers: `openai`, `anthropic`, `google`, `ollama`.

## Compare Two Workflows

```bash
agent-lint compare workflow-a.yaml workflow-b.yaml
```

## CI Gate with Threshold

```bash
agent-lint lint workflows/ --fail-under 80
```

Exits with code 1 if the lint score is below 80.

## Get Auto-fix Suggestions

```bash
agent-lint lint workflow.yaml --fix
```

Prints a unified diff patch for fixable findings.
