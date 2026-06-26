# ADK Patterns → Anthropic SDK Equivalents

Google ADK structures an app as a tree of agents. To port it, identify which ADK construct each agent uses, then map to the Anthropic equivalent. Read this before writing code.

## Table of contents
- Agent types
- Orchestration agents
- Tools
- Sessions & state
- Runner / entry points
- Mapping cheat sheet

## Agent types

### `LlmAgent` / `Agent`
The workhorse: an LLM with an `instruction` (system prompt), a `model`, and optional `tools` and `sub_agents`.

```python
from google.adk.agents import LlmAgent
agent = LlmAgent(
    name="researcher",
    model="gemini-2.0-flash",
    instruction="You research topics and summarize findings.",
    tools=[search_tool],
)
```

→ Anthropic equivalent: one `Agent` (from `agent_runtime.py`) whose `system` is the `instruction`, whose `tools` are ported tool schemas, run through `run_agent()` (a `messages.create` tool-use loop). The `model` maps via `model-mapping.md`.

## Orchestration agents

ADK provides workflow agents that contain `sub_agents`. These define control flow, not LLM calls themselves.

### `SequentialAgent`
Runs sub-agents in order; each sees prior output (often via shared session state keyed by `output_key`).
→ Call each ported agent loop in sequence, threading the previous result into the next agent's input message. See `orchestration.md` → Sequential.

### `ParallelAgent`
Runs sub-agents concurrently, results gathered.
→ `asyncio.gather` over async agent loops using `AsyncAnthropic`, then merge results. See `orchestration.md` → Parallel.

### `LoopAgent`
Repeats its sub-agent(s) until `max_iterations` or an escalation/exit signal.
→ A `while` loop around the agent call with the same termination condition (iteration cap and/or a checked exit predicate). See `orchestration.md` → Loop.

### Agent-as-tool / `sub_agents` delegation
An orchestrator `LlmAgent` lists other agents in `sub_agents` (or wraps them with `AgentTool`) and decides at runtime which to invoke.
→ Expose each sub-agent as an Anthropic tool whose handler runs that sub-agent's loop and returns its output. The orchestrator's tool-use loop then performs delegation naturally. See `orchestration.md` → Delegation.

## Tools

ADK `FunctionTool` (or a bare function passed to `tools=`) = a Python function whose signature + docstring define the schema. The model calls it; ADK runs it and feeds the result back.

→ Keep the function body unchanged. Produce an Anthropic tool definition:
```python
{
  "name": "fn_name",
  "description": "<docstring summary>",
  "input_schema": { "type": "object", "properties": {...}, "required": [...] },
}
```
Map Python types: `str`→`string`, `int`→`integer`, `float`→`number`, `bool`→`boolean`, `list`→`array`, `dict`→`object`. `agent_runtime.py` has `tool_from_function()` to autogenerate this from a signature; prefer explicit schemas when types are complex.

ADK special tools (`google_search`, `built_in_code_execution`, etc.) have no 1:1 Anthropic builtin in the raw SDK — reimplement as a normal tool (e.g. a real search function) or note the gap in `INVENTORY.md`.

**MCP toolsets** (`MCPToolset.from_server`, `StdioServerParameters`) are a different beast — tools
loaded dynamically from an MCP server, not local functions. Port via the native Anthropic
`mcp_servers` connector (remote servers) or a local MCP client bridge (stdio servers). See
`references/mcp-and-a2a.md`. The verifier's residue scan fails if `MCPToolset`/`StdioServerParameters`
survive in the port.

## Sessions & state

ADK uses `SessionService` + `session.state` (a dict) to pass data between agents, often via `output_key`. The raw Anthropic SDK is stateless per call.
→ Replace session state with explicit Python variables / a plain dict passed between agent calls. `output_key="foo"` means "store this agent's final text under `foo`" — model it as `state["foo"] = result`.

## Runner / entry points

ADK runs agents via `Runner(agent=..., session_service=...).run(...)` or `runner.run_async(...)`, yielding events.
→ Replace with a direct call to your top-level orchestration function. Preserve the same inputs (query string, args) and final output. Keep a `if __name__ == "__main__":` CLI if the original had one.

## Mapping cheat sheet

| ADK | Anthropic SDK port |
|-----|--------------------|
| `LlmAgent`/`Agent` | `Agent` + `run_agent()` tool-use loop |
| `instruction` | `system` prompt |
| `model="gemini-..."` | Anthropic model id (see model-mapping.md) |
| `FunctionTool` / function | tool schema + unchanged handler |
| `SequentialAgent` | ordered calls, thread output→input |
| `ParallelAgent` | `asyncio.gather` over async loops |
| `LoopAgent` | `while` with iteration cap / exit check |
| `sub_agents` / `AgentTool` | sub-agent exposed as a tool, or direct call |
| `session.state` / `output_key` | plain dict / variables |
| `Runner.run` | top-level orchestration function |
