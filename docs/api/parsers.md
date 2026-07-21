# API Reference — Parsers

## `parse_workflow(path: Path) -> ParsedWorkflow`

Parse a workflow YAML file into a `ParsedWorkflow` object.

```python
from agent_lint.parsers import parse_workflow
from pathlib import Path

wf = parse_workflow(Path("workflow.yaml"))
```

## `load_yaml(path: Path) -> dict[str, Any]`

Load a YAML file as a raw Python dict. Useful for autofix operations that mutate the raw structure.

```python
from agent_lint.parsers import load_yaml
from pathlib import Path

raw = load_yaml(Path("workflow.yaml"))
```

## Supported Workflow Formats

| Parser | File Patterns |
|--------|--------------|
| Generic YAML | Any `.yaml` / `.yml` |
| LangChain | `langchain_*.yaml` |
| CrewAI | `crewai_*.yaml` |
| Gorgon | `gorgon_*.yaml` |

The parser auto-detects format based on file content and naming.
