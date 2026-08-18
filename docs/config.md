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

## Bundled Pricing Data

Pricing is stored in `src/agent_lint/data/providers.yaml` in USD per 1,000
tokens. The OpenAI default is `gpt-5.6`, an alias for `gpt-5.6-sol`.

| Model | Input / 1M | Output / 1M | Context |
|-------|------------|-------------|---------|
| GPT-5.6 Sol | $5.00 | $30.00 | 1,050,000 |
| GPT-5.6 Terra | $2.00 | $12.00 | 1,050,000 |
| GPT-5.6 Luna | $0.20 | $1.20 | 1,050,000 |

These estimates use standard, short-context API rates. Cached input, cache
writes, Batch/Flex/Fast processing, regional uplifts, and the surcharge for
prompts above 272K input tokens are not modeled. Verify rates against the
[official OpenAI pricing reference](https://developers.openai.com/api/docs/pricing)
before using estimates for financial controls.
