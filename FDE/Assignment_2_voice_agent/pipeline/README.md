# Pipeline — Hands-On Voice Loop (Layer A + B)

The part attendees build/run live. A terminal voice agent:

```
  mic  →  VAD  →  STT  →  LLM agent (+tools)  →  TTS  →  speakers
```

No phone, no SIP — just your laptop mic. Telephony is covered by `../mocks/`.

## Provider: one adaptor, two backends (Groq / OpenAI)

Groq speaks the OpenAI API dialect, so `providers.py` is a single code path for both.
**You switch backends by flipping one line in `.env`** (`PROVIDER=groq` → `openai`); model
names default sensibly per provider.

| Stage | Groq (free tier) | OpenAI (your key) |
|-------|------------------|-------------------|
| LLM | `llama-3.3-70b-versatile` | `gpt-4o-mini` |
| STT | `whisper-large-v3-turbo` | `whisper-1` |
| TTS | `playai-tts` *(preview — accept terms)* | `tts-1` |

**Recommended for the workshop:** `PROVIDER=groq` (free + fast). If Groq TTS gives you
trouble, set `TTS_BACKEND=system` to use a local voice command — the demo keeps working
at zero cost. Switching to OpenAI later is just `PROVIDER=openai` + your key.

For a more natural OpenAI voice, use:

```env
TTS_BACKEND=provider
TTS_MODEL=gpt-4o-mini-tts
TTS_VOICE=marin
TTS_INSTRUCTIONS=Speak warmly and naturally, like a calm support representative.
```

> Avoid the OpenAI **Realtime** API for this — it's ~10–20× the price. The pipeline here keeps
> STT/LLM/TTS separate, which is both cheaper *and* what you want pedagogically (each stage is
> visible and individually timed).

## Setup (send to attendees the day before)

```bash
cd voice-agent-workshop/pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config.example.env .env      # set PROVIDER + the matching API key
```

- Get a **free Groq key** at https://console.groq.com and put it in `GROQ_API_KEY`.
- `sounddevice` needs PortAudio: `brew install portaudio` if the import fails.
- Groq TTS requires accepting model terms once in the Groq console.

## Test it with no network (offline mock)

There's a third backend, `PROVIDER=mock`, that returns scripted STT/LLM/TTS with **no key,
no network, and no SDK installed** — the same interface as Groq/OpenAI, so it exercises the
real loop and tool calls. Use it for rehearsals, CI, or a projector that has no internet.

```bash
python smoke_test.py                    # asserted offline end-to-end (tools + actions)
PROVIDER=mock python voice_loop.py --text   # play with it interactively, offline
```

`smoke_test.py` drives scripted turns through the real `Agent` and checks the
hotel-booking guardrail, availability lookup, booking confirmation, transfer,
and hangup paths. Green here means the wiring is correct before you ever add a key.

## Run

```bash
python voice_loop.py          # real mic (VAD endpointing + STT + TTS)
python voice_loop.py --text   # type your turn — needs NO audio libs, NO mic
```

`--text` mode still uses the real LLM + tools over your chosen provider, so it's the
always-works fallback when someone's mic or PortAudio misbehaves. Each turn prints a
per-stage latency breakdown (stt / llm+tools / tts) against the ~800 ms target.

## Files

| File | Role |
|------|------|
| `providers.py` | The adaptor — Groq/OpenAI via the OpenAI SDK. `chat` / `transcribe` / `synthesize`. |
| `agent.py` | The brain — system prompt + hotel tools (`check_availability`, `create_booking`, `transfer_to_human`, `end_call`) via OpenAI-style tool calling. |
| `voice_loop.py` | The loop — VAD endpointing, STT, agent turn, TTS playback, latency timing, `--text` mode. |

Try: *"I need a room from August 12 to August 14 for two guests."* → watch
`check_availability` fire and the agent offer room options. Then say
*"Book it for Priya Shah at priya@example.com."* → `create_booking` returns a confirmation.
*"Can I talk to a person?"* → `transfer_to_human` → `[SIP REFER]`.

## What to demo at each checkpoint

1. **Layer A:** ask for a room, hear it answer. "We have a voice agent."
2. **Layer B:** "I need a room for two guests..." → `check_availability` fires in the logs.
3. **Latency:** point at the per-turn breakdown — the LLM stage dominates; that's why a fast
   model (Groq) matters.
4. **Hand-off:** "Now — how does a real phone call get here?" → open `../mocks/`.

## Budget check
On Groq's free tier the whole workshop is **$0**. If you fall back to OpenAI: pipeline STT+LLM+TTS
≈ **~$1–2** for a full session — comfortably under $10.
