"""WebSocket voice endpoint — orchestrates the cascade around the UNTOUCHED text pipeline.

Turn model (accumulate-and-combine):
  * The user can speak in several bursts. Each burst is transcribed (STT) and APPENDED
    to a pending buffer, so the query grows: "status of my order" + "and summary of
    last month".
  * Whenever the user starts speaking again, any answer in progress is STOPPED
    (the agent turn is cancelled) — the user is still adding to their question.
  * When the user goes quiet for SETTLE_MS, the WHOLE combined buffer is sent through
    sanitize -> A2A Judge -> ADK agent (+MCP tools, Mem0) -> A2A Masker -> streamed TTS.
The Judge/agent/Masker are the exact objects web.py uses for /api/chat — nothing dupes.

Protocol (see ui.js for the client side):
  client -> server   binary frame              one speech burst, 16-bit PCM mono @16kHz
  client -> server   {"type":"interrupt"}      user started speaking: stop the answer
  server -> client   {"type":"partial_transcript","text":...}   combined query so far
  server -> client   {"type":"processing"}     combined query sent to the agent
  server -> client   {"type":"tool_call"|"response_text"|"blocked"|"timing"
                      |"turn_end"|"error", ...}
  server -> client   binary frame              TTS audio chunk, 16-bit PCM mono @24kHz
"""

import asyncio
import json
import os
import re
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode

from cs_agent.security.sanitizer import sanitize_input
from cs_agent.voice.stt import transcribe
from cs_agent.voice.tts import synthesize_stream


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# MASK=true  -> buffer the full reply and run the A2A Masker before speaking (safe).
# AGENT_RESPONSE_STREAM=true -> speak each sentence as the agent generates it.
# Interlock: streaming is only allowed when masking is OFF (you can't mask a reply
# you're speaking sentence-by-sentence before it exists). MASK wins.
MASK_ENABLED = _flag("MASK", "true")
AGENT_RESPONSE_STREAM = _flag("AGENT_RESPONSE_STREAM", "false")
STREAM_ENABLED = AGENT_RESPONSE_STREAM and not MASK_ENABLED


def _config_warnings() -> list[str]:
    """Surface conflicting / degenerate voice-config combinations at startup."""
    warnings = []
    if AGENT_RESPONSE_STREAM and MASK_ENABLED:
        warnings.append(
            "AGENT_RESPONSE_STREAM=true is being IGNORED because MASK=true. A reply "
            "cannot be masked while it is spoken sentence-by-sentence, so streaming is "
            "turned OFF. Set MASK=false to enable streaming.")
    if MASK_ENABLED and not os.getenv("GOOGLE_CLOUD_PROJECT", "").strip():
        warnings.append(
            "MASK=true but GOOGLE_CLOUD_PROJECT is not set. The Data Masker still runs "
            "(costing ~5s per reply) but returns the text UNMASKED — no PII is actually "
            "removed. Set GOOGLE_CLOUD_PROJECT to mask for real, or MASK=false to skip it.")
    return warnings


def print_config_warnings():
    for msg in _config_warnings():
        print(f"\033[1;33mWARNING (voice config):\033[0m {msg}")

_UI_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.js")
_AUDIO_CHUNK = 48000   # bytes per binary frame (~1s of 24 kHz PCM)
_SETTLE_MS = 1500      # quiet time after the last burst before the query is sent

# Pull the COMPLETE sentences off a growing buffer, leaving the trailing partial behind.
_SENT_END = re.compile(r"[.!?…](?:[\"')\]]+)?(?:\s|$)")


def _take_complete(buf: str):
    matches = list(_SENT_END.finditer(buf))
    if not matches:
        return "", buf
    cut = matches[-1].end()
    return buf[:cut], buf[cut:]


def make_voice_router(*, runners, session_service, judge, mask) -> APIRouter:
    router = APIRouter()

    @router.get("/voice/ui.js", include_in_schema=False)
    def ui_js():
        return FileResponse(_UI_JS, media_type="application/javascript")

    @router.websocket("/voice/ws")
    async def voice_ws(ws: WebSocket):
        await ws.accept()
        user_id = ws.query_params.get("user_id", "")
        if not user_id or user_id not in runners:
            await ws.send_text(json.dumps({"type": "error", "message": "Not logged in."}))
            await ws.close()
            return

        pending = ""                       # accumulated, not-yet-answered transcript
        agent_task: asyncio.Task | None = None
        settle_task: asyncio.Task | None = None
        stt_lock = asyncio.Lock()          # serialize STT so bursts append in order

        async def send_json(obj: dict):
            await ws.send_text(json.dumps(obj))

        # ---- the answer half of the cascade (runs on the COMBINED query) ----------
        async def run_agent(text: str):
            nonlocal pending
            timing: dict[str, float] = {}

            def clock(stage, t0):
                timing[stage] = round(time.perf_counter() - t0, 2)

            try:
                await send_json({"type": "processing"})

                # [1] local sanitizer
                try:
                    clean = sanitize_input(text)
                except ValueError as exc:
                    await send_json({"type": "blocked", "stage": "sanitizer",
                                     "response": f"Input rejected by sanitizer: {exc}"})
                    await send_json({"type": "turn_end"})
                    pending = ""
                    return

                # [2] A2A Security Judge
                t = time.perf_counter()
                if not await judge(clean):
                    await send_json({"type": "blocked", "stage": "judge",
                                     "response": "Blocked by the A2A Security Judge."})
                    await send_json({"type": "turn_end"})
                    pending = ""
                    return
                clock("judge", t)

                runner = runners[user_id]
                content = types.Content(role="user", parts=[types.Part(text=clean)])

                if STREAM_ENABLED:
                    # ---- STREAMING (no mask) — text paced to the AUDIO ------------
                    # Gemini TTS returns NO word timestamps, so we fake sync: for each
                    # finished sentence we synthesise the whole clip, measure its exact
                    # playback duration from the PCM byte count, and send a `caption`
                    # (sentence text + dur_ms) right before its audio. The browser then
                    # reveals that sentence's words spread across that duration, anchored
                    # to when the clip actually starts playing — so words appear roughly
                    # as they're heard. Approximate (no real alignment) but looks synced.
                    t = time.perf_counter()
                    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
                    tool_calls = []
                    tts_buffer = ""    # generated text not yet synthesised to speech
                    display = ""       # full text spoken/shown so far
                    first_audio = True

                    async def speak_segment(segment: str):
                        nonlocal first_audio, display, pending
                        audio = bytearray()
                        async for chunk in synthesize_stream(segment):
                            audio.extend(chunk)
                        if not audio:
                            return
                        # 24 kHz, 16-bit (2 bytes), mono -> seconds = bytes / 2 / 24000
                        dur_ms = int(len(audio) / 2 / 24000 * 1000)
                        if first_audio:
                            timing["first_audio"] = round(time.perf_counter() - t, 2)
                            first_audio = False
                            pending = ""   # answer started -> next speech is a NEW query
                        # caption BEFORE audio so the client can arm the word reveal
                        await send_json({"type": "caption", "text": segment, "dur_ms": dur_ms})
                        display += segment
                        for i in range(0, len(audio), _AUDIO_CHUNK):
                            await ws.send_bytes(bytes(audio[i:i + _AUDIO_CHUNK]))

                    seen_partial = False
                    async for event in runner.run_async(
                            user_id=user_id, session_id=f"session_{user_id}",
                            new_message=content, run_config=run_config):
                        for fc in (event.get_function_calls() or []):
                            call = {"name": fc.name, "args": dict(fc.args or {})}
                            tool_calls.append(call)
                            await send_json({"type": "tool_call", **call})
                        txt = None
                        if event.content and event.content.parts and event.content.parts[0].text:
                            txt = event.content.parts[0].text
                        if txt is None:
                            continue
                        if getattr(event, "partial", False):
                            seen_partial = True
                        elif seen_partial:
                            continue   # redundant final aggregate that repeats the partials
                        tts_buffer += txt
                        head, tts_buffer = _take_complete(tts_buffer)
                        if head.strip():
                            await speak_segment(head)         # caption + audio per sentence
                    if tts_buffer.strip():
                        await speak_segment(tts_buffer)       # trailing partial sentence
                    clock("agent_tts", t)
                    # finalise the bubble (full text + tool steps) once, after the reveal
                    await send_json({"type": "response_text", "text": display.strip(),
                                     "tool_calls": tool_calls})
                    pending = ""
                else:
                    # ---- BUFFERED: full reply, optional A2A Masker, then speak ----
                    t = time.perf_counter()
                    tool_calls, final_text = [], ""
                    async for event in runner.run_async(
                            user_id=user_id, session_id=f"session_{user_id}", new_message=content):
                        for fc in (event.get_function_calls() or []):
                            call = {"name": fc.name, "args": dict(fc.args or {})}
                            tool_calls.append(call)
                            await send_json({"type": "tool_call", **call})
                        if event.is_final_response() and event.content:
                            final_text = event.content.parts[0].text or ""
                    clock("agent", t)

                    if MASK_ENABLED:
                        t = time.perf_counter()
                        final_text = await mask(final_text)
                        clock("mask", t)

                    t = time.perf_counter()
                    text_sent = False
                    async for chunk in synthesize_stream(final_text):
                        if not text_sent:
                            timing["first_audio"] = round(time.perf_counter() - t, 2)
                            await send_json({"type": "response_text", "text": final_text,
                                             "tool_calls": tool_calls})
                            text_sent = True
                            pending = ""
                        for i in range(0, len(chunk), _AUDIO_CHUNK):
                            await ws.send_bytes(chunk[i:i + _AUDIO_CHUNK])
                    clock("tts", t)
                    if not text_sent:
                        await send_json({"type": "response_text", "text": final_text,
                                         "tool_calls": tool_calls})
                        pending = ""

                await send_json({"type": "timing", "stages": timing})
                await send_json({"type": "turn_end"})
                pending = ""                          # answered — clear the buffer
            except asyncio.CancelledError:
                # user spoke again; keep `pending` so the next run includes it.
                await send_json({"type": "turn_end", "reason": "interrupted"})
                raise
            except Exception as exc:                  # keep the socket alive
                await send_json({"type": "error", "message": str(exc)[:300]})
                await send_json({"type": "turn_end"})
                pending = ""

        # ---- fire the agent once the user has been quiet for SETTLE_MS ------------
        async def settle_then_run():
            nonlocal agent_task
            try:
                await asyncio.sleep(_SETTLE_MS / 1000)
            except asyncio.CancelledError:
                return
            query = pending.strip()
            if query:
                agent_task = asyncio.create_task(run_agent(query))

        def restart_settle():
            nonlocal settle_task
            if settle_task and not settle_task.done():
                settle_task.cancel()
            settle_task = asyncio.create_task(settle_then_run())

        # ---- one speech burst arrived: stop any answer, transcribe, accumulate ----
        async def handle_burst(pcm: bytes):
            nonlocal pending, settle_task
            if settle_task and not settle_task.done():
                settle_task.cancel()
            async with stt_lock:
                text = await transcribe(pcm)
            if text:
                pending = f"{pending} {text}".strip() if pending else text
                await send_json({"type": "partial_transcript", "text": pending})
            restart_settle()

        def stop_answer():
            nonlocal agent_task
            if agent_task and not agent_task.done():
                agent_task.cancel()

        try:
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if msg.get("bytes") is not None:
                    stop_answer()                       # a burst supersedes any answer
                    asyncio.create_task(handle_burst(msg["bytes"]))
                elif msg.get("text"):
                    try:
                        data = json.loads(msg["text"])
                    except json.JSONDecodeError:
                        continue
                    if data.get("type") == "interrupt":
                        stop_answer()                   # immediate stop on speech onset
        except WebSocketDisconnect:
            pass
        finally:
            for t in (agent_task, settle_task):
                if t and not t.done():
                    t.cancel()

    return router
