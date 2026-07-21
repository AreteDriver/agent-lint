"""Workflow format detection and parsing dispatch.

Parser modules self-register via the @parser_for decorator. To add a new
workflow format, create a parser module and decorate its entry function
with @parser_for(WorkflowFormat.YOUR_FORMAT).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from agent_lint.exceptions import ParseError
from agent_lint.models import ParsedWorkflow, WorkflowFormat

logger = logging.getLogger(__name__)

# Gorgon step types that signal the format.
_GORGON_STEP_TYPES = {
    "claude_code",
    "openai",
    "shell",
    "parallel",
    "checkpoint",
    "fan_out",
    "fan_in",
    "map_reduce",
    "branch",
    "loop",
    "mcp_tool",
}

_PARSER_REGISTRY: dict[WorkflowFormat, Callable[..., ParsedWorkflow]] = {}


def parser_for(
    fmt: WorkflowFormat,
) -> Callable[[Callable[..., ParsedWorkflow]], Callable[..., ParsedWorkflow]]:
    """Decorator to register a parser function for a workflow format."""

    def decorator(func: Callable[..., ParsedWorkflow]) -> Callable[..., ParsedWorkflow]:
        _PARSER_REGISTRY[fmt] = func
        return func

    return decorator


def detect_format(raw: dict[str, Any]) -> WorkflowFormat:
    """Detect workflow format from YAML structure."""
    # CrewAI: has both 'agents' and 'tasks' top-level keys.
    if "agents" in raw and "tasks" in raw:
        return WorkflowFormat.CREWAI

    # LangChain/LangGraph: has 'nodes' or 'edges', or langgraph in metadata.
    if "nodes" in raw or "edges" in raw:
        return WorkflowFormat.LANGCHAIN
    meta = raw.get("metadata", {})
    if isinstance(meta, dict) and "langgraph" in str(meta).lower():
        return WorkflowFormat.LANGCHAIN

    # Gorgon: has 'steps' list where items have 'type' in known set.
    steps = raw.get("steps", [])
    if isinstance(steps, list) and steps:
        for step in steps:
            if isinstance(step, dict) and step.get("type") in _GORGON_STEP_TYPES:
                return WorkflowFormat.GORGON

    return WorkflowFormat.GENERIC


def load_yaml(path: Path) -> dict[str, Any]:
    """Load and validate a YAML file."""
    if not path.is_file():
        raise ParseError(f"File not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ParseError(f"Failed to read {path}: {exc}") from exc

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ParseError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ParseError(f"Expected YAML mapping at top level in {path}")

    return raw


def parse_workflow(path: Path) -> ParsedWorkflow:
    """Load a workflow YAML and parse it into a normalized model."""
    raw = load_yaml(path)
    fmt = detect_format(raw)
    parser = _PARSER_REGISTRY.get(fmt)
    if parser is None:
        parser = _PARSER_REGISTRY[WorkflowFormat.GENERIC]
    return parser(raw, source_path=str(path))


# Eagerly import parser modules so their @parser_for decorators self-register.
from agent_lint.parsers import crewai as crewai  # noqa: E402, F401
from agent_lint.parsers import generic as generic  # noqa: E402, F401
from agent_lint.parsers import gorgon as gorgon  # noqa: E402, F401
from agent_lint.parsers import langchain as langchain  # noqa: E402, F401
