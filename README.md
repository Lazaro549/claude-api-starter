# claude-api-starter 🤖

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude%20API-purple)](https://www.anthropic.com)

A clean, opinionated **Python starter kit** for building with the Anthropic Claude API.  
Covers basic completions, streaming, multi-turn conversations, tool use, and a simple ReAct-style agent.

> Built by [Lazaro Gomez Vitolo](https://lazaro549.github.io/Portafolio/) after completing the **Building with the Claude API** course on Anthropic Academy.

---

## ✨ Features

- ✅ Basic messages & system prompts
- ✅ Multi-turn conversation management
- ✅ Streaming responses
- ✅ Tool use (function calling)
- ✅ Simple ReAct-style agent loop
- ✅ Token counting & cost estimation
- ✅ Environment-based configuration (no hardcoded keys)
- ✅ Ready-to-run example scripts
- ✅ Unit tests included

---

## 📁 Project Structure

```text
claude-api-starter/
├── src/
│   ├── agents/
│   │   └── react_agent.py       # ReAct agent loop with tool use
│   ├── tools/
│   │   ├── calculator.py        # Safe math evaluation tool
│   │   └── web_search.py        # Search tool stub (ready to extend)
│   └── utils/
│       ├── client.py            # Anthropic client factory
│       ├── conversation.py      # Conversation history manager
│       └── tokens.py            # Token counting & cost helpers
├── examples/
│   ├── 01_basic_message.py
│   ├── 02_streaming.py
│   ├── 03_multi_turn.py
│   ├── 04_tool_use.py
│   └── 05_agent.py
├── tests/
│   ├── test_conversation.py
│   └── test_tools.py
├── docs/
│   └── CONCEPTS.md              # Key concepts from the Anthropic course
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Lazaro549/claude-api-starter.git
cd claude-api-starter

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Run an example

```bash
python examples/01_basic_message.py
python examples/05_agent.py
```

---

## 📚 Examples Overview

| #  | File                  | What it teaches                          |
|----|-----------------------|------------------------------------------|
| 01 | `01_basic_message.py` | Simplest possible Claude API call        |
| 02 | `02_streaming.py`     | Real-time streaming responses            |
| 03 | `03_multi_turn.py`    | Conversation history management          |
| 04 | `04_tool_use.py`      | Single-round tool use (calculator)       |
| 05 | `05_agent.py`         | Full ReAct agent loop with multiple tools|

---

## 💡 Usage Examples

### Basic message

```python
from src.utils.client import get_client, get_model
from src.utils.tokens import print_usage

client = get_client()

response = client.messages.create(
    model=get_model(),
    max_tokens=512,
    messages=[
        {"role": "user", "content": "Explain recursion in one paragraph."}
    ],
)

print(response.content[0].text)
print_usage(response)
```

### Multi-turn conversation

```python
from src.utils.client import get_client, get_model
from src.utils.conversation import ConversationManager

client = get_client()
conv = ConversationManager(system="You are a helpful coding assistant.")

conv.add_user("What is a closure in Python?")
response = client.messages.create(
    model=get_model(),
    max_tokens=1024,
    system=conv.system,
    messages=conv.messages,
)
conv.add_assistant(response.content[0].text)

conv.add_user("Give me a short example.")
# ... continue the conversation
```

### ReAct Agent

```python
from src.utils.client import get_client
from src.agents.react_agent import run_agent

client = get_client()

answer = run_agent(
    "What is the square root of 1764 multiplied by pi? Round to 4 decimal places.",
    client,
    verbose=True,
)
print(answer)
```

---

## 🧠 Key Concepts

See [`docs/CONCEPTS.md`](docs/CONCEPTS.md) for notes on:

- Messages API structure
- System prompts
- Stop reasons (`end_turn`, `tool_use`, `max_tokens`...)
- Tool use lifecycle (`tool_use` → `tool_result`)
- Streaming with the `stream()` context manager
- Token limits and cost management

---

## 📦 Requirements

```text
anthropic>=0.25.0
python-dotenv>=1.0.0
```

---

## 🧪 Running Tests

```bash
python tests/test_conversation.py
python tests/test_tools.py
```

---

## 💸 Donations

If you find this project useful and want to support it:

| Currency | Alias |
|----------|-------|
| 🇦🇷 ARS (Argentina) | `lazaro.503.alaba.mp` |
| 🌎 USD (Argentina — local transfers only) | `ahogada.duras.foca` |

---

## 📄 License

MIT — use freely, attribution appreciated.

---

**Made with ❤️ after completing the official Anthropic Academy course.**
```