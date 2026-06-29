"""
src/tools/calculator.py
A simple math evaluation tool for demonstrating tool use with Claude.
"""

import math
import ast
import operator as op

# Allowed operations for safe eval
ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.Mod: op.mod,
}

ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval(node):
    """Recursively evaluate an AST node with a safe subset of operations."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in ALLOWED_FUNCTIONS:
            return ALLOWED_FUNCTIONS[node.id]
        raise ValueError(f"Unknown name: {node.id}")
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op_func = ALLOWED_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported operator: {type(node.op)}")
        return op_func(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op_func = ALLOWED_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        return op_func(operand)
    if isinstance(node, ast.Call):
        func = _safe_eval(node.func)
        if not callable(func):
            raise ValueError("Not callable")
        args = [_safe_eval(a) for a in node.args]
        return func(*args)
    raise ValueError(f"Unsupported node type: {type(node)}")


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression string.

    Args:
        expression: A math expression like "2 + 2" or "sqrt(16)"

    Returns:
        String with the result or an error message.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


# Tool definition for the Anthropic API
CALCULATOR_TOOL = {
    "name": "calculator",
    "description": (
        "Evaluate a mathematical expression. Supports basic arithmetic, "
        "powers, modulo, and functions: sqrt, abs, round, sin, cos, tan, log, log10. "
        "Constants: pi, e."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The math expression to evaluate, e.g. '2 ** 10' or 'sqrt(144)'",
            }
        },
        "required": ["expression"],
    },
}


def run_calculator(tool_input: dict) -> str:
    """Execute the calculator tool given raw tool_input from the API."""
    return calculate(tool_input["expression"])
