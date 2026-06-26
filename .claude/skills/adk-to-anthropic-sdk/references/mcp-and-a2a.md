# MCP Toolsets & A2A → Anthropic SDK

ADK projects often pull tools from an **MCP server** and/or expose agents over the **A2A**
(agent-to-agent) protocol. These are not plain `FunctionTool`s and need their own handling.
Read this when the source imports `MCPToolset`, `StdioServerParameters`, `mcp_tool`, or any
A2A server/client (`a2a`, agent cards, `/.well-known/agent.json`, task endpoints).

## MCP toolsets (was `MCPToolset.from_server`)

ADK loads MCP tools dynamically:

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

tools, exit_stack = await MCPToolset.from_server(
    connection_params=StdioServerParameters(command="python", args=["./servers/server_mcp.py"]),
)
agent = LlmAgent(model="gemini-2.5-pro", name="sql", instruction="...", tools=tools)
```

You have **two faithful ports**. Pick by how the MCP server is reached:

### Option A — native Anthropic MCP connector (preferred when the server is remote/HTTP)
The Anthropic Messages API can talk to MCP servers directly via the `mcp_servers` parameter
(the MCP connector). The model calls MCP tools without you writing a tool-use dispatch loop
for them. Use this when the MCP server is reachable over HTTP/SSE.

```python
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=instruction,
    messages=messages,
    mcp_servers=[{"type": "url", "url": "https://your-mcp-server/sse", "name": "security-hub"}],
)
```
Confirm the exact `mcp_servers` shape and any required beta header against `claude-api`
(load that skill) — the connector's request shape and headers change, so don't hardcode from
memory.

### Option B — local MCP client + tool bridge (when the server is stdio/local)
The repo's `StdioServerParameters(command="python", args=["./servers/server_mcp.py"])` spawns a
**local** stdio MCP server — the API connector can't reach a subprocess on your machine. Bridge
it yourself with the official `mcp` Python package:

1. Start the server as an MCP client session (`mcp.client.stdio.stdio_client`).
2. `await session.list_tools()` → convert each MCP tool's `inputSchema` into an Anthropic tool
   schema (the schema is already JSON Schema — usually a direct pass-through to `input_schema`).
3. In your tool-use loop, dispatch each `tool_use` by calling `await session.call_tool(name, input)`
   and feed the result back as a `tool_result`.

This keeps the same MCP server the ADK app used; only the *client* changes from ADK to your loop.
`agent_runtime.py`'s loop already handles dispatch — register MCP-backed handlers that call
`session.call_tool`.

> Either way: `MCPToolset`/`StdioServerParameters` must be **gone** from the port (the residue
> scan now fails on them). Record which option you chose, and the server's transport, in
> `INVENTORY.md`.

## A2A (agent-to-agent protocol)

A2A exposes an agent as a network service (an agent card at `/.well-known/agent.json`, task
submission/streaming endpoints) so *other* agents call it over HTTP. This is a **transport/
deployment** concern, not an LLM concern — the Anthropic SDK has no A2A equivalent.

Decide with the user, and write the decision in `INVENTORY.md`:

- **In-process port (default).** If A2A was only used to wire local sub-agents together, drop the
  protocol entirely and call the ported agents as plain Python (sequential/parallel/delegation
  recipes in `orchestration.md`). This is almost always what's wanted.
- **Keep the service boundary.** If agents genuinely run as separate networked services, port each
  agent's *logic* to the Anthropic SDK but keep a thin HTTP layer (e.g. FastAPI) in front. The A2A
  framing is out of scope for this skill — port the agent behind it and flag the boundary so the
  user re-wires transport if they need it.

Do **not** silently delete an A2A server and pretend the topology is unchanged — call it out.

## Other non-ADK tool sources

`ToolboxSyncClient` / `toolbox_core` (`load_toolset(...)`) and similar dynamic tool registries are
*not* ADK — they're separate deps that return a list of tools at runtime. The skill doesn't have to
remove them, but the Anthropic loop needs explicit schemas, so either keep the client and convert
each loaded tool to an Anthropic schema, or replace it with the underlying functions. Note the
choice in `INVENTORY.md`.
