"""
FDE · Assignment 1 · Python AI Service  (this is the real assignment)
=====================================================================
A small FastAPI service that translates English → Mexican Spanish with:
  - an LLM call            (lib/llm.py)
  - a two-tier cache       (lib/cache.py)  — memory + SQLite
  - structured logging     (lib/logger.py) — provided, wired for you

The Node gateway forwards the browser's requests here. You implement the
TODOs so the widget lights up. Run:

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # then add your API key
    uvicorn app:app --reload --port 8000
"""
import asyncio
import os
import time
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lib.cache import TwoTierCache, _key
from lib.llm import MODEL_DEFAULT, translate_text
from lib.logger import get_logger

load_dotenv()

MODEL = os.getenv("MODEL", MODEL_DEFAULT)
DB_PATH = os.getenv("TRANSLATION_DB_PATH", "translations.db")
# Client-side cap on concurrent LLM calls, shared across all in-flight batches.
# The real ceiling is your Anthropic tier's RPM/TPM (see the x-ratelimit-*
# response headers); this just keeps bursts in check. Env-tunable.
BATCH_CONCURRENCY = int(os.getenv("BATCH_CONCURRENCY", "8"))

app = FastAPI(title="FDE Live Translate — AI Service")
log = get_logger("ai-service")
cache = TwoTierCache(DB_PATH)
_batch_semaphore = asyncio.Semaphore(BATCH_CONCURRENCY)
# One lock per (text, target) key, held across a miss → LLM → set, so concurrent
# identical misses collapse to a single LLM call (upholds "never translate twice").
_inflight: dict[str, asyncio.Lock] = {}

# request/response shapes ----------------------------------------------------
class TranslateIn(BaseModel):
    text: str
    target: str = "es-MX"

class BatchIn(BaseModel):
    texts: list[str]
    target: str = "es-MX"


def _elapsed_ms(t0: float) -> int:
    """Milliseconds since a time.perf_counter() timestamp."""
    return int((time.perf_counter() - t0) * 1000)


# --- cross-cutting: trace id + access log + error boundary -----------------
# One middleware reuses the gateway's X-Request-Id (or mints one), logs every
# request, and echoes the id back; one exception handler turns any unhandled
# error into a 502 with that id. This keeps the route handlers free of that
# plumbing — the same shape the Node gateway uses in its single app.use(...).
@app.middleware("http")
async def trace_and_log(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = rid
    t0 = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-Id"] = rid
    log.info(
        "request",
        extra={
            "requestId": rid,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latencyMs": _elapsed_ms(t0),
        },
    )
    return response


@app.exception_handler(Exception)
async def on_unhandled(request: Request, exc: Exception):
    # Never swallow: log the failure (with detail) and surface a 502 whose body
    # stays generic — internal exception text must not leak to the caller. Echo
    # the trace id on the error response so a 502 is still greppable end-to-end.
    rid = getattr(request.state, "request_id", None)
    log.error("request_error", extra={"requestId": rid, "path": request.url.path, "error": str(exc)})
    headers = {"X-Request-Id": rid} if rid else None
    return JSONResponse(status_code=502, content={"error": "upstream failure"}, headers=headers)


@app.on_event("startup")
async def startup():
    await cache.init()
    log.info("ai_service_started", extra={"model": MODEL, "db": DB_PATH})


# --- core: translate one string --------------------------------------------
async def translate_one(text: str, target: str) -> dict:
    """Translate a single string, using the cache first.

    Returns a dict shaped exactly like the widget expects:
        {"translated": str, "cached": bool, "latencyMs": int, "model": str}
    """
    text = (text or "").strip()
    if not text:
        return {"translated": "", "cached": False, "latencyMs": 0, "model": MODEL}

    t0 = time.perf_counter()

    # Cache first — a hit never calls the LLM.
    cached_value = await cache.get(text, target)
    if cached_value is not None:
        return {"translated": cached_value, "cached": True, "latencyMs": _elapsed_ms(t0), "model": MODEL}

    # Miss. Single-flight per (text, target): concurrent identical misses wait on
    # one lock so the LLM runs once; the waiters find the value on the re-check.
    async with _inflight.setdefault(_key(text, target), asyncio.Lock()):
        cached_value = await cache.get(text, target)
        if cached_value is not None:
            return {"translated": cached_value, "cached": True, "latencyMs": _elapsed_ms(t0), "model": MODEL}
        # (may raise → 502 via the exception handler)
        translated = await translate_text(text, target, model=MODEL)
        await cache.set(text, target, translated, model=MODEL)

    return {"translated": translated, "cached": False, "latencyMs": _elapsed_ms(t0), "model": MODEL}


@app.post("/translate")
async def translate(request: Request, body: TranslateIn):
    result = await translate_one(body.text, body.target)
    log.info(
        "translate",
        extra={
            "requestId": request.state.request_id,
            "cached": result["cached"],
            "latencyMs": result["latencyMs"],
            "chars": len(body.text),
        },
    )
    return result


@app.post("/translate/batch")
async def translate_batch(request: Request, body: BatchIn):
    t0 = time.perf_counter()

    async def translate_bounded(t: str) -> dict:
        async with _batch_semaphore:  # cap concurrent LLM calls
            return await translate_one(t, body.target)

    # Translate each DISTINCT string once, in parallel (bounded). A web page
    # repeats strings, so deduping both avoids redundant LLM calls and keeps the
    # "never call the LLM twice for identical input" guarantee that plain
    # concurrent misses would break. Duplicates reuse the representative result.
    unique = list(dict.fromkeys(body.texts))
    done = await asyncio.gather(*(translate_bounded(t) for t in unique))
    by_text = dict(zip(unique, done))
    results = [by_text[t] for t in body.texts]

    latency = _elapsed_ms(t0)
    hits = sum(1 for r in results if r["cached"])
    log.info(
        "translate_batch",
        extra={
            "requestId": request.state.request_id,
            "count": len(results),
            "unique": len(unique),
            "hits": hits,
            "latencyMs": latency,
        },
    )
    # widget expects {results: [{translated, cached}], latencyMs}
    return {"results": [{"translated": r["translated"], "cached": r["cached"]} for r in results], "latencyMs": latency}


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL, "cacheSize": await cache.size()}


@app.get("/stats")
async def stats():
    return await cache.stats()
