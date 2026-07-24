# agent-lint

**CLI tool for cost estimation and anti-pattern detection in agent workflow YAML configs.**

Catch expensive, fragile, or ungoverned agent workflows before they hit production.

## Why agent-lint?

Agent workflows fail in predictable ways:

- Unbounded retry loops with no `max_retries` or `timeout`
- Missing cost guards on high-token operations
- Parallel agent branches with no merge strategy
- Hard-coded API keys in config files
- Missing checkpointing on long-running workflows

Most teams find these problems in production — after a `$400` API bill or a stuck workflow that ran for six hours. `agent-lint` finds them at config time.

## Quick Start

```bash
pip install agentlinter

# Lint a single workflow
agent-lint lint workflow.yaml

# Estimate cost
agent-lint estimate workflow.yaml --provider anthropic

# Lint all workflows in a directory, fail CI if score < 80
agent-lint lint workflows/ --fail-under 80
```

## Features

| Feature | Status |
|---------|--------|
| Anti-pattern detection (17 rules) | ✅ |
| Cost estimation (Claude, GPT-4, Gemini) | ✅ |
| CI integration with threshold gating | ✅ |
| Markdown audit reports | ✅ |
| SARIF output for GitHub Advanced Security | ✅ |
| Project config file support | ✅ |
| VS Code extension | 🚧 Roadmap |
| Auto-fix suggestions | 🚧 Roadmap |

## License

Business Source License 1.1 — see [LICENSE](https://github.com/AreteDriver/agent-lint/blob/main/LICENSE).
