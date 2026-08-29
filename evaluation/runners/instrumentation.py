"""
evaluation/runners/instrumentation.py
A thin, non-invasive wrapper around the Anthropic client that records
token usage and tool-call outcomes for a single agent run, without any
changes to src/agents/react_agent.py.

Why a client wrapper and not a modified agent:
`run_agent()` only ever calls `client.messages.create(...)` and returns a
plain string — it exposes no usage or tool-call data. Rather than
reaching into or duplicating the agent loop, this wrapper sits between
the agent and the real Anthropic client and reconstructs that data by
observing the request/response pairs that already flow through it:

  - Token usage comes straight from each response's `.usage` block.
  - Every tool the agent asks to use is a `tool_use` content block in a
    response.
  - Whether that tool call *succeeded* is inferred from the matching
    `tool_result` block the agent loop sends back on its *next* call —
    the existing tools already signal failure via a string prefixed
    with "Error:" (see src/tools/calculator.py and the "unknown tool"
    branch in react_agent.py), so no new success/failure protocol is
    introduced here.

Limitation: if the agent loop exits (e.g. it hits max_iterations) right
after requesting a tool but before sending the next request, this
wrapper never observes that tool's result. Such calls are reported with
`success=None` ("unresolved") rather than being guessed as a success or
a failure — see `InstrumentedClient.reset()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _ToolCallRecord:
    tool_name: str
    tool_input: dict
    tool_use_id: str
    result: str | None = None
    success: bool | None = None  # None until a matching tool_result is observed


@dataclass
class _UsageStats:
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    model: str | None = None


class _MessagesProxy:
    """Proxies `client.messages` so `.create()` calls can be observed."""

    def __init__(self, real_messages: Any, tracker: InstrumentedClient):
        self._real_messages = real_messages
        self._tracker = tracker

    def create(self, **kwargs: Any) -> Any:
        self._tracker._resolve_pending_from_request(kwargs.get("messages") or [])
        response = self._real_messages.create(**kwargs)
        self._tracker._record_response(response)
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real_messages, name)


class InstrumentedClient:
    """Wraps an Anthropic client instance to capture per-task telemetry.

    Usage:
        raw_client = get_client()
        instrumented = InstrumentedClient(raw_client)
        answer = run_agent(prompt, instrumented, verbose=False)
        telemetry = instrumented.reset()   # usage + tool calls for this run
    """

    def __init__(self, real_client: Any):
        self._real_client = real_client
        self.messages = _MessagesProxy(real_client.messages, self)
        self._usage = _UsageStats()
        self._resolved_calls: list[_ToolCallRecord] = []
        self._pending: dict[str, _ToolCallRecord] = {}

    def _resolve_pending_from_request(self, messages: list[dict]) -> None:
        """Look at the outgoing request for tool_result blocks and mark the
        matching pending tool call as resolved (success or failure)."""
        if not messages:
            return
        last = messages[-1]
        if not isinstance(last, dict) or last.get("role") != "user":
            return
        content = last.get("content")
        if not isinstance(content, list):
            return
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tool_use_id = block.get("tool_use_id")
                if not isinstance(tool_use_id, str):
                    continue
                record = self._pending.pop(tool_use_id, None)
                if record is None:
                    continue
                result_text = block.get("content")
                if not isinstance(result_text, str):
                    result_text = str(result_text)
                record.result = result_text
                record.success = not result_text.startswith("Error:")
                self._resolved_calls.append(record)

    def _record_response(self, response: Any) -> None:
        """Capture token usage and any new tool_use requests from a response."""
        usage = getattr(response, "usage", None)
        if usage is not None:
            self._usage.api_calls += 1
            self._usage.input_tokens += getattr(usage, "input_tokens", 0) or 0
            self._usage.output_tokens += getattr(usage, "output_tokens", 0) or 0
            self._usage.model = getattr(response, "model", self._usage.model)

        for block in getattr(response, "content", None) or []:
            if getattr(block, "type", None) == "tool_use":
                block_input = getattr(block, "input", None) or {}
                record = _ToolCallRecord(
                    tool_name=block.name,
                    tool_input=dict(block_input),
                    tool_use_id=block.id,
                )
                self._pending[block.id] = record

    def reset(self) -> dict[str, Any]:
        """Return this run's telemetry and clear internal state for the next task.

        Any tool call still pending when this is called (no matching
        tool_result was ever observed) is flushed with success=None so
        it is never misreported as a success or a failure.
        """
        unresolved = list(self._pending.values())
        all_calls = self._resolved_calls + unresolved
        usage = self._usage

        telemetry = {
            "api_calls": usage.api_calls,
            "input_tokens": usage.input_tokens if usage.api_calls else None,
            "output_tokens": usage.output_tokens if usage.api_calls else None,
            "model": usage.model,
            "tool_calls": [
                {
                    "tool_name": c.tool_name,
                    "tool_input": c.tool_input,
                    "success": c.success,
                    "result": c.result,
                }
                for c in all_calls
            ],
        }

        self._usage = _UsageStats()
        self._resolved_calls = []
        self._pending = {}
        return telemetry

    def __getattr__(self, name: str) -> Any:
        # Delegate anything the agent might touch that isn't `.messages`.
        return getattr(self._real_client, name)
