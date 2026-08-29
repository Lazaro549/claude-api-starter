"""
evaluation/evaluators/metrics.py
Reusable aggregation functions over a list of per-task evaluation
results, as produced by evaluation.runners.run_eval.run_task().

Every function here is a pure function over `results: list[dict]` — no
I/O, no API calls — which keeps them trivial to unit test. Any metric
whose inputs are unavailable for every task in the run (e.g. no token
usage was ever captured) is reported as `None`, never as a fabricated
0 or 0.0, per the evaluation suite's design principle: an unmeasured
metric must never be presented as a measured one.
"""

from __future__ import annotations

from typing import Any

Result = dict[str, Any]


def total_tasks(results: list[Result]) -> int:
    return len(results)


def successful_tasks(results: list[Result]) -> int:
    return sum(1 for r in results if r.get("status") == "success")


def success_rate(results: list[Result]) -> float | None:
    total = total_tasks(results)
    if total == 0:
        return None
    return successful_tasks(results) / total


def agent_failures(results: list[Result]) -> dict[str, int]:
    """Breakdown of non-successful task outcomes by failure type."""
    breakdown = {"agent_error": 0, "max_iterations_exceeded": 0}
    for r in results:
        status = r.get("status")
        if status in breakdown:
            breakdown[status] += 1
    breakdown["total"] = breakdown["agent_error"] + breakdown["max_iterations_exceeded"]
    return breakdown


def correctness_stats(results: list[Result]) -> dict[str, int | float | None]:
    """Correctness counts and rate, over tasks that actually configured a check."""
    checked = [r for r in results if r.get("correctness", {}).get("checked")]
    correct = [r for r in checked if r["correctness"].get("correct") is True]
    rate = (len(correct) / len(checked)) if checked else None
    return {
        "checked_tasks": len(checked),
        "correct_tasks": len(correct),
        "correctness_rate": rate,
    }


def tool_selection_stats(results: list[Result]) -> dict[str, int | float | None]:
    """Tool-selection accuracy, over tasks that actually configured a check."""
    checked = [r for r in results if r.get("tool_use", {}).get("checked")]
    correct = [r for r in checked if r["tool_use"].get("selection_correct") is True]
    rate = (len(correct) / len(checked)) if checked else None
    return {
        "checked_tasks": len(checked),
        "correct_tasks": len(correct),
        "tool_selection_accuracy": rate,
    }


def tool_execution_stats(results: list[Result]) -> dict[str, int | float | None]:
    """Tool-execution success rate, across every individual tool call in the run."""
    total = sum(r.get("tool_use", {}).get("tool_calls_total", 0) for r in results)
    succeeded = sum(r.get("tool_use", {}).get("tool_calls_successful", 0) for r in results)
    rate = (succeeded / total) if total else None
    return {
        "tool_calls_total": total,
        "tool_calls_successful": succeeded,
        "tool_execution_success_rate": rate,
    }


def average_latency(results: list[Result]) -> float | None:
    latencies = [
        float(r["latency_seconds"]) for r in results if r.get("latency_seconds") is not None
    ]
    if not latencies:
        return None
    return sum(latencies) / len(latencies)


def token_totals(results: list[Result]) -> dict[str, int | float | None]:
    """Token usage totals/averages, over tasks where usage was actually captured.

    A task's usage is unavailable when the run errored before any API
    response was received, so it is excluded from both totals and
    averages rather than counted as zero.
    """
    with_tokens = [
        r
        for r in results
        if r.get("tokens", {}).get("input_tokens") is not None
        and r.get("tokens", {}).get("output_tokens") is not None
    ]
    if not with_tokens:
        return {
            "tasks_with_token_data": 0,
            "total_input_tokens": None,
            "total_output_tokens": None,
            "total_tokens": None,
            "average_input_tokens": None,
            "average_output_tokens": None,
        }

    total_input = sum(r["tokens"]["input_tokens"] for r in with_tokens)
    total_output = sum(r["tokens"]["output_tokens"] for r in with_tokens)
    n = len(with_tokens)
    return {
        "tasks_with_token_data": n,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "average_input_tokens": total_input / n,
        "average_output_tokens": total_output / n,
    }


def estimated_total_cost(results: list[Result]) -> float | None:
    """Sum of per-task estimated costs, or None if no task priced out."""
    costs = [
        float(r["estimated_cost_usd"]) for r in results if r.get("estimated_cost_usd") is not None
    ]
    if not costs:
        return None
    return round(sum(costs), 6)


def aggregate(results: list[Result]) -> dict[str, Any]:
    """Build the full summary block for an evaluation run.

    This is the single entry point run_eval.py calls; individual
    functions above remain independently usable and independently
    testable.
    """
    correctness = correctness_stats(results)
    tool_selection = tool_selection_stats(results)
    tool_execution = tool_execution_stats(results)
    tokens = token_totals(results)
    failures = agent_failures(results)

    return {
        "total_tasks": total_tasks(results),
        "successful_tasks": successful_tasks(results),
        "success_rate": success_rate(results),
        "agent_failures": failures["total"],
        "agent_failures_breakdown": {
            "agent_error": failures["agent_error"],
            "max_iterations_exceeded": failures["max_iterations_exceeded"],
        },
        "correctness_checked_tasks": correctness["checked_tasks"],
        "correctness_correct_tasks": correctness["correct_tasks"],
        "correctness_rate": correctness["correctness_rate"],
        "tool_selection_checked_tasks": tool_selection["checked_tasks"],
        "tool_selection_correct_tasks": tool_selection["correct_tasks"],
        "tool_selection_accuracy": tool_selection["tool_selection_accuracy"],
        "tool_calls_total": tool_execution["tool_calls_total"],
        "tool_calls_successful": tool_execution["tool_calls_successful"],
        "tool_execution_success_rate": tool_execution["tool_execution_success_rate"],
        "average_latency_seconds": average_latency(results),
        "tasks_with_token_data": tokens["tasks_with_token_data"],
        "total_input_tokens": tokens["total_input_tokens"],
        "total_output_tokens": tokens["total_output_tokens"],
        "total_tokens": tokens["total_tokens"],
        "average_input_tokens": tokens["average_input_tokens"],
        "average_output_tokens": tokens["average_output_tokens"],
        "estimated_cost_usd": estimated_total_cost(results),
    }
