"""
evaluation/tests/test_correctness.py
Unit tests for evaluation.evaluators.correctness — no API calls needed.
"""

import pytest

from evaluation.evaluators.correctness import evaluate_correctness


def test_numeric_within_tolerance():
    task = {"answer_check": "numeric", "expected_answer": "42", "tolerance": 0.5}
    result = evaluate_correctness(task, "The answer is 42.3")
    assert result.checked is True
    assert result.correct is True


def test_numeric_outside_tolerance():
    task = {"answer_check": "numeric", "expected_answer": "42", "tolerance": 0.1}
    result = evaluate_correctness(task, "The answer is 45")
    assert result.correct is False


def test_numeric_strips_thousands_separators_and_currency_symbols():
    task = {"answer_check": "numeric", "expected_answer": "2315.25", "tolerance": 0.5}
    result = evaluate_correctness(task, "The final amount is $2,315.25.")
    assert result.correct is True


def test_numeric_no_number_in_answer_is_incorrect():
    task = {"answer_check": "numeric", "expected_answer": "4", "tolerance": 0.01}
    result = evaluate_correctness(task, "I cannot compute that.")
    assert result.correct is False


def test_contains_case_insensitive_by_default():
    task = {"answer_check": "contains", "expected_answer": "tokyo"}
    result = evaluate_correctness(task, "The capital of Japan is Tokyo.")
    assert result.correct is True


def test_contains_case_sensitive_avoids_false_positive():
    task = {"answer_check": "contains", "expected_answer": "Au", "case_sensitive": True}
    result = evaluate_correctness(task, "The author explained the symbol is au.")
    assert result.correct is False


def test_exact_normalizes_whitespace_and_case():
    task = {"answer_check": "exact", "expected_answer": "yes"}
    result = evaluate_correctness(task, "  Yes  ")
    assert result.correct is True


def test_exact_case_sensitive():
    task = {"answer_check": "exact", "expected_answer": "Yes", "case_sensitive": True}
    result = evaluate_correctness(task, "yes")
    assert result.correct is False


def test_none_check_is_not_evaluated():
    task = {"answer_check": "none"}
    result = evaluate_correctness(task, "anything at all")
    assert result.checked is False
    assert result.correct is None


def test_missing_final_answer_is_incorrect_when_checked():
    task = {"answer_check": "contains", "expected_answer": "Paris"}
    result = evaluate_correctness(task, None)
    assert result.checked is True
    assert result.correct is False


def test_unknown_check_strategy_raises():
    task = {"answer_check": "bogus"}
    with pytest.raises(ValueError):
        evaluate_correctness(task, "x")
