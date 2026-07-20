#!/usr/bin/env python3
"""Accuracy benchmark for agent-lint rules.

Runs the linter against a corpus of annotated workflows and measures
precision / recall per rule category.

Usage:
    python scripts/benchmark-accuracy.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_ground_truth() -> list[dict]:
    """Load annotated workflow fixtures with expected findings."""
    bench_dir = PROJECT_ROOT / "tests" / "fixtures" / "benchmarks"
    if not bench_dir.exists():
        return []
    records: list[dict] = []
    for path in bench_dir.glob("*.yaml"):
        meta_path = path.with_suffix(".json")
        if not meta_path.exists():
            continue
        with open(meta_path) as fh:
            meta = json.load(fh)
        meta["path"] = str(path)
        records.append(meta)
    return records


def run_benchmark() -> dict:
    """Execute lint on each fixture and compare to ground truth."""
    from agent_lint.linter import run_lint
    from agent_lint.parsers import parse_workflow

    records = load_ground_truth()
    if not records:
        return {"status": "no_fixtures", "message": "No benchmark fixtures found."}

    per_rule: dict[str, dict] = {}
    total_tp = total_fp = total_fn = 0

    for rec in records:
        wf = parse_workflow(Path(rec["path"]))
        report = run_lint(wf)
        actual = {f.rule_id for f in report.findings}
        expected = set(rec.get("expected_findings", []))

        tp = len(expected & actual)
        fp = len(actual - expected)
        fn = len(expected - actual)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        for rid in expected | actual:
            if rid not in per_rule:
                per_rule[rid] = {"tp": 0, "fp": 0, "fn": 0}
            if rid in expected and rid in actual:
                per_rule[rid]["tp"] += 1
            elif rid in actual:
                per_rule[rid]["fp"] += 1
            elif rid in expected:
                per_rule[rid]["fn"] += 1

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "status": "ok",
        "total_fixtures": len(records),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "per_rule": {
            rid: {
                "precision": round(v["tp"] / (v["tp"] + v["fp"]), 4) if (v["tp"] + v["fp"]) else 0.0,
                "recall": round(v["tp"] / (v["tp"] + v["fn"]), 4) if (v["tp"] + v["fn"]) else 0.0,
            }
            for rid, v in per_rule.items()
        },
    }


if __name__ == "__main__":
    result = run_benchmark()
    print(json.dumps(result, indent=2))
    if result.get("status") != "ok":
        sys.exit(1)
