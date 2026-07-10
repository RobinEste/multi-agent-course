# Voice Agent Workshop — 90-Minute Hands-On

A self-contained project for an internal workshop: build a working **voice agent**, run a
**simple voice pipeline** locally, understand **how it scales in production**, and see
**mocks of how a real phone call (IVR + SIP) reaches the agent**.

The goal is that every attendee leaves with a running loop:

> **you speak → speech-to-text → LLM agent → text-to-speech → you hear a reply**

…and a clear mental model of what changes when that same loop is put behind a phone number.

> **Just want to run it?** Follow [`RUNBOOK.md`](RUNBOOK.md) — every command with its real
> expected output. Part 1 runs fully offline (no key, no install). Running the session itself?
> Use [`WORKSHOP_SCRIPT.md`](WORKSHOP_SCRIPT.md).

---

## 1. What we're building

Three layers, each demoable on its own:

| Layer | What it is | Demo surface |
|-------|-----------|--------------|
| **A. Core voice loop** | STT → LLM → TTS turn loop | Terminal / browser mic. No phone needed. |
| **B. Agent brain** | System prompt + tools (lookup, transfer, end call) | Same loop, smarter responses |
| **C. Telephony edge** | How a PSTN/SIP call turns into audio frames for layer A | **Mocked** — SIP messages + call-flow diagrams |

Layers A and B are **hands-on and run for real**. Layer C is **mocked** (SIP payloads,
sequence diagrams, a fake IVR menu) so nobody needs a carrier account or a phone number
during the workshop.

### Architecture

```
                        ┌──────────────────────────────────────────────┐
                        │                VOICE AGENT LOOP                │
   caller audio  ─────▶ │  ┌──────┐   ┌────────┐   ┌───────┐   ┌──────┐ │ ─────▶ caller audio
   (mic or phone)       │  │ VAD  │──▶│  STT   │──▶│  LLM  │──▶│ TTS  │ │
                        │  └──────┘   └────────┘   │ agent │   └──────┘ │
                        │   detect     transcribe  │+ tools│    speak   │
                        │   speech                  └───┬───┘            │
                        └───────────────────────────────┼────────────────┘
                                                         │
                                         tools: knowledge lookup,
                                         transfer-to-human, end-call
```

- **VAD (Voice Activity Detection)** — decides when the caller has stopped talking (turn-taking).
- **STT (Speech-to-Text)** — streaming transcription (partial + final).
- **LLM agent** — takes the transcript, decides a reply and/or calls a tool.
- **TTS (Text-to-Speech)** — streams synthesized audio back.
- **Barge-in** — if the caller talks while the agent is speaking, cut TTS and listen.

---

## 2. Repo layout

```
voice-agent-workshop/
├── README.md              ← this file (the plan)
├── RUNBOOK.md             ← follow-along: every command + its real expected output
├── WORKSHOP_SCRIPT.md     ← minute-by-minute facilitator run-of-show (mock strategy)
├── pipeline/              ← hands-on Layer A + B (see pipeline/README.md)
│   ├── requirements.txt
│   ├── config.example.env
│   ├── providers.py       ← adaptor: Groq / OpenAI / mock (chat, transcribe, synthesize)
│   ├── agent.py           ← LLM + tools (the "brain")
│   ├── voice_loop.py      ← VAD→STT→LLM→TTS turn loop (terminal mic + --text)
│   ├── smoke_test.py      ← offline end-to-end assertion (PROVIDER=mock)
│   └── README.md
└── mocks/                 ← Layer C: telephony, no real carrier
    ├── sip-ivr-call-flow.md   ← SIP messages + sequence diagrams + IVR tree
    ├── demo_call.py           ← FULL simulated inbound call, offline (SIP→agent→SIP)
    └── ivr_menu_mock.py       ← fake DTMF/IVR menu you can run in the terminal
```

> Running the workshop? Follow [`WORKSHOP_SCRIPT.md`](WORKSHOP_SCRIPT.md) — a verbatim
> minute-by-minute script where every step runs on the offline mock, so you can rehearse the
> full 90 minutes and fall back to it live if Groq/Wi-Fi fails.

> The `pipeline/*.py` files are provided as **reference skeletons** to build live during
> the session — the workshop value is typing them together, not pasting them.

---

## 3. The 90-minute agenda

| Time | Segment | Mode | Outcome |
|------|---------|------|---------|
| 0:00–0:10 | **Framing** — what a voice agent is, the loop, where latency lives | Talk + the diagram above | Shared vocabulary |
| 0:10–0:35 | **Build Layer A** — VAD→STT→LLM→TTS in `voice_loop.py` | Hands-on | Everyone talks to a bot |
| 0:35–0:55 | **Build Layer B** — system prompt + 2 tools (lookup, transfer) | Hands-on | Bot does something useful |
| 0:55–1:10 | **Latency & barge-in** — measure the loop, add interruption | Hands-on + demo | Feels like a real call |
| 1:10–1:25 | **Telephony & SIP** — walk the mocks, run the fake IVR | Demo (`mocks/`) | Understand the phone edge |
| 1:25–1:30 | **Production scaling** — the slide, Q&A | Talk (Section 5) | Know what "real" costs |

Keep Layer A on the clock — if it slips, hand out the finished `voice_loop.py` and move on.
The demo everyone remembers is *talking to the bot*, so protect that.

---

## 4. The core concepts to teach

### Turn-taking is the hard part, not the models
Anyone can call an STT and a TTS API. The product quality lives in:
- **Endpointing** — knowing the caller finished (silence timeout + VAD). Too short = you
  interrupt them; too long = it feels laggy.
- **Barge-in** — stop talking the instant the caller talks over you.
- **Streaming everything** — never wait for a full transcript or full audio file. Partial
  STT → start LLM early; first TTS chunk → start playback.

### Latency budget (the number to burn into their heads)
A natural conversation wants **< ~800 ms** from "caller stops talking" to "agent starts talking."
Rough budget:

```
  endpoint detection   ~150 ms
  final STT            ~150 ms
  LLM first token      ~300 ms   ← usually the biggest + most variable
  TTS first audio      ~150 ms
  network/jitter       ~ 50 ms
  ─────────────────────────────
  total               ~800 ms
```

Teaching point: you optimize **time-to-first-token** and **time-to-first-audio-chunk**, not
total tokens. Streaming + a fast model for the first turn beats a "smarter" slow model.

---

## 5. Production scaling (the talk track)

The workshop loop is one process, one caller, one machine. Production is thousands of
concurrent calls. Here is what changes, in the order it bites you:

### 5.1 From one loop to many — the media/agent split
Split the system into two planes:

- **Media plane** — carries real-time audio (RTP/WebRTC), does VAD/mixing, is latency- and
  jitter-sensitive, and is *sticky* to a call. Scales with **concurrent calls**.
- **Agent/logic plane** — STT/LLM/TTS calls, tools, business logic. Stateless-ish, scales
  with **requests** and can autoscale independently.

```
  PSTN/SIP ─▶ SBC ─▶ Media servers ─▶ (audio frames) ─▶ Agent workers ─▶ STT/LLM/TTS
             (edge)  (WebRTC/RTP,                        (autoscaled,      (managed or
                      1 per call)                         pooled)           self-hosted)
```

### 5.2 The scaling knobs, by concern

| Concern | Small demo | Production |
|---------|-----------|-----------|
| **Concurrency** | 1 call = 1 python process | Media workers pinned per-call; agent workers pooled + autoscaled on queue depth |
| **STT/TTS** | 1 API call at a time | Batched/streamed, connection-pooled, regional endpoints, fallbacks |
| **LLM** | Single model | Small/fast model for turn latency, escalate to bigger model for hard turns; prompt caching; token/cost caps |
| **State** | In-memory | Call state in Redis; transcripts to durable store; resume on worker crash |
| **Session affinity** | N/A | Sticky routing so a call's audio always hits the same media worker |
| **Backpressure** | None | Reject/queue new calls past capacity; graceful "please hold" instead of dropping audio |
| **Latency** | Best effort | Region-local media + models; measure p95/p99 per stage, alert on time-to-first-audio |
| **Observability** | print() | Per-turn traces (STT ms / LLM ms / TTS ms), call recordings, barge-in counts, WER sampling |
| **Cost** | Ignore | $/minute is the unit. STT + LLM + TTS + telephony per min. Watch idle media workers. |
| **Reliability** | Crash = call dies | Health checks, drain-on-deploy, per-stage fallbacks, "escalate to human" as the safety net |
| **Compliance** | None | Recording consent, PII redaction in transcripts, retention limits, regional data residency |

### 5.3 The rules of thumb to say out loud
1. **Separate media from logic.** They scale on different axes and fail differently.
2. **Everything streams.** Buffering full audio anywhere kills the conversation feel.
3. **$/minute is the metric.** Concurrency × minutes × (STT+LLM+TTS+telephony) = the bill.
4. **Always have a human fallback.** "Let me transfer you" is the correct error handler.
5. **Measure per-stage p95.** One slow stage (usually the LLM) ruins the whole turn.

---

## 6. Layer C — telephony without a carrier (the mocks)

Attendees always ask "but how does a *phone call* get here?" Section is covered by
[`mocks/sip-ivr-call-flow.md`](mocks/sip-ivr-call-flow.md):

- What **SIP** is (signaling — set up/tear down the call) vs **RTP** (the actual audio).
- A full **annotated SIP INVITE → 200 OK → ACK → BYE** exchange (sample payloads).
- How the audio (**SDP/RTP**) becomes the frames Layer A's VAD consumes.
- An **IVR menu tree** ("press 1 to book a room…") and how DTMF maps to intents.
- Where a hosted platform (Twilio / LiveKit / Genesys / a self-hosted Asterisk+SBC) slots in
  so you don't hand-roll SIP in production.

Run the fake IVR in the terminal to demo the menu logic without any telephony:

```bash
python mocks/ivr_menu_mock.py
```

---

## 7. Prerequisites & setup

See [`pipeline/README.md`](pipeline/README.md) for the hands-on setup. Short version:

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.env .env    # set PROVIDER=groq + a free GROQ_API_KEY
python voice_loop.py          # or: python voice_loop.py --text
```

**Providers:** one adaptor (`providers.py`) covers **Groq** (free tier, fast) and **OpenAI**
(your key) — both speak the OpenAI API dialect, so you switch by flipping `PROVIDER` in `.env`.
Recommended default is `PROVIDER=groq` for **$0**; OpenAI pipeline fallback is ~$1–2 total.
Avoid the OpenAI *Realtime* API (~10–20× pricier); keep STT/LLM/TTS separate.

Send attendees the setup steps **before** the workshop so the 90 minutes is spent building,
not installing. `--text` mode (type instead of speak) still uses the real LLM + tools and needs
no mic/audio libs — the always-works fallback when someone's mic misbehaves.
