# Configuration

## Config File Discovery

`agent-lint` loads config from the first source found, in order:

1. CLI flags (highest priority)
2. Environment variables (`AGENT_LINT_*`)
3. `.agent-lint.toml` in the current directory
4. `pyproject.toml` under `[tool.agent-lint]`
5. Built-in defaults

## Example `.agent-lint.toml`

```toml
fail_under = 80
category = "budget"
severity = "warning"
```

## Example `pyproject.toml` Section

```toml
[tool.agent-lint]
fail_under = 80
category = "budget"
severity = "warning"
```

## Environment Variables

| Variable | Maps To |
|----------|---------|
| `AGENT_LINT_FAIL_UNDER` | `fail_under` |
| `AGENT_LINT_CATEGORY` | `category` |
| `AGENT_LINT_SEVERITY` | `severity` |

## Full Option Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fail_under` | int | `None` | Minimum lint score to pass CI |
| `category` | string | `None` | Filter to one rule category |
| `severity` | string | `None` | Filter to one severity level |
