	# Assignment 2 voice agents Run Notes & Evidence (Robin Bertus)

**Date:** 2026-07-22
**Video demo:** [https://www.loom.com/share/6b46f77044524a459ae7c87b8b0d7d6e](https://www.loom.com/share/6b46f77044524a459ae7c87b8b0d7d6e)
**Provider:** Groq — LLM `openai/gpt-oss-120b`, STT `whisper-large-v3-turbo`, TTS provider (Orpheus `canopylabs/orpheus-v1-english`, voice `troy`) with automatic browser-speech fallback
**Environment:** macOS (Darwin 25.5), Python 3.14, local LiveKit dev server (Docker `livekit/livekit-server:latest`) on `127.0.0.1:7880`
**Secrets:** via Infisical (project **FDE-training**, env `dev`, key `GROQ_API_KEY`) injected with `infisical run`. No `.env` holding a real key is committed or written to disk.

All numbers below come from actual runs on this machine on 2026-07-22. The telemetry log (`logs/voice-events.jsonl`) is gitignored per upstream policy and is **not** committed; counts were taken from the local log.

## Stage completion matrix

| RUNBOOK stage | Status | Evidence |
|---------------|--------|----------|
| 1 — Deterministic text agent (mock) | ✅ | `smoke_test.py` → **RESULT: PASS** (availability via `check_availability`, booking **AH-4827**, transfer, hangup); `PROVIDER=mock` text loop verified |
| — Offline test suite | ✅ | `python -m unittest test_features` → **16/16 OK** |
| 2 — Live provider, same agent | ✅ | Live Groq via `talk_server.py` browser path; telemetry shows **45 turns on `groq` / `openai/gpt-oss-120b`** |
| 3 — Tools, RAG, guardrails, language routing | ✅ | **21× `tool.requested`** (`check_availability`, `create_booking`); **2× retrieval** (`search_hotel_knowledge`, grounding source logged); EN↔ES routing (**5× `router.language_changed`**); `run_evals.py --suite all` → **12/12** |
| 4 — Local voice cascade (terminal mic) | ⚠️ covered via Stage 5 | Live audio through the LiveKit browser UI (Whisper STT, endpointing, per-stage timings). Standalone terminal-mic cascade **not run** — PortAudio deliberately skipped on this setup; the browser is the demo path. |
| 5 — Local LiveKit room | ✅ | Room `aurora-demo-room`; caller + agent participants; web client served by `talk_server.py` on `http://localhost:5173` |
| 6 — Turn-taking & barge-in | ✅ | Endpoint-silence / speech-sensitivity sliders in the browser UI (endpoint raised from 650 ms → ~1100 ms to stop clipping natural pauses); **7× `barge_in.turn_started`** |
| 7 — Telemetry | ✅ | **50 turns / 3 sessions** in local `voice-events.jsonl`; `traceId` / `sessionId` / `turnId`, provider, model, language, locale, per-stage timings; redaction verified (see below) |
| 8 — Evaluation & red-teaming | ✅ | `run_evals.py --suite all` → **12/12** (prompt-injection, fabricated-policy grounding, cross-guest privacy, tool SQL-injection, language guardrail, hangup control) |
| 9 — Scale check | ✅ | `scale_check.py --dau 1000000` → 250k daily calls, peak **5,555.6** concurrent, **7,223** provisioned sessions, **181** workers, **23.1** call-starts/sec |
| 10 — SIP mapping | ✅ | `demo_call.py` → booking → **SIP BYE**; `demo_call.py --transfer` → escalation → **SIP REFER** (`Refer-To: sip:front-desk@voice.demo`, 202 Accepted) |

## Telemetry evidence (from `logs/voice-events.jsonl`, 2026-07-22)

**Volume:** 50 turns across 3 sessions (45 agent turns + 5 greetings), all on Groq `openai/gpt-oss-120b`.

**Languages:** `en` 38, `es` 7 (locales `en-US` / `es-ES`) — Spanish switch demonstrated, 5 `router.language_changed` events.

**Per-stage latency (ms), across 45 agent turns — min / median / max:**

| Stage | min | median | max |
|-------|-----|--------|-----|
| STT (Whisper) | 196 | 314 | 932 |
| routing | 0 | 0 | 0 |
| LLM | 245 | **827** | 6738 (cold start) |
| tools | 0 | 0 | 2 |
| retrieval (RAG) | 1 | 1 | 2 |
| TTS | 52 | 1030 | 4940 |
| **TOTAL** | — | **1576** | 7106 |

**Event counts:** 21 `tool.requested` / 21 `tool.result`; 2 `retrieval.*` (RAG grounding); 7 `barge_in.turn_started`; 5 `router.language_changed`; 5 `greeting.requested`.

**TTS resilience:** 32 `tts.started`/`tts.completed`, and **5 `tts.failed` → 5 `tts.fallback`** — five Orpheus calls transiently failed and the bridge fell back to browser speech for that turn, recovering automatically on the next. (Audible as a brief "tinny" voice mid-demo.)

**Privacy redaction verified** (`TELEMETRY_INCLUDE_CONTENT=false`): transcript content is omitted at the edge —
`caller.transcript → {"text": "[OMITTED:6]"}`, `assistant.response → {"text": "[OMITTED:108]"}` (only character counts, no content).

## Findings (honest FDE notes)

**Groq TTS (Orpheus) does work — with terms + a fallback.** `canopylabs/orpheus-v1-english` returns `model_terms_required` (HTTP 400) until you accept the model terms in the Groq console. After accepting, `TTS_BACKEND=provider` produces neural audio. `talk_server.py` wraps `synthesize()` in a try/except and falls back to browser speech on failure, so a transient Orpheus error degrades gracefully (5 such turns this run) instead of crashing.

**Key naming matters — it's not cosmetic.** `providers.py` maps the provider to a base_url: a Groq key must be stored as `GROQ_API_KEY` with `PROVIDER=groq` (Groq endpoint). Storing a Groq key as `OPENAI_API_KEY` with `PROVIDER=openai` sends it to OpenAI's servers → 401. Secrets are injected from Infisical, so no key touches disk.

**Booking requires an explicit room.** `create_booking` has `room_type` as a required parameter (`agent.py:135`). "Book it" without naming a room makes the agent (correctly) ask which room before booking — no room, no `create_booking`. The confirmation ID **AH-4827** is hardcoded in the tool (`agent.py:293`); the model only relays it, so it can't be fabricated.

**VAD/endpointing trade-off is real.** Default endpoint-silence is 650 ms (`talk.js`), short enough that a natural pause commits the turn and clips you. Raising the browser slider to ~1100 ms fixed it — the classic "too short clips / too long = dead air" trade-off.

**Changes and RAG:** language change to Spanish and back to English went well. Mentioning the service dog (first transcribed as "duck") got the right answer from the hotel policies.

**Acoustic echo / self-barge-in.** In one of the trial runs I had an error, probably because the voice agent picked up the speaker voice. In the next 2 runs I had no problems.

**macOS / Python 3.14 setup.** Dependencies install cleanly as cp314 wheels (`openai` 2.46, `livekit-api`, `PyJWT`). Audio libs (PortAudio) skipped by choice → Stage 4's terminal-mic cascade not run; the browser is the cascade demo. `import jwt` resolves via **PyJWT**, not the `jwt` package.

## Capacity & cost (right-sized to a real deployment)

`scale_check.py`'s default `--dau 1000000` models a *platform*, not a single hotel. A single 150-room hotel generates only ~40 reservation calls/day (rooms × occupancy ÷ average stay, minus the OTA/web share) — trivial to serve. The economics of a voice agent only make sense at chain or platform scale, so I re-ran the model for a **500-hotel chain (~20,000 calls/day)** with real Groq rates.

Cost per call-minute is built from Groq pricing (STT `whisper-large-v3-turbo` $0.04/hr; LLM `gpt-oss-120b` $0.15/$0.60 per M tokens; **Orpheus TTS $22/M characters**) and anchored to this run's telemetry (~1.5 LLM calls/turn from 66 calls over 45 turns; ~180-char replies): **~$0.014/min with Orpheus, ~$0.002/min with browser TTS.**

| Metric | 1 hotel (~40 calls/day) | 500-hotel chain (Orpheus TTS) | 500-hotel chain (browser TTS) |
|--------|------------------------|-------------------------------|-------------------------------|
| workers | 1 | 15 | 15 |
| peak concurrent calls | 0.9 | 444 | 444 |
| cost / day | $2.24 | **$1,120** | **$160** |
| cost / year (×365) | ~$818 | **~$409k** | **~$58k** |

**The lever is TTS, not infrastructure.** 15 workers serve 500 hotels comfortably — this is not a "million-user" problem. But Orpheus at $22/M characters is ~85% of the per-minute cost: $1,120/day vs $160/day on the browser voice, i.e. ~$350k/year. The neural-voice choice is the dominant cost decision at scale, worth weighing against a cheaper TTS.

*Caveat:* the model bills every call for its full 4-minute duration end-to-end; real calls include silence and human escalations (the `transfer`/REFER path), so actual cost runs lower. STT/LLM rates are stable; the TTS rate and the real speech volume are the soft assumptions to measure first with the client's own call-center data.

## How I ran it (reproduction — macOS + Infisical)

```bash
# --- offline (no key needed): pipeline venv → smoke, tests ---
cd FDE/Assignment_2_voice_agent/pipeline
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PROVIDER=mock .venv/bin/python smoke_test.py
PROVIDER=mock .venv/bin/python -m unittest test_features

cd ../evals && PROVIDER=mock ../pipeline/.venv/bin/python run_evals.py --suite all
cd ../pipeline && .venv/bin/python scale_check.py --dau 1000000
cd ../mocks && PROVIDER=mock ../pipeline/.venv/bin/python demo_call.py
                PROVIDER=mock ../pipeline/.venv/bin/python demo_call.py --transfer

# --- live LiveKit stack (secrets from Infisical, key never on disk) ---
cd ../livekit
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt PyJWT && npm install

# terminal 1 — LiveKit dev server (Docker):
./start_local_server.sh

# terminal 2 — room + browser bridge (live Groq via Infisical):
.venv/bin/python create_room.py
PROVIDER=groq LLM_MODEL=openai/gpt-oss-120b STT_MODEL=whisper-large-v3-turbo \
  TTS_BACKEND=provider TELEMETRY_JSONL=../logs/voice-events.jsonl \
  infisical run --env=dev -- .venv/bin/python talk_server.py

# browser: http://localhost:5173 → Start call → allow mic
```

**Config note:** only `GROQ_API_KEY` is a secret (in Infisical). `PROVIDER`, model overrides, `TTS_BACKEND` and `TELEMETRY_JSONL` are non-secrets set inline; `env_loader.py` uses `os.environ.setdefault`, so the Infisical-injected key is never overwritten. LiveKit dev credentials default in code (`devkey`/`secret`).
