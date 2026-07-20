# Contributing to agent-lint

Thank you for considering contributing to agent-lint. This document covers
the process for submitting bug reports, feature requests, and code changes.

## Quick Start

```bash
# 1. Fork and clone
git clone https://github.com/AreteDriver/agent-lint.git
cd agent-lint

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 4. Verify the setup
pytest tests/ -v
```

## Development Workflow

### Branch Naming

| Prefix | Use For |
|--------|---------|
| `fix/` | Bug fixes |
| `feat/` | New features |
| `docs/` | Documentation only |
| `ci/` | CI/CD changes |
| `refactor/` | Code restructuring |
| `test/` | Test additions/changes |
| `chore/` | Maintenance tasks |

Example: `fix/b003-negative-budget-calculation`

### Pre-Commit Checks

Before committing, run the quality gates:

```bash
# Linting and formatting
ruff check src/ tests/
ruff format --check src/ tests/

# Type checking (strict mode)
mypy src/

# Tests with coverage
pytest tests/ -v
```

If any of these fail, CI will block the merge. You can auto-fix most issues:

```bash
ruff check src/ tests/ --fix
ruff format src/ tests/
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short description>

<body explaining what and why>

Co-Authored-By: Name <email@example.com>
```

| Type | When to Use |
|------|-------------|
| `fix:` | Bug fix |
| `feat:` | New feature |
| `docs:` | Documentation |
| `test:` | Tests only |
| `ci:` | CI/CD config |
| `refactor:` | Code restructure |
| `chore:` | Maintenance |

Example:
```
feat: add CrewAI workflow parser

Adds support for CrewAI YAML configs with agents and tasks keys.
Maps CrewAI-specific fields (role, goal, backstory) to normalized
ParsedStep and ParsedWorkflow models.

Includes 6 parser tests and 2 integration fixtures.
```

## Adding a New Lint Rule

Rules live in `src/agent_lint/rules/` and are registered via the `@lint_rule`
decorator. Here's a minimal example:

```python
from agent_lint.models import LintFinding, ParsedWorkflow, RuleCategory, Severity
from agent_lint.rules import lint_rule

@lint_rule(
    rule_id="B005",
    category=RuleCategory.BUDGET,
    severity=Severity.WARNING,
    description="Workflow timeout exceeds 1 hour without justification",
)
def check_long_timeout(workflow: ParsedWorkflow) -> list[LintFinding]:
    if workflow.timeout_seconds and workflow.timeout_seconds > 3600:
        return [
            LintFinding(
                rule_id="B005",
                category=RuleCategory.BUDGET,
                severity=Severity.WARNING,
                message="Workflow timeout > 1h — may indicate unbounded execution.",
                suggestion="Add checkpoint steps or reduce timeout.",
            )
        ]
    return []
```

### Rule ID Convention

| Prefix | Category | Range |
|--------|----------|-------|
| B | Budget | B001–B099 |
| R | Resilience | R001–R099 |
| E | Efficiency | E001–E099 |
| S | Security | S001–S099 |

Every new rule needs:
1. A rule function in the appropriate `rules/*.py` file
2. At least one test in `tests/test_rules.py`
3. A mention in the README rules table (if applicable)

## Adding a New Workflow Parser

To support a new workflow format:

1. Add a `WorkflowFormat` enum value in `models.py`
2. Add detection logic in `parsers/__init__.py:detect_format()`
3. Implement `parsers/{format_name}.py:parse_{format_name}()`
4. Register it in `parsers/__init__.py:parse_workflow()`
5. Add integration tests with a real fixture in `tests/fixtures/workflows/`

## Code Style

- **Line length**: 100 characters (enforced by ruff)
- **Python version**: 3.11+ (enforced by ruff target-version)
- **Type hints**: Required on all public functions (enforced by mypy strict mode)
- **Docstrings**: Google-style for modules and functions

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage (must stay ≥ 90%)
pytest tests/ --cov=agent_lint --cov-report=term-missing

# Run specific test file
pytest tests/test_linter.py -v

# Run specific test
pytest tests/test_linter.py::TestRunLint::test_clean_workflow_scores_100 -v
```

## Security

Never commit:
- API keys or tokens
- License keys
- Internal server URLs
- Personal data

The repository has `.gitleaks.toml` configured and runs secret scanning in CI.

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for architecture questions
- Tag `@AreteDriver` for maintainer attention
