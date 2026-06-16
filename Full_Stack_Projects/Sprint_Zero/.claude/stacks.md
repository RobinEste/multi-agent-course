# Sprint Zero — stack catalog

> This file is the single source of truth for what Sprint Zero can build and how
> each option behaves. The scope command captures three choices into
> `docs/scope.md`. Every agent reads those choices and looks the concrete facts
> (directories, ports, run commands, test strategy) up here. Do not hardcode a
> stack assumption anywhere else — read it from `docs/scope.md` and resolve it
> against this catalog.

The three choices are orthogonal: a **project type**, a **stack profile**, and a
**data layer**. Most combinations are valid. The default is
`web-app` + `node-react` + `local` — a clone-and-go build that needs no external
account.

---

## Dimension 1 — Project type

What shape of thing are we building?

| Type          | Has frontend? | Has backend/API? | What QA drives                                        |
| ------------- | ------------- | ---------------- | ----------------------------------------------------- |
| `web-app`     | yes           | yes              | Browser (Playwright) + API integration tests          |
| `api-service` | no            | yes              | API integration tests + curl smoke checks, no browser |
| `cli-tool`    | no            | no (a program)   | Runs the CLI with sample args, asserts on stdout/exit |

- **`web-app`** — the original Sprint Zero shape. Backend API plus a frontend UI,
  optional auth, one core loop end-to-end. Spawn backend-engineer **and**
  frontend-engineer.
- **`api-service`** — a backend/API only. No `client/`, no browser tests. Spawn
  backend-engineer only; skip frontend-engineer. QA runs integration tests and
  curl smoke checks and verifies the auth flow at the API level (no auth *dance*
  in a browser). The "core loop" is an endpoint sequence, not a screen flow.
- **`cli-tool`** — a command-line program, no server and no frontend. Spawn
  backend-engineer only (it owns the CLI source). QA runs the CLI with sample
  arguments and asserts on stdout and exit codes. Data layer is usually `local`
  (a SQLite file or flat file); `supabase` is unusual but allowed.

---

## Dimension 2 — Stack profile

Which languages and frameworks the code-bearing parts use. The profile only
shapes the parts a project type actually has (e.g. `api-service` ignores the
frontend half of a profile).

### `node-react` (default)

| Part      | Tech                          | Directory  | Run command            | Port |
| --------- | ----------------------------- | ---------- | ---------------------- | ---- |
| Backend   | Express (Node, plain JS)      | `server/`  | `node index.js`        | 3001 |
| Frontend  | React + Vite (plain JS/JSX)   | `client/`  | `npm run dev`          | 5173 |
| CLI (if `cli-tool`) | Node, plain JS      | `cli/`     | `node cli/index.js`    | n/a  |

### `nextjs`

A single Next.js app (App Router) that serves both UI and API — there is no
separate `server/`/`client/` split.

| Part      | Tech                                   | Directory        | Run command     | Port |
| --------- | -------------------------------------- | ---------------- | --------------- | ---- |
| App       | Next.js App Router (JS, not TS by default) | `app/`       | `npm run dev`   | 3000 |
| API       | Route handlers under `app/api/*/route.js` | `app/api/`    | (same process)  | 3000 |
| CLI (if `cli-tool`) | falls back to a Node CLI in `cli/` | `cli/` | `node cli/index.js` | n/a |

For `nextjs`, "backend-engineer" owns `app/api/` and any server-side data code;
"frontend-engineer" owns the pages and components under `app/`. Both write into
the same Next.js project — backend-engineer scaffolds the project first, frontend
builds on top. The API base URL is same-origin (`/api/...`), not a separate port.

### `python-react`

| Part      | Tech                              | Directory  | Run command                              | Port |
| --------- | --------------------------------- | ---------- | ---------------------------------------- | ---- |
| Backend   | FastAPI (Python 3.11+)            | `server/`  | `uvicorn main:app --port 8000`           | 8000 |
| Frontend  | React + Vite (plain JS/JSX)       | `client/`  | `npm run dev`                            | 5173 |
| CLI (if `cli-tool`) | Python (argparse / Typer) | `cli/`     | `python cli/main.py`                     | n/a  |

Python deps go in `server/requirements.txt`. Use a venv: `python -m venv .venv`
then `pip install -r requirements.txt`. FastAPI app object is `app` in
`server/main.py`. CORS configured to allow the frontend origin.

---

## Dimension 3 — Data layer

How data and auth are stored. **Orthogonal to the stack profile** — every profile
supports both. This is the zero-setup lever.

### `local` (default — no external account needed)

The build runs immediately after clone. No `.env`, no signup, no credentials.

- **Storage:** a single SQLite file at the backend root (`server/data.db`, or
  `data.db` at project root for `nextjs`). Add the `.db` file to `.gitignore`.
  - Node / Next: `better-sqlite3`.
  - Python: the stdlib `sqlite3` module (or SQLModel/SQLAlchemy if the contract is complex).
- **Auth (when the project type needs it):** self-issued JWT.
  - A `users` table (`id`, `email`, `password_hash`, `created_at`).
  - `POST /auth/signup` and `POST /auth/login` endpoints **in our own backend**
    hash the password (`bcryptjs` for Node, `bcrypt`/`passlib` for Python) and
    return `{ access_token }` — a JWT signed with a secret read from
    `process.env.JWT_SECRET` / `os.environ` and **defaulting to a baked-in dev
    secret** (e.g. `"sprint-zero-dev-secret"`) so nothing must be configured.
  - Protected-route middleware verifies the JWT with that same secret and sets
    `req.user = { id }`.
  - The frontend calls these backend `/auth/*` endpoints (it does **not** use any
    third-party auth SDK in local mode).
- **Seed:** writes rows directly into the SQLite file. Creates the schema if
  missing (run on seed and on server start). Idempotent.
- **No env file required.** If you want to override the JWT secret or DB path,
  read optional env vars, but never *require* them.

### `supabase` (opt-in — real Postgres + hosted auth)

The original Sprint Zero data layer. Requires a Supabase project and a `.env`.

- **Storage:** Supabase Postgres via `@supabase/supabase-js` (Node/Next) or the
  Supabase Python client / direct `psycopg`/SQLModel against `DATABASE_URL`.
- **Auth:** Supabase Auth. Frontend uses the Supabase client SDK for
  signup/login/session; backend verifies Supabase JWTs via the project JWKS
  endpoint (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`, algorithms
  `['RS256','ES256']`).
- **Schema:** created via a direct postgres connection (`DATABASE_URL`) — DDL
  cannot run through PostgREST. Node uses `pg` + a `migrate.js`; Python uses the
  DB driver directly.
- **Requires `.env`** with `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`,
  `SUPABASE_SECRET_KEY`, `DATABASE_URL`. The orchestrator runs the Supabase
  preflight only when this data layer is chosen.

---

## How scope levels interact with these choices

The scope level (`clickable` / `MVP` / `Prod`) is a fourth, independent dial that
still means what it always did:

- `clickable` — mock/in-memory data, no real auth, regardless of data layer. The
  data layer choice is recorded but only takes effect at `MVP`+. (A clickable
  build needs no SQLite and no Supabase.)
- `MVP` — real data + real auth via the chosen data layer, on the core loop.
- `Prod` — `MVP` plus validation, error handling, loading states, and an
  error-path test per loop.

---

## Resolved facts cheat-sheet (what agents need at a glance)

Resolve `(project type, stack profile, data layer)` from `docs/scope.md`, then:

- **Backend dir / run / port:** from the stack-profile table above.
- **Frontend dir / run / port:** from the stack-profile table — but **only build a
  frontend for `web-app`**. Skip it for `api-service` and `cli-tool`.
- **`nextjs` special case:** one app, one port (3000), same-origin `/api`. No
  separate frontend port; the "frontend" and "backend" engineers cooperate on one
  project.
- **Auth implementation:** `local` → backend `/auth/*` + self-signed JWT;
  `supabase` → Supabase Auth SDK + JWKS verification. `clickable` → none.
- **Preflight / env:** `local` → none required; `supabase` → run the Supabase
  preflight and require the four keys.
- **QA target:** `web-app` → browser + API; `api-service` → API only; `cli-tool`
  → command runs. Use the resolved ports above, never a hardcoded 3001/5173.

When in doubt, prefer the simplest thing that satisfies the contract at the chosen
scope level. The contract in `docs/api-contract.md` is always law.
