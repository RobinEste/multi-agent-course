# Sprint Zero

> **Part of the [Enterprise RAG & Multi-Agent Applications](../../README.md) course** — a full-stack, multi-agent capstone project.
> Built by **[Yousuf Alvi](https://github.com/yousuf-alvi)** and **[Hamza Farooq](https://www.linkedin.com/in/hamzafarooq/)**.

**Point it at a product. Answer three questions. Get back a complete spec set and a working app.**

Sprint Zero is a Claude Code kit that gives a PM or founder a full sub-agent product team on their laptop. You bring the idea and a reference URL. Sprint Zero handles scoping, research, specs, parallel engineering, and QA — and hands back a running product.

---

## The problem

Validating a product idea today looks something like this:

- Write a rough PRD, argue about it in Notion
- Hand-wave an API contract, hope the engineers read it the same way
- Wait a week or three for a prototype
- Find out on demo day that the core loop doesn't actually work
- Go back to the PRD

Every step loses signal. By the time a PM sees something clickable, the idea has passed through three games of telephone. Nothing is built to one shared interface. Nothing is testable against the original intent.

Sprint Zero collapses that cycle into one terminal session. The PM stays in the loop the whole way through because the loop is now minutes long, not weeks.

---

## The promise

One command. One reference URL. Three scoping answers. You get:

- A full spec set in `docs/` — scope, research brief, PRD, decisions, user stories, API contract
- A working build in `server/` and `client/` — Express + Supabase API, React frontend, real auth
- Playwright-driven QA covering the auth dance and the core product loop

For a `MVP` scope, expect ten to twenty minutes end-to-end.

---

## How it flows

```mermaid
flowchart LR
    A[You]
    B[Scoping]
    C[Spec set]
    D[Parallel build]
    E[QA]
    F[Running product]

    A -->|URL + 3 answers| B
    B --> C
    C --> D
    D --> E
    E --> F
```

One command drives the whole flow. You watch it happen in the Claude Code terminal and can read every spec file before code gets written.

---

## The three scope levels

You pick one when you answer the scoping question. The level is stored in `docs/scope.md` and calibrates every agent downstream.

| Level       | What it produces                                   | Good for                        |
| ----------- | -------------------------------------------------- | ------------------------------- |
| `clickable` | Mock backend, fake data, no auth                   | Pitching and flow reviews       |
| `MVP`       | Real Supabase, real auth, one core loop end-to-end | Showing the idea actually works |
| `Prod`      | MVP plus error states, validation, loading states  | Handing to 5–10 real users      |

`MVP` is the main demo path for v1. `clickable` is an escape hatch for very early ideation.

---

## The agent team

Sprint Zero has four sub-agents. You only ever talk to the main session — it orchestrates the rest.

```mermaid
flowchart TD
    User[You]
    Main[Main session]
    TL[tech-lead]
    BE[backend-engineer]
    FE[frontend-engineer]
    QA[qa-engineer]

    User -->|/sprint-zero url| Main
    Main -->|reads specs| TL
    TL -->|build brief| Main
    Main -->|parallel| BE
    Main -->|parallel| FE
    BE --> QA
    FE --> QA
    QA -->|report| Main
    Main -->|delivery summary| User
```

- **tech-lead** reads the spec set and returns a structured build brief. It does not write code.
- **backend-engineer** builds Express + Supabase in `server/`.
- **frontend-engineer** builds React + Vite + Supabase Auth in `client/`.
- **qa-engineer** runs Playwright against the live app — auth dance plus the core loop.

Backend and frontend never talk to each other. The API contract is the shared interface.

### Why orchestration lives in the main session

Claude Code does not permit sub-agents to spawn other sub-agents. `tech-lead` could not spawn the engineers even if we wanted it to. So tech-lead is a briefing layer, and the main session is the orchestrator. This also makes the demo clearer — the PM watching the session sees the parallel spawn happen in the main view, not buried inside a sub-agent's output.

---

## The spec pipeline

Before any code runs, Sprint Zero writes six documents to `docs/`. Each feeds the next.

```mermaid
flowchart LR
    S1[scope.md]
    S2[reference-brief.md]
    S3[prd.md]
    S4[decisions.md]
    S5[user-stories.md]
    S6[api-contract.md]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6
```

| File                 | What's in it                                      |
| -------------------- | ------------------------------------------------- |
| `scope.md`           | Build level, core loop, excludes                  |
| `reference-brief.md` | What the reference product does and how           |
| `prd.md`             | What we're building and why                       |
| `decisions.md`       | Every scope cut, tied to the chosen level         |
| `user-stories.md`    | Acceptance criteria Playwright can drive          |
| `api-contract.md`    | The shared interface both engineers build against |

The pipeline is resumable. Each step checks whether its output file already exists and skips if so. If something fails, re-run `/sprint-zero` and it picks up where it stopped.

---

## The API contract is law

```mermaid
flowchart TD
    C[api-contract.md]
    C --> BE[backend-engineer<br/>implements]
    C --> FE[frontend-engineer<br/>consumes]
    C --> QA[qa-engineer<br/>validates]
```

Endpoint paths, request shapes, response shapes, status codes — all defined in one file. The engineers build in parallel without ever speaking to each other because they are both building to the same contract. If any agent needs to deviate, it stops and flags it rather than diverging silently.

---

## The stack (fixed)

Not configurable in v1. Picking one stack is what makes Sprint Zero actually ship.

| Layer           | Technology                          |
| --------------- | ----------------------------------- |
| Frontend        | React + Vite                        |
| Backend         | Express (Node.js)                   |
| Database + Auth | Supabase (Postgres + Supabase Auth) |
| Testing         | Playwright via Playwright MCP       |

You bring your own Supabase project. Free tier is fine.

---

## Quick start

### 1. Prerequisites

- [Node.js](https://nodejs.org) 18+
- [Claude Code](https://claude.com/claude-code) installed and authenticated
- A free [Supabase](https://supabase.com) account
- Playwright MCP registered in Claude Code (so QA can drive the browser). If `claude mcp list` does not show `playwright`, install it and register it under that name.

### 2. Create a Supabase project

Go to [supabase.com](https://supabase.com), click **New project**, pick any name and region, and wait for it to provision. Then go to **Authentication → Providers → Email** and confirm it is enabled.

### 3. Collect four credentials

From your Supabase project's **Settings** page:

| Where                                                                   | Value                      | Goes into `.env` as        |
| ----------------------------------------------------------------------- | -------------------------- | -------------------------- |
| Settings → API → Project URL                                            | `https://xxxx.supabase.co` | `SUPABASE_URL`             |
| Settings → API Keys → Publishable key                                   | `sb_publishable_...`       | `SUPABASE_PUBLISHABLE_KEY` |
| Settings → API Keys → Secret key (click Reveal)                         | `sb_secret_...`            | `SUPABASE_SECRET_KEY`      |
| Settings → Database → Connection string → URI (Session mode, port 5432) | `postgresql://postgres...` | `DATABASE_URL`             |

Use the new **API Keys** tab in Supabase, not the **Legacy** tab — the legacy tab still shows "anon" and "service*role", but Sprint Zero expects the new `sb_publishable*...`/`sb*secret*...` format.

`DATABASE_URL` is the direct Postgres connection string. Sprint Zero uses it to create tables automatically — no manual SQL pasting.

### 4. Clone and configure

```bash
git clone https://github.com/yousuf-labs/sprint-zero
cd sprint-zero
cp .env.example .env
# open .env and paste in the four values from step 3
```

### 5. Run Sprint Zero

```bash
claude
```

Then in Claude Code:

```
/sprint-zero https://twenty.com/ https://github.com/twentyhq/twenty
```

Pass any product URL you want to reference (a landing page, an open-source tool, a competitor). Sprint Zero will ask you three questions in one message — answer in a paragraph, no formatting needed:

1. **Project name** — a short slug for this build
2. **What level?** — `clickable`, `MVP`, or `Prod`
3. **What's the core loop?** — the one user flow that must work
4. **Anything to exclude?** — features you don't want

#### Example answer — a mini CRM referenced from [twenty.com](https://twenty.com/)

> **What level are we building?**
> MVP
>
> **What's the core loop?**
> The core loop is: user creates a contact (name, email, company), creates a deal linked to that contact (name, value, stage), and moves the deal across pipeline stages (Lead → Qualified → Proposal → Closed Won / Closed Lost). That's what a MVP has to prove.
>
> **Anything to exclude?**
> Companies as a separate entity (roll company into the contact record as a text field), custom fields, activities and notes on records, email integration, import / export, filters and saved views, search, reporting and dashboards, tasks, calendar, and any admin / settings UI.

Notice how the excludes list is long and specific. That's the point — naming what you're cutting is how you keep a `MVP` to ten to twenty minutes and stop the agents from quietly building a full CRM.

Sprint Zero handles the rest.

### 6. The app launches itself

Once QA passes, `/sprint-zero` automatically:

1. Runs `npm install` in `server/` and `client/` (skipped if `node_modules/` already exists)
2. Writes `client/.env` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` pulled from the root `.env`
3. Runs `node seed.js` to create tables and demo data
4. Starts the backend on [http://localhost:3001](http://localhost:3001) in the background
5. Starts the frontend on [http://localhost:5173](http://localhost:5173) in the background
6. Prints the demo user's email and password

Open [http://localhost:5173](http://localhost:5173). You'll land on a polished marketing page — click **Log in** in the top nav and use the credentials from the launch summary to enter the product.

To stop the servers when you're done:

```bash
pkill -f "node index.js" && pkill -f "vite"
```

Pass `--no-launch` to `/sprint-zero` if you'd rather wire it up by hand — see the next section.

---

## Start the app manually

You can skip auto-launch with `/sprint-zero <url> --no-launch`, or run these steps any time afterward to restart things.

```bash
# Terminal 1 — backend
cd server
npm install       # first run only
node seed.js      # creates tables + demo data (first run only)
node index.js     # API on http://localhost:3001

# Terminal 2 — frontend
cd client
npm install              # first run only
cp .env.example .env     # first run only — then paste VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY
npm run dev              # app on http://localhost:5173
```

The seed script prints the demo user's email and password. Use those to log in at [http://localhost:5173](http://localhost:5173).

> The frontend needs its own `.env` with `VITE_`-prefixed variables because Vite only exposes env vars with that prefix to the browser. Reuse the same `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` values from the root `.env`.

---

## What `node seed.js` does

```mermaid
flowchart LR
    A[node seed.js] --> B[Create tables<br/>via migrate.js]
    B --> C[Create demo user<br/>via Supabase admin]
    C --> D[Insert seed rows]
    D --> E[Print credentials]
```

It is idempotent. Running it twice is safe. Tables are created with `IF NOT EXISTS`. The demo user is checked before creation. Seed rows are cleared and re-inserted each run.

---

## Repo layout

```
sprint-zero/
├── .claude/
│   ├── commands/                    ← slash commands (the pipeline)
│   │   ├── sprint-zero.md             main orchestrator
│   │   ├── sprint-zero-scope.md       scoping question → scope.md
│   │   ├── explain-me-a-repo.md       research → reference-brief.md
│   │   ├── prd-generator.md           → prd.md
│   │   ├── decisions-writer.md        → decisions.md
│   │   ├── user-story-writer.md       → user-stories.md
│   │   └── api-contract-writer.md     → api-contract.md
│   └── agents/                      ← sub-agents (the build layer)
│       ├── tech-lead.md
│       ├── backend-engineer.md
│       ├── frontend-engineer.md
│       └── qa-engineer.md
├── docs/                            ← generated specs (gitignored; filled at runtime)
├── examples/                        ← worked examples (Mini Twenty lands here in Phase 5)
├── server/                          ← Express + Supabase (gitignored; created at runtime)
├── client/                          ← React + Vite (gitignored; created at runtime)
├── .env.example                     ← copy to .env and fill in
├── .gitignore
├── CLAUDE.md                        ← project instructions for Claude Code
├── LICENSE
├── plan.md                          ← phased build plan for this repo
└── README.md
```

On a fresh clone you'll only see the committed items. `docs/`, `server/`, and `client/` are populated when `/sprint-zero` runs.

---

## Re-running pieces individually

Every spec command works on its own. Delete the target file first if you want to regenerate it.

```
/sprint-zero-scope      re-run scoping
/explain-me-a-repo      re-research the reference
/prd-generator          regenerate the PRD
/decisions-writer       regenerate decisions
/user-story-writer      regenerate stories
/api-contract-writer    regenerate the contract
```

### Flags on `/sprint-zero`

| Flag          | Effect                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------ |
| `--fresh`     | Delete `docs/` and regenerate all specs from scratch                                       |
| `--rebuild`   | Delete `server/` and `client/` and rebuild from existing specs                             |
| `--no-launch` | Skip auto-launch at the end. Start the servers manually afterwards.                        |
| `--present`   | Boot the presenter UI in the browser. Collects scoping via a form and shows live progress. |

Example: `/sprint-zero https://example.com --fresh`

### Named failure states

If anything goes wrong, `/sprint-zero` prints a named state and a recovery instruction.

| State                | Meaning                         | Recovery                                      |
| -------------------- | ------------------------------- | --------------------------------------------- |
| `SCOPE_NEEDED`       | `docs/scope.md` was not written | Re-run with a reachable URL                   |
| `DISCOVERY_NEEDED`   | Reference brief failed          | Fix connectivity, re-run                      |
| `SPEC_INCOMPLETE`    | A spec file is missing          | Run the failing command directly, then re-run |
| `BUILD_BRIEF_NEEDED` | tech-lead flagged a doc problem | Fix the doc, re-invoke tech-lead              |
| `BUILD_NEEDED`       | An engineer failed              | Re-spawn the failing engineer, then QA        |
| `QA_NEEDED`          | Tests failed                    | Fix the reported issues, re-spawn QA          |
| `LAUNCH_FAILED`      | Auto-launch at the end failed   | Start the servers manually (see above)        |

---

## Sprint Zero — `--present` mode

For walking PMs or non-developers through Sprint Zero, run it with `--present`:

```
/sprint-zero https://twenty.com https://github.com/twentyhq/twenty --present
```

A polished local UI boots at `http://localhost:4000` and opens in the browser. Use it for three phases of the demo:

1. **About** — explains scope levels, the agent topology, and the spec pipeline. Stay here while you talk through the concept.
2. **Start a run** — a form replaces the terminal scoping conversation. Submitting it writes `docs/scope.md`.
3. **Live** — a vertical pipeline timeline updates in real time as each spec doc lands. Click any completed step to view its rendered markdown. The build phase shows backend and frontend as side-by-side cards. When the run finishes, the screen reveals the running app's URL with a copyable demo login.

The presenter is a permanent committed part of the kit, not a one-off. The terminal narration is unchanged, so you can also screen-share the Claude Code window alongside the UI.

To boot the presenter on its own (without a Sprint Zero run):

```
cd presenter && npm install && npm run build && npm start
```

---

## Troubleshooting

**The page shows "Failed to load contacts" (or similar).** Database tables aren't created yet. Run `cd server && node seed.js`.

**The server crashes on startup.** `server/.env` is missing or incomplete. The error message will name the missing key.

**Every API call returns 401.** New Supabase projects issue ES256 tokens, not RS256. `middleware/auth.js` must accept both, and the JWKS URI must be `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (not `/auth/v1/jwks`).

**QA didn't run the browser tests.** The Playwright MCP server isn't registered under the name `playwright`. Run `claude mcp list` to check, then register it and re-spawn `qa-engineer`.

**`node seed.js` says "relation does not exist".** `DATABASE_URL` is wrong. Get it from Settings → Database → Connection string → URI, Session mode, port 5432. It looks like `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`.

---

## What's not in v1

Deliberate cuts, tracked in [plan.md](plan.md) as v2 candidates:

- Multiple stacks (Next.js, Python/Django, Vue)
- Deployment automation — Sprint Zero produces code, you deploy it
- Multi-user collaboration in the generated product
- Design system integration — the generated UI is utilitarian
- Payment / Stripe integration
- File upload beyond what Supabase gives you out of the box
- A hosted version of Sprint Zero itself

---

## Status

- Phase 1 — Foundation — complete
- Phase 2 — Scoping and discovery layer — complete
- Phase 3 — Build layer — complete
- Phase 4 — Kickoff orchestrator — complete
- Phase 5 — Mini Twenty worked example — not started
- Phase 6 — Polish for launch — not started

See [plan.md](plan.md) for the full roadmap.

---

## Authors

- **[Yousuf Alvi](https://github.com/yousuf-alvi)** · [LinkedIn](https://www.linkedin.com/in/yousufalvi/) — original author
- **[Hamza Farooq](https://www.linkedin.com/in/hamzafarooq/)** — course integration ([Enterprise RAG & Multi-Agent Applications](https://maven.com/boring-bot/advanced-llm))

Originally published at [yousuf-labs/sprint-zero](https://github.com/yousuf-labs/sprint-zero).

MIT licensed. See [LICENSE](LICENSE).
