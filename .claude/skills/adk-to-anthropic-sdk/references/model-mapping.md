# Model Mapping: ADK → Anthropic

ADK projects specify models as Gemini strings, or via `LiteLlm("provider/model")`, or already-Anthropic strings through LiteLlm. Map to a current Anthropic model id by intent, not by exact name.

## Current Anthropic model IDs
- `claude-opus-4-8` — most capable; use where the source wanted the strongest reasoning model.
- `claude-sonnet-4-6` — balanced default; use this unless there's a clear reason not to.
- `claude-haiku-4-5-20251001` — fastest/cheapest; use for high-volume, simple, or latency-sensitive agents.

When in doubt, default to `claude-sonnet-4-6`.

## Heuristic mapping

| Source model string | Map to | Why |
|----------------------|--------|-----|
| `gemini-*-pro`, `gemini-2.5-pro`, "pro"/"ultra" tiers | `claude-opus-4-8` | top-tier intent |
| `gemini-*-flash`, `gemini-2.0-flash`, default mid models | `claude-sonnet-4-6` | balanced default |
| `gemini-*-flash-lite`, `*-nano`, "lite"/"mini" | `claude-haiku-4-5-20251001` | cheap/fast intent |
| `LiteLlm("anthropic/claude-...")` | the matching current Claude id | already Anthropic; upgrade to current id |
| `LiteLlm("openai/...")` or other providers | `claude-sonnet-4-6` (note in INVENTORY) | cross-provider; pick balanced default and flag |
| unknown / unrecognized | `claude-sonnet-4-6` | safe default |

## Notes
- Record every mapping decision in `INVENTORY.md` so the user can override (e.g. bump everything to Opus, or pin Haiku for cost).
- Don't hardcode a model in `agent_runtime.py`; pass it per-`Agent` so different agents can use different tiers exactly as the ADK tree did.
- These ids are current as of this skill's writing; if a call 404s on model id, the id may have changed — tell the user to check https://docs.claude.com/en/docs/about-claude/models for the latest and update the mapping.
