# 90-Minute Workshop Script — Facilitator Run-of-Show

A minute-by-minute script you can **follow verbatim**. Every step runs on the **mock provider**
(`PROVIDER=mock`) so you can rehearse the entire 90 minutes offline — and the mock doubles as
your **live safety net** if Groq/Wi-Fi dies mid-session.

Legend for each block:
**🎯 Goal** · **🗣️ Say** (talk track) · **⌨️ Do** (commands) · **📺 Show** (expected output) · **⚠️ Fallback**

---

## The mock strategy (read this first)

Three provider modes, one interface. You *rehearse and de-risk* on `mock`, *demo for real* on `groq`:

| Mode | Needs | Use it for |
|------|-------|-----------|
| `PROVIDER=mock` | nothing (offline) | Rehearsal, the SIP call demo, and the fallback if live fails |
| `PROVIDER=groq` | free key | The real "talk to a bot" moment |
| `PROVIDER=openai` | your key | Backup / if attendees prefer OpenAI |

**Golden rule:** if anything live breaks, say *"let's use the mock"*, flip one env var, and keep
going. You never get stuck. Do a full dry run on `mock` the day before — it exercises the same
code path attendees will run.

### Pre-flight checklist (do 15 min before)
```bash
cd voice-agent-workshop/pipeline
python smoke_test.py                       # must print PASS ✓  (offline, no key)
PROVIDER=mock python voice_loop.py --text  # type "room for two guests" then "goodbye"
python ../mocks/demo_call.py               # the full mocked call prints cleanly
# then, if using live: set PROVIDER=groq + GROQ_API_KEY, run voice_loop.py once
```
Have two terminals open: **T1** = pipeline dir, **T2** = mocks dir. Font size up.

---

## 0:00–0:10 — Framing (talk)

**🎯 Goal:** shared mental model before anyone touches code.
**🗣️ Say:**
- "A voice agent is one loop: **you speak → STT → LLM → TTS → you hear a reply.**"
- "The hard part isn't the models — it's **turn-taking and latency**. A natural call wants the
  reply to start in **under ~800 ms**."
- "We'll build that loop, make it use a tool, then see how a real **phone call over SIP** reaches it —
  all mocked, so no one needs a phone number or a paid account."
**📺 Show:** the architecture diagram in `README.md` §1.
**⚠️ Fallback:** none — this is pure talk.

---

## 0:10–0:35 — Build Layer A: the voice loop (hands-on)

**🎯 Goal:** everyone runs a talking agent.
**🗣️ Say:** "Open `voice_loop.py`. Find the loop: capture → `transcribe` → `agent.respond` →
`say`. Each turn is timed. Let's run it in mock first so we all see the same thing."
**⌨️ Do (T1):**
```bash
python smoke_test.py                        # prove the wiring: PASS ✓
PROVIDER=mock python voice_loop.py --text   # everyone types a turn
```
**📺 Show:** greeting → type `I need a room from August 12 to August 14 for two guests.` →
agent replies → per-stage latency table.
**Then go live:**
```bash
cp config.example.env .env      # set PROVIDER=groq + GROQ_API_KEY
python voice_loop.py            # real mic, real speech
```
**⚠️ Fallback:** mic/PortAudio fails → `python voice_loop.py --text`. Key/Wi-Fi fails →
`PROVIDER=mock`. Both keep the exact same loop running.

---

## 0:35–0:55 — Build Layer B: the agent brain + tools (hands-on)

**🎯 Goal:** the bot *does* something — calls a tool.
**🗣️ Say:** "Open `agent.py`. The `TOOLS` list is `check_availability`, `create_booking`,
`transfer_to_human`, and `end_call`. The model decides when to call them; `run_tool` executes
and we feed the result back. This is the whole booking desk, but flexible."
**⌨️ Do (T1):**
```bash
PROVIDER=mock python voice_loop.py --text
```
Type: `I need a room from August 12 to August 14 for two guests.` → then
`book it for Priya Shah at priya@example.com.` → then `can I talk to a person?`
**📺 Show:** first turn fires `check_availability`; second returns confirmation `AH-4827`;
third returns action `transfer` → `[SIP REFER]`. Point at the room data in `agent.py`.
**🗣️ Say:** "Notice the safety net — when it can't help, it *transfers to a human*. That's the
correct error handler for a voice agent."
**⚠️ Fallback:** stays in mock the whole time; no external dependency.

---

## 0:55–1:10 — Latency & the turn budget (hands-on + talk)

**🎯 Goal:** make latency *visible* and explain what you'd optimize.
**🗣️ Say:** "Every turn prints stt / llm+tools / tts. In mock they're ~0 ms. Switch to Groq and
watch where the time goes — the **LLM stage dominates**, and it's the most variable."
**⌨️ Do (T1, if live):**
```bash
python voice_loop.py            # speak a turn, read the latency table aloud
```
**📺 Show:** the `── turn latency ──` breakdown; compare mock (~0) vs Groq (real ms).
**🗣️ Say the rules of thumb:** stream everything; optimize **time-to-first-token** and
**first-audio-chunk**, not total tokens; a fast model on turn 1 beats a smart slow one.
Mention **barge-in** (talk over the agent → cut TTS) as the next thing you'd add.
**⚠️ Fallback:** no live key → talk through the numbers using README §4's budget table.

---

## 1:10–1:25 — Telephony & SIP: watch a whole call (demo)

**🎯 Goal:** answer "how does a real phone call get here?" — end to end, mocked.
**🗣️ Say:** "Two protocols: **SIP** sets up/tears down the call (signaling), **RTP** carries the
audio. A platform like Twilio/LiveKit/Asterisk terminates those and hands our agent clean
audio. Let's watch a full call."
**⌨️ Do (T2):**
```bash
python demo_call.py             # INVITE→200→ACK, agent turns, lookup, BYE
python demo_call.py --transfer  # same, but caller asks for a human → SIP REFER
python ivr_menu_mock.py         # optional: interactive DTMF/speech menu
```
**📺 Show:** the SIP handshake, RTP audio arrows, the tool firing mid-call, and the teardown
(`BYE` vs `REFER`). Cross-reference `sip-ivr-call-flow.md` for the annotated raw messages.
**🗣️ Say:** "Same `Agent` you built — we just wrapped it in the SIP signaling a carrier would send."
**⚠️ Fallback:** none needed — `demo_call.py` is 100% offline by design.

---

## 1:25–1:30 — Production scaling + Q&A (talk)

**🎯 Goal:** what changes from one laptop to thousands of calls.
**🗣️ Say (the 5 rules from README §5):**
1. **Separate the media plane from the logic plane** — they scale on different axes.
2. **Everything streams.**
3. **$/minute is the metric** — concurrency × minutes × (STT+LLM+TTS+telephony).
4. **Always have a human fallback.**
5. **Measure per-stage p95** — one slow stage ruins the turn.
**📺 Show:** the scaling table in README §5.2 and the media/agent split diagram.
**Close:** "You built the loop, gave it a tool, and saw it behind a phone call — all runnable
offline. The repo has everything to take further."

---

## Timing cheat-sheet (tape to your monitor)

| Time | Block | One command that carries it |
|------|-------|------------------------------|
| 0:00 | Framing | *(diagram)* |
| 0:10 | Voice loop | `PROVIDER=mock python voice_loop.py --text` → then live |
| 0:35 | Tools | `PROVIDER=mock python voice_loop.py --text` (1001 → person) |
| 0:55 | Latency | `python voice_loop.py` (read the table) |
| 1:10 | SIP call | `python ../mocks/demo_call.py` (+ `--transfer`) |
| 1:25 | Scaling | *(README §5)* |

**If you fall behind:** protect 0:10 (the loop) and 1:10 (the SIP call) — those are the two
"wow" moments. Compress 0:55 and 1:25 to talk-only. Everything you demo can run on `mock`, so
you can always fast-forward by scripting instead of waiting on live audio.
