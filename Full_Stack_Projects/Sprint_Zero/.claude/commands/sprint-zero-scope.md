# /sprint-zero-scope

You are the scoping lead for Sprint Zero. Your job: turn a company URL (and optional repo URL) plus a single conversational reply from the user into a clean `docs/scope.md` that every downstream command in the chain will read.

## Arguments

`$ARGUMENTS` contains one or two URLs:

- First URL (required): the company / product being referenced
- Second URL (optional): a specific repo to reverse-engineer

If no URL was provided, ask the user for one before proceeding. Do not invent one.

## Step 1 — Ask the scoping question

First read `.claude/stacks.md` so you can describe the options accurately and pick sane defaults.

Ask the user exactly this, in one message:

> Before we kick off, a few things — answer in a paragraph, no need to format. Skip anything you don't care about and I'll use the sensible default (noted in brackets).
>
> 1. **What level are we building?**
>    - `clickable` — walkthrough with fake data, no backend (for pitching / stakeholder demos)
>    - `MVP` — real auth, real data, one core loop works end-to-end (for showing the idea actually works) **[default]**
>    - `Prod` — MVP plus error handling, loading states, input validation, polished enough for 5-10 real users
> 2. **What's the core loop?** The one user flow that matters most. If only one thing works, what is it?
> 3. **What kind of project is it?**
>    - `web-app` — a UI plus an API **[default]**
>    - `api-service` — a backend/API only, no frontend
>    - `cli-tool` — a command-line program
> 4. **Which stack?**
>    - `node-react` — Express + React/Vite **[default]**
>    - `nextjs` — one Next.js app (UI + API together)
>    - `python-react` — FastAPI + React/Vite
> 5. **Where does data live?**
>    - `local` — SQLite on your machine, no account or keys needed, runs right after clone **[default]**
>    - `supabase` — real Postgres + hosted auth (needs a free Supabase project and a `.env`)
> 6. **Anything to exclude?** Features or patterns from the reference you explicitly do NOT want.

Wait for the reply.

## Step 2 — Parse the reply

Extract the fields from the paragraph. If anything is unclear, fill the gap with a sensible default rather than re-asking — and log the assumption in `scope.md`.

Defaults when ambiguous:

- **Level** — default to `MVP`. That's the main demo path for v1.
- **Core loop** — infer from the company URL (e.g. a CRM's core loop is "add a contact, move a deal through a pipeline"). State the inference plainly.
- **Project type** — default to `web-app`.
- **Stack profile** — default to `node-react`.
- **Data layer** — default to `local`. It needs no account and runs straight after clone, which is the right default for a demo kit.
- **Excludes** — leave empty if not mentioned. No guessing.

Validate the combination against `.claude/stacks.md`. All combinations are allowed, but note these implications (and log them as assumptions):

- `api-service` and `cli-tool` have **no frontend** — the stack profile's frontend half is ignored, and there will be no auth *dance* in a browser.
- `cli-tool` has no server; the data layer is almost always `local`.
- For `nextjs`, UI and API live in one app on one port — there is no separate `server/`/`client/` split.

## Step 3 — Write `docs/scope.md`

Write the file in this exact structure:

```markdown
# Sprint Zero — Scope

## Reference

- **Company URL:** [first URL from $ARGUMENTS]
- **Repo URL:** [second URL, or "not provided"]

## Build configuration

- **Project type:** [web-app | api-service | cli-tool]
- **Stack profile:** [node-react | nextjs | python-react]
- **Data layer:** [local | supabase]

[One sentence on what this combination means concretely — e.g. "A React+Vite UI talking to an Express API, with data and auth stored locally in SQLite (no external account needed)." Resolve the concrete dirs/ports/commands from .claude/stacks.md downstream — do not restate them here.]

## Build level

**[clickable | MVP | Prod]**

[One sentence describing what this level means for this build.]

## Core loop

[One or two sentences describing the one user flow that must work end-to-end.]

## Excludes

- [item]
- [item]

(or "None specified." if empty)

## Assumptions made during scoping

- [Each default or inference, one bullet. Tag with `[ASSUMED]`.]

(or omit this section entirely if nothing was assumed)
```

## Rules

- Write `docs/scope.md` directly — no preamble in chat beyond the scoping question and a one-line confirmation after the file is written.
- Never invent excludes. If the user didn't mention any, the section says "None specified."
- Every default or inference must appear in the Assumptions section with `[ASSUMED]`. The downstream chain treats the scope as source of truth, so assumptions need to be visible.
- After writing the file, print a one-line summary: `Scope set: [level] · [project-type]/[stack]/[data-layer] · core loop: [one phrase] · excludes: [count]. Ready for /explain-me-a-repo.`

$ARGUMENTS
