# Module 06 — Recap & Preview (15-Minute Warm-Up)

<!-- INSTRUCTOR: A quick "before class" bridge. Recaps Module 05 and previews Module 06.
     This is the LAST module in the course — there's no Module 07 to preview at the end,
     so close with a course-wrap note instead of a "coming up next" pointer. -->

## Last time (Module 05 — Multi-Agent Systems & the Protocol Layer)
The big ideas you should still have in your head:
- A **protocol layer** (MCP, A2A, ADK) replaces N² point-to-point glue with shared standards.
- **ADK defines** agents (`LlmAgent`, `SequentialAgent`, `Runner`), **A2A connects** them as
  network services (agent cards + JSON-RPC), **MCP feeds** them discoverable tools.
- The capstone wraps its support agent in a security **pipeline**: sanitize → A2A Judge →
  agent → A2A Masker — each layer independently swappable.

**Quick gut-check:** In the capstone, is the A2A Security Judge a function call inside the
agent's code, or something else? What's different about calling it?

## How it connects
Module 5's entire pipeline — the ADK agent, its MCP tools, its Mem0 memory, and its
sanitize → Judge → agent → Masker security chain — doesn't get replaced in Module 6. It gets
**wrapped in speech**, two different ways. Cascade keeps that exact pipeline intact and adds
STT/TTS at the edges. Speech-to-speech fuses it into one live audio model — and in doing so,
turns the Judge from a pre-agent gate into a post-hoc, concurrent check. Same security pipeline,
new constraint: the model can now hear the user before any check has run.

## Coming up (Module 06 — Voice Agents)
What you'll be able to do after today:
- Explain what turn-taking and latency budgets add on top of a text agent
- Contrast **cascade** (discrete, inspectable, additive latency) vs. **speech-to-speech**
  (fused, faster, weaker security guarantee)
- Read the benchmark that holds the agent fixed and isolates architecture as the only variable

**Watch for:** why speech-to-speech can't gate input the way cascade does — it's not a missing
feature, it's a direct consequence of the model hearing raw audio before any text exists to
check. That one causal chain (audio-first → no pre-check → post-hoc guardrail) explains most of
the trade-offs in this module.

## If you only remember one thing walking into class
> Cascade trades latency for control; speech-to-speech trades control for latency and
> naturalness. Neither is "better" — the benchmark exists precisely because the right answer
> depends on what you're willing to give up.

---

**This is the last module in the course.** There's no Module 07 to preview — after today, the
warm-up is done. If you want a synthesis session instead of a fresh module, ask to review across
all six modules or to be quizzed on the ones you marked as weak spots in `learner-progress.md`.
