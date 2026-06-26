# Anthropic Tool-Use Loop

The core primitive every ported agent uses. The model may ask to call tools; you run them and feed results back until it stops requesting tools.

## Minimal shape

```python
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY

def run_agent(system, tools, tool_handlers, user_input, model="claude-sonnet-4-6", max_turns=10):
    messages = [{"role": "user", "content": user_input}]
    for _ in range(max_turns):
        resp = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system,
            tools=tools,             # list of tool schemas (may be empty)
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            # final answer: concatenate text blocks
            return "".join(b.text for b in resp.content if b.type == "text")

        # run each requested tool, collect results
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                handler = tool_handlers[block.name]
                try:
                    output = handler(**block.input)
                    result = {"type": "tool_result", "tool_use_id": block.id,
                              "content": str(output)}
                except Exception as e:
                    result = {"type": "tool_result", "tool_use_id": block.id,
                              "content": f"Error: {e}", "is_error": True}
                tool_results.append(result)
        messages.append({"role": "user", "content": tool_results})
    return "".join(b.text for b in messages[-1]["content"] if getattr(b, "type", None) == "text")
```

## Key rules
- Append the assistant's **full `content` list** (text + tool_use blocks) back into messages, not just text.
- Every `tool_use` block in a turn must be answered by a `tool_result` with the matching `tool_use_id` in the next user message — answer all of them before the next `create` call.
- `max_tokens` is required on every call.
- Set `system` as a top-level kwarg, not as a message.
- Cap turns (`max_turns`) so a misbehaving loop can't run forever — mirror any ADK `max_iterations` here.

## Async variant
Use `AsyncAnthropic` and `await client.messages.create(...)` for parallel orchestration. Tool handlers can stay sync (call them directly) or be awaited if they're coroutines.

`agent_runtime.py` packages all of this so ports don't copy the loop by hand.
