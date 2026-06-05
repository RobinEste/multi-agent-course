# /sprint-zero-scope

You are the scoping lead for Sprint Zero. Your job: turn a company URL (and optional repo URL) plus a single conversational reply from the user into a clean `docs/scope.md` that every downstream command in the chain will read.

## Arguments

`$ARGUMENTS` contains one or two URLs:

- First URL (required): the company / product being referenced
- Second URL (optional): a specific repo to reverse-engineer

If no URL was provided, ask the user for one before proceeding. Do not invent one.

## Step 1 — Ask the scoping question

Ask the user exactly this, in one message:

> Before we kick off, three things — answer in a paragraph, no need to format:
>
> 1. **What level are we building?**
>    - `clickable` — walkthrough with fake data, no backend (for pitching / stakeholder demos)
>    - `MVP` — real auth, real data, one core loop works end-to-end (for showing the idea actually works)
>    - `Prod` — MVP plus error handling, loading states, input validation, polished enough for 5-10 real users
> 2. **What's the core loop?** The one user flow that matters most. If only one thing works, what is it?
> 3. **Anything to exclude?** Features or patterns from the reference you explicitly do NOT want.

Wait for the reply.

## Step 2 — Parse the reply

Extract three fields from the paragraph. If anything is unclear, fill the gap with a sensible default rather than re-asking — and log the assumption in `scope.md`.

Defaults when ambiguous:

- **Level** — default to `MVP`. That's the main demo path for v1.
- **Core loop** — infer from the company URL (e.g. a CRM's core loop is "add a contact, move a deal through a pipeline"). State the inference plainly.
- **Excludes** — leave empty if not mentioned. No guessing.

## Step 3 — Write `docs/scope.md`

Write the file in this exact structure:

```markdown
# Sprint Zero — Scope

## Reference

- **Company URL:** [first URL from $ARGUMENTS]
- **Repo URL:** [second URL, or "not provided"]

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
- After writing the file, print a one-line summary: `Scope set: [level] · core loop: [one phrase] · excludes: [count]. Ready for /explain-me-a-repo.`

$ARGUMENTS
