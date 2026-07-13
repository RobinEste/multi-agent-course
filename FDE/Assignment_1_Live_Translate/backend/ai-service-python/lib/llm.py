"""
lib/llm.py — the LLM translation call  (TODO: you implement)
============================================================
One job: turn an English string into Mexican Spanish using an LLM.

Provider is your choice. The default example below is Anthropic Claude
(`pip install anthropic`, set ANTHROPIC_API_KEY). Hamza's launched version
used Google Gemini — either is fine. Whatever you pick:

  - Write a PROMPT that pins the register to Mexican Spanish (es-MX), not
    generic/Castilian Spanish. Ask for ONLY the translation, no preamble.
  - Keep numbers, prices ($), and product/model codes unchanged.
  - Return a clean string (strip quotes/whitespace the model may add).

FAIL LOUD: do NOT wrap the call in a try/except that returns `text` on error.
If the provider fails, let the exception propagate so the caller returns a 502.
Silently returning the untranslated input is an automatic fail on this
assignment (and a real production bug — it ships English while looking healthy).
"""
import os

from anthropic import AsyncAnthropic

# Default is Anthropic's Haiku 4.5: fast and cheap, which is the right trade-off
# for short UI strings (helps both the miss-latency SLA and the cost model).
# Override with MODEL in the environment (e.g. via Infisical) to use another model.
MODEL_DEFAULT = os.getenv("MODEL", "claude-haiku-4-5-20251001")

_SYSTEM_PROMPT = """\
You are a professional localizer specializing in Mexican Spanish (es-MX).

Translate the English text in the user message into natural, idiomatic Mexican \
Spanish — the vocabulary and register a reader in Mexico expects, never Castilian \
or neutral "international" Spanish.

<rules>
- Output only the translated text, and nothing else.
- Keep numbers, prices, currency symbols ($), URLs, emails, and product/model/SKU codes exactly as written.
- Mirror the source's capitalization and punctuation; a short UI label stays a short UI label.
- If a segment has nothing to translate (a brand name, a bare code, or text already in Spanish), return it unchanged.
</rules>

<mexican_vocabulary>
Prefer Mexican terms over Spain's: computadora (not ordenador), celular (not móvil), lentes (not gafas), carro (not coche), camión (not autobús).
</mexican_vocabulary>

<examples>
Add to cart → Agregar al carrito
Free shipping on orders over $50. → Envío gratis en pedidos de más de $50.
Track your SKU-4471 shipment → Rastrea tu envío SKU-4471
</examples>"""

# One shared async client per process; it reads ANTHROPIC_API_KEY from the env.
_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic()
    return _client


def _clean(text: str) -> str:
    """Strip whitespace and a single pair of wrapping quotes the model may add.

    Only strips when the quote genuinely wraps the whole string (the same quote
    does not occur inside), so content quotes like  "Sí", dijo, "no"  stay intact.
    """
    out = text.strip()
    if len(out) >= 2 and out[0] in "\"'" and out[-1] == out[0] and out[0] not in out[1:-1]:
        out = out[1:-1].strip()
    return out


async def translate_text(text: str, target: str = "es-MX", model: str = MODEL_DEFAULT) -> str:
    """Return `text` translated into Mexican Spanish (es-MX).

    Fails loud: any provider/LLM error propagates so the caller returns a 502.
    We never return the untranslated input as if it succeeded.
    """
    client = _get_client()
    # 2026-07-13: system is a plain string on purpose — no prompt caching yet.
    # Haiku 4.5's cacheable minimum is 4096 tokens; this prompt is far below it, so a
    # cache_control marker would silently do nothing. Switch to the structured
    # system=[{"type":"text","text":..., "cache_control":{"type":"ephemeral"}}] form
    # only once the prompt exceeds that minimum (per-tenant glossary). See opleiding.md.
    msg = await client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.2,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    parts = [block.text for block in msg.content if getattr(block, "type", None) == "text"]
    return _clean("".join(parts))
