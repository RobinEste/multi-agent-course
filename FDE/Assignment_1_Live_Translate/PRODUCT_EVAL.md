# Product Evaluation — Live Translate

- **Student:** Robin Bertus
- **Date:** 2026-07-16
- **Video demo:** https://www.loom.com/share/cb8e3ac947c849de9bb8a66f5c0838b8
- **LLM provider / model:** Anthropic · claude-haiku-4-5-20251001
- **Backend target:** https://fde.noblesseproducts.com

## Verdict

The two-tier cache is great. The proposition I am looking at (internal company translation) would work if some kind of RAG was added with specific company vocabulary. 

**Rubric score (from `eval/report.json`):** 70 / 70 auto (+ 30 manual)

## 1. Performance & cost (from `benchmark/bench.py`)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | 10 ms | ≤ 60 ms | ✅ |
| Cache miss p95 | 1721 ms | ≤ 3500 ms | ✅ |
| Cache hit rate | 78 % | ≥ 60 % | ✅ |
| Throughput | 1220 req/s | ≥ 20 | ✅ |
| Error rate | 0 % | ≤ 1 % | ✅ |
| Cost per miss | $0.000055 | — | — |
| Monthly savings from cache | $21.18 | — | — |

## 2. Live-website test

- **Site tested:** https://www.coolblue.nl/en/product/967626/bluebuilt-qi2-2-wireless-charger-25w-black.html. Homedepot is geoblocked from Europe so I tested a different site. 
- **Translated whole page?** yes, layout intact. 
- **Coverage gaps:** Everything translated. Names of places of other stores stayed intact.
- **Cache on re-translate:** yes, very quickly
- **Resilience:** some words need a " " behind it
- **Screenshots:** attached to submission (Loom video)

### Sample translations (6–8)

| Original (EN)                                                                                   | Translation (es-MX)                                                                     | Numbers/prices/codes kept?                  | OK? |
| ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------- | --- |
| Retail price 49,99                                                                              | Precio de venta al público 49,99                                                        | yes, but price is with "," = dutch notation | ?   |
| BlueBuilt Qi2.2 Wireless Charger 25W Black                                                      | Cargador Inalámbrico BlueBuilt Qi2.2 25W Negro                                          | yes                                         | yes |
| Pros and cons<br>According to our wireless charger expert                                       | Ventajas y desventajas Según nuestro experto en cargadores inalámbricos                 | yes                                         | yes |
| At least a **5 year** warranty on your product                                                  | Al menos un**5 años**garantía en tu producto                                            | yes, but extra " " needed                   | no  |
| The Samsung A series and iPhone models older than the iPhone 8 don't support wireless charging. | La serie Samsung A e iPhones más antiguos que el iPhone 8 no soportan carga inalámbrica | yes                                         | yes |
| Place your device on the charger to start charging.                                             | Coloca tu dispositivo en el cargador para comenzar a cargar.                            | yes                                         | yes |
| In my shopping cart                                                                             | En mi carrito de compras                                                                | yes                                         | yes |

## 3. Dimension scorecard

| Dimension                          | Pass / Partial / Fail | Evidence                                                                          |
| ---------------------------------- | --------------------- | --------------------------------------------------------------------------------- |
| Translation accuracy               | Pass                  | cart => carrito                                                                   |
| Mexican-Spanish register (es-MX)   | Pass                  | cart => carrito instead of cesta                                                  |
| Numbers / prices / codes preserved | Pass                  | eval-sample + `<source>`-prompt keeps prices and codes and numbers intact         |
| Page coverage                      | Pass                  | see Loom video                                                                    |
| Cache effectiveness                | Pass                  | hit p95 10 ms vs miss p95 1721 ms; 78% hit rate; survives redeploy (named volume) |
| Latency vs SLA                     | Pass                  | all 5 SLA-checks green (see §1)                                                   |
| Error handling (no silent English) | Pass                  | `lib/llm.py` fails → 502; no English output                                       |
| Resilience on a real site          | Pass                  | see Loom video                                                                    |
| UX polish                          | Partial               | ok, but could be a bit more polished                                              |

## 4. Top fixes before shipping

1. Deliver the rate-limit message to the user. The gateway returns a friendly JSON body on a 429, but the provided widget (widget/translation-widget.js:243) does throw new Error("HTTP " + res.status) and discards the body — so a rate-limited user just sees "HTTP 429" in red. Fixing it means editing widget/, which the red-line forbids, so it needs an upstream change to the provided widget.

2. Bound memory growth. app.py's _inflight dict never removes its per-key locks, and the in-memory cache tier (lib/cache.py) has no eviction. A caller sending many distinct strings grows the process without limit; mem_limit (512m) only caps the blast radius, and on a shared host the OOM killer could take a neighbouring container. Fix: drop _inflight entries after use, and add an LRU/size cap to the in-memory tier.

3. Add cache invalidation and a retention policy. The SQLite cache lives in a named volume and is permanent — a source page that changes its wording keeps the stale translation forever, and the DB accumulates raw page text with no TTL. Add a POST /clear-cache endpoint (an unbuilt stretch goal) plus TTL-based invalidation, and a retention limit — the stored source text is also a privacy consideration for real content.

4. Preserve whitespace around inline fragments. The widget translates each text node separately, but `lib/llm.py`'s `_clean()` does `text.strip()`, which drops the leading/trailing spaces on a bolded fragment (`" 5 year "` → `"5 años"`), so it runs into its neighbours (`un5 añosgarantía` — see §2). Fix: only strip when the node is standalone, or re-attach the original leading/trailing whitespace after translating.

5. Add company-specific vocabulary (next feature, not a shipping blocker). Out of the box the model produces general Mexican Spanish. For the internal-company-translation use case in the Verdict, a RAG step that retrieves a per-tenant glossary — product names, internal jargon, preferred terms — and injects it into the prompt would keep translations on-brand and consistent across the organization.
