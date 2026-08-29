"""
evaluation/evaluators/tool_use.py
Evaluate whether the ReAct agent selected and executed the expected
tools, adapted to the tool_use / tool_result block structure of the
Anthropic Messages API used by src/agents/react_agent.py.

This module does not talk to the Anthropic client directly. It consumes
the per-task tool-call telemetry produced by
`evaluation.runners.instrumentation.InstrumentedClient`, which records,
for every tool_use block the agent emitted:
    {"tool_name": str, "tool_input": dict, "success": bool | None, "result": str | None}

`success` is derived from the *existing* tool implementations' own error
convention (a result string starting with "Error:" — see
src/tools/calculator.py and the "unknown tool" branch in react_agent.py).
`success` is None when no matching tool_result was ever observed (e.g.
the agent hit max_iterations immediately after requesting the tool) —
that outcome is reported as "unresolved", never guessed as success or
failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolUseResult:
    """Outcome of evaluating tool selection and execution for one task."""

    checked: bool
    selection_correct: bool | None
    expected_tools: list[str]
    actual_tools: list[str]
    unexpected_tools: list[str]
    missing_tools: list[str]
    tool_calls_total: int
    tool_calls_successful: int
    tool_calls_failed: int
    tool_calls_unresolved: int
    detail: str


def evaluate_tool_use(task: dict[str, Any], tool_calls: list[dict[str, Any]]) -> ToolUseResult:
    """Evaluate tool selection and execution outcomes for a single task.

    Args:
        task: The task definition. Uses `expected_tools` (list[str]) and
            `tool_match` ("exact" | "subset" | "none").
        tool_calls: Per-call telemetry as produced by
            `InstrumentedClient.reset()["tool_calls"]`.
    """
    tool_match = task.get("tool_match", "none")
    expected_tools = set(task.get("expected_tools", []) or [])
    actual_tools = sorted({call["tool_name"] for call in tool_calls})
    actual_set = set(actual_tools)

    unexpected = sorted(actual_set - expected_tools)
    missing = sorted(expected_tools - actual_set)

    total = len(tool_calls)
    successful = sum(1 for call in tool_calls if call.get("success") is True)
    failed = sum(1 for call in tool_calls if call.get("success") is False)
    unresolved = sum(1 for call in tool_calls if call.get("success") is None)

    if tool_match == "none":
        checked = False
        selection_correct = None
        detail = "Tool selection not evaluated for this task."
    elif tool_match == "exact":
        checked = True
        selection_correct = actual_set == expected_tools
        detail = f"exact match required: expected={sorted(expected_tools)} actual={actual_tools}"
    elif tool_match == "subset":
        checked = True
        selection_correct = expected_tools.issubset(actual_set)
        detail = (
            f"expected tools must all appear: expected={sorted(expected_tools)} "
            f"actual={actual_tools}"
        )
    else:
        raise ValueError(f"Unknown tool_match strategy: {tool_match!r}")

    return ToolUseResult(
        checked=checked,
        selection_correct=selection_correct,
        expected_tools=sorted(expected_tools),
        actual_tools=actual_tools,
        unexpected_tools=unexpected,
        missing_tools=missing,
        tool_calls_total=total,
        tool_calls_successful=successful,
        tool_calls_failed=failed,
        tool_calls_unresolved=unresolved,
        detail=detail,
    )
