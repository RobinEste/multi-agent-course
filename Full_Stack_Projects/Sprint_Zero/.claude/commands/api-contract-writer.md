# /api-contract-writer

Produce `docs/api-contract.md` — the single source of truth both the backend engineer and frontend engineer build against. Stack is Express + Supabase. Auth is bearer tokens from Supabase Auth.

## Step 1 — Read inputs

Read all three:

- `docs/scope.md` — build level affects whether endpoints are mocked vs real
- `docs/prd.md` — entities and features
- `docs/user-stories.md` — the flows that need backing endpoints

If any is missing, stop and tell the user which command to run first.

## Step 2 — Identify entities and endpoints

From the PRD and user stories:

1. List every data entity (e.g. contacts, deals, projects — whatever this build uses)
2. For each entity, define: list, get by id, create, update, delete
3. Add any non-CRUD endpoints implied by specific user stories (e.g. a "move deal to next stage" action)
4. Every endpoint that touches user data is protected — requires `Authorization: Bearer <token>`

## Step 3 — Auth conventions (fixed for Sprint Zero)

These don't need to be re-specified per endpoint — document them once at the top of the contract:

- **Sign up / log in / log out** are handled by Supabase Auth directly on the client. The Express backend does NOT expose `/auth/*` endpoints. The client calls `supabase.auth.signUp()`, `signInWithPassword()`, `signOut()`.
- **Session tokens** are JWTs issued by Supabase. The client sends them as `Authorization: Bearer <token>` on every protected API call.
- **Backend verification** — every protected Express route runs JWT middleware that validates the token against Supabase's JWKS. Invalid or expired tokens return `401`.
- **User scoping** — every entity has an implicit `user_id` column tied to the authenticated user. List endpoints return only the current user's records. Get/update/delete check ownership before responding.

## Step 4 — Build level affects implementation (not shape)

The contract shape is the same across levels — same endpoints, same request/response bodies. What changes:

- `clickable` — backend returns hardcoded example responses, no database writes, no JWT verification. The contract documents the shape but marks every endpoint with `[MOCK]` in the Notes field.
- `MVP` — full Supabase integration, JWT verification on protected routes.
- `Prod` — same as MVP plus: input validation with explicit error responses, rate limiting notes, and at least one error-path example per endpoint (e.g. 400, 401, 404, 409).

## Step 5 — Write `docs/api-contract.md`

```markdown
# API contract

_Sprint Zero build. Stack: Express + Supabase. Level: [level]._

## Auth

All user-facing auth (sign up, log in, log out, password reset) is handled client-side via `@supabase/supabase-js`. The Express backend does not expose `/auth/*` routes.

Protected endpoints require an `Authorization: Bearer <token>` header. The token is the Supabase session access token. Express middleware validates it against Supabase's JWKS. Invalid or expired tokens return `401 Unauthorized`.

Every entity is scoped to the authenticated user by `user_id`. List endpoints return only the current user's records. Ownership is checked on every write.

## Base URL

`http://localhost:3000/api` (development). Production URL is environment-configured.

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
- IDs are UUID v4 strings (Supabase default).
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
- Never document `/auth/*` endpoints on the Express API. Supabase Auth owns that flow client-side.
- Write to `docs/api-contract.md`. No user confirmation needed.
- After writing, print: `API contract written. [N] entities, [N] endpoints. Spec set complete. Ready to hand off to the build layer (Phase 3 sub-agents).`

$ARGUMENTS
