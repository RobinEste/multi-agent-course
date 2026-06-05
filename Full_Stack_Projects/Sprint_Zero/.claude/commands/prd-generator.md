# /prd-generator

Generate `docs/prd.md` from the scope and reference brief. This is a chained command — it reads inputs from files, not from the user.

## Step 1 — Read inputs

Read both:

- `docs/scope.md` — build level, core loop, excludes
- `docs/reference-brief.md` — what the reference does, its features, its core user flow

If either is missing, stop and tell the user which one to run first (`/sprint-zero-scope` or `/explain-me-a-repo`).

## Step 2 — Shape the PRD

The PRD describes the product Sprint Zero will build, **not** the reference. Use the reference brief for inspiration; the scope file is the boundary.

Rules for shaping:

- The core loop from `docs/scope.md` is the spine of the PRD. User stories should make it work.
- Excludes from `docs/scope.md` must NOT appear as features. Acknowledge them in Non-Goals.
- **Authentication is non-negotiable** and always appears as Must-have user stories. The stack is Supabase Auth. Include sign up, log in, log out, and session persistence across reloads as explicit stories. Do not mark auth as [NEEDS INPUT] — it's a fixed part of the stack.
- The build level shapes acceptance criteria:
  - `clickable` — acceptance criteria describe the UI behaviour only. No persistence.
  - `MVP` — acceptance criteria describe real data persistence and the full auth dance on the core loop.
  - `Prod` — acceptance criteria include error states, validation, and one empty/loading state per screen.

## Step 3 — Write `docs/prd.md`

Use this structure:

```markdown
# [Product name] — PRD

_Built with Sprint Zero. Reference: [company name]. Level: [clickable | MVP | Prod]._

## 1. Problem statement

What pain are we solving and for whom? Why does this matter now?

## 2. Goals

3-5 measurable outcomes. Format: "Enable [user] to [action] in under [constraint]" or "Increase [metric] by [amount]".

## 3. Non-goals

What this build explicitly will NOT do. Pull directly from `docs/scope.md` excludes. Also list anything the reference does that's out of scope for this level.

## 4. Users & use cases

Who uses this and in what context? 2-3 concrete scenarios as short narrative paragraphs (not bullets).

## 5. User stories

Format: "As a [user type], I want to [action] so that [outcome]."

Group into:

### Must-have

Always includes these auth stories at minimum:

- As a new user, I want to sign up with email and password so that I can access the product.
- As a returning user, I want to log in so that I can see my own data.
- As a signed-in user, I want my session to persist across reloads so that I don't have to log in every time.
- As a signed-in user, I want to log out so that my session ends.

Plus the core loop stories derived from `docs/scope.md`.

### Should-have

Stories that round out the core loop but aren't critical.

### Nice-to-have

Stories from the reference that are out of scope for this level but worth noting.

## 6. Acceptance criteria

Given/When/Then format for every Must-have story. Be concrete — the engineers read this as their build spec.

For `Prod` builds, every Must-have story also gets one error-path acceptance criterion.

## 7. Risks & assumptions

- **Risks** — what could go wrong, what dependencies exist (call out Supabase tier limits if relevant)
- **Assumptions** — what's being treated as true but not confirmed. Mark with `[ASSUMPTION]`.

## 8. Open questions

Unresolved decisions. Format as questions. Mark with `[NEEDS INPUT]` only if the question genuinely blocks building — don't pad this section.

## 9. Success metrics

Leading indicators (early signals) and lagging indicators (final outcomes). One of each minimum.
```

## Rules

- Write the full PRD directly — no preamble, no chat commentary beyond a final one-line confirmation.
- Plain English. No technical jargon outside Section 7 (Risks) where Supabase etc. is fine.
- Mark assumptions with `[ASSUMPTION]`. Mark unresolved blockers with `[NEEDS INPUT]`.
- Never mark auth as an assumption or open question. It's a fixed stack choice.
- Write to `docs/prd.md`. Do not ask the user to confirm the save — just write it.
- After writing, print: `PRD written. [N] must-have stories, [N] should-have. Ready for /decisions-writer.`

$ARGUMENTS
