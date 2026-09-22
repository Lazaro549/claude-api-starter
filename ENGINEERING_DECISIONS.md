# Engineering Decisions

This document records the main engineering decisions behind this project, including the reasoning, trade-offs, and constraints that shaped the implementation.

The goal is to make the project's technical judgment explicit rather than relying only on the code to communicate design intent.

---

## 1. Custom ReAct Loop Instead of an Agent Framework

### Decision

Implement a minimal custom ReAct-style agent loop instead of using an external agent framework.

### Context

The project demonstrates how tool-using agents work at a low level:

1. Send messages to Claude.
2. Detect tool-use requests.
3. Execute the requested tool.
4. Return the tool result to the model.
5. Continue until the model produces a final response.

### Why

A framework would reduce implementation effort but hide important parts of the agent execution model.

The project is intended as a starter kit and learning-oriented reference, so keeping the control loop explicit makes the architecture easier to inspect, debug, and modify.

### Trade-offs

**Advantages**

* Full control over the agent lifecycle.
* Minimal dependencies.
* Easier to understand and debug.
* Makes tool execution behavior explicit.
* Provides a clear foundation for experimentation.

**Disadvantages**

* More code must be maintained manually.
* Production concerns such as retries, persistence, tracing, and advanced orchestration are not provided automatically.
* The implementation is intentionally less feature-rich than mature agent frameworks.

### Consequence

The agent implementation remains small and transparent, while more advanced orchestration can be added later if the project requirements justify it.

---

## 2. Explicit Maximum Iterations to Prevent Unbounded Agent Loops

### Decision

The ReAct agent uses a configurable `max_iterations` limit.

### Context

Tool-using agents can potentially continue requesting tools indefinitely if the model does not reach a final answer.

### Why

An explicit iteration limit provides a deterministic safety boundary around the agent loop.

The default value is intentionally conservative while remaining configurable for evaluation and experimentation.

### Trade-offs

**Advantages**

* Prevents infinite loops.
* Limits unnecessary API usage.
* Controls worst-case execution time and cost.
* Makes failure behavior observable.

**Disadvantages**

* A legitimate task may require more iterations.
* A low limit can cause premature termination.

### Consequence

The agent explicitly reports when it reaches the iteration limit instead of silently continuing or fabricating a result.

---

## 3. Deterministic Evaluation Instead of an LLM-as-Judge

### Decision

The evaluation suite uses deterministic evaluators rather than an LLM judge.

### Context

Agent evaluation can use another language model to judge whether an answer is correct. While flexible, that approach introduces another source of variability.

### Why

This project prioritizes reproducibility and transparent evaluation.

Correctness is evaluated using deterministic methods such as:

* Exact matching.
* Substring matching.
* Numeric comparison with tolerance.

This makes evaluation results easier to reproduce and inspect.

### Trade-offs

**Advantages**

* Reproducible results.
* No additional judge-model cost.
* Easier to debug failed evaluations.
* Evaluation logic is explicit.
* No dependency on another model's subjective judgment.

**Disadvantages**

* Less suitable for open-ended natural-language answers.
* Requires evaluation cases to define measurable expectations.
* Cannot capture every aspect of qualitative answer quality.

### Consequence

The evaluation suite deliberately optimizes for measurable and repeatable signals rather than broad semantic judgment.

---

## 4. Instrumentation Outside the Agent Implementation

### Decision

Evaluation telemetry is collected through an instrumented client wrapper instead of modifying the production agent implementation.

### Context

The evaluation suite needs information such as:

* Latency.
* Input tokens.
* Output tokens.
* Estimated cost.
* API calls.

Adding evaluation-specific logic directly to the agent would couple the agent implementation to the evaluation system.

### Why

A thin instrumentation layer provides observability while keeping the core agent unchanged.

The evaluator can therefore test the same agent implementation that normal users run.

### Trade-offs

**Advantages**

* Keeps production logic simple.
* Separates execution from measurement.
* Reduces evaluation-specific coupling.
* Makes instrumentation reusable.

**Disadvantages**

* Some internal behavior cannot be observed without additional hooks.
* The wrapper adds another abstraction layer.

### Consequence

The evaluation system measures the existing agent rather than creating a special evaluation-only version of it.

---

## 5. Separate Tool Selection from Tool Execution Metrics

### Decision

Tool-use evaluation measures both tool selection and tool execution separately.

### Context

An agent can fail in two fundamentally different ways:

1. Select the wrong tool.
2. Select the correct tool but fail during execution.

Treating these as a single metric makes diagnosis harder.

### Why

Separating the two dimensions makes failures more actionable.

For example:

```text
Tool selection: correct
Tool execution: failed
```

points to a different engineering problem than:

```text
Tool selection: incorrect
Tool execution: not applicable
```

### Trade-offs

**Advantages**

* Better failure diagnosis.
* More useful benchmark data.
* Easier to identify whether problems originate in the model or tool implementation.

**Disadvantages**

* Requires additional evaluation logic.
* Some execution checks are necessarily heuristic.

### Consequence

The evaluation report exposes tool-selection and tool-execution behavior as separate metrics.

---

## 6. Centralized Token and Cost Estimation

### Decision

Token and cost calculations are centralized rather than scattered throughout the codebase.

### Context

Agent experiments often compare different prompts, models, and execution paths. Token usage and estimated API cost are important engineering signals.

### Why

Centralizing pricing and cost estimation makes the calculation consistent across evaluations.

The system also avoids treating unknown pricing information as zero cost.

### Trade-offs

**Advantages**

* Consistent calculations.
* Easier to update model pricing.
* Makes cost visible alongside quality and latency.
* Prevents misleading zero-cost results when pricing is unavailable.

**Disadvantages**

* Pricing information must be maintained.
* Estimated cost may differ from the final provider invoice.

### Consequence

Reports expose estimated cost as a measurable engineering metric while returning `null` when pricing information is unavailable.

---

## 7. Explicit Failure States Instead of Silent Failures

### Decision

Evaluation runs distinguish between successful execution, maximum-iteration termination, and agent errors.

### Context

A benchmark should distinguish between:

* A task that was completed.
* An agent that stopped because of its safety limit.
* An execution that failed unexpectedly.

### Why

Treating all non-successful runs as a generic failure loses important diagnostic information.

### Trade-offs

**Advantages**

* Better debugging.
* More accurate benchmark interpretation.
* Easier identification of agent-loop problems.
* Prevents accidental classification of incomplete executions as successful.

**Disadvantages**

* Evaluation logic becomes slightly more complex.
* Reports contain more states that consumers need to interpret.

### Consequence

Evaluation reports preserve the reason an execution did not produce a normal successful result.

---

## 8. No Fabricated Metrics

### Decision

Metrics that cannot be reliably calculated are represented as `null` rather than being assigned a default value.

### Context

Benchmark systems can create misleading results when unavailable measurements are silently converted into zeroes or estimated values.

### Why

A missing metric is different from a measured zero.

For example:

```text
cost: null
```

means pricing information was unavailable.

It should not be interpreted as:

```text
cost: 0
```

### Trade-offs

**Advantages**

* Preserves measurement integrity.
* Prevents misleading benchmark results.
* Makes limitations visible to downstream consumers.

**Disadvantages**

* Reports require consumers to handle missing values.

### Consequence

The evaluation system favors honest incomplete measurements over artificially complete reports.

---

## 9. Keep Web Search as a Stub

### Decision

The web-search tool remains a stub in the starter project rather than introducing a real external search dependency.

### Context

The project demonstrates tool calling and agent orchestration, but external search infrastructure would introduce additional API credentials, dependencies, network variability, and evaluation complexity.

### Why

The primary objective is to demonstrate the agent/tool architecture rather than build a production search engine.

Keeping the tool as a stub allows the rest of the system to remain deterministic and easy to understand.

### Trade-offs

**Advantages**

* Minimal external dependencies.
* Easier local development.
* Easier testing.
* Lower operational complexity.
* Keeps the focus on agent architecture.

**Disadvantages**

* Does not represent real-world search behavior.
* Tool execution results are limited.
* Some end-to-end scenarios cannot be evaluated realistically.

### Consequence

The limitation is explicitly documented instead of being hidden behind a simulated production implementation.

---

## 10. Keep Conversation State Lightweight

### Decision

Conversation history is represented using a lightweight `ConversationManager` closely aligned with the Anthropic message format.

### Context

The project needs multi-turn conversation support without introducing a persistence or state-management framework.

### Why

A small abstraction is sufficient for a starter project and keeps the underlying API representation visible.

### Trade-offs

**Advantages**

* Simple mental model.
* Minimal abstraction.
* Easy to inspect and modify.
* Closely maps to the underlying API.

**Disadvantages**

* No persistent storage.
* No automatic context-window management.
* No distributed state management.

### Consequence

The project provides a clear foundation for conversation management without pretending to solve production-scale state management.

---

# Decision Principles

The implementation follows several broader principles:

### 1. Prefer explicit behavior over hidden framework behavior

Important agent mechanics remain visible in the code.

### 2. Optimize for reproducibility in evaluation

When possible, measurements are deterministic and independently inspectable.

### 3. Separate execution from observability

The agent should not need to know that it is being benchmarked.

### 4. Measure engineering constraints, not only task success

Quality alone is insufficient. The evaluation also considers:

* Latency
* Token usage
* Estimated cost
* Tool selection
* Tool execution
* Failure modes

### 5. Document limitations instead of hiding them

The project intentionally identifies limitations such as:

* No LLM judge.
* Stubbed web search.
* Live-model non-determinism.
* Heuristic tool-execution evaluation.
* Real API costs during evaluation.

---

# Summary

The architecture intentionally favors **simplicity, transparency, reproducibility, and measurable behavior** over framework complexity.

The main design philosophy is:

> Build the smallest system that makes agent behavior observable, testable, and understandable.

These decisions are appropriate for a starter/reference project and provide a foundation for adding more production-oriented capabilities such as persistent state, retries, tracing, real external tools, advanced evaluation methods, and distributed execution.
