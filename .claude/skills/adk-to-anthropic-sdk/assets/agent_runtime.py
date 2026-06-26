"""
agent_runtime.py — reusable Agent runtime on top of the Anthropic SDK.

Copy this file into a ported project. It provides:
  - Agent: a configured agent (system prompt, model, tools, handlers)
  - run_agent / Agent.run: synchronous tool-use loop
  - Agent.arun: async tool-use loop (for parallel orchestration)
  - tool_from_function: build an Anthropic tool schema from a Python function

The point is to keep ports small: recreate each ADK agent as an Agent and
wire orchestration with plain Python, instead of re-implementing the tool
loop everywhere.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

try:
    from anthropic import Anthropic, AsyncAnthropic
except ImportError:  # allows static import-checks without the package installed
    Anthropic = AsyncAnthropic = None  # type: ignore

_PY_TO_JSON = {
    str: "string", int: "integer", float: "number",
    bool: "boolean", list: "array", dict: "object",
}


def tool_from_function(func: Callable) -> dict:
    """Generate an Anthropic tool schema from a function's signature + docstring.

    For complex types, prefer writing the schema explicitly.
    """
    sig = inspect.signature(func)
    props, required = {}, []
    for name, param in sig.parameters.items():
        ann = param.annotation
        json_type = _PY_TO_JSON.get(ann, "string")
        props[name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)
    doc = (func.__doc__ or func.__name__).strip().split("\n")[0]
    return {
        "name": func.__name__,
        "description": doc,
        "input_schema": {"type": "object", "properties": props, "required": required},
    }


def _final_text(content) -> str:
    return "".join(b.text for b in content if getattr(b, "type", None) == "text")


class Agent:
    """A single Claude-powered agent: system prompt + model + tools."""

    def __init__(
        self,
        name: str,
        system: str,
        model: str = "claude-sonnet-4-6",
        tools: list[dict] | None = None,
        handlers: dict[str, Callable] | None = None,
        max_tokens: int = 4096,
        max_turns: int = 10,
        client: Any = None,
        async_client: Any = None,
    ):
        self.name = name
        self.system = system
        self.model = model
        self.tools = tools or []
        self.handlers = handlers or {}
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self._client = client
        self._async_client = async_client

    # ---- tool registration helper ----
    def add_function_tool(self, func: Callable):
        self.tools.append(tool_from_function(func))
        self.handlers[func.__name__] = func
        return self

    def _get_client(self):
        if self._client is None:
            if Anthropic is None:
                raise RuntimeError("anthropic package not installed")
            self._client = Anthropic()
        return self._client

    def _get_async_client(self):
        if self._async_client is None:
            if AsyncAnthropic is None:
                raise RuntimeError("anthropic package not installed")
            self._async_client = AsyncAnthropic()
        return self._async_client

    def _dispatch(self, block) -> dict:
        handler = self.handlers.get(block.name)
        if handler is None:
            return {"type": "tool_result", "tool_use_id": block.id,
                    "content": f"Error: no handler for tool '{block.name}'",
                    "is_error": True}
        try:
            output = handler(**(block.input or {}))
            return {"type": "tool_result", "tool_use_id": block.id,
                    "content": str(output)}
        except Exception as e:  # surface tool errors to the model
            return {"type": "tool_result", "tool_use_id": block.id,
                    "content": f"Error: {e}", "is_error": True}

    # ---- synchronous run ----
    def run(self, user_input: str,
            extra_tools: list[dict] | None = None,
            extra_handlers: dict[str, Callable] | None = None) -> str:
        client = self._get_client()
        tools = self.tools + (extra_tools or [])
        handlers = {**self.handlers, **(extra_handlers or {})}
        messages = [{"role": "user", "content": user_input}]
        for _ in range(self.max_turns):
            kwargs = dict(model=self.model, max_tokens=self.max_tokens,
                          system=self.system, messages=messages)
            if tools:
                kwargs["tools"] = tools
            resp = client.messages.create(**kwargs)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                return _final_text(resp.content)
            results = [self._dispatch(b) for b in resp.content
                       if getattr(b, "type", None) == "tool_use"]
            messages.append({"role": "user", "content": results})
        return _final_text(messages[-1]["content"]) if messages else ""

    # ---- async run (for ParallelAgent ports) ----
    async def arun(self, user_input: str,
                   extra_tools: list[dict] | None = None,
                   extra_handlers: dict[str, Callable] | None = None) -> str:
        client = self._get_async_client()
        tools = self.tools + (extra_tools or [])
        handlers = {**self.handlers, **(extra_handlers or {})}
        messages = [{"role": "user", "content": user_input}]
        for _ in range(self.max_turns):
            kwargs = dict(model=self.model, max_tokens=self.max_tokens,
                          system=self.system, messages=messages)
            if tools:
                kwargs["tools"] = tools
            resp = await client.messages.create(**kwargs)
            messages.append({"role": "assistant", "content": resp.content})
            if resp.stop_reason != "tool_use":
                return _final_text(resp.content)
            results = []
            for b in resp.content:
                if getattr(b, "type", None) == "tool_use":
                    h = handlers.get(b.name)
                    if h is None:
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": f"Error: no handler for '{b.name}'",
                                        "is_error": True})
                        continue
                    try:
                        out = h(**(b.input or {}))
                        if inspect.isawaitable(out):
                            out = await out
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": str(out)})
                    except Exception as e:
                        results.append({"type": "tool_result", "tool_use_id": b.id,
                                        "content": f"Error: {e}", "is_error": True})
            messages.append({"role": "user", "content": results})
        return _final_text(messages[-1]["content"]) if messages else ""


# Convenience functional form mirroring the reference doc.
def run_agent(system, tools, tool_handlers, user_input,
              model="claude-sonnet-4-6", max_turns=10, max_tokens=4096):
    agent = Agent(name="agent", system=system, model=model, tools=tools or [],
                  handlers=tool_handlers or {}, max_turns=max_turns,
                  max_tokens=max_tokens)
    return agent.run(user_input)
