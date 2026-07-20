# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-20

### Added

#### Output Formats
- **SARIF v2.1.0** output format (`--format sarif`) for GitHub Advanced Security integration (#16)
- **GitHub PR annotations** output format (`--format github`) that emits `::error`, `::warning`, and `::notice` workflow commands (#18)

#### Configuration
- **Project-level config file support** via `.agent-lint.toml` or `pyproject.toml [tool.agent-lint]` with cascading precedence: CLI flags → env vars → config file → defaults (#17)

#### Autofix
- **Autofix engine** with `--fix` flag on `lint` command. Generates unified diff patches for fixable findings including B001, R003, R004, S003, and E004 (#21)

#### CI / CD
- **Composite GitHub Action** at `.github/actions/agent-lint/action.yml` for reusable workflow integration (#15)
- **PyPI publish workflow** triggered on `v*` tags using OIDC trusted publishing (#24)
- **Docker image** with multi-stage build and `docker-bake.hcl` for `linux/amd64` + `linux/arm64` (#24)
- **Automated changelog generation** on releases via git-cliff (#25)

#### Quality Assurance
- **Accuracy benchmark scaffold** with annotated workflow fixtures for measuring precision / recall / F1 per rule (#22)
- **Performance benchmark** (`scripts/benchmark-performance.py`) validating lint latency and memory thresholds across 10–1000 step workflows (#25)
- **Real-world corpus test** (`scripts/fetch-corpus.py`) for false-positive rate measurement against public agent workflow YAMLs (#25)
- **Mypy typecheck** job in CI with ratchet strategy (#12)
- **Pre-commit hooks** configuration for downstream consumers (#13)

#### Documentation
- **MkDocs site** with Material theme, API reference, and CI deploy to GitHub Pages (#20)
- **CONTRIBUTING.md**, issue templates, and pull request template (#19)

### Fixed
- License metadata in `pyproject.toml` aligned to MIT (#11)
- Asymmetric rule imports in `linter.py` replaced with uniform top-level imports (#14)
- Rich `console.print()` soft-wrap corruption of SARIF JSON replaced with plain `print()` (#16)
- Config file kebab-case normalization ordering bug with env overrides (#17)

## [0.2.1] - 2026-07-07

### Added
- Pro-gated coverage tests and tiered coverage gates (90% for open-source, 95% for Pro)
- Free vs Pro pricing documentation with Stripe payment links

### Security
- Scrubbed local paths from repository
- License switched to BSL-1.1 for Pro feature differentiation

## [0.2.0] - 2026-06-15

### Added
- License server validation and Stripe integration scaffolding
- Coverage gate CI job (85%)
- Release workflow and gitleaks secret scanning
- Rename package to `agentlinter` for PyPI availability

## [0.1.1] - 2026-06-01

### Added
- Initial release of `agent-lint` CLI tool
- Cost estimation and anti-pattern detection for agent workflow YAML configs
