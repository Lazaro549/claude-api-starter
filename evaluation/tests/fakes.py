"""
evaluation/tests/fakes.py
Lightweight fakes that mimic just enough of the Anthropic Python SDK's
response shape to exercise InstrumentedClient and the evaluation
runner without any network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeToolUseBlock:
    name: str
    input: dict
    id: str
    type: str = "tool_use"


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    content: list
    stop_reason: str
    model: str = "claude-sonnet-4-6"
    usage: FakeUsage = field(default_factory=lambda: FakeUsage(0, 0))


class _FakeMessages:
    def __init__(self, responses: list[FakeResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("FakeAnthropicClient ran out of scripted responses")
        return self._responses.pop(0)


class FakeAnthropicClient:
    """A scripted stand-in for `anthropic.Anthropic`.

    Returns one pre-built FakeResponse per `.messages.create()` call, in
    order, so a full multi-turn ReAct loop can be simulated
    deterministically and offline.
    """

    def __init__(self, responses: list[FakeResponse]):
        self.messages = _FakeMessages(responses)


class ExplodingMessages:
    """A `.messages` stand-in that always raises, for testing error handling."""

    def create(self, **kwargs: Any) -> Any:
        raise RuntimeError("boom")


class ExplodingClient:
    def __init__(self) -> None:
        self.messages = ExplodingMessages()
