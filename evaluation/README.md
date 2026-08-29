# Agent Evaluation Suite

An evaluation harness for the ReAct-style agent in
[`src/agents/react_agent.py`](../src/agents/react_agent.py). It exists to
answer, with numbers instead of vibes, whether a change to the agent, its
tools, or its prompt made things better or worse — and to demonstrate a
realistic, minimal LLM/agent evaluation setup as part of this portfolio
project.

It is intentionally not a general-purpose eval platform: no LLM-judge
scoring, no external eval framework, no database. Just a dataset, a few
deterministic evaluators, and a runner — reused against the *existing*
agent and tools without modifying them.

## Why this exists

`run_agent()` is convenient to call but returns only a final string — no
record of which tools it used, whether they succeeded, how many tokens
were spent, or how long it took. This suite adds exactly that
observability around the agent, from the outside, so runs are
comparable over time.

## Methodology

For each task in the dataset:

1. The existing `run_agent()` is called unmodified, through a thin
   instrumented wrapper around the Anthropic client
   (`evaluation/runners/instrumentation.py`) that records token usage and
   every tool call/result pair by observing the requests and responses
   that already flow through `client.messages.create()`.
2. **Correctness** is checked deterministically
   (`evaluation/evaluators/correctness.py`) — exact match, substring
   match, or numeric match with a tolerance. No LLM judge is used, so
   results are reproducible and free to compute.
3. **Tool use** is checked against the task's expected tools
   (`evaluation/evaluators/tool_use.py`), separately for *selection*
   (did the agent pick the right tool(s)?) and *execution* (did the
   tool call actually succeed?).
4. Latency, token usage, and estimated cost are recorded per task.
5. Results are aggregated into a run summary
   (`evaluation/evaluators/metrics.py`).

Because everything runs against the live Claude API, outcomes for
open-ended tasks (e.g. `ambiguous` or `reasoning` categories) can vary
between runs. Tasks with a strict `answer_check`/`tool_match` are chosen
to be as deterministic as a real model call allows.

## Dataset

`evaluation/datasets/agent_tasks.json` — 20 tasks covering:

| Category         | What it tests                                              |
|-------------------|-------------------------------------------------------------|
| `reasoning`       | Simple arithmetic/word problems; tool use is optional        |
| `no_tool`         | Factual/logic questions where using a tool would be a mistake |
| `calculator`      | Straightforward calculator usage                             |
| `multi_step`      | Tasks that may require more than one tool call                |
| `tool_selection`  | Picking `web_search` over `calculator` (or not using a tool)  |
| `ambiguous`       | Vague/underspecified requests — checks graceful handling      |
| `edge_case`       | Deliberately provokes tool or agent-loop failures              |

### Task schema

```jsonc
{
  "id": "calc_001",                 // unique task id
  "category": "calculator",
  "prompt": "What is 847 multiplied by 293?",
  "expected_tools": ["calculator"], // tools the agent should use
  "tool_match": "exact",            // "exact" | "subset" | "none"
  "answer_check": "numeric",        // "exact" | "numeric" | "contains" | "none"
  "expected_answer": "248171",
  "tolerance": 0.001,               // only used by "numeric"
  "case_sensitive": false,          // only used by "exact"/"contains"
  "max_iterations": 10,             // optional override of run_agent()'s default
  "notes": "..."                    // optional, human-readable rationale
}
```

- `tool_match`: `"exact"` requires the set of tools actually used to equal
  `expected_tools`; `"subset"` only requires `expected_tools` to all
  appear (extras allowed); `"none"` skips the check entirely.
- `answer_check`: `"none"` skips correctness checking — used for tasks
  where the only thing worth measuring is tool selection, or robustness
  (did the agent complete without crashing?).
- `web_search` is a stub in this repo (see `src/tools/web_search.py`), so
  every `tool_selection` task uses `answer_check: "none"` — the stubbed
  result can't be judged for correctness, only tool *selection* can be.

### Adding a new evaluation case

Append an object to `evaluation/datasets/agent_tasks.json` following the
schema above, and give it a unique `id`. `evaluation/tests/test_dataset.py`
will fail if the id collides with an existing one or the schema is
incomplete — run it after adding a case.

## Metrics

Computed by `evaluation/evaluators/metrics.py`, all as pure functions
over the list of per-task results:

- **Task success rate** — fraction of tasks where the agent completed
  without a harness-level error and without exhausting `max_iterations`.
- **Agent failures** — count/breakdown of `agent_error` (an exception
  during the run) vs. `max_iterations_exceeded`.
- **Correctness rate** — fraction of *correctness-checked* tasks
  (`answer_check != "none"`) whose final answer matched.
- **Tool selection accuracy** — fraction of *tool-checked* tasks
  (`tool_match != "none"`) where the right tool(s) were used.
- **Tool execution success rate** — fraction of individual tool calls,
  across the whole run, that did not return an `"Error: ..."` result.
- **Latency** — average wall-clock time per task.
- **Token usage** — total/average input and output tokens, only over
  tasks where usage data was actually captured.
- **Estimated cost** — reuses `src/utils/tokens.estimate_cost()` and its
  `PRICING` table, so pricing assumptions live in exactly one place in
  the repo. If a task's model isn't in `PRICING`, its cost is reported
  as unavailable (`null`), never guessed as `0`.

Any metric that cannot actually be computed for a given run (e.g. no
tool was ever called, so there's nothing to compute an execution success
rate from) is reported as `null` in the JSON report — never fabricated.

## Running the evaluation suite

Requires a valid `ANTHROPIC_API_KEY` (see the repo's `.env.example`) —
every task makes a real call to the Claude API through the existing
agent. Run from the repository root:

```bash
python -m evaluation.runners.run_eval
python -m evaluation.runners.run_eval --dataset evaluation/datasets/agent_tasks.json
python -m evaluation.runners.run_eval --limit 5
python -m evaluation.runners.run_eval --category calculator
python -m evaluation.runners.run_eval --no-report   # print the summary only
```

If `ANTHROPIC_API_KEY` is missing, the runner prints a clear message and
exits with a non-zero status instead of raising a traceback.

### Reports

Each run (unless `--no-report` is passed) writes a timestamped JSON
report to `evaluation/reports/`, shaped like:

```jsonc
{
  "meta": { "dataset": "...", "generated_at": "...", "tasks_run": 20 },
  "summary": {
    "total_tasks": 20,
    "successful_tasks": 18,
    "success_rate": 0.9,
    "agent_failures": 2,
    "correctness_rate": 0.95,
    "tool_selection_accuracy": 0.94,
    "tool_execution_success_rate": 0.97,
    "average_latency_seconds": 2.31,
    "total_input_tokens": 5000,
    "total_output_tokens": 3000,
    "estimated_cost_usd": 0.08
    // ...see evaluation/evaluators/metrics.py for the full set of fields
  },
  "tasks": [ /* one detailed result per task */ ]
}
```

Reports are generated files and are excluded from version control (see
the root `.gitignore`) since they reflect a specific run rather than
the evaluation suite's source.

## Running the evaluation suite's own tests

These are unit tests for the evaluation framework itself — they mock the
Anthropic client and never make a live API call, so no key is needed:

```bash
python -m pytest evaluation/tests -v
```

This is separate from the main `pytest tests/ -v` command, matching this
repository's `[tool.pytest.ini_options] testpaths = ["tests"]` setting;
CI runs both (see `.github/workflows/ci.yml`).

## Limitations

- **No LLM-judge scoring.** Correctness is deterministic by design. Open-
  ended tasks (`ambiguous`, most of `reasoning`) can't be judged for
  correctness this way, so they only check that the agent completes.
- **`web_search` is a stub** in this starter kit, so `tool_selection`
  tasks only validate *which* tool was picked, never the factual
  correctness of the (stubbed) result.
- **Non-determinism.** Live model calls mean outcomes for loosely-
  constrained tasks can vary run to run; only the report from a specific
  run is a source of truth for that run.
- **Tool execution success is a heuristic.** It's inferred from the
  existing tools' own `"Error: ..."` string convention, not a structured
  success flag — there isn't one to observe, since the tools return
  plain strings.
- **`max_iterations` overrides are opt-in per task.** `edge_002` sets
  `max_iterations: 1` specifically to force the agent's fallback path
  deterministically, which is the one case in the dataset expected *not*
  to succeed — this is intentional, not a bug in the harness.

## Cost considerations

Every task run makes at least one, and sometimes several, real calls to
the Claude API — running the full 20-task dataset has a real (small)
dollar cost. Estimated cost is computed from `src/utils/tokens.PRICING`,
which the source file itself notes may go stale; check
[anthropic.com/pricing](https://www.anthropic.com/pricing) for current
rates and update that one table if needed. Use `--limit` or `--category`
while iterating to avoid running the whole dataset unnecessarily.
