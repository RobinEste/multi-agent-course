# Module 01 — World of Agents & ReAct + Agent Harness
## Slide-by-Slide Deck (Technical Content)

**Scope:** ~52 min of lecture (intro/welcome excluded). Lab (build a ReAct loop) runs in the second hour.
**Arc:** Agents are a loop → ReAct is how the loop decides → a production harness is what makes the loop survive contact with reality.
**Four parts:** (0) Why this matters ~4 min · (1) World of Agents ~12 min · (2) ReAct ~16 min · (3) Agent Harness ~20 min

> Notation: each slide lists **[on screen]** (what the audience sees) and **[say]** (speaker note + intent). Timing is cumulative target.

> Audience: technical PMs and engineers who already know Python and the LLM APIs. We are not teaching what an LLM is. We are teaching how to turn one into a system you can ship.

---

# PART 0 — WHY THIS MATTERS  (~4 min)

## Slide 0a — The gap nobody warns you about
**[on screen]**
- A working agent demo takes an afternoon.
- A *reliable* agent takes a quarter.
- The distance between those two is this entire course.
- That distance is **engineering**, not model capability — and it's where your job is moving.

**[say]** Open with the uncomfortable truth this audience has already felt. Everyone in the room can wire up an LLM and a tool by lunch — the demo works, the room claps. Then it hits production and silently fails 1 in 4 times, and nobody can say *why*. The model didn't get dumber; the surrounding system was never built. The people who can close that gap are the ones companies are paying for right now. This is not a prompting course. It's a systems course that happens to have an LLM in the loop. *(0:00–0:01)*

---

## Slide 0b — Why a *technical* audience specifically
**[on screen]**
- **For engineers:** the agent is a new kind of distributed system — non-deterministic, partially observable, fails in prose instead of stack traces. Your debugging instincts mostly transfer; your reliability instincts must be rebuilt.
- **For technical PMs:** "we need an agent" is usually wrong. Knowing *when an agent is the right tool* — and when a boring workflow wins — is a scoping superpower that saves quarters.
- **The shared skill:** reasoning about **where control lives** — model vs. code — and putting each decision on the right side of that line.

**[say]** Speak to both halves of the room. To engineers: you already know how to make deterministic systems reliable; the new muscle is reasoning about a component that's right 95% of the time and wrong in creative ways. To PMs: the highest-leverage thing you'll learn today is restraint — most agent projects that fail were workflows wearing an agent costume. The common thread, and the thing we'll return to all day, is a single question: *who decides what happens next — the model, or your code?* Get that boundary right and everything downstream gets easier. *(0:01–0:03)*

---

## Slide 0c — What you'll be able to do by tonight
**[on screen]**
- **Build** a ReAct loop from scratch (next hour) — no framework, no magic.
- **Read** a failed agent run like a stack trace and locate the actual bug.
- **Decide** agent vs. workflow vs. chatbot, and defend it.
- **Name** the ~10 things a production harness adds to your 50-line loop — and why each one exists.

**[say]** Set the four concrete outcomes so the room knows what "paying attention" buys them. Emphasize the second bullet — *reading trajectories* — because it's the skill that separates people who say "the model is dumb" from people who fix the actual problem. Promise it explicitly: by the end of today you will never again be stuck staring at an agent that "just doesn't work." *(0:03–0:04)*

---

# PART 1 — WORLD OF AGENTS  (~12 min)

## Slide 1 — One idea for the whole module
**[on screen]**
- "An agent is an LLM running in a loop with tools and a stopping condition."
- Everything else today is detail on that sentence.

**[say]** Set the thesis. This audience already knows Python and LLM APIs, so we are not defining LLMs. The job of part 1 is to make "the loop" feel inevitable, not magical. Repeat the sentence twice — it's the spine the whole module hangs on, and we'll close on it earned. *(0:04–0:05)*

---

## Slide 2 — From LLM to Agent: the loop
**[on screen]**
```python
while not done:
    response = llm(messages)              # think
    if response.stop_reason == "end":     # stopping condition
        return response.text
    result = run_tool(response.tool_call) # act
    messages.append(result)               # observe
```
- perceive → think → act → observe → repeat
- The model's only output is **text or a tool request**. The loop does everything else.

**[say]** Show the entire idea in ~8 lines. The "wow" is that there is no magic — a production agent is this loop, hardened. Three things to point at explicitly: (1) the LLM is *stateless* — it knows nothing between calls except what's in `messages`, so the loop's append is the agent's entire continuity; (2) the model never *runs* anything — it asks, your code decides whether and how to execute; (3) the loop is plain control flow you've written a thousand times. Tell them: "You will write exactly this in the lab. By the end of today you'll know what the other ~5,000 lines of a real harness add to it — and that every one of those lines exists to fix a specific failure." *(0:05–0:07)*

---

## Slide 3 — Anatomy of an agent
**[on screen]**
- **Generator (LLM)** — produces text / structured output / tool calls. The only non-deterministic part.
- **Prompt assembler** — builds each request: system prompt + running message list + tool metadata.
- **Tool executor + formatter** — validates args, runs the tool, turns the result back into text the model can read.
- **Control loop** — decides continue vs. stop; owns retries, limits, and termination.

**[say]** Frame each as "a thing the toy loop on the last slide hides." Two emphases for a technical room: the **prompt assembler** is where most behavior actually lives (we'll tear it apart in Part 3), and the **control loop** is the component people forget is a component — it's the only part that's fully deterministic and therefore the only part you can fully trust. Note what's *not* on this list: there's no "intelligence" box. The intelligence is borrowed from the model per-call; everything you build is plumbing around it. *(0:07–0:09)*

---

## Slide 4 — Agent vs. Workflow vs. Chatbot
**[on screen]**

| | Tools? | Loop? | Who controls flow? | Reliability |
|---|:--:|:--:|---|:--:|
| **Chatbot** | no | no | the prompt | high |
| **Workflow** | yes | fixed | **you** (hardcoded steps) | high |
| **Agent** | yes | dynamic | **the model** | lower, tunable |

- Agents trade reliability for flexibility. You pay for autonomy in predictability.

**[say]** The single decision-oriented slide, and a callback to Part 0's "who controls flow" question. The axis that separates the three is *who controls the control flow* — not "is there an LLM" (all three can have one). Punchline: reach for an agent only when you **cannot enumerate the steps in advance**. If you can draw the flowchart, build the flowchart — it's cheaper, faster, debuggable, and doesn't fail 5% of the time per step. The agent earns its unreliability only when the branching is genuinely open-ended. *(0:09–0:11)*

---

## Slide 5 — Four levels of agentic architecture
**[on screen]**
- **L1 — Simple LLM:** "Draft me a vacation email." Pure chat, zero tools, one call.
- **L2 — LLM + Tools:** "Find all product releases from Google I/O 2025." Mappable flowchart, finite known paths.
- **L3 — Thinking & Reasoning:** "Build a fitness app that syncs to Apple Watch." Branching explosion; the model chooses tools dynamically.
- **L4 — Agent ↔ Agent:** "Source candidates, schedule interviews, run background checks." Multi-agent coordination, parallel sub-tasks.
- Spectrum: **deterministic workflow → autonomy + self-reflection**

**[say]** Reuse the four-level framing — it's strong and it maps cleanly onto "how much control you hand the model." Keep examples concrete and escalating. Locate the class: we live in **L2–L3** today, which is exactly where most production value is; L4 is Week 5 and is still mostly research-grade in the wild (more on its failure rates two slides from now). The key insight: levels are a *cost/risk dial*, not a maturity ladder — higher is not better, it's more autonomous and more expensive to make reliable. *(0:11–0:13)*

---

## Slide 6 — When to level up (and when not to)
**[on screen]**
- **Stay at L2 (tools/workflow) when:** the process maps to a flowchart · fewer than ~15–20 branches · finishes in seconds–minutes · the value is automating a *known* process.
- **Go to L3 (agent) when:** 30+ nodes and growing weekly · users phrase requests unpredictably · the right tool depends on context discovered mid-task · requests are ambiguous and multi-step.
- **Heuristic:** if you can write the spec as a sequence diagram, you don't need an agent yet.

**[say]** This is the judgment slide that tutorial courses skip — and it's aimed squarely at the PMs. Most "we need an agent" instincts are actually L2 problems dressed up. Selling restraint here builds credibility for the rest of the course: we're not agent maximalists, we're matching the tool to the problem. Concrete tell: if your "agent" always takes the same path, you built a workflow with extra latency and a failure rate. Promote to L3 only when the *variety of valid paths* exceeds what you're willing to hand-code. *(0:13–0:15)*

---

## Slide 7 — Reality check: errors compound
**[on screen]**
> "If each step of an AI agent is 95% accurate, none of the 30-step workflows will work. Going 95% → 99.9% is the same last-mile problem as self-driving cars." — Richard Socher

- 0.95³⁰ ≈ **21%** end-to-end success
- 0.99¹⁰⁰ ≈ **37%** — even *near-perfect* steps collapse over a long horizon
- Measured in the wild: ~3-step trajectories ≈ **90%** accuracy; 8+ step trajectories drop to **~43%** with high variance.

**[say]** Do the math live: type `0.95**30` and let the 0.21 land in the silence. Then the kicker — even 99% per step, the bar self-driving cars spent a decade chasing, only gets you to 37% over 100 steps. This is *the* motivation for everything in Part 3 (the harness) and for Week 6 (evals). The third bullet is fresh empirical data: reliability doesn't just decay, its *variance* explodes as horizons grow, so long-running agents are unpredictable as well as wrong. Plant the flag hard: **reliability is an engineering problem, not a prompting problem.** You do not prompt your way out of exponential decay. *(0:15–0:16)*

---

# PART 2 — ReAct  (~16 min)

## Slide 8 — ReAct: Reason + Act
**[on screen]**
- Interleave **reasoning** (Thought) with **acting** (Action → Observation) in one loop.
- Flow: Query → **Thought** → **Action** → **Observation** → (answer? → Final / else loop)
- It fuses chain-of-thought reasoning with external tool use — the model thinks *and* checks reality each turn.

**[say]** Define the pattern (Yao et al., 2022 — the paper that named it). The key word is **interleaved**: thinking and acting alternate every turn instead of being separate phases. Why this matters mechanically — pure chain-of-thought reasons in a vacuum and can confidently reason its way off a cliff; ReAct forces a reality check (an Observation) between each reasoning step, so errors get caught one step after they're made instead of compounding silently. That single property is most of why it became the default tool-using pattern. *(0:16–0:18)*

---

## Slide 9 — Why ReAct beats plan-then-execute
**[on screen]**
- **Plan-then-Execute:** plan all steps up front → run them blind. One bad assumption → the whole plan derails.
- **ReAct:** re-plan after *every* observation → recovers from surprises mid-run.
- **Trade-off:** ReAct spends more tokens and latency (an LLM call per step) to buy robustness.

**[say]** The one comparison worth doing well. Concrete example: a search returns zero results. Plan-then-execute had "step 3: summarize the results" queued and marches on into nonsense; ReAct *sees the empty observation* and rewrites the query before continuing. That's the whole argument — ReAct closes the loop with reality on every iteration, so it degrades gracefully where rigid plans shatter. Be honest about the cost: every reasoning step is a full inference pass, so ReAct is the expensive, slow, robust choice. We'll name when *not* to pay that on Slide 12. *(0:18–0:20)*

---

## Slide 10 — Anatomy of a real ReAct step
**[on screen]** (annotated trace)
```
Thought:  I need current weather for the user's city.
Action:   get_weather(city="Lahore")
Obs:      {"temp_c": 41, "cond": "clear"}
Thought:  41°C is high; the user asked if they need a jacket. No.
Answer:   No jacket needed — it's 41°C and clear.
```
- decision → tool call → result → re-decision → answer

**[say]** Walk it line by line, slowly. Point at exactly where the **model** decided (Thought, Action), where your **code** ran and returned (Obs — note it's structured JSON the model didn't write), and where the model **course-corrected** using a fact it could not have known before the call (41°C). This is the mental model they'll debug with for the rest of the course. Make the boundary vivid: Thought/Action/Answer come from the model; Obs comes from your harness. Every bug lives on one side of that line, and step one of debugging is always "which side?" *(0:20–0:22)*

---

## Slide 11 — The two things that make ReAct actually work
**[on screen]**
1. **The system prompt** — defines the Thought/Action/Observation format and the tool list. *This is the agent's policy.*
2. **The parse-and-dispatch loop** — turns model text into a real tool call, runs it, feeds the result back as the next Observation.
- That's the whole lab. Two halves, ~50 lines.

**[say]** Demystify completely: ReAct is **a prompt format plus a loop that parses it**. There is no third secret ingredient. The system prompt is where you *specify* the contract (here's the format, here are your tools, here's when to stop); the loop is where you *enforce* it. Foreshadow the lab directly — "you're about to build both halves, and once you have, every framework's 'agent' abstraction will look like exactly what it is: these two pieces with error handling bolted on." *(0:22–0:24)*

---

## Slide 12 — The pattern family (when to use which)
**[on screen]**
- **ReAct** — default for tool use; react to each observation. Max robustness, max cost.
- **Plan-and-Execute** — when steps are knowable and you want fewer LLM calls / cost control / lower latency.
- **Reflection** — add a self-critique pass when quality matters more than speed (drafting, code, analysis).
- These **compose** — real agents mix them (e.g. plan coarse-grained, ReAct within each step, reflect before finalizing).

**[say]** One slide, not three — resist deep-diving each into its own lecture. The takeaway is they're **tools in a kit, not competing religions**, and the senior move is composition: a router plans the high-level phases, ReAct handles the open-ended middle, reflection gates the output. Tie back to cost: each pattern is a different point on the tokens-vs-robustness curve, and you pick per sub-task, not per project. *(0:24–0:26)*

---

## Slide 13 — Modern reality: you rarely parse text by hand
**[on screen]**
- Native **tool-calling APIs** return structured tool calls (a `tool_use` block) — no regex on "Action:".
- `stop_reason` tells the loop what the model wants: `tool_use` → run a tool; `end_turn` → it's done.
- Frontier models (Claude, GPT-5, Gemini) now run the reason-act loop natively — explicit ReAct *prompting* is often unnecessary.
- **But:** you build it by hand once (the lab) so the abstraction is never a black box.

**[say]** Honesty slide, and an important one for a technical audience that's about to use SDKs. The hand-rolled "Thought:/Action:" text format from the original paper is largely historical — modern APIs hand you a typed tool call and a `stop_reason`, and the model was trained to use them. So why build it by hand? Because when the SDK's agent does something baffling in production, the people who once wrote the parse-and-dispatch loop themselves *know what's underneath* and can reason about it; everyone else files a bug and waits. Understanding the primitive makes the SDK legible. This also bridges straight into the harness — the SDK is doing a slice of what Part 3 is about. *(0:26–0:29)*

---

## Slide 14 — ReAct's three structural weaknesses
**[on screen]**
- **Serial latency** — one inference pass per step; long tasks feel slow because steps can't overlap.
- **Quadratic context growth** — every Thought/Action/Obs is appended, so each step re-sends the whole history; cost and latency climb with the square of trajectory length.
- **Prompt-injection & hallucination surface** — observations are untrusted text fed back into the prompt; a malicious tool result can hijack the next Thought, and ungrounded models will invent tools that don't exist.

**[say]** New slide — give the room the failure modes *before* they hit them, because all three are non-obvious until they bite. Serial latency is why a 12-step agent feels sluggish even on a fast model. Quadratic growth is the silent budget-killer: a 20-step run isn't 20× a single call, it's closer to 20² in accumulated tokens — name it now, Part 3's context management exists to fight it. And prompt injection is the one that gets people fired: an Observation is data from the outside world, but it lands in the model's context looking exactly like instructions. This is the threat model behind the hooks and boundaries we build in Part 3 and harden in Week 6. *(0:29–0:31)*

---

## Slide 15 — Reading trajectories like stack traces
**[on screen]**
- A failed agent run = a **trajectory** you read top-down, like a stack trace.
- Common failure signatures: wrong tool chosen · bad arguments · misread observation · stuck in a loop · stopped too early · injected by a tool result.
- The trace *is* your debugger. **Most "the model is dumb" bugs are prompt or tool-description bugs.**

**[say]** This is the single most differentiating skill in the module — slow down and make it land. Show (or narrate) a deliberately broken trace and locate the failure live: walk down it asking at each step "did the model decide wrong, or did my code feed it something wrong?" Tie it to Slide 10's anatomy — you're checking each Thought/Action/Obs boundary. Hammer the punchline: when an agent misbehaves, the bug is almost never that the model "isn't smart enough" — it's a vague tool description, a missing instruction, or a malformed observation. The fix lives in *your* text, not in waiting for a better model. This sets up the debugging demo in the lab. *(0:31–0:35)*

---

# PART 3 — AGENT HARNESS  (~20 min)

## Slide 16 — Toy loop → production harness
**[on screen]**
- You can write the loop in 50 lines. So what do Claude Code, Codex, Cursor & friends actually add?
- An **agentic harness** = the deterministic execution + orchestration layer around the LLM that makes it stateful, safe, and reliable.
- It's "everything between the language model and the real world" — and it decides what the model's text is allowed to touch.
- Rest of this part = that gap, component by component.

**[say]** Frame Part 3 as "everything between your 50-line lab and a real agent." The mental model that makes the whole part click: the **model proposes, the harness disposes**. The LLM emits a *request* to act; the deterministic code around it decides whether, how, and with what guardrails that request becomes a real action. This is the flagship teardown of the day — give it room, and keep returning to that proposes/disposes framing. *(0:35–0:36)*

---

## Slide 17 — The nine components of a real harness
**[on screen]**
1. **Model interface** — abstracts which LLM you're using; handles formatting and parsing.
2. **Tool registry** — catalog of tools: names, descriptions, schemas, executors.
3. **Context manager** — decides what the model sees each step (truncation, compression, retrieval, selective injection).
4. **Planning module** — reactive (ReAct), pre-planned, or hierarchical.
5. **Execution engine** — runs tools with sandboxing, timeouts, output formatting, optional parallelism.
6. **State tracking** — checkpointing, idempotency keys, progress across steps.
7. **Feedback/observation loop** — surfaces errors readably; detects loops and off-track runs.
8. **Safety & guardrails** — confirmation gates, action filtering, scope limits, rate limits, audit logs.
9. **Orchestration** — multi-agent routing, sub-agent spawning, result aggregation.

**[say]** This is the map for the rest of Part 3 — every remaining slide zooms into one or two of these. The point isn't to memorize nine boxes; it's to see that your 50-line loop already contains crude versions of #1, #2, #5, and #7, and that "productionizing" is just hardening each box for the failure it owns. Whether it's Claude Code, LangChain, or your own build, the *implementations* differ but these nine *problems* are invariant. Tell the room: when you evaluate a framework, this is your checklist — which boxes does it give you, and which are you still on the hook for? *(0:36–0:38)*

---

## Slide 18 — The core loop, for real
**[on screen]**
- Prompt → Intent → Tool execution → Observation → repeat until `stop_reason`
- Translate model text into *validated* API calls (schema-check args before executing).
- Feed observations — including failures — back into context.
- **Errors are observations, not crashes** — a failed tool returns text the model can read and react to.

**[say]** Contrast directly with the lab loop: the toy version throws an unhandled exception the moment a tool errors and the whole run dies; the harness *catches* it, formats it as an Observation ("Error: city not found — did you mean a valid city?"), and hands it back so the model can recover on the next turn. That one design choice — **errors are data, not exceptions** — is most of the robustness, and it's the cheapest reliability win you'll ever ship. The other half is validation *before* execution: never let unvalidated model output reach a real side effect. *(0:38–0:41)*

---

## Slide 19 — The tool contract
**[on screen]**
Every tool needs:
- **Purpose** — natural-language description (the model routes on *this alone*).
- **Schema** — strict, typed JSON in and out; validated by the harness.
- **Boundaries** — constraints, limits, and edge-case behavior stated explicitly.

Rules:
- One tool, one behavior. Name it short, descriptive, unambiguous.
- Never put "OR" in a tool definition — split it into two tools.
- A vague description = the wrong tool gets chosen. **Tool design *is* prompt engineering.**

**[say]** Keep this — it's core, and now it connects to the registry (#2) and the trajectory-debugging skill from Slide 15. Drive the central point: the model selects a tool by *reading its description* and nothing else — it can't see your implementation, your comments, or your intentions. So the description is the API the model programs against, and a fuzzy one is a bug you've shipped into every future run. Two field-tested details: tool *names* should be short and unambiguous because the model invokes them by name under load; and good harnesses make descriptions *context-aware* (a file-reader describes itself differently for text vs. images, and only exposes tools the current permissions allow). This is the slide that closes the loop with Slide 15 — "most bugs are tool-description bugs" — now they know how to write the description that prevents them. *(0:41–0:44)*

---

## Slide 20 — System prompt anatomy
**[on screen]**
A production system prompt has structure:
- **Role / identity** — who the agent is and what it's for.
- **Tool-use rules** — when to call, how to parallelize, when to stop, what to never do.
- **Environment / harness context** — what the agent can see and do right now.
- **Safety & boundaries** — hard limits stated in plain language.
- **Tone / output format** — how results should look.

The system prompt *is* the agent's policy — **most behavior tuning lives here, not in code.**

**[say]** This is the Claude Code teardown moment, and the highest-"wow" artifact of the day. If you can show even a redacted real system-prompt structure, do it — people are genuinely surprised how much "AI behavior" is just well-organized instructions in English. The lesson for engineers: before you write code to fix a behavior, try writing a sentence — the system prompt is the highest-leverage, fastest-iteration surface you have. The lesson for PMs: a huge fraction of "product behavior" is editable text a non-engineer can read and reason about. Caveat that bridges to the next slide: the prompt *suggests*; it doesn't *guarantee*. *(0:44–0:47)*

---

## Slide 21 — Interception points: hooks
**[on screen]**
- **Pre-hook (PreToolUse)** — runs *before* the tool: enforce authorization, business limits, rate limits; can block or rewrite the call.
- **Post-hook (PostToolUse)** — runs *after* the tool: redact PII, normalize formats, log for audit.
- The harness **gates** what the agent is allowed to do — deterministically.

**[say]** Return to the proposes/disposes framing and make it concrete. The model can *request* `delete_account(id=...)`; the pre-hook is the deterministic code that checks "is this user authorized? is this within today's limit?" and refuses if not — no probability involved. Hooks are where you put the rules you **cannot afford to leave to a 95%**. They're also your primary defense against the prompt-injection surface from Slide 14: an injected Observation might convince the model to call a dangerous tool, but the pre-hook doesn't read prose and can't be sweet-talked. Foreshadows Week 6 guardrails. *(0:47–0:49)*

---

## Slide 22 — Deterministic boundaries
**[on screen]**
- **Prompts suggest** → ~95% reliability (and you can't easily push past it).
- **Hooks / code enforce** → 100% reliability for the thing they check.
- **Rule:** if a failure causes real-world harm, build a hook — don't ask the prompt nicely.

**[say]** The single most important engineering lesson of the module — say it that plainly. Callback to Socher on Slide 7: you cannot prompt your way to 99.9%, because the model is a probabilistic component and exponential decay is unforgiving. The last mile is **deterministic code wrapped around a probabilistic core.** Give them the decision rule to take home: for every capability, ask "what's the blast radius if the model gets this wrong?" Low blast radius → trust the prompt and move fast. High blast radius (money, deletion, external sends, PII) → put a hook in front of it, because 95% reliability on an irreversible action is a 1-in-20 incident waiting to happen. *(0:49–0:51)*

---

## Slide 23 — Scaling the harness: router + sub-agents
**[on screen]**
- A **Router Agent** delegates to specialized sub-agents (Search, Code, DB).
- Each sub-agent spawns with its **own isolated context window** — shard context, avoid pollution.
- Run parallel sub-tasks in isolated environments; **merge** results back into the main thread.
- Why bother: context isolation + parallelism — *not* because "more agents = smarter."

**[say]** Brief — this is the on-ramp to Week 5 (multi-agent), so establish the pattern and its *real* motivation, then move on. The honest framing the room needs: multi-agent is not a capability upgrade, it's a **context-management and parallelism** technique. You split work so each sub-agent gets a clean, focused window instead of one bloated shared one, and so independent branches run at once. Plant the caution flag for Week 5: multi-agent systems fail in production at high rates (studies report 40–85%) precisely because coordination, role ambiguity, and merge conflicts are *hard* — reach for a single well-built agent first. *(0:51–0:53)*

---

## Slide 24 — Graceful handoff to a human
**[on screen]**
On ambiguity, repeated failure, or a high-stakes call, hand off with a **structured payload**:
- ❌ Don't dump the raw transcript on a human.
- ✅ Synthesize state: **Summary · Actions taken · Recommended next steps**.
- Wait for resolution, then resume the loop where it left off.

**[say]** Production agents know when to *stop* and escalate — knowing your limits is a feature, not a failure. Make the contrast vivid: a transcript dump makes the human do the agent's synthesis work (and they won't); a structured handoff respects their time and makes the decision fast. This is also a reliability lever — escalating on uncertainty beats confidently acting wrong on a 5% case. Quick but memorable; it's the human side of the deterministic-boundaries lesson. *(0:53–0:54)*

---

## Slide 25 — Takeaway + bridge to the lab
**[on screen]**
- Production agents are not magic — they're a well-engineered loop plus: a strong system prompt, validated tool contracts, deliberate context management, and deterministic hooks where it counts.
- The model supplies intelligence; **you supply reliability.**
- **Next hour:** build the 50-line ReAct loop yourself. You now know exactly what it's missing — and why each missing piece exists.

**[say]** Close on the thesis from Slide 1, now earned: "an LLM in a loop with tools and a stopping condition" — and you can now annotate every word with the engineering it implies. Land the division of labor one last time: intelligence is rented from the model per call; reliability is the system you build around it, and that system is the actual job. Hand off to the lab with momentum — they're not building a toy, they're building the core that every harness on the planet is a hardened version of. *(0:54)*

---

## Appendix / cut-for-time
- **AgentPro repo** (`Calculator`, `CodeInterpreter`, `AresInternetSearch`, `TraversaalProRAGTool`) — concrete tool examples for the lab: https://github.com/traversaal-ai/AgentPro
- **Claude Code system prompts** (Piebald-AI) — real, version-tracked system prompt + tool descriptions to show on Slide 20 if you want the live artifact: https://github.com/Piebald-AI/claude-code-system-prompts
- **Manus AI case study** — Claude Sonnet + ~29 tools, *single* agent, `browser_use` — strong "you don't need multi-agent" evidence; use if Slide 6 or Slide 23 needs reinforcement.
- **Industry applications grid** (Finance / Sales / Healthcare / Hiring) — drop in after Slide 5 if the room wants motivation over mechanics.
- **Original ReAct paper** — Yao et al., 2022, "ReAct: Synergizing Reasoning and Acting in Language Models" — cite on Slide 8 for provenance.

---

## Sources for refreshed content
- ReAct pattern, limitations, and native tool-calling evolution — [mbrenndoerfer.com](https://mbrenndoerfer.com/writing/react-pattern-llm-reasoning-action-agents), [n8n blog](https://blog.n8n.io/react-agent/), [APXML](https://apxml.com/courses/agentic-llm-memory-architectures/chapter-2-advanced-agent-architectures-reasoning/react-framework-reasoning-acting)
- Agent harness architecture & nine components — [MindStudio](https://www.mindstudio.ai/blog/what-is-agent-harness-architecture-explained), [SAP Community](https://community.sap.com/t5/artificial-intelligence-blogs-posts/agentic-harness-architecture-seven-pillars-that-make-claude-code-production/ba-p/14395198), [Dive into Claude Code (arXiv)](https://arxiv.org/html/2604.14228v1)
- Tool contract design — [Ken Huang, Claude Code Harness Pattern 2](https://kenhuangus.substack.com/p/claude-code-harness-pattern-2-tool)
- Error compounding & trajectory-length reliability data — [Prodigal](https://www.prodigaltech.com/blog/why-most-ai-agents-fail-in-production), [MindStudio reliability](https://www.mindstudio.ai/blog/reliability-compounding-problem-ai-agent-stacks), [ReliabilityBench (arXiv)](https://arxiv.org/pdf/2601.06112)
- Multi-agent production failure rates — [Augment Code](https://www.augmentcode.com/guides/why-multi-agent-llm-systems-fail-and-how-to-fix-them)
