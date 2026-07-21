# API Reference — Models

## `ParsedWorkflow`

Represents a parsed agent workflow YAML.

```python
class ParsedWorkflow(BaseModel):
    name: str
    version: str
    token_budget: int | None
    steps: list[ParsedStep]
```

## `ParsedStep`

Represents a single step in a workflow.

```python
class ParsedStep(BaseModel):
    id: str
    step_type: StepType
    model: str | None
    estimated_tokens: int | None
    on_failure: str | None
    raw_params: dict[str, Any]
```

## `LintFinding`

Represents a single rule violation.

```python
class LintFinding(BaseModel):
    rule_id: str
    category: RuleCategory
    severity: Severity
    message: str
    step_id: str | None
    suggestion: str | None
```

## `LintReport`

Aggregated result of running all rules.

```python
class LintReport(BaseModel):
    workflow_name: str
    score: int
    findings: list[LintFinding]
    error_count: int
    warning_count: int
    info_count: int
```
