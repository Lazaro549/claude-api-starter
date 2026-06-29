"""
src/agents/react_agent.py
A minimal ReAct-style agent loop that uses Claude with tools.

The loop:
  1. Send messages to Claude with available tools.
  2. If Claude returns stop_reason="tool_use", execute the requested tool.
  3. Append the tool_result back to messages and repeat.
  4. Stop when stop_reason="end_turn" or max_iterations is reached.
"""

from anthropic import Anthropic
from src.utils.client import get_model
from src.tools.calculator import CALCULATOR_TOOL, run_calculator
from src.tools.web_search import WEB_SEARCH_TOOL, run_web_search

TOOLS = [CALCULATOR_TOOL, WEB_SEARCH_TOOL]

TOOL_EXECUTORS = {
    "calculator": run_calculator,
    "web_search": run_web_search,
}

SYSTEM_PROMPT = """You are a helpful assistant with access to tools.
Think step by step. Use tools when you need to compute something or look up information.
Always provide a clear final answer to the user after using tools."""


def run_agent(
    user_message: str,
    client: Anthropic,
    max_iterations: int = 10,
    verbose: bool = True,
) -> str:
    """
    Run the ReAct agent loop for a single user message.

    Args:
        user_message: The user's question or task.
        client: An Anthropic client instance.
        max_iterations: Safety cap on tool call rounds.
        verbose: Print intermediate steps if True.

    Returns:
        The agent's final text response.
    """
    messages = [{"role": "user", "content": user_message}]
    model = get_model()

    for iteration in range(max_iterations):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if verbose:
            print(f"\n[agent iter={iteration+1}] stop_reason={response.stop_reason}")

        # Collect all content blocks into the messages history
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            # Extract the final text response
            for block in assistant_content:
                if block.type == "text":
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    if verbose:
                        print(f"  → tool={tool_name}  input={tool_input}")
                    executor = TOOL_EXECUTORS.get(tool_name)
                    if executor:
                        result = executor(tool_input)
                    else:
                        result = f"Error: unknown tool '{tool_name}'"
                    if verbose:
                        print(f"  ← result={result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — break to avoid infinite loop
        break

    return "[agent] Max iterations reached without a final answer."
