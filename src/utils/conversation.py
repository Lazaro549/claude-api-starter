"""
src/utils/conversation.py
Lightweight multi-turn conversation history manager.
"""

from typing import Optional


class ConversationManager:
    """
    Manages a list of messages in the format the Anthropic API expects.

    Usage:
        conv = ConversationManager(system="You are a helpful assistant.")
        conv.add_user("Hello!")
        response = client.messages.create(..., messages=conv.messages)
        conv.add_assistant(response.content[0].text)
    """

    def __init__(self, system: Optional[str] = None):
        self.system: Optional[str] = system
        self.messages: list[dict] = []

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def clear(self) -> None:
        self.messages = []

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"<ConversationManager turns={len(self.messages)} system={'yes' if self.system else 'no'}>"
