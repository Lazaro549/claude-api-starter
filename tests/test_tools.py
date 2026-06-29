"""
tests/test_tools.py
Unit tests for the calculator tool — no API calls needed.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.calculator import calculate, run_calculator


def test_basic_arithmetic():
    assert calculate("2 + 2") == "4"
    assert calculate("10 - 3") == "7"
    assert calculate("6 * 7") == "42"
    assert calculate("10 / 4") == "2.5"


def test_power():
    assert calculate("2 ** 10") == "1024"


def test_sqrt():
    assert calculate("sqrt(144)") == "12.0"


def test_modulo():
    assert calculate("17 % 5") == "2"


def test_nested():
    result = calculate("sqrt(2 ** 8)")
    assert result == "16.0"


def test_error_on_invalid():
    result = calculate("import os")
    assert result.startswith("Error")


def test_run_calculator_wrapper():
    result = run_calculator({"expression": "3 * 3"})
    assert result == "9"


if __name__ == "__main__":
    test_basic_arithmetic()
    test_power()
    test_sqrt()
    test_modulo()
    test_nested()
    test_error_on_invalid()
    test_run_calculator_wrapper()
    print("All calculator tests passed ✓")
