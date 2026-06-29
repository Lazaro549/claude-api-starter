"""
examples/04_tool_use.py
Single-round tool use: Claude calls the calculator, we execute it,
then pass the result back and get the final answer.
"""

from src.utils.client import get_client, get_model
from src.tools.calculator import CALCULATOR_TOOL, run_calculator

client = get_client()
model = get_model()

messages = [{"role": "user", "content": "What is 2 to the power of 32, and what is its square root?"}]

# Round 1: Claude decides to use the calculator
response = client.messages.create(
    model=model,
    max_tokens=1024,
    tools=[CALCULATOR_TOOL],
    messages=messages,
)

print(f"stop_reason: {response.stop_reason}")

if response.stop_reason == "tool_use":
    messages.append({"role": "assistant", "content": response.content})

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            print(f"→ tool_use: {block.name}({block.input})")
            result = run_calculator(block.input)
            print(f"← result: {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

    messages.append({"role": "user", "content": tool_results})

    # Round 2: Claude sees the result and writes the final answer
    final = client.messages.create(
        model=model,
        max_tokens=512,
        tools=[CALCULATOR_TOOL],
        messages=messages,
    )
    print(f"\n[final answer]\n{final.content[0].text}")
