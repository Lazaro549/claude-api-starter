"""
evaluation/evaluators/correctness.py
Deterministic correctness checks for the ReAct agent's final answer.

No LLM judge is used anywhere in this module. Every check is a plain
string or numeric comparison so results are reproducible, free to
compute, and easy to audit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Matches the first integer/decimal number in free-form text, including
# thousands separators (e.g. "2,315.25") and a leading minus sign.
_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def _normalize_text(text: str) -> str:
    """Collapse whitespace and lowercase for tolerant exact-match comparisons."""
    return re.sub(r"\s+", " ", text).strip().lower()


def _extract_first_number(text: str) -> float | None:
    """Extract the first numeric value found in free-form text.

    Strips thousands-separator commas before parsing. Returns None if no
    number is present or the matched substring cannot be parsed as a float.
    """
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    raw = match.group(0).replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


@dataclass
class CorrectnessResult:
    """Outcome of evaluating one task's final answer.

    `checked` is False when the task's `answer_check` is "none" — in that
    case `correct` is None rather than True/False, since correctness was
    never actually evaluated and reporting a boolean would be misleading.
    """

    checked: bool
    correct: bool | None
    detail: str


def evaluate_correctness(task: dict[str, Any], final_answer: str | None) -> CorrectnessResult:
    """Evaluate a single task's final answer against its expected result.

    Supported `answer_check` strategies (set per-task in the dataset):
      - "none":     correctness is not evaluated for this task.
      - "exact":    normalized string equality (whitespace/case collapsed
                    unless `case_sensitive` is true).
      - "contains": `expected_answer` must appear as a substring of the
                    final answer (case-insensitive unless `case_sensitive`
                    is true).
      - "numeric":  the first number found in the final answer must match
                    `expected_answer` within `tolerance` (default 0.01).
    """
    check = task.get("answer_check", "none")

    if check == "none":
        return CorrectnessResult(
            checked=False, correct=None, detail="No correctness check configured for this task."
        )

    if not final_answer:
        return CorrectnessResult(
            checked=True, correct=False, detail="Agent produced no final answer to evaluate."
        )

    expected = task.get("expected_answer")
    case_sensitive = bool(task.get("case_sensitive", False))

    if check == "exact":
        actual = final_answer if case_sensitive else _normalize_text(final_answer)
        exp = str(expected) if case_sensitive else _normalize_text(str(expected))
        ok = actual == exp
        return CorrectnessResult(
            checked=True, correct=ok, detail=f"expected='{exp}' actual='{actual}'"
        )

    if check == "contains":
        haystack = final_answer if case_sensitive else final_answer.lower()
        needle = str(expected) if case_sensitive else str(expected).lower()
        ok = needle in haystack
        return CorrectnessResult(checked=True, correct=ok, detail=f"expected substring='{needle}'")

    if check == "numeric":
        tolerance = float(task.get("tolerance", 0.01))
        actual_num = _extract_first_number(final_answer)
        try:
            expected_num = float(expected)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return CorrectnessResult(
                checked=True,
                correct=False,
                detail=f"Task's expected_answer '{expected}' is not numeric.",
            )
        if actual_num is None:
            return CorrectnessResult(
                checked=True, correct=False, detail="No number found in the agent's final answer."
            )
        ok = abs(actual_num - expected_num) <= tolerance
        return CorrectnessResult(
            checked=True,
            correct=ok,
            detail=f"expected={expected_num} actual={actual_num} tolerance={tolerance}",
        )

    raise ValueError(f"Unknown answer_check strategy: {check!r}")
