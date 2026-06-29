"""
examples/05_agent.py
Full ReAct agent loop: Claude reasons, calls tools, observes results, repeats.
"""

from src.utils.client import get_client
from src.agents.react_agent import run_agent

client = get_client()

tasks = [
    "What is the square root of 1764, multiplied by pi? Round to 4 decimal places.",
    "If I invest $5000 at 7% annual compound interest for 10 years, what is the final amount? Use the formula A = P * (1 + r)^t",
]

for task in tasks:
    print(f"\n{'='*60}")
    print(f"[task] {task}")
    answer = run_agent(task, client, verbose=True)
    print(f"\n[answer] {answer}")
