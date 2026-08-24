# Project Status

| Attribute | Value |
|-----------|-------|
| Status | **OPERATIONAL** |
| Last verified | 2026-08-18 |
| Installable? | Yes — `pip install agentlinter` |
| Tested? | CI green; see badge below |
| Documented? | README + MkDocs site + inline help |
| Hosted docs | Build is verified; GitHub Pages must be enabled before public deployment |
| Docker image | `ghcr.io/aretedriver/agent-lint:latest` |
| CI | [![CI](https://github.com/AreteDriver/agent-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/AreteDriver/agent-lint/actions/workflows/ci.yml) |

## What Works

- **PyPI Package:** Published as `agentlinter`
- **Linting:** Detects unbounded loops, missing cost guards, parallel branches without coordination, fragile retry patterns
- **Cost Estimation:** Token/cost exposure estimates for Anthropic, OpenAI GPT-5.6
  and legacy models, plus self-hosted Ollama models
- **CI Integration:** `--fail-under` flag for gated deployments
- **Output Formats:** Terminal tables, JSON, Markdown audit reports, SARIF, GitHub PR annotations
- **Autofix:** `--fix` generates diff patches for fixable findings
- **Docs:** MkDocs site builds in GitHub Actions; public Pages deployment awaits repository setup
- **Docker:** Multi-arch images (`linux/amd64`, `linux/arm64`) on GHCR

## What Doesn't Work Yet

- Dashboard for historical lint trends (not planned)
- Integration with Animus Forge as a native quality gate (roadmap)
- VS Code extension

## Install

```bash
pip install agentlinter
agent-lint lint workflow.yaml
```

## Relationship to Animus

Used as a pre-flight quality gate in the Animus Layered Build Workflow (LCK). Evaluated for integration into Forge's `check` stage.
