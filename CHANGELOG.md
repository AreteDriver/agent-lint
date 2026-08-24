# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-08-24

### Added

- Root-level GitHub Action metadata for direct `AreteDriver/agent-lint@v0.4.0` usage and
  GitHub Marketplace eligibility.
- End-to-end Action contract tests for passing and fail-closed quality gates.
- Recursive directory linting with stable file ordering and valid multi-report JSON/SARIF output.

### Fixed

- Registered built-in lint rules during normal package import; previously a clean CLI process
  could execute with an empty rule registry and incorrectly report 100/100.
- Kept JSON and SARIF stdout valid when a score threshold fails by writing the diagnostic to stderr.
- Wired the documented `github` and `sarif` CLI formats into the `lint` command.
- Installed the Action from its checked-out release source so Action behavior matches its tag.
- Passed Action inputs through environment variables to avoid shell expression injection.

## [0.3.5] - 2026-08-18

### Added

- **Current OpenAI GPT-5.6 pricing** for `gpt-5.6` (Sol alias), `gpt-5.6-sol`,
  `gpt-5.6-terra`, and `gpt-5.6-luna`, using standard short-context API rates
  verified against OpenAI's official pricing reference on 2026-08-18.

### Changed

- The default OpenAI estimate now uses the current `gpt-5.6` alias instead of legacy `gpt-4o`.

### Fixed

- Runtime version reporting now reads installed package metadata, eliminating drift between `pyproject.toml` and `agent_lint.__version__`.
- Packaging now uses current SPDX license metadata without setuptools deprecation warnings.

## [0.3.4] - 2026-07-24

### Fixed

- **Corrected license metadata misdeclaration.** `pyproject.toml` and documentation falsely declared MIT since v0.1.1 despite the LICENSE file always being Business Source License 1.1. This created a real legal liability: downstream consumers and automated license scanners received incorrect terms. The invalid `License :: OSI Approved :: MIT License` Trove classifier has been removed. BSL-1.1 is not OSI-approved; no replacement classifier exists at this time. Corrected in PR #42; released as v0.3.4 to fix the PyPI public artifact record (#42).
- Corrected historical CHANGELOG entry for v0.3.0 which incorrectly claimed the license was "aligned to MIT" — it was in fact misaligned, creating the defect fixed above.

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
- ~~License metadata in `pyproject.toml` aligned to MIT (#11)~~  
  **Correction (2026-07-24):** This entry was incorrect. The metadata was misaligned — `pyproject.toml` falsely declared MIT while the LICENSE file was BSL-1.1. The defect was introduced in v0.1.1 and corrected in v0.3.4 (see #42).
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
