"""
evaluation/tests/test_metrics.py
Unit tests for evaluation.evaluators.metrics — pure functions, no API calls.
"""

from evaluation.evaluators import metrics


def _task_result(**overrides):
    base = {
        "status": "success",
        "latency_seconds": 1.0,
        "tokens": {"input_tokens": 100, "output_tokens": 50},
        "estimated_cost_usd": 0.001,
        "correctness": {"checked": True, "correct": True},
        "tool_use": {
            "checked": True,
            "selection_correct": True,
            "tool_calls_total": 1,
            "tool_calls_successful": 1,
        },
    }
    base.update(overrides)
    return base


def test_success_rate():
    results = [_task_result(status="success"), _task_result(status="agent_error")]
    assert metrics.success_rate(results) == 0.5


def test_success_rate_empty_dataset_is_none():
    assert metrics.success_rate([]) is None


def test_agent_failures_breakdown():
    results = [
        _task_result(status="success"),
        _task_result(status="agent_error"),
        _task_result(status="max_iterations_exceeded"),
    ]
    breakdown = metrics.agent_failures(results)
    assert breakdown["agent_error"] == 1
    assert breakdown["max_iterations_exceeded"] == 1
    assert breakdown["total"] == 2


def test_correctness_rate_only_over_checked_tasks():
    results = [
        _task_result(correctness={"checked": True, "correct": True}),
        _task_result(correctness={"checked": True, "correct": False}),
        _task_result(correctness={"checked": False, "correct": None}),
    ]
    stats = metrics.correctness_stats(results)
    assert stats["checked_tasks"] == 2
    assert stats["correctness_rate"] == 0.5


def test_correctness_rate_none_when_nothing_checked():
    results = [_task_result(correctness={"checked": False, "correct": None})]
    stats = metrics.correctness_stats(results)
    assert stats["correctness_rate"] is None


def test_tool_selection_accuracy():
    results = [
        _task_result(
            tool_use={
                "checked": True,
                "selection_correct": True,
                "tool_calls_total": 1,
                "tool_calls_successful": 1,
            }
        ),
        _task_result(
            tool_use={
                "checked": True,
                "selection_correct": False,
                "tool_calls_total": 1,
                "tool_calls_successful": 0,
            }
        ),
    ]
    stats = metrics.tool_selection_stats(results)
    assert stats["tool_selection_accuracy"] == 0.5


def test_tool_execution_success_rate_none_when_no_calls_made():
    results = [
        _task_result(
            tool_use={
                "checked": False,
                "selection_correct": None,
                "tool_calls_total": 0,
                "tool_calls_successful": 0,
            }
        )
    ]
    stats = metrics.tool_execution_stats(results)
    assert stats["tool_execution_success_rate"] is None


def test_average_latency():
    results = [_task_result(latency_seconds=1.0), _task_result(latency_seconds=3.0)]
    assert metrics.average_latency(results) == 2.0


def test_token_totals_excludes_tasks_without_usage_data():
    results = [
        _task_result(tokens={"input_tokens": 100, "output_tokens": 50}),
        _task_result(tokens={"input_tokens": None, "output_tokens": None}),
    ]
    totals = metrics.token_totals(results)
    assert totals["tasks_with_token_data"] == 1
    assert totals["total_input_tokens"] == 100
    assert totals["average_input_tokens"] == 100


def test_token_totals_none_when_no_task_has_usage_data():
    results = [_task_result(tokens={"input_tokens": None, "output_tokens": None})]
    totals = metrics.token_totals(results)
    assert totals["total_input_tokens"] is None
    assert totals["average_input_tokens"] is None


def test_estimated_total_cost_sums_available_costs_only():
    results = [_task_result(estimated_cost_usd=0.001), _task_result(estimated_cost_usd=None)]
    assert metrics.estimated_total_cost(results) == 0.001


def test_estimated_total_cost_none_when_unavailable():
    results = [_task_result(estimated_cost_usd=None)]
    assert metrics.estimated_total_cost(results) is None


def test_aggregate_produces_all_documented_summary_keys():
    results = [_task_result()]
    summary = metrics.aggregate(results)
    expected_keys = {
        "total_tasks",
        "successful_tasks",
        "success_rate",
        "agent_failures",
        "correctness_checked_tasks",
        "correctness_correct_tasks",
        "correctness_rate",
        "tool_selection_checked_tasks",
        "tool_selection_correct_tasks",
        "tool_selection_accuracy",
        "tool_calls_total",
        "tool_calls_successful",
        "tool_execution_success_rate",
        "average_latency_seconds",
        "total_input_tokens",
        "total_output_tokens",
        "total_tokens",
        "average_input_tokens",
        "average_output_tokens",
        "estimated_cost_usd",
    }
    assert expected_keys.issubset(summary.keys())
