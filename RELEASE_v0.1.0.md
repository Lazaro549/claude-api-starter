## 🚀 claude-api-starter v0.1.0

First public release of the Claude API Starter Kit.

A clean and opinionated Python starter for the Anthropic Claude API, covering the main concepts from the official **Building with the Claude API** course.

### ✨ What's included

- Basic messages & system prompts
- Streaming responses
- Multi-turn conversation management
- Tool use (function calling)
- Simple ReAct-style agent loop
- Token counting & cost estimation utilities
- Environment-based configuration
- Unit tests
- Modern project setup (`pyproject.toml`, `.gitignore`, `.env.example`)

### 📁 Project structure

```
src/
├── agents/          # ReAct agent
├── tools/           # Calculator + web search stub
└── utils/           # Client, conversation manager, tokens
examples/            # 5 progressive examples
tests/
docs/CONCEPTS.md
```

### 🚀 Quick start

```bash
git clone https://github.com/Lazaro549/claude-api-starter.git
cd claude-api-starter
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Add your ANTHROPIC_API_KEY
python examples/01_basic_message.py
```

### 📦 Requirements

- Python ≥ 3.10
- `anthropic>=0.25.0`
- `python-dotenv>=1.0.0`

---

**Built after completing the official Anthropic Academy course.**
```
