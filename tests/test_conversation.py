"""
tests/test_conversation.py
Unit tests for ConversationManager — no API calls needed.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.conversation import ConversationManager


def test_empty_on_init():
    conv = ConversationManager()
    assert len(conv) == 0
    assert conv.messages == []


def test_add_messages():
    conv = ConversationManager(system="You are helpful.")
    conv.add_user("Hello")
    conv.add_assistant("Hi there!")
    assert len(conv) == 2
    assert conv.messages[0] == {"role": "user", "content": "Hello"}
    assert conv.messages[1] == {"role": "assistant", "content": "Hi there!"}


def test_clear():
    conv = ConversationManager()
    conv.add_user("test")
    conv.clear()
    assert len(conv) == 0


def test_system_optional():
    conv = ConversationManager()
    assert conv.system is None
    conv2 = ConversationManager(system="Be concise.")
    assert conv2.system == "Be concise."


if __name__ == "__main__":
    test_empty_on_init()
    test_add_messages()
    test_clear()
    test_system_optional()
    print("All conversation tests passed ✓")
