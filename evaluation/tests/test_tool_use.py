"""
evaluation/tests/test_tool_use.py
Unit tests for evaluation.evaluators.tool_use — no API calls needed.
"""

from evaluation.evaluators.tool_use import evaluate_tool_use


def _call(tool_name: str, success: bool | None) -> dict:
    return {
        "tool_name": tool_name,
        "tool_input": {},
        "success": success,
        "result": "ok" if success else "Error: x",
    }


def test_exact_match_success():
    task = {"expected_tools": ["calculator"], "tool_match": "exact"}
    result = evaluate_tool_use(task, [_call("calculator", True)])
    assert result.checked is True
    assert result.selection_correct is True
    assert result.tool_calls_successful == 1


def test_exact_match_missing_tool():
    task = {"expected_tools": ["calculator"], "tool_match": "exact"}
    result = evaluate_tool_use(task, [])
    assert result.selection_correct is False
    assert result.missing_tools == ["calculator"]


def test_exact_match_unexpected_tool():
    task = {"expected_tools": [], "tool_match": "exact"}
    result = evaluate_tool_use(task, [_call("calculator", True)])
    assert result.selection_correct is False
    assert result.unexpected_tools == ["calculator"]


def test_exact_match_no_tools_expected_and_none_used():
    task = {"expected_tools": [], "tool_match": "exact"}
    result = evaluate_tool_use(task, [])
    assert result.selection_correct is True


def test_subset_allows_extra_tools():
    task = {"expected_tools": ["calculator"], "tool_match": "subset"}
    result = evaluate_tool_use(task, [_call("calculator", True), _call("web_search", True)])
    assert result.selection_correct is True


def test_subset_fails_when_expected_tool_missing():
    task = {"expected_tools": ["calculator", "web_search"], "tool_match": "subset"}
    result = evaluate_tool_use(task, [_call("calculator", True)])
    assert result.selection_correct is False


def test_none_strategy_is_not_checked():
    task = {"expected_tools": [], "tool_match": "none"}
    result = evaluate_tool_use(task, [_call("calculator", True)])
    assert result.checked is False
    assert result.selection_correct is None


def test_execution_failure_is_independent_of_selection_correctness():
    task = {"expected_tools": ["calculator"], "tool_match": "exact"}
    result = evaluate_tool_use(task, [_call("calculator", False)])
    assert result.selection_correct is True  # right tool was chosen
    assert result.tool_calls_successful == 0
    assert result.tool_calls_failed == 1


def test_unresolved_call_not_counted_as_success_or_failure():
    task = {"expected_tools": ["calculator"], "tool_match": "exact"}
    call = _call("calculator", None)
    result = evaluate_tool_use(task, [call])
    assert result.tool_calls_successful == 0
    assert result.tool_calls_failed == 0
    assert result.tool_calls_unresolved == 1


def test_multiple_calls_to_same_tool_count_once_toward_selection():
    task = {"expected_tools": ["calculator"], "tool_match": "exact"}
    result = evaluate_tool_use(task, [_call("calculator", True), _call("calculator", True)])
    assert result.actual_tools == ["calculator"]
    assert result.tool_calls_total == 2
