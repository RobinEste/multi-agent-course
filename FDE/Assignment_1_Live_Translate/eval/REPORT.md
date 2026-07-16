# Submission Report — Assignment 1 — Live Translate

- **Student:** Robin Bertus
- **Video demo:** https://www.loom.com/share/cb8e3ac947c849de9bb8a66f5c0838b8
- **Backend target:** `http://localhost:8787`
- **Auto-graded score:** **70 / 70**  ·  manual portion: 30 pts (grader)

## Rubric

| Criterion | Type | Points | Result |
|---|---|---|---|
| Widget lights up (contract works end to end) | auto | 15/15 | translate + batch return valid shapes |
| Caching correctness (two-tier, provable, persistent) | auto | 20/20 | 2nd cached=True, faster=True, sqlite_persisted=True |
| Performance & SLA gate | auto | 15/15 | bench SLA gate PASS |
| Logging & observability | auto | 10/10 | stats_hit_rate=True, health_reports_ai=True, ai_log_file=True, trace_correlated=True |
| Service separation & correct status codes | auto | 10/10 | 400_on_bad_input=True, gateway_nests_ai_health=True |
| LLM & prompt quality (natural Mexican Spanish) | manual | —/20 | **grader** — see evidence + video |
| Deploy & docs | manual | —/10 | **grader** — see evidence + video |

## Evidence

- Sample translation (`Good morning, welcome!`): **¡Buenos días, bienvenido!**
- Cache latency: first `1220 ms` → second `0 ms`
- Trace correlation (one request across both logs): ✅ yes
- Benchmark: hit p95 `10 ms`, miss p95 `1721 ms`, hit rate `78%`, throughput `1220 rps`, SLA **PASS**
- Cost: `$0.000055`/miss; monthly savings from cache `$21.18`
- Deploy: `https://fde.noblesseproducts.com/health` → ✅ ok

<details><summary>Benchmark output</summary>

```
    cost per MISS (avg)         $0.000055
    @ 500,000/mo, no cache      $27.33
    @ 500,000/mo, cached        $6.15
    monthly savings from cache  $21.18
── SLA GATE ────────────────────────────────────────
    PASS  cache_hit_p95_ms         10.1 <= 60
    PASS  cache_miss_p95_ms        1721.0 <= 3500
    PASS  min_cache_hit_rate_pct   77.5 >= 60
    PASS  max_error_rate_pct       0.0 <= 1.0
    PASS  min_throughput_rps       1219.8 >= 20

✅ ALL SLAs MET

Wrote /Users/robin/ODIN/resources/opleidingen/actief/agent-engineering-bootcamp/multi-agent-course/FDE/Assignment_1_Live_Translate/eval/_bench.json
```
</details>
