# Agent Engineering Bootcamp — Pitch Deck

*Slide-by-slide overview · 11 slides · ~6 weeks, one 2-hour live session per week*

---

## Slide 1 — Title / Intro

**Agent Engineering Bootcamp**
*Build, evaluate, and harden production agents — in 6 weeks.*

- A hands-on, build-every-week bootcamp for engineers who already write Python and have touched LLM APIs.
- Six live 2-hour sessions. Every week ends with a working artifact you wrote yourself.
- You leave with the **judgment** that separates engineers who ship agents from engineers who follow tutorials.

> *Speaker note: open on the promise — by week 6 you've shipped a ReAct loop, a quantized model, an agentic RAG pipeline, a voice agent, a multi-agent system, and an eval harness around all of it.*

---

## Slide 2 — The Problem We're Solving

**Everyone is "building agents." Most are wiring prompts and hoping.**

- Tutorials show the happy path; production breaks on the trajectory, the latency, and the cost.
- Teams reach for frameworks before they understand the loop underneath — and can't debug when it fails.
- "Just use RAG" / "just go multi-agent" / "ship it" — decisions made on vibes, not numbers.

**This course replaces vibes with patterns, instincts, and measurement.**

> *Speaker note: name the pain the audience already feels. The course is the cure.*

---

## Slide 3 — What You'll Walk Away With

**Six real artifacts + four durable skills.**

| Artifacts (you build these) | Skills (you keep these) |
|---|---|
| A from-scratch ReAct loop | Pattern fluency — recognize loops & topologies, not recipes |
| A quantized, deployed model | Production instincts — latency, cost, caching, guardrails by design |
| An agentic RAG pipeline + cache | Evaluation discipline — answer "is it good?" with numbers |
| A live voice agent | A real reference point — the Claude Code harness teardown |
| A 2-agent orchestrator system | |
| An eval harness over all of it | |

> *Speaker note: the table is the whole value prop in one glance.*

---

## Slide 4 — Week 1: The World of Agents + ReAct + Claude Harness

**Demystify what an agent actually is.**

- The agent loop: perceive → think → act — and why it changes how you design software.
- Agent vs. workflow vs. chatbot: where agents fit, and where they don't.
- The **ReAct pattern**: interleaved reasoning and action; debugging via the trace.
- **Flagship teardown:** the Claude Code harness as a real production agent — tool loop, system-prompt anatomy, planning behavior.
- **Lab:** build a 50-line ReAct loop from scratch, no framework.

*Walk away with:* a working loop you wrote line-by-line, and the confidence that production agents are well-engineered loops, not magic.

---

## Slide 5 — Week 2: LLM Quantization + Optimization

**Make the agent loop fast and cheap enough to ship.**

- Why quantization matters for agent economics: latency, cost, deployment.
- Methods compared: GPTQ vs. GGUF vs. QLoRA — accuracy vs. throughput tradeoffs.
- KV caching mechanics and speculative-decoding intuition.
- Hosting paths: Ollama (local) and RunPod (cloud).
- **Lab:** quantize a model, deploy it, and benchmark inference.

*Walk away with:* a deployed quantized model, intuition for where latency really comes from, and cost numbers you can take to finance.

---

## Slide 6 — Week 3: Agentic RAG + Caching

**Retrieval as a tool the agent decides to use — not a bolt-on.**

- Why naive RAG breaks for agents; what "retrieval as a tool" looks like.
- Query planning, multi-hop search, and reflection loops on retrieval failure.
- Re-ranking and adaptive query rewriting.
- **Semantic caching:** vector-proximity cache layers, hit/miss handling, real latency wins.
- **Lab:** build an agentic RAG pipeline with a semantic cache layer.

*Walk away with:* a working agentic RAG system, a cache that cuts cost and latency, and the vocabulary to push back when someone says "just use RAG."

---

## Slide 7 — Week 4: Voice AI

**Ship an agent that talks — and survives real conversation.**

- The voice stack: STT → LLM → TTS, plus turn-taking and end-of-turn detection.
- Latency budgeting: streaming, barge-in, interruption handling — why sub-second feels alive.
- Provider landscape: Deepgram, ElevenLabs, OpenAI Realtime, Vapi, Retell.
- Tool calling inside a voice loop — the part most teams underestimate.
- **Lab:** ship a working voice agent end-to-end.

*Walk away with:* a live voice agent you can demo, a defensible latency budget, and an understanding of why voice agents fail in production.

---

## Slide 8 — Week 5: Multi-Agent Systems (MCP, A2A, ADK)

**When many agents beat one — and the more common case where they don't.**

- The judgment call: should this be one agent or many?
- Topologies: orchestrator-worker, hierarchical, swarm, handoff.
- The protocol layer demystified: **MCP** (tools), **A2A** (agent-to-agent), **ADK** (Google's framework) — what each actually is, beyond the marketing.
- Coordination patterns: handoff, shared memory, message passing.
- **Lab:** build a 2-agent orchestrator-worker system with real coordination.

*Walk away with:* a working multi-agent system and the judgment to resist multi-agent when a single agent with better tools would do.

---

## Slide 9 — Week 6: Guardrails + Evals

**Ship with measurable quality — not hope.**

- Guardrails: input/output filtering, prompt-injection and jailbreak defense, Llama Guard.
- The eval mindset: **trajectory eval** (was the path right?) vs. **outcome eval** (was the answer right?).
- LLM-as-judge: when it works, when it quietly lies, and how to validate the judge.
- Golden task sets and the eval → iterate loop.
- **Lab:** write evals for the Week 5 multi-agent system.

*Walk away with:* a drop-in guardrail layer, a reusable eval harness, and a real answer to "how do I know my agent got better?"

---

## Slide 10 — Who It's For & How It Runs

**Format**
- 6 weeks · one 2-hour live session per week · build every single week.

**You'll get the most out of it if you**
- Can write Python and have called an LLM API.
- Want to ship production agents, not just prototype them.

**The arc**
- Weeks 1–3: foundations & efficiency (loop, optimization, retrieval).
- Weeks 4–6: real-world surface area (voice, multi-agent, evaluation).
- Every artifact composes into the next; the eval harness measures it all.

---

## Slide 11 — Outro / Close

**On Day 1 of your next agent project, you'll know what to build, what to measure, and what to push back on.**

- Six shipped artifacts. Four durable skills. One real production reference point.
- You won't just follow tutorials — you'll recognize the patterns underneath them.

**Join the next cohort.**
*Agent Engineering Bootcamp — from loops to production.*

> *Speaker note: end on the transformation, then a single clear CTA.*
