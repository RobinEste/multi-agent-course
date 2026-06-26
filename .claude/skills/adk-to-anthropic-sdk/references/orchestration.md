# Orchestration Recipes

How to rebuild each ADK workflow agent on top of `run_agent()` (from `agent_runtime.py`). Pick the one matching the topology you recorded in `INVENTORY.md`.

## Sequential (was `SequentialAgent`)

Each agent feeds the next. Replace ADK session `output_key` with a plain dict.

```python
def pipeline(query):
    state = {}
    state["research"] = researcher.run(query)
    state["draft"]    = writer.run(f"Write based on:\n{state['research']}")
    state["final"]    = editor.run(f"Polish:\n{state['draft']}")
    return state["final"]
```

Where `researcher`, `writer`, `editor` are `Agent` instances. Thread the prior output into the next prompt exactly as ADK passed state.

**Short-circuit guards.** If a stage can stop the pipeline — e.g. a security/judge agent that
returns `"BLOCKED"` so downstream stages don't run — port that conditional, don't just thread
output→input:

```python
def secure_pipeline(query):
    verdict = judge.run(query)
    if "BLOCKED" in verdict:
        return verdict                      # stop early, exactly as ADK did
    result = sql_agent.run(query)
    return mask_agent.run(result)
```

Losing the guard is a silent behavior change — the masker/SQL stage would run on input the judge
meant to reject.

## Parallel (was `ParallelAgent`)

Run independent agents concurrently with the async runtime, then merge.

```python
import asyncio

async def fan_out(query):
    results = await asyncio.gather(
        agent_a.arun(query),
        agent_b.arun(query),
        agent_c.arun(query),
    )
    return merge(results)   # however ADK combined them (concat, vote, summarizer agent)
```

If ADK fed the gathered outputs into a final synthesizer agent, call that synthesizer after the gather.

## Loop (was `LoopAgent`)

Repeat until a cap or an exit condition. ADK loops exit on `max_iterations` or an escalation signal (often a tool that sets `escalate=True`, or a checker agent returning a sentinel).

```python
def refine(initial, max_iterations=5):
    current = initial
    for i in range(max_iterations):
        current = refiner.run(f"Improve this:\n{current}")
        if is_good_enough(current):   # port the ADK exit predicate
            break
    return current
```

Preserve the original termination logic precisely — both the iteration cap and the condition.

## Delegation (was `sub_agents` / `AgentTool`)

The orchestrator decides at runtime which sub-agent to invoke. Expose each sub-agent as a tool.

```python
def make_delegation_tools():
    schemas = [
        {"name": "ask_billing", "description": "Handle billing questions.",
         "input_schema": {"type": "object",
                          "properties": {"query": {"type": "string"}},
                          "required": ["query"]}},
        {"name": "ask_tech", "description": "Handle technical support.",
         "input_schema": {"type": "object",
                          "properties": {"query": {"type": "string"}},
                          "required": ["query"]}},
    ]
    handlers = {
        "ask_billing": lambda query: billing_agent.run(query),
        "ask_tech":    lambda query: tech_agent.run(query),
    }
    return schemas, handlers

schemas, handlers = make_delegation_tools()
answer = orchestrator.run(user_query, extra_tools=schemas, extra_handlers=handlers)
```

The orchestrator's tool-use loop now delegates by calling these tools. If delegation in the source was static (always the same order, no LLM decision), just call the sub-agents directly instead — simpler and faithful.

## Choosing
- One agent, some tools → no orchestration file, just `agent.run(...)`.
- Fixed order → Sequential.
- Independent + merge → Parallel.
- Repeat-until → Loop.
- LLM-decided routing → Delegation.

Combine freely (a pipeline whose middle step is a loop, etc.) to match the source tree.
