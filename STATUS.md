# Project Status

| Attribute | Value |
|-----------|-------|
| Status | **OPERATIONAL** |
| Last verified | 2026-07-16 |
| Installable? | Yes — `pip install agentlinter` |
| Tested? | CI green; see badge below |
| Documented? | README + inline help; no hosted docs |
| CI | [![CI](https://github.com/AreteDriver/agent-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/AreteDriver/agent-lint/actions/workflows/ci.yml) |

## What Works

- **PyPI Package:** Published as `agentlinter`
- **Linting:** Detects unbounded loops, missing cost guards, parallel branches without coordination, fragile retry patterns
- **Cost Estimation:** Token/cost exposure estimates per workflow, per provider
- **CI Integration:** `--fail-under` flag for gated deployments
- **Output Formats:** Terminal tables, JSON, Markdown audit reports

## What Doesn't Work Yet

- Dashboard for historical lint trends (not planned)
- Integration with Animus Forge as a native quality gate (roadmap)
- No hosted documentation

## Install

```bash
pip install agentlinter
agent-lint lint workflow.yaml
```

## Relationship to Animus

Used as a pre-flight quality gate in the Animus Layered Build Workflow (LCK). Evaluated for integration into Forge's `check` stage.
