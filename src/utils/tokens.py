"""
src/utils/tokens.py
Token counting and rough cost estimation helpers.
"""

# Approximate prices per million tokens (as of mid-2025).
# Update these if pricing changes: https://www.anthropic.com/pricing
PRICING = {
    "claude-opus-4-6":    {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5":   {"input": 0.80,  "output": 4.00},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Return estimated cost in USD for a single API call.

    Args:
        model: Model string, e.g. "claude-sonnet-4-6"
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated

    Returns:
        Estimated cost in USD (float)
    """
    prices = PRICING.get(model)
    if not prices:
        return 0.0
    cost = (input_tokens / 1_000_000) * prices["input"]
    cost += (output_tokens / 1_000_000) * prices["output"]
    return round(cost, 6)


def print_usage(response) -> None:
    """Print token usage and estimated cost from a Messages response."""
    usage = response.usage
    model = response.model
    cost = estimate_cost(model, usage.input_tokens, usage.output_tokens)
    print(
        f"[tokens] input={usage.input_tokens}  "
        f"output={usage.output_tokens}  "
        f"est. cost=${cost:.5f}"
    )
