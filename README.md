# agent-lint

**CLI tool for cost estimation and anti-pattern detection in agent workflow YAML configs.**
Catch expensive, fragile, or ungoverned agent workflows before they hit production.

[![PyPI](https://img.shields.io/pypi/v/agentlinter.svg)](https://pypi.org/project/agentlinter/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: BSL-1.1](https://img.shields.io/badge/License-BSL--1.1-blue.svg)](LICENSE)
[![CI](https://github.com/AreteDriver/agent-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/AreteDriver/agent-lint/actions)

---

## The Problem

Agent workflows fail in predictable ways: unbounded loops, no retry limits, missing cost guards, parallel branches with no coordination. Most teams find these problems in production — after a $400 API bill or a stuck workflow that ran for six hours.

`agent-lint` finds them at config time.

---

## Install

```bash
pip install agentlinter
```

---

## Usage

```bash
# Lint a single workflow config
agent-lint lint workflow.yaml

# Lint all workflows in a directory, fail CI if score < 80
agent-lint lint workflows/ --fail-under 80

# Estimate token/cost exposure for a workflow
agent-lint estimate workflow.yaml --provider anthropic

# Generate a full audit report
agent-lint lint workflows/ --format markdown

# Suggest autofixes as a diff patch
agent-lint lint workflow.yaml --fix
```

---

## What It Detects

**Anti-patterns:**
- Unbounded retry loops (no max_retries or timeout)
- Missing cost guards on high-token operations
- Parallel agent branches with no merge strategy
- Hard-coded API keys in config (security)
- Missing checkpointing on long-running workflows
- Agents with no defined output schema

**Cost estimation:**
- Token budget projection per workflow step
- Worst-case / expected-case / best-case cost ranges
- Model-aware pricing (Claude, GPT-4, Gemini)

**Scoring:**
- 0-100 score per workflow
- Error (-15 pts), warning (-5 pts), info (-1 pt)
- CI integration: `--fail-under` threshold

---

## CI Integration

```yaml
# .github/workflows/agent-lint.yml
- name: Lint agent workflows
  run: agent-lint lint workflows/ --fail-under 80
```

Treat your agent configs like production code. Gate them the same way.

---

## Licensing & Tiers

`agent-lint` is available in two tiers:

**Free** — Always free, no license key required:
- `lint` — anti-pattern detection
- `estimate` — token/cost estimation
- `status` — show version and tier info

**Pro** — Unlock additional features with a license key:
- `compare` — compare costs across providers side-by-side
- Markdown export for audit reports
- Custom pricing tables
- Custom rule packs
- Historical tracking and trend analysis

Activate Pro with an environment variable:
```bash
export AGENT_LINT_LICENSE=ALNT-XXXX-XXXX-XXXX
```

---

## Why Static Analysis

No LLM dependency. No API calls. No variance between runs.
Agent configs are deterministic artifacts — they should be audited deterministically.

---

## Status

- [x] Anti-pattern detection (17 rules)
- [x] Cost estimation (Claude, GPT-4)
- [x] CI integration with threshold gating
- [x] Markdown audit reports
- [x] SARIF output for GitHub Advanced Security
- [x] GitHub PR annotation format
- [x] Autofix diff generation (`--fix`)
- [x] Docker images (multi-arch)
- [ ] Gemini pricing model
- [ ] VS Code extension

---

## Related Projects

- **[mcp-manager](https://github.com/AreteDriver/mcp-manager)** — MCP server manager with built-in audit (`pip install arete-mcp`)
- **[ai-spend](https://github.com/AreteDriver/ai-spend)** — Cost observability for the workflows agent-lint guards (`pip install ai-spend`)
- **[animus](https://github.com/AreteDriver/animus)** — The AI operating environment with built-in quality gates and eval pipeline

*Part of the [AreteDriver](https://github.com/AreteDriver) AI tooling ecosystem.*
