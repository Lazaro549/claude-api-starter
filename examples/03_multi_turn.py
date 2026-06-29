"""
examples/03_multi_turn.py
Multi-turn conversation using the ConversationManager.
"""

from src.utils.client import get_client, get_model
from src.utils.conversation import ConversationManager

client = get_client()
conv = ConversationManager(system="You are a concise Python tutor. Keep answers short.")

turns = [
    "What is a decorator in Python?",
    "Show me the simplest possible decorator example.",
    "What is a real-world use case for decorators?",
]

for user_msg in turns:
    conv.add_user(user_msg)
    print(f"\n[user] {user_msg}")

    response = client.messages.create(
        model=get_model(),
        max_tokens=512,
        system=conv.system,
        messages=conv.messages,
    )

    assistant_text = response.content[0].text
    conv.add_assistant(assistant_text)
    print(f"[claude] {assistant_text}")

print(f"\n[done] {len(conv)} messages in history")
