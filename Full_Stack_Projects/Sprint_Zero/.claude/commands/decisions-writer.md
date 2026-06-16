# /decisions-writer

Compare what we're building (PRD) to what the reference does (reference brief). Write a plain-language decisions log for a PM audience.

## Step 1 — Read inputs

Read all three:

- `docs/scope.md` — build level drives how aggressive the cuts are
- `docs/reference-brief.md` — the feature inventory to compare against
- `docs/prd.md` — what we're actually building

If any is missing, stop and tell the user which command to run first.

## Step 2 — Identify gaps

Walk the reference brief's feature inventory. For each feature:

- **Present in PRD** — no decision needed, skip
- **Simplified in PRD** — write a scope decision (reference does X, we do a lighter Y)
- **Absent in PRD** — write a scope decision (reference does X, we chose not to)
- **Deliberately excluded** (matches `docs/scope.md` excludes) — write a scope decision citing the exclusion

Then capture the deliberate technical choices — read the **build configuration** from `docs/scope.md` and record the *actual* choices, not a fixed stack:

- The resolved stack profile (e.g. React + Vite + Express, or Next.js, or FastAPI + React)
- The data layer (`local` SQLite + self-issued JWT, or `supabase` Postgres + Auth) and why
- The project type (web-app / api-service / cli-tool)
- Testing approach (Playwright via MCP for web apps; HTTP tests for services; command runs for CLIs)
- Build level cuts (see below)

## Step 3 — Scope level calibration

The build level determines how much explanation each cut needs:

- `clickable` — many cuts, brief reasoning ("out of scope for a clickable demo")
- `MVP` — moderate cuts, per-cut reasoning ("core loop only")
- `Prod` — fewer cuts, more considered reasoning (these are the cuts that survive real users)

**Auth is never a scope cut.** It's in every level. Don't list "authentication" as a decision.

## Step 4 — Write `docs/decisions.md`

```markdown
# Decisions

_Sprint Zero build compared to [reference name]. Level: [level]._

## Why this document exists

Short paragraph: what we built, what we compared it against, and why the cuts were made. Frame for a PM audience — this is the doc stakeholders read to understand the simplification.

## Scope decisions

### [Decision title, written as a short phrase]

- **Reference does:** [what the reference does, one line]
- **We chose to:** [what we're doing instead, one line]
- **Reason:** [tie to the build level and/or core loop from scope.md]

(repeat for each gap)

## Technical decisions

### Stack: [resolved profile + data layer from scope.md]

- **We chose:** [e.g. "React (Vite) frontend, Express backend, local SQLite + self-issued JWT" — state what scope.md actually specifies]
- **Reason:** [tie to why — e.g. "local data layer so the demo runs with zero setup", or "Supabase for a real hosted Postgres the team can inspect". Sprint Zero ships from a small catalog of profiles so the build stays predictable.]

### Testing: Playwright via MCP

- **We chose:** Playwright driven by the QA sub-agent through the Playwright MCP
- **Reason:** Browser-driven tests catch the real user journey, including the auth dance. MCP means the agent drives the browser without us wiring a test framework by hand.

### Build level: [clickable | MVP | Prod]

- **We chose:** [level]
- **Reason:** [one or two sentences on why this level fits the user's goal from scope.md]

(add more technical decisions here if the PRD surfaced any)

## What we'd add next

The most valuable cuts that could be restored in a v2. Rank them — what would deliver the most user value per hour of work? 3-5 entries.
```

## Rules

- Plain language for a PM audience. No "authentication middleware" — say "login and sessions."
- Every scope decision must tie its reasoning back to either the build level or the core loop from `docs/scope.md`. "We cut it because we felt like it" is not a valid reason.
- Do not list authentication as a scope decision. It's in every level.
- Write to `docs/decisions.md`. No user confirmation needed.
- After writing, print: `Decisions logged. [N] scope cuts, [N] technical decisions. Ready for /user-story-writer.`

$ARGUMENTS
