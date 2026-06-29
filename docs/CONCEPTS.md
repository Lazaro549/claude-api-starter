# Claude API — Key Concepts

Notes from the *Building with the Claude API* Anthropic Academy course.

---

## Messages API

Every call goes to `POST /v1/messages`. The core fields:

| Field | Required | Notes |
|---|---|---|
| `model` | ✅ | e.g. `claude-sonnet-4-6` |
| `max_tokens` | ✅ | Hard cap on output tokens |
| `messages` | ✅ | Alternating `user`/`assistant` list |
| `system` | ❌ | Top-level system prompt (preferred over a system message in the list) |
| `tools` | ❌ | List of tool definitions |
| `stream` | ❌ | Use `stream()` context manager instead |

---

## Stop Reasons

| `stop_reason` | Meaning |
|---|---|
| `end_turn` | Claude finished naturally |
| `tool_use` | Claude wants to call one or more tools |
| `max_tokens` | Hit the `max_tokens` limit |
| `stop_sequence` | Matched a custom stop string |

---

## Tool Use Lifecycle

```
user message
     │
     ▼
Claude (stop_reason=tool_use)
  └── content includes tool_use block(s) with id, name, input
     │
     ▼
Your code executes the tool
     │
     ▼
Append tool_result block(s) to messages
  (role=user, content=[{type: tool_result, tool_use_id: ..., content: "..."}])
     │
     ▼
Claude (stop_reason=end_turn)
  └── content includes final text answer
```

---

## Streaming

Use `client.messages.stream()` as a context manager:

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
final = stream.get_final_message()
```

---

## Token Counting

- Input tokens = system prompt + all messages + tool definitions
- Output tokens = only what Claude generates
- Use `response.usage.input_tokens` and `response.usage.output_tokens`
- See `src/utils/tokens.py` for cost estimation helpers

---

## Best Practices

1. **Always use a system prompt** to give Claude a clear role.
2. **Keep messages alternating** — never two consecutive `user` or `assistant` turns.
3. **Set `max_tokens` conservatively** for cost control; raise it only when needed.
4. **Never hardcode your API key** — use environment variables.
5. **Handle `tool_use` stop reason** in a loop, not just once (Claude may need multiple tool calls).
6. **Validate tool inputs** before executing them — Claude can occasionally hallucinate fields.
