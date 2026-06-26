# Verification

`scripts/verify_port.py <port-dir>` is the "error-free" guarantee. It runs four stages, cheapest first, and prints PASS/FAIL for each plus a final summary. Run it after every translation pass and fix until green.

## Stages

1. **Syntax** — `compile(source, path, "exec")` on every `.py` under the port dir. Any `SyntaxError` is reported with file and line.

2. **Imports (mocked)** — each module is imported in a fresh subprocess with a fake `anthropic` package injected via `sys.modules` before import. This means:
   - no real API key needed,
   - no network calls,
   - missing names, bad imports, and leftover `google.adk` imports surface as `ImportError`/`ModuleNotFoundError`.
   The fake exposes `Anthropic`, `AsyncAnthropic`, and the response shape the runtime expects.

3. **ADK residue scan** — greps every `.py` for `google.adk`, `from google import adk`, common ADK symbols (`LlmAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`, `FunctionTool`, `AgentTool`), the MCP-toolset wiring (`MCPToolset`, `StdioServerParameters`), and `google.genai` (the `types.Content`/`types.Part` helpers). Any hit in live code (comments/strings are stripped first) fails the stage — these dependencies must be gone.

4. **Mocked dry run** — if an entry point is detected (a top-level `main`/`run`/`pipeline`/`orchestrate` function, **sync or `async def`**), the script executes it against a `FakeAnthropic` client. Coroutine entry points are awaited with `asyncio.run` — a coroutine that's created but never awaited would otherwise PASS without running the orchestration at all (the common ADK shape, since ADK is `run_async`-based). that returns scripted responses: first a tool_use block (if the agent has tools) then a final text block. This exercises orchestration, tool dispatch, message threading, and termination without spending tokens. Failures (unhandled exceptions, infinite-loop guard trip, KeyErrors on tool dispatch) are reported with traceback.

## How the mock works

The fake client mimics the subset of the SDK the runtime touches:
- `messages.create(...)` returns an object with `.content` (a list of blocks with `.type`, `.text`, `.name`, `.input`, `.id`) and `.stop_reason`.
- It alternates: if `tools` were passed and it hasn't "used" one yet this call-sequence, it returns a `tool_use` block; otherwise a `text` block with `stop_reason="end_turn"`.
- `AsyncAnthropic.messages.create` is the async twin.

This is enough to drive any port built on `agent_runtime.py`. If a port uses the SDK directly in an unusual way, extend `FakeAnthropic` in the script (it's small and documented inline).

## Extending the dry run

Auto-detection covers the common cases. For an unusual entry point, pass `--entry "module:function"` to point the verifier at it, or `--entry-arg "some input"` to supply the initial query. If a port needs richer fake responses (specific tool outputs to flow correctly), add cases to `FakeAnthropic._next_response()`.

## Live smoke test

Separate from `verify_port.py`. Only when the user asks and `ANTHROPIC_API_KEY` is set: run the real entry point once with a trivial input and the cheapest model (`claude-haiku-4-5-20251001`) to confirm real connectivity. Keep it to a single short call.

## Interpreting results
- All four stages PASS → the port is import-clean, ADK-free, and runs end-to-end under mock. That's the deliverable bar.
- Any FAIL → read the stage output, fix the specific file, re-run. Don't hand back a port with a failing stage.
