#!/usr/bin/env python3
"""Performance benchmark: measure lint latency and memory across workflow sizes.

Usage:
    python scripts/benchmark-performance.py

Fails if latency exceeds thresholds or memory RSS > 50 MB.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

THRESHOLDS = {
    10: {"latency_ms": 20, "memory_mb": 50},
    100: {"latency_ms": 50, "memory_mb": 50},
    500: {"latency_ms": 100, "memory_mb": 75},
    1000: {"latency_ms": 200, "memory_mb": 100},
}


def generate_workflow(steps: int) -> str:
    """Generate a minimal workflow YAML with *steps* LLM steps."""
    lines = [
        "name: benchmark",
        "version: '1.0'",
        f"token_budget: {steps * 1000}",
        "steps:",
    ]
    for i in range(steps):
        lines += [
            f"  - id: step_{i}",
            "    type: llm",
            "    model: gpt-4o",
            f"    prompt: 'Step {i}'",
            "    estimated_tokens: 1000",
        ]
    return "\n".join(lines) + "\n"


def benchmark(steps: int, runs: int = 3) -> dict:
    """Run lint *runs* times and return median latency + peak RSS."""
    from agent_lint.linter import run_lint
    from agent_lint.parsers import parse_workflow

    yaml_text = generate_workflow(steps)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as fh:
        fh.write(yaml_text)
        path = fh.name

    try:
        wf = parse_workflow(Path(path))
        # Warm-up
        run_lint(wf)

        latencies: list[float] = []
        for _ in range(runs):
            start = time.perf_counter()
            run_lint(wf)
            latencies.append((time.perf_counter() - start) * 1000)

        median_latency = sorted(latencies)[runs // 2]

        # Peak RSS via /proc/self/status (Linux only)
        peak_rss_mb = 0.0
        try:
            with open("/proc/self/status") as fh:
                for line in fh:
                    if line.startswith("VmHWM:"):
                        peak_rss_kb = int(line.split()[1])
                        peak_rss_mb = peak_rss_kb / 1024
                        break
        except FileNotFoundError:
            pass

        return {
            "steps": steps,
            "latency_ms": round(median_latency, 2),
            "memory_mb": round(peak_rss_mb, 2),
        }
    finally:
        os.unlink(path)


def main() -> int:
    results: list[dict] = []
    failed = False

    for steps in sorted(THRESHOLDS):
        print(f"Benchmarking {steps} steps...", end=" ", flush=True)
        result = benchmark(steps)
        thresholds = THRESHOLDS[steps]
        ok = (
            result["latency_ms"] <= thresholds["latency_ms"]
            and result["memory_mb"] <= thresholds["memory_mb"]
        )
        status = "PASS" if ok else "FAIL"
        print(f"latency={result['latency_ms']}ms memory={result['memory_mb']}MB [{status}]")
        results.append(result)
        if not ok:
            failed = True

    summary = {
        "status": "fail" if failed else "pass",
        "thresholds": THRESHOLDS,
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
