# API Reference — Formatters

## `format_lint_table(report: LintReport, console: Console) -> None`

Render a rich text table to the console.

## `format_lint_json(report: LintReport, console: Console) -> None`

Render JSON output to the console.

## `format_lint_markdown(report: LintReport, console: Console) -> None`

Render a Markdown summary to the console.

## `format_sarif(report: LintReport) -> str`

Generate SARIF v2.1.0 JSON string for GitHub Advanced Security upload.

```python
from agent_lint.sarif_formatter import format_sarif

sarif_json = format_sarif(report)
```

## `format_github_annotations(report: LintReport) -> str`

Generate GitHub Actions workflow command annotations.

```python
from agent_lint.github_formatter import format_github_annotations

annotations = format_github_annotations(report)
print(annotations)
```
