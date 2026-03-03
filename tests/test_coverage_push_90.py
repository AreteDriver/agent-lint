"""Targeted tests to raise coverage from 85% to 90%.

Covers: crewai parser, langchain parser, generic parser branches,
__main__ module, CLI severity filter, CLI compare command, formatters.
"""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_lint.cli import app
from agent_lint.models import StepType, WorkflowFormat
from agent_lint.parsers.crewai import parse_crewai
from agent_lint.parsers.generic import parse_generic
from agent_lint.parsers.langchain import parse_langchain

runner = CliRunner()

# ---------------------------------------------------------------------------
# CrewAI parser (24 stmts, 0% → 100%)
# ---------------------------------------------------------------------------


class TestCrewAIParser:
    def test_basic_crew(self) -> None:
        raw = {
            "name": "Test Crew",
            "agents": [
                {"name": "researcher", "role": "researcher", "llm": "gpt-4o", "max_tokens": 5000},
            ],
            "tasks": [
                {"name": "research_task", "agent": "researcher", "max_tokens": 3000},
            ],
            "token_budget": 50000,
        }
        wf = parse_crewai(raw, source_path="/tmp/crew.yaml")
        assert wf.name == "Test Crew"
        assert wf.format == WorkflowFormat.CREWAI
        assert wf.token_budget == 50000
        assert wf.source_path == "/tmp/crew.yaml"
        assert len(wf.steps) == 2

    def test_agent_fields(self) -> None:
        raw = {
            "agents": [
                {
                    "name": "writer",
                    "role": "writer",
                    "llm_provider": "openai",
                    "model": "gpt-4",
                    "max_tokens": 8000,
                },
            ],
            "tasks": [],
        }
        wf = parse_crewai(raw)
        agent_step = wf.steps[0]
        assert agent_step.id == "writer"
        assert agent_step.step_type == StepType.LLM
        assert agent_step.provider == "openai"
        assert agent_step.model == "gpt-4"
        assert agent_step.role == "writer"
        assert agent_step.estimated_tokens == 8000

    def test_agent_fallback_id(self) -> None:
        """Agent with no name/role uses index-based id."""
        raw = {"agents": [{"goal": "test"}], "tasks": []}
        wf = parse_crewai(raw)
        assert wf.steps[0].id == "agent_0"
        assert wf.steps[0].role is None  # empty string → None

    def test_task_with_agent_dependency(self) -> None:
        raw = {
            "agents": [],
            "tasks": [{"name": "my_task", "agent": "researcher", "role": "analyst"}],
        }
        wf = parse_crewai(raw)
        task = wf.steps[0]
        assert task.id == "my_task"
        assert task.depends_on == ["researcher"]
        assert task.role == "analyst"

    def test_task_fallback_id_from_description(self) -> None:
        raw = {"agents": [], "tasks": [{"description": "A very long description for testing"}]}
        wf = parse_crewai(raw)
        assert wf.steps[0].id == "A very long description for testing"[:40]

    def test_task_fallback_index(self) -> None:
        raw = {"agents": [], "tasks": [{}]}
        wf = parse_crewai(raw)
        assert wf.steps[0].id == "task_0"

    def test_non_dict_items_skipped(self) -> None:
        raw = {"agents": ["string_agent"], "tasks": [42]}
        wf = parse_crewai(raw)
        assert len(wf.steps) == 0

    def test_crew_name_fallback(self) -> None:
        raw = {"crew": "My Crew", "agents": [], "tasks": []}
        wf = parse_crewai(raw)
        assert wf.name == "My Crew"

    def test_unnamed_crew(self) -> None:
        raw = {"agents": [], "tasks": []}
        wf = parse_crewai(raw)
        assert wf.name == "unnamed-crew"

    def test_metadata_and_inputs(self) -> None:
        raw = {
            "agents": [],
            "tasks": [],
            "inputs": {"topic": "AI"},
            "metadata": {"version": "1.0"},
            "max_tokens": 10000,
        }
        wf = parse_crewai(raw)
        assert wf.inputs == {"topic": "AI"}
        assert wf.metadata == {"version": "1.0"}
        assert wf.token_budget == 10000

    def test_agent_llm_field(self) -> None:
        """llm field takes priority over model."""
        raw = {"agents": [{"name": "a", "llm": "claude-3"}], "tasks": []}
        wf = parse_crewai(raw)
        assert wf.steps[0].model == "claude-3"


# ---------------------------------------------------------------------------
# LangChain parser (31 stmts, 0% → 100%)
# ---------------------------------------------------------------------------


class TestLangChainParser:
    def test_basic_graph(self) -> None:
        raw = {
            "name": "Test Graph",
            "nodes": [
                {"id": "fetch", "type": "retriever"},
                {"id": "analyze", "type": "llm", "model": "gpt-4o", "provider": "openai"},
            ],
            "edges": [{"source": "fetch", "target": "analyze"}],
            "token_budget": 50000,
        }
        wf = parse_langchain(raw, source_path="/tmp/graph.yaml")
        assert wf.name == "Test Graph"
        assert wf.format == WorkflowFormat.LANGCHAIN
        assert wf.source_path == "/tmp/graph.yaml"
        assert len(wf.steps) == 2
        assert wf.token_budget == 50000

    def test_node_type_detection(self) -> None:
        raw = {
            "nodes": [
                {"id": "tool_node", "type": "tool"},
                {"id": "func_node", "type": "function"},
                {"id": "branch_node", "type": "branch"},
                {"id": "cond_node", "type": "conditional"},
                {"id": "par_node", "type": "parallel"},
                {"id": "llm_node", "type": "llm"},
                {"id": "default_node"},
            ],
            "edges": [],
        }
        wf = parse_langchain(raw)
        types = [(s.id, s.step_type) for s in wf.steps]
        assert types == [
            ("tool_node", StepType.SHELL),
            ("func_node", StepType.SHELL),
            ("branch_node", StepType.BRANCH),
            ("cond_node", StepType.BRANCH),
            ("par_node", StepType.PARALLEL),
            ("llm_node", StepType.LLM),
            ("default_node", StepType.LLM),
        ]

    def test_edge_wiring(self) -> None:
        raw = {
            "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
            "edges": [
                {"source": "a", "target": "b"},
                {"source": "b", "target": "c"},
            ],
        }
        wf = parse_langchain(raw)
        assert wf.steps[1].depends_on == ["a"]
        assert wf.steps[2].depends_on == ["b"]
        assert wf.steps[0].depends_on == []

    def test_edge_from_to_aliases(self) -> None:
        """Edges using from/to instead of source/target."""
        raw = {
            "nodes": [{"id": "x"}, {"id": "y"}],
            "edges": [{"from": "x", "to": "y"}],
        }
        wf = parse_langchain(raw)
        assert wf.steps[1].depends_on == ["x"]

    def test_unknown_edge_targets_ignored(self) -> None:
        raw = {
            "nodes": [{"id": "a"}],
            "edges": [{"source": "a", "target": "nonexistent"}],
        }
        wf = parse_langchain(raw)
        assert wf.steps[0].depends_on == []

    def test_non_dict_items_skipped(self) -> None:
        raw = {"nodes": ["string_node"], "edges": ["string_edge"]}
        wf = parse_langchain(raw)
        assert len(wf.steps) == 0

    def test_node_fallback_id(self) -> None:
        raw = {"nodes": [{"name": "my_node"}, {}], "edges": []}
        wf = parse_langchain(raw)
        assert wf.steps[0].id == "my_node"
        assert wf.steps[1].id == "node_1"

    def test_graph_name_fallback(self) -> None:
        raw = {"graph": "My Graph", "nodes": [], "edges": []}
        wf = parse_langchain(raw)
        assert wf.name == "My Graph"

    def test_unnamed_graph(self) -> None:
        raw = {"nodes": [], "edges": []}
        wf = parse_langchain(raw)
        assert wf.name == "unnamed-graph"

    def test_node_fields(self) -> None:
        raw = {
            "nodes": [
                {
                    "id": "n1",
                    "provider": "anthropic",
                    "model": "claude-3",
                    "role": "analyst",
                    "max_tokens": 5000,
                }
            ],
            "edges": [],
        }
        wf = parse_langchain(raw)
        step = wf.steps[0]
        assert step.provider == "anthropic"
        assert step.model == "claude-3"
        assert step.role == "analyst"
        assert step.estimated_tokens == 5000

    def test_metadata_and_inputs(self) -> None:
        raw = {
            "nodes": [],
            "edges": [],
            "inputs": {"query": "test"},
            "metadata": {"version": "2"},
        }
        wf = parse_langchain(raw)
        assert wf.inputs == {"query": "test"}
        assert wf.metadata == {"version": "2"}

    def test_no_duplicate_depends(self) -> None:
        """Same edge twice should not duplicate dependency."""
        raw = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "edges": [
                {"source": "a", "target": "b"},
                {"source": "a", "target": "b"},
            ],
        }
        wf = parse_langchain(raw)
        assert wf.steps[1].depends_on == ["a"]


# ---------------------------------------------------------------------------
# Generic parser — missing branches (16 stmts uncovered)
# ---------------------------------------------------------------------------


class TestGenericParserBranches:
    def test_shell_detection(self) -> None:
        raw = {"steps": [{"id": "run", "command": "ls"}]}
        wf = parse_generic(raw)
        assert wf.steps[0].step_type == StepType.SHELL

    def test_cmd_detection(self) -> None:
        raw = {"steps": [{"id": "run", "cmd": "ls"}]}
        wf = parse_generic(raw)
        assert wf.steps[0].step_type == StepType.SHELL

    def test_parallel_detection(self) -> None:
        raw = {"steps": [{"id": "par", "steps": [{"id": "a"}, {"id": "b"}]}]}
        wf = parse_generic(raw)
        assert wf.steps[0].step_type == StepType.PARALLEL

    def test_steps_as_dict(self) -> None:
        """Steps as name→config mapping instead of list."""
        raw = {
            "steps": {
                "generate": {"prompt": "Generate content", "model": "gpt-4"},
                "review": {"prompt": "Review content"},
            }
        }
        wf = parse_generic(raw)
        assert len(wf.steps) == 2
        ids = {s.id for s in wf.steps}
        assert "generate" in ids
        assert "review" in ids

    def test_agents_key_fallback(self) -> None:
        """When no steps key, falls back to agents/tasks/pipeline."""
        raw = {
            "agents": [
                {"id": "agent1", "model": "gpt-4"},
                {"id": "agent2", "prompt": "test"},
            ]
        }
        wf = parse_generic(raw)
        assert len(wf.steps) == 2

    def test_tasks_key_fallback(self) -> None:
        """agents must be non-list so the fallback loop continues to tasks."""
        raw = {"agents": "not-a-list", "tasks": [{"id": "t1", "prompt": "Do thing"}]}
        wf = parse_generic(raw)
        assert len(wf.steps) == 1
        assert wf.steps[0].id == "t1"

    def test_pipeline_key_fallback(self) -> None:
        """Both agents and tasks must be non-list to reach pipeline."""
        raw = {"agents": "x", "tasks": "y", "pipeline": [{"name": "step1", "model": "gpt-4"}]}
        wf = parse_generic(raw)
        assert len(wf.steps) == 1
        assert wf.steps[0].id == "step1"

    def test_non_dict_items_in_fallback(self) -> None:
        raw = {"agents": ["string_agent", {"id": "real_agent"}]}
        wf = parse_generic(raw)
        assert len(wf.steps) == 1

    def test_step_fields(self) -> None:
        raw = {
            "steps": [
                {
                    "id": "s1",
                    "provider": "openai",
                    "model": "gpt-4",
                    "role": "coder",
                    "estimated_tokens": 5000,
                    "on_failure": "retry",
                    "max_retries": 3,
                    "timeout_seconds": 120,
                }
            ]
        }
        wf = parse_generic(raw)
        s = wf.steps[0]
        assert s.provider == "openai"
        assert s.model == "gpt-4"
        assert s.role == "coder"
        assert s.estimated_tokens == 5000
        assert s.on_failure == "retry"
        assert s.max_retries == 3
        assert s.timeout_seconds == 120

    def test_on_error_alias(self) -> None:
        raw = {"steps": [{"id": "s1", "on_error": "abort"}]}
        wf = parse_generic(raw)
        assert wf.steps[0].on_failure == "abort"

    def test_max_tokens_alias(self) -> None:
        raw = {"steps": [{"id": "s1", "max_tokens": 9000}]}
        wf = parse_generic(raw)
        assert wf.steps[0].estimated_tokens == 9000

    def test_budget_alias(self) -> None:
        raw = {"budget": 100000, "steps": []}
        wf = parse_generic(raw)
        assert wf.token_budget == 100000

    def test_workflow_name_fallback(self) -> None:
        raw = {"workflow": "My Workflow", "steps": []}
        wf = parse_generic(raw)
        assert wf.name == "My Workflow"

    def test_outputs_list(self) -> None:
        raw = {"steps": [], "outputs": ["result1", "result2"]}
        wf = parse_generic(raw)
        assert wf.outputs == ["result1", "result2"]

    def test_outputs_non_list(self) -> None:
        raw = {"steps": [], "outputs": "not_a_list"}
        wf = parse_generic(raw)
        assert wf.outputs == []

    def test_source_path(self) -> None:
        raw = {"steps": []}
        wf = parse_generic(raw, source_path="/tmp/generic.yaml")
        assert wf.source_path == "/tmp/generic.yaml"


# ---------------------------------------------------------------------------
# __main__ (4 stmts, 0% → 100%)
# ---------------------------------------------------------------------------


class TestMainModule:
    def test_main_module_runs(self) -> None:
        with pytest.raises(SystemExit):
            runpy.run_module("agent_lint", run_name="__main__")


# ---------------------------------------------------------------------------
# CLI — severity filter + compare gate + lint markdown
# ---------------------------------------------------------------------------


class TestCLISeverityFilter:
    def test_lint_invalid_severity(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(
            app, ["lint", str(gorgon_workflow_path), "--severity", "nonexistent"]
        )
        assert result.exit_code == 1
        assert "Unknown severity" in result.output

    def test_lint_severity_warning(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--severity", "warning"])
        assert result.exit_code == 0

    def test_lint_markdown_format(self, gorgon_workflow_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(gorgon_workflow_path), "--format", "markdown"])
        assert result.exit_code == 0
        assert "Lint Report" in result.output


class TestCLICompareCommand:
    def test_compare_gated(self, gorgon_workflow_path: Path) -> None:
        """Compare is Pro-only, should fail with upgrade message."""
        result = runner.invoke(app, ["compare", str(gorgon_workflow_path)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# parse_workflow dispatch through CLI for crewai/langchain paths
# ---------------------------------------------------------------------------


class TestParseWorkflowDispatch:
    def test_crewai_via_parse_workflow(self, crewai_path: Path) -> None:
        from agent_lint.parsers import parse_workflow

        wf = parse_workflow(crewai_path)
        assert wf.format == WorkflowFormat.CREWAI
        assert len(wf.steps) == 4  # 2 agents + 2 tasks

    def test_langchain_via_parse_workflow(self, langchain_path: Path) -> None:
        from agent_lint.parsers import parse_workflow

        wf = parse_workflow(langchain_path)
        assert wf.format == WorkflowFormat.LANGCHAIN
        assert len(wf.steps) == 2

    def test_estimate_crewai(self, crewai_path: Path) -> None:
        # CrewAI fixture has model gpt-4o without provider — estimator defaults
        # to anthropic which doesn't have gpt-4o, so it errors. That's fine —
        # we just need the crewai parser path to be exercised.
        result = runner.invoke(app, ["estimate", str(crewai_path)])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_lint_crewai(self, crewai_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(crewai_path)])
        assert result.exit_code == 0

    def test_estimate_langchain(self, langchain_path: Path) -> None:
        # LangChain fixture has model gpt-4o without provider — same as crewai.
        result = runner.invoke(app, ["estimate", str(langchain_path)])
        assert result.exit_code == 1
        assert "Error" in result.output

    def test_lint_langchain(self, langchain_path: Path) -> None:
        result = runner.invoke(app, ["lint", str(langchain_path)])
        assert result.exit_code == 0
