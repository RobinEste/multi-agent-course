---
name: adk-to-anthropic-sdk
description: Convert Google ADK (Agent Development Kit) multi-agent Python projects into equivalent code that runs directly on the Anthropic SDK (the `anthropic` Python package). Use this skill whenever the user points at a folder, repo, or set of Python files built with Google ADK — anything importing `google.adk`, using `Agent`/`LlmAgent`, `SequentialAgent`, `ParallelAgent`, `LoopAgent`, `Runner`, `FunctionTool`, ADK `tools`, `sub_agents`, or `session`/`Runner` orchestration — and wants it rewritten, ported, migrated, or "translated" to the Anthropic SDK. Trigger this even if the user just says "convert this agent project to use Claude/Anthropic," "port my ADK code," "migrate off Google ADK," or "make this run on the Anthropic API," and even when they don't name ADK explicitly but the code clearly uses it. The skill takes a project folder, produces a working Anthropic-SDK port, and verifies it is import-clean, syntactically valid, and passes a mocked dry run before optionally doing a live API smoke test.
---

# ADK → Anthropic SDK Converter

Port a Google ADK multi-agent project to run on the raw Anthropic Python SDK, preserving behavior (agent roles, tools, orchestration topology, control flow) while removing the `google.adk` dependency. Then prove the port works.

## Workflow

Follow these phases in order. Don't skip the analysis phase — ADK projects encode their agent graph implicitly, and getting the topology wrong is the most common failure.

### Phase 1 — Inventory the source project

1. Locate the project. The user gives you a folder (often under `/mnt/user-data/uploads`). Copy it to a writable workspace (`/home/claude/port/`) before touching anything — never edit the read-only original.
2. Map the codebase: list all `.py` files, find every `google.adk` import, and identify entry points (files with `Runner`, `__main__`, or a `root_agent`).
3. Build an **agent inventory**. For each ADK agent capture: its name, `model`, `instruction`/`description` (becomes the system prompt), `tools`, and `sub_agents`. Record how agents connect — this is the orchestration topology.
4. Identify the orchestration pattern. ADK ships a few; see `references/adk-patterns.md` for the full mapping. The common ones: a single `LlmAgent` with tools, `SequentialAgent` (pipeline), `ParallelAgent` (fan-out/gather), `LoopAgent` (iterate until a condition), and agent-as-tool / `sub_agents` delegation.
5. Inventory tools: ADK `FunctionTool`s are plain Python functions plus a schema. They port almost directly to Anthropic tool-use definitions — keep the function bodies, regenerate the schema.
6. Flag the protocol layer. If the project imports `MCPToolset`/`StdioServerParameters` (tools from an MCP server) or uses A2A (agent cards, `/.well-known/agent.json`, networked agent services), those are **not** plain tools — they need dedicated handling. See `references/mcp-and-a2a.md` and record the transport (local stdio vs. remote HTTP) and your port decision in `INVENTORY.md`.

Write the inventory to `port/INVENTORY.md` so the mapping is explicit and reviewable before you write code.

### Phase 2 — Choose the target shape

Pick the simplest Anthropic-SDK structure that preserves behavior. Don't over-engineer — a three-agent ADK pipeline should not become a framework.

- **Single agent + tools** → one `messages.create` tool-use loop. See `references/sdk-tool-loop.md`.
- **Sequential / pipeline** → call each agent loop in order, threading output → input. See `references/orchestration.md`.
- **Parallel fan-out** → run agent loops concurrently (`asyncio.gather` with `AsyncAnthropic`), then merge.
- **Loop until condition** → wrap an agent loop in a `while` with the ADK exit condition.
- **Delegation / sub-agents** → expose each sub-agent as a tool the orchestrator can call, or as a direct function call when delegation is static.
- **MCP tools / A2A services** → port the MCP toolset (native `mcp_servers` connector for remote servers, or a local MCP client bridge for stdio servers) and decide whether A2A boundaries collapse in-process or stay as a thin HTTP layer. See `references/mcp-and-a2a.md`.

Watch for **short-circuit control flow** inside a pipeline — e.g. a guard/judge sub-agent that returns `"BLOCKED"` to stop the chain. Preserve that conditional exactly; a naive output→input thread silently loses it.

Read `references/adk-patterns.md` and the matching orchestration reference before writing code. Reuse the helpers in `assets/agent_runtime.py` rather than reinventing the tool-use loop each time — copy that file into the port and build on it.

### Phase 3 — Translate

1. Copy `assets/agent_runtime.py` into `port/`. It provides a reusable `Agent` class and `run_agent()` tool-use loop on top of the Anthropic SDK so the ported code stays small and consistent.
2. Recreate each ADK agent as an `Agent` instance (system prompt from `instruction`, tools from the ported functions, model mapped per `references/model-mapping.md`).
3. Port tools: keep each function body verbatim; generate an Anthropic tool schema from its signature/docstring (the runtime has a helper, or write explicit schemas for clarity).
4. Reconstruct the orchestration in a top-level entry point that mirrors the original control flow.
5. Map models: ADK model strings (e.g. Gemini names, or `LiteLlm(...)`) map to current Anthropic model IDs per `references/model-mapping.md`. Default to `claude-sonnet-4-6` unless the source clearly wanted the most capable (`claude-opus-4-8`) or cheapest/fastest (`claude-haiku-4-5-20251001`) tier.
6. Preserve I/O contracts: same CLI args, same function names for public entry points, same return shapes, so the port is a drop-in where possible.
7. Write a `requirements.txt` (`anthropic`, plus whatever non-ADK deps the original used) and a short `README_PORT.md` explaining what changed.

Keep the original file structure where reasonable so a reviewer can diff mentally.

### Phase 4 — Verify (this is the "error-free" guarantee)

Verification is layered, cheapest first. Run `scripts/verify_port.py <port-dir>`, which performs:

1. **Syntax check** — `compile()` every `.py` file. Fails loudly with file + line on any `SyntaxError`.
2. **Import check** — import each module in a subprocess with a **mocked `anthropic` package** injected, so no network or key is needed. Catches missing names, bad signatures, leftover `google.adk` references.
3. **ADK-residue scan** — grep for any surviving `google.adk` / ADK symbols and fail if found (the whole point is removing that dependency).
4. **Mocked dry run** — if the project exposes a detected entry point, execute it against a fake Anthropic client that returns canned tool-use and text responses, exercising the orchestration end-to-end without spending tokens.

The script prints a clear PASS/FAIL per stage and a final summary. Iterate: read the failure, fix the port, re-run, until all stages pass. See `references/verification.md` for how the mock works and how to extend the dry run for unusual entry points.

**Live smoke test (optional, only if the user asks and a key is present):** if `ANTHROPIC_API_KEY` is set and the user wants real confirmation, run the entry point once with a tiny input and the cheapest model. Keep it minimal — the goal is "it really talks to the API," not a full eval.

### Phase 5 — Deliver

Present the ported folder, the `INVENTORY.md`, the verification output, and a brief changelog. If `present_files` is available, present the port directory's key files. Tell the user exactly how to run it (`pip install -r requirements.txt`, set `ANTHROPIC_API_KEY`, run the entry point).

## Principles

- **Behavior-preserving, not framework-preserving.** The user wants Claude-powered agents that do the same thing — not a clone of ADK's abstractions on top of Anthropic.
- **Smallest faithful structure wins.** Prefer plain functions and a thin runtime over a new framework.
- **Verification is not optional.** A port that imports but was never dry-run is not done. Always run `verify_port.py` and report results.
- **Never edit the original.** Always work on a copy.
- **When the ADK topology is ambiguous**, state your interpretation in `INVENTORY.md` and ask the user to confirm rather than guessing silently.

## Reference files

- `references/adk-patterns.md` — ADK agent types & orchestration → Anthropic equivalents (read first).
- `references/sdk-tool-loop.md` — the canonical Anthropic tool-use loop.
- `references/orchestration.md` — sequential / parallel / loop / delegation recipes.
- `references/mcp-and-a2a.md` — porting MCP toolsets (native connector or local client bridge) and A2A services.
- `references/model-mapping.md` — Gemini/LiteLlm model strings → Anthropic model IDs.
- `references/verification.md` — how `verify_port.py` works and how to extend it.
- `assets/agent_runtime.py` — reusable Agent class + tool-use loop to copy into ports.
- `scripts/verify_port.py` — the layered verifier.
