"""
evaluation/evaluators
Deterministic, dependency-free evaluators for the ReAct agent evaluation
suite: correctness checking, tool-use checking, and metric aggregation.
"""

from evaluation.evaluators import metrics
from evaluation.evaluators.correctness import CorrectnessResult, evaluate_correctness
from evaluation.evaluators.tool_use import ToolUseResult, evaluate_tool_use

__all__ = [
    "CorrectnessResult",
    "evaluate_correctness",
    "ToolUseResult",
    "evaluate_tool_use",
    "metrics",
]
