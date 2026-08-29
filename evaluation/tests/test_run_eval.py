"""
evaluation/tests/test_run_eval.py
Unit tests for evaluation.runners.run_eval and instrumentation.
Every Anthropic API call is replaced with a fake — none of these tests
touch the network or require ANTHROPIC_API_KEY.
"""

from evaluation.runners.run_eval import DEFAULT_DATASET, load_dataset, main, run_task
from evaluation.tests.fakes import (
    ExplodingClient,
    FakeAnthropicClient,
    FakeResponse,
    FakeTextBlock,
    FakeToolUseBlock,
    FakeUsage,
)


def test_load_dataset_reads_the_real_dataset():
    tasks = load_dataset(DEFAULT_DATASET)
    assert len(tasks) >= 15
    assert all("id" in t for t in tasks)


def test_run_task_no_tool_scenario():
    client = FakeAnthropicClient(
        [
            FakeResponse(
                content=[FakeTextBlock("Tokyo is the capital of Japan.")],
                stop_reason="end_turn",
                usage=FakeUsage(40, 8),
            )
        ]
    )
    task = {
        "id": "t1",
        "category": "no_tool",
        "prompt": "What is the capital of Japan?",
        "expected_tools": [],
        "tool_match": "exact",
        "answer_check": "contains",
        "expected_answer": "Tokyo",
    }
    result = run_task(task, client)

    assert result["status"] == "success"
    assert result["correctness"]["checked"] is True
    assert result["correctness"]["correct"] is True
    assert result["tool_use"]["selection_correct"] is True
    assert result["tokens"]["input_tokens"] == 40
    assert result["tokens"]["output_tokens"] == 8
    assert result["estimated_cost_usd"] is not None


def test_run_task_tool_use_scenario_across_two_turns():
    client = FakeAnthropicClient(
        [
            FakeResponse(
                content=[
                    FakeToolUseBlock(name="calculator", input={"expression": "2+2"}, id="call_1")
                ],
                stop_reason="tool_use",
                usage=FakeUsage(100, 20),
            ),
            FakeResponse(
                content=[FakeTextBlock("The answer is 4.")],
                stop_reason="end_turn",
                usage=FakeUsage(120, 10),
            ),
        ]
    )
    task = {
        "id": "t2",
        "category": "calculator",
        "prompt": "What is 2+2?",
        "expected_tools": ["calculator"],
        "tool_match": "exact",
        "answer_check": "numeric",
        "expected_answer": "4",
        "tolerance": 0.01,
    }
    result = run_task(task, client)

    assert result["status"] == "success"
    assert result["correctness"]["correct"] is True
    assert result["tool_use"]["actual_tools"] == ["calculator"]
    assert result["tool_use"]["tool_calls_successful"] == 1
    # Usage accumulates across both turns of the loop.
    assert result["tokens"]["input_tokens"] == 220
    assert result["tokens"]["output_tokens"] == 30


def test_run_task_reports_forced_max_iterations_as_a_failure():
    client = FakeAnthropicClient(
        [
            FakeResponse(
                content=[
                    FakeToolUseBlock(name="calculator", input={"expression": "2+2"}, id="call_1")
                ],
                stop_reason="tool_use",
                usage=FakeUsage(10, 5),
            )
        ]
    )
    task = {
        "id": "t3",
        "category": "edge_case",
        "prompt": "Needs several tool calls.",
        "expected_tools": [],
        "tool_match": "none",
        "answer_check": "none",
        "max_iterations": 1,
    }
    result = run_task(task, client)

    assert result["status"] == "max_iterations_exceeded"
    # The tool_use block was requested but its result was never sent
    # back (the loop exited first), so it must be reported as unresolved.
    assert result["tool_use"]["tool_calls_unresolved"] == 1


def test_run_task_captures_agent_errors_instead_of_raising():
    task = {
        "id": "t4",
        "category": "edge_case",
        "prompt": "anything",
        "expected_tools": [],
        "tool_match": "none",
        "answer_check": "none",
    }
    result = run_task(task, ExplodingClient())

    assert result["status"] == "agent_error"
    assert "boom" in result["error"]
    assert result["final_answer"] is None


def test_main_exits_gracefully_when_api_key_is_missing(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main(["--dataset", str(DEFAULT_DATASET), "--limit", "1"])

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "ANTHROPIC_API_KEY" in captured.err


def test_main_reports_no_matching_tasks_for_unknown_category(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-a-real-key")
    exit_code = main(["--dataset", str(DEFAULT_DATASET), "--category", "does_not_exist"])
    assert exit_code != 0
