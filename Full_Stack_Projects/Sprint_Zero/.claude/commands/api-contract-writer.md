# /api-contract-writer

Produce `docs/api-contract.md` — the single source of truth the build agents build against. The stack and auth model come from the build configuration in `docs/scope.md` (resolved against `.claude/stacks.md`), not a fixed assumption.

## Step 1 — Read inputs

Read all of:

- `docs/scope.md` — build level (mock vs real) **and build configuration** (project type / stack profile / data layer), which decides the auth model and base URL below
- `.claude/stacks.md` — to resolve the API base URL and the auth approach for the chosen config
- `docs/prd.md` — entities and features
- `docs/user-stories.md` — the flows that need backing endpoints

If any of the `docs/*` is missing, stop and tell the user which command to run first. Note for `cli-tool` project type: the "contract" describes commands, arguments, and output shapes rather than HTTP endpoints — keep the same rigor (every command's inputs and output JSON/text are specified) but skip HTTP-specific sections.

## Step 2 — Identify entities and endpoints

From the PRD and user stories:

1. List every data entity (e.g. contacts, deals, projects — whatever this build uses)
2. For each entity, define: list, get by id, create, update, delete
3. Add any non-CRUD endpoints implied by specific user stories (e.g. a "move deal to next stage" action)
4. Every endpoint that touches user data is protected — requires `Authorization: Bearer <token>`

## Step 3 — Auth conventions (depends on the data layer)

Document these once at the top of the contract. The auth model is set by the **data layer** in `docs/scope.md`:

**If data layer is `local`:**

- The backend **does expose** `POST /auth/signup` and `POST /auth/login` (and optionally `GET /auth/me`). They take `{ email, password }` and return `{ access_token, user }`. Document these endpoints explicitly in the contract.
- **Session tokens** are JWTs the backend itself signs. The client stores the returned `access_token` and sends it as `Authorization: Bearer <token>` on every protected call.
- **Backend verification** — protected routes verify the JWT with the backend's own secret. Invalid/expired tokens return `401`.

**If data layer is `supabase`:**

- **Sign up / log in / log out** are handled by Supabase Auth on the client. The backend does NOT expose `/auth/*` endpoints. The client calls `supabase.auth.signUp()`, `signInWithPassword()`, `signOut()`.
- **Session tokens** are JWTs issued by Supabase, sent as `Authorization: Bearer <token>` on every protected call.
- **Backend verification** — protected routes verify the token against Supabase's JWKS. Invalid/expired tokens return `401`.

**Both:** **user scoping** — every entity has an implicit `user_id` tied to the authenticated user. List endpoints return only the current user's records; get/update/delete check ownership first.

## Step 4 — Build level affects implementation (not shape)

The contract shape is the same across levels — same endpoints, same request/response bodies. What changes:

- `clickable` — backend returns hardcoded example responses, no database writes, no JWT verification. The contract documents the shape but marks every endpoint with `[MOCK]` in the Notes field.
- `MVP` — real persistence + auth via the chosen data layer, JWT verification on protected routes.
- `Prod` — same as MVP plus: input validation with explicit error responses, rate limiting notes, and at least one error-path example per endpoint (e.g. 400, 401, 404, 409).

## Step 5 — Write `docs/api-contract.md`

```markdown
# API contract

_Sprint Zero build. Stack: [stack-profile]. Data layer: [local | supabase]. Level: [level]._

## Auth

[For `local`: The backend exposes `POST /auth/signup` and `POST /auth/login` (and `GET /auth/me`), which return `{ access_token, user }`. The client stores the token and sends it as `Authorization: Bearer <token>` on protected calls; the backend verifies its own JWT.]

[For `supabase`: All user-facing auth (sign up, log in, log out) is handled client-side via `@supabase/supabase-js`. The backend does not expose `/auth/*` routes. Protected endpoints require an `Authorization: Bearer <token>` header (the Supabase session access token), verified against Supabase's JWKS.]

Invalid or expired tokens return `401 Unauthorized`. Every entity is scoped to the authenticated user by `user_id`. List endpoints return only the current user's records. Ownership is checked on every write.

## Base URL

Resolve from the stack profile in `.claude/stacks.md`: `node-react` → `http://localhost:3001`; `python-react` → `http://localhost:8000`; `nextjs` → same-origin `/api` (no separate host/port). State the resolved value here.

## Entities

- `[EntityName]` — [one-line description]
- ...

## Endpoints

### [METHOD] /path

**Purpose:** one line description
**Auth:** required | public
**Request body:** JSON example, or "none"
**Response:** JSON example (use realistic data, not `"string"` placeholders)
**Error responses (Prod only):** List relevant 4xx codes with example bodies
**Notes:** Any edge cases, mock flags (`[MOCK]` for clickable level), or constraints

(repeat for every endpoint)

## Conventions

- All request and response bodies are JSON.
- Timestamps are ISO 8601 strings (e.g. `"2026-01-15T09:30:00Z"`).
- IDs are UUID v4 strings (or the store's native id — keep it consistent across the contract).
- The backend never returns `user_id` in response bodies — it's implicit from the session.
- `POST` returns `201 Created` with the created resource.
- `PUT` returns `200 OK` with the updated resource.
- `DELETE` returns `204 No Content`.
- Error responses use shape: `{ "error": "short_code", "message": "Human readable." }`

## What agents must NOT do

- Do not add or remove endpoints without updating this file first.
- Do not change response shapes. The frontend and backend engineers build against this document in parallel — shape drift breaks the build.
- Do not skip JWT middleware on protected routes (except on `clickable` level where it's explicitly mocked).
```

## Rules

- Every entity needs list / get / create / update / delete unless a user story explicitly rules one out.
- Use realistic example data. "John Chen" not "string". "acme-corp" not "example".
- Mark `clickable` endpoints with `[MOCK]` in Notes. Otherwise they're real.
- For `Prod`, include error responses for every Must-have endpoint.
- Document `/auth/*` endpoints **only for the `local` data layer** (the backend owns auth there). For `supabase`, do NOT document `/auth/*` — Supabase Auth owns that flow client-side.
- Write to `docs/api-contract.md`. No user confirmation needed.
- After writing, print: `API contract written. [N] entities, [N] endpoints. Spec set complete. Ready to hand off to the build layer (Phase 3 sub-agents).`

$ARGUMENTS
