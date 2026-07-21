# API Reference — Rules

## `@lint_rule(rule_id, category, severity, description)`

Decorator to register a lint rule function.

```python
from agent_lint.models import LintFinding, ParsedWorkflow, RuleCategory, Severity
from agent_lint.rules import lint_rule

@lint_rule(
    rule_id="X001",
    category=RuleCategory.BUDGET,
    severity=Severity.WARNING,
    description="My custom rule",
)
def check_custom(workflow: ParsedWorkflow) -> list[LintFinding]:
    findings: list[LintFinding] = []
    # ... check logic ...
    return findings
```

## Rule Function Signature

All rule functions must accept a `ParsedWorkflow` and return `list[LintFinding]`.

## Built-in Rule Modules

| Module | Rule IDs | Focus |
|--------|----------|-------|
| `rules.budget` | B001–B004 | Cost guards |
| `rules.resilience` | R001–R005 | Error handling |
| `rules.efficiency` | E001–E004 | Performance |
| `rules.security` | S001–S004 | Security |
