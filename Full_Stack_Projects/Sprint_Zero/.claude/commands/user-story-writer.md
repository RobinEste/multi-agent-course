# /user-story-writer

Expand the PRD's user stories into a detailed, buildable story set. This is the file the frontend and backend engineers read most closely, so acceptance criteria need to be concrete and driveable by Playwright.

## Step 1 — Read inputs

Read:

- `docs/scope.md` — build level affects edge-case depth
- `docs/prd.md` — the story list and acceptance criteria to expand

If either is missing, stop and tell the user which command to run first.

## Step 2 — Expand each story

For every Must-have and Should-have story in the PRD, produce:

1. **The story**, restated: "As a [user type], I want to [action] so that [value]."
2. **Acceptance criteria** in Given/When/Then. Concrete enough for Playwright to verify — e.g. "then the 'Log in' button becomes visible" not "then the UI updates."
3. **Priority** — Must-have / Should-have / Nice-to-have (carry over from PRD)
4. **Effort** — Small (< 1 day) / Medium (2-3 days) / Large (1 week+)

Nice-to-have stories can be summarised in a single bullet list at the end. Don't expand them.

## Step 3 — Auth stories are always included

The following four stories must appear in Must-have, fully expanded, regardless of what the PRD looks like. If the PRD is missing any, add them:

- Sign up with email and password
- Log in with email and password
- Log out
- Session persists across reload

Each needs acceptance criteria that include the Supabase Auth behaviour — e.g. "Given a new user on /signup, when they submit valid email and password, then a Supabase session is created and they land on the authenticated home screen."

## Step 4 — Edge cases and questions

After the stories, add two sections:

**Edge cases to discuss** — 3-5 scenarios the team should talk through before building. For `Prod`, include at least one error-path case per Must-have story. For `clickable` and `MVP`, keep edge cases tighter.

**Questions for the team** — 2-3 questions that genuinely block building. Format as questions. Mark each with `[NEEDS CLARIFICATION]` only if it actually blocks — don't pad.

## Step 5 — Write `docs/user-stories.md`

```markdown
# User stories

_Level: [level]. Expanded from `docs/prd.md`._

## Must-have

### Story 1 — [short phrase]

**Story:** As a [user type], I want to [action] so that [value].

**Acceptance criteria:**

- Given [context], when [action], then [result].
- Given [context], when [action], then [result].

**Priority:** Must-have
**Effort:** Small / Medium / Large

(repeat)

## Should-have

(same format)

## Nice-to-have

- [one-line story]
- [one-line story]

## Edge cases to discuss

- [scenario]
- [scenario]

## Questions for the team

1. [question] `[NEEDS CLARIFICATION]` (only if actually blocking)
2. [question]
```

## Rules

- Write stories directly — no preamble, no chat commentary beyond the final confirmation.
- Acceptance criteria must be concrete enough for Playwright. Anchor them to visible UI elements, URLs, or data state — not vague UX concepts.
- Language stays simple enough for a non-technical stakeholder to read, even though engineers will also use it.
- Always include the four auth stories in Must-have, fully expanded.
- Write to `docs/user-stories.md`. No user confirmation needed.
- After writing, print: `User stories written. [N] must-have expanded, [N] should-have, [N] nice-to-have. Ready for /api-contract-writer.`

$ARGUMENTS
