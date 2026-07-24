# Contributing

Thank you for your interest in `agent-lint`! This is a small but opinionated project. To keep quality high, please follow the guidelines below.

## Development Setup

```bash
git clone https://github.com/AreteDriver/agent-lint.git
cd agent-lint
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

Coverage gate is 90%. PRs that drop coverage below this will fail CI.

## Linting and Formatting

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Type Checking

```bash
mypy src/
```

## Adding a New Rule

1. Add the rule function in the appropriate `src/agent_lint/rules/*.py` file.
2. Decorate it with `@lint_rule(rule_id=..., category=..., severity=..., description=...)`.
3. Add tests in `tests/test_rules.py`.
4. Update the relevant docs page under `docs/rules/`.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature or rule
- `fix:` — bug fix
- `docs:` — documentation changes
- `test:` — test-only changes
- `ci:` — CI/CD changes
- `chore:` — maintenance

## License

By contributing, you agree that your contributions will be licensed under the Business Source License 1.1.
