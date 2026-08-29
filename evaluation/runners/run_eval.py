"""
evaluation/runners/run_eval.py
Command-line evaluation runner for the ReAct agent in
src/agents/react_agent.py.

Must be invoked from the repository root so that `src` and `evaluation`
resolve as packages, e.g.:

    python -m evaluation.runners.run_eval
    python -m evaluation.runners.run_eval --dataset evaluation/datasets/agent_tasks.json
    python -m evaluation.runners.run_eval --limit 5
    python -m evaluation.runners.run_eval --category calculator
    python -m evaluation.runners.run_eval --no-report

Requires a valid ANTHROPIC_API_KEY (see .env.example) since every task
makes real calls to the Claude API through the existing agent. If the
key is missing, the runner prints a clear message and exits with a
non-zero status instead of failing with a raw traceback.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.evaluators import metrics
from evaluation.evaluators.correctness import evaluate_correctness
from evaluation.evaluators.tool_use import evaluate_tool_use
from evaluation.runners.instrumentation import InstrumentedClient
from src.agents.react_agent import run_agent
from src.utils.tokens import PRICING, estimate_cost

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = REPO_ROOT / "evaluation" / "datasets" / "agent_tasks.json"
DEFAULT_REPORTS_DIR = REPO_ROOT / "evaluation" / "reports"

# The exact fallback string returned by run_agent() when it exhausts
# max_iterations without producing a final answer. Treated as a
# distinct failure status rather than a "successful" empty-ish answer.
_MAX_ITERATIONS_MESSAGE = "[agent] Max iterations reached without a final answer."


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load evaluation tasks from a JSON file.

    Accepts either a plain JSON list of task objects, or an object of
    the form {"tasks": [...]}.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "tasks" in data:
        data = data["tasks"]
    if not isinstance(data, list):
        raise ValueError(f"Dataset at {path} must be a JSON list of task objects.")
    return data


def run_task(task: dict[str, Any], client: Any) -> dict[str, Any]:
    """Execute a single evaluation task against the existing ReAct agent
    and evaluate the outcome. Never raises: any failure while running the
    agent itself is captured as an "agent_error" result.
    """
    instrumented = InstrumentedClient(client)
    agent_kwargs: dict[str, Any] = {"verbose": False}
    if "max_iterations" in task:
        agent_kwargs["max_iterations"] = task["max_iterations"]

    final_answer: str | None = None
    status = "success"
    error: str | None = None

    start = time.perf_counter()
    try:
        # InstrumentedClient duck-types the .messages.create() surface that
        # run_agent() actually uses; it is not an Anthropic subclass, so
        # this deliberately doesn't match run_agent()'s declared type.
        final_answer = run_agent(task["prompt"], instrumented, **agent_kwargs)  # type: ignore[arg-type]
        if final_answer == _MAX_ITERATIONS_MESSAGE:
            status = "max_iterations_exceeded"
    except Exception as exc:  # noqa: BLE001 - any agent/API failure is a result to report, not a crash
        status = "agent_error"
        error = f"{type(exc).__name__}: {exc}"
    latency_seconds = time.perf_counter() - start

    telemetry = instrumented.reset()

    correctness = evaluate_correctness(task, final_answer)
    tool_use = evaluate_tool_use(task, telemetry["tool_calls"])

    cost: float | None = None
    if telemetry["input_tokens"] is not None and telemetry["model"] in PRICING:
        cost = estimate_cost(
            telemetry["model"], telemetry["input_tokens"], telemetry["output_tokens"]
        )

    return {
        "id": task["id"],
        "category": task.get("category"),
        "prompt": task["prompt"],
        "expected_answer": task.get("expected_answer"),
        "expected_tools": task.get("expected_tools", []),
        "final_answer": final_answer,
        "status": status,
        "error": error,
        "latency_seconds": round(latency_seconds, 4),
        "tokens": {
            "input_tokens": telemetry["input_tokens"],
            "output_tokens": telemetry["output_tokens"],
            "api_calls": telemetry["api_calls"],
            "model": telemetry["model"],
        },
        "estimated_cost_usd": cost,
        "correctness": {
            "checked": correctness.checked,
            "correct": correctness.correct,
            "detail": correctness.detail,
        },
        "tool_use": {
            "checked": tool_use.checked,
            "selection_correct": tool_use.selection_correct,
            "expected_tools": tool_use.expected_tools,
            "actual_tools": tool_use.actual_tools,
            "unexpected_tools": tool_use.unexpected_tools,
            "missing_tools": tool_use.missing_tools,
            "tool_calls_total": tool_use.tool_calls_total,
            "tool_calls_successful": tool_use.tool_calls_successful,
            "tool_calls_failed": tool_use.tool_calls_failed,
            "tool_calls_unresolved": tool_use.tool_calls_unresolved,
            "detail": tool_use.detail,
        },
    }


def build_report(dataset_path: Path, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "meta": {
            "dataset": str(dataset_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tasks_run": len(results),
        },
        "summary": metrics.aggregate(results),
        "tasks": results,
    }


def _fmt(value: Any, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}{suffix}"
    return f"{value}{suffix}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1%}"


def print_summary(summary: dict[str, Any]) -> None:
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total tasks:              {summary['total_tasks']}")
    print(
        f"Successful tasks:         {summary['successful_tasks']} "
        f"({_fmt_pct(summary['success_rate'])})"
    )
    print(
        f"Agent failures:           {summary['agent_failures']} "
        f"(errors={summary['agent_failures_breakdown']['agent_error']}, "
        f"max_iterations={summary['agent_failures_breakdown']['max_iterations_exceeded']})"
    )
    print(
        f"Correctness:              {summary['correctness_correct_tasks']}/"
        f"{summary['correctness_checked_tasks']} checked "
        f"(rate={_fmt(summary['correctness_rate'], 2)})"
    )
    print(
        f"Tool selection accuracy:  {summary['tool_selection_correct_tasks']}/"
        f"{summary['tool_selection_checked_tasks']} checked "
        f"(rate={_fmt(summary['tool_selection_accuracy'], 2)})"
    )
    print(
        f"Tool execution success:   {summary['tool_calls_successful']}/"
        f"{summary['tool_calls_total']} calls "
        f"(rate={_fmt(summary['tool_execution_success_rate'], 2)})"
    )
    print(f"Average latency (s):      {_fmt(summary['average_latency_seconds'])}")
    print(
        f"Tokens (in/out/total):    {_fmt(summary['total_input_tokens'])}/"
        f"{_fmt(summary['total_output_tokens'])}/{_fmt(summary['total_tokens'])} "
        f"({summary['tasks_with_token_data']}/{summary['total_tasks']} tasks with usage data)"
    )
    print(f"Estimated cost (USD):     {_fmt(summary['estimated_cost_usd'], 5)}")
    print("=" * 60 + "\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the claude-api-starter ReAct agent evaluation suite."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help="Path to the evaluation dataset JSON file.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N tasks.")
    parser.add_argument(
        "--category", type=str, default=None, help="Only run tasks in this category."
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Directory to write the JSON report to.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip writing a report file; print the summary only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "ANTHROPIC_API_KEY is not set. The evaluation suite calls the real "
            "Claude API through the existing agent, so a valid key is required.\n"
            "Copy .env.example to .env, add your key, and re-run this command.",
            file=sys.stderr,
        )
        return 1

    try:
        from src.utils.client import get_client

        client = get_client()
    except Exception as exc:
        print(f"Could not initialize the Anthropic client: {exc}", file=sys.stderr)
        return 1

    try:
        tasks = load_dataset(args.dataset)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Could not load dataset {args.dataset}: {exc}", file=sys.stderr)
        return 1

    if args.category:
        tasks = [t for t in tasks if t.get("category") == args.category]
    if args.limit is not None:
        tasks = tasks[: args.limit]

    if not tasks:
        print("No tasks matched the given filters. Nothing to run.", file=sys.stderr)
        return 1

    print(f"Running {len(tasks)} evaluation task(s) from {args.dataset} ...")
    results = []
    for i, task in enumerate(tasks, start=1):
        print(f"  [{i}/{len(tasks)}] {task['id']} ...", end=" ", flush=True)
        result = run_task(task, client)
        print(result["status"])
        results.append(result)

    report = build_report(args.dataset, results)
    print_summary(report["summary"])

    if not args.no_report:
        args.reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = args.reports_dir / f"eval_report_{stamp}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Report saved to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
