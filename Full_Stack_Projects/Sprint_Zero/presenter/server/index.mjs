import express from "express";
import chokidar from "chokidar";
import { createServer } from "node:http";
import { promises as fs } from "node:fs";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..", "..");
const PRESENTER_DIR = path.resolve(__dirname, "..");
const DIST_DIR = path.join(PRESENTER_DIR, "dist");
const DOCS_DIR = path.join(ROOT, "docs");
const STATUS_DIR = path.join(ROOT, ".sprint-zero");
const STATUS_FILE = path.join(STATUS_DIR, "status.json");
const SERVER_DIR = path.join(ROOT, "server");
const CLIENT_DIR = path.join(ROOT, "client");

const DOC_FILES = [
  "scope.md",
  "reference-brief.md",
  "prd.md",
  "decisions.md",
  "user-stories.md",
  "api-contract.md",
];

/* ----------------------------- state ------------------------------- */

const EMPTY_STATUS = {
  phase: "idle",
  docs: [],
  build: { backend: "idle", frontend: "idle" },
  appUrl: null,
  credentials: null,
  projectName: null,
  failure: null,
};

async function readStatus() {
  try {
    const raw = await fs.readFile(STATUS_FILE, "utf8");
    const parsed = JSON.parse(raw);
    const docs = await listDocs();
    return { ...EMPTY_STATUS, ...parsed, docs };
  } catch {
    const docs = await listDocs();
    // If we have scope.md but no status file, we're past scoping
    const phase = docs.includes("scope.md") ? "research" : "idle";
    return { ...EMPTY_STATUS, phase, docs };
  }
}

async function listDocs() {
  try {
    const entries = await fs.readdir(DOCS_DIR);
    return DOC_FILES.filter((name) => entries.includes(name));
  } catch {
    return [];
  }
}

/* --------------------------- SSE clients --------------------------- */

const sseClients = new Set();

function broadcast(status) {
  const payload = `event: status\ndata: ${JSON.stringify(status)}\n\n`;
  for (const res of sseClients) {
    try {
      res.write(payload);
    } catch {
      /* ignore */
    }
  }
}

let broadcastTimer = null;
function scheduleBroadcast() {
  if (broadcastTimer) return;
  broadcastTimer = setTimeout(async () => {
    broadcastTimer = null;
    const status = await readStatus();
    broadcast(status);
  }, 120); // coalesce rapid file events
}

/* ----------------------------- watcher ----------------------------- */

function startWatcher() {
  const paths = [DOCS_DIR, STATUS_DIR, SERVER_DIR, CLIENT_DIR].filter(Boolean);

  const watcher = chokidar.watch(paths, {
    ignored: (p) =>
      p.includes("node_modules") ||
      p.includes(".git") ||
      p.endsWith(".DS_Store") ||
      p.includes("playwright-report") ||
      p.includes("test-results"),
    persistent: true,
    ignoreInitial: true,
    depth: 3,
  });

  watcher.on("all", () => scheduleBroadcast());
  watcher.on("error", (err) => {
    console.error("[presenter] watcher error:", err);
  });
}

/* ----------------------------- server ------------------------------ */

const app = express();
app.use(express.json({ limit: "256kb" }));

app.get("/api/state", async (_req, res) => {
  res.json(await readStatus());
});

app.get("/api/stream", (req, res) => {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });
  res.write(": connected\n\n");

  sseClients.add(res);

  // Push initial state immediately
  readStatus().then((s) => {
    res.write(`event: status\ndata: ${JSON.stringify(s)}\n\n`);
  });

  // Heartbeat so proxies don't drop the connection
  const heartbeat = setInterval(() => {
    try {
      res.write(": ping\n\n");
    } catch {
      /* ignore */
    }
  }, 20_000);

  req.on("close", () => {
    clearInterval(heartbeat);
    sseClients.delete(res);
  });
});

app.get("/api/doc/:name", async (req, res) => {
  const name = req.params.name;
  if (!DOC_FILES.includes(name)) {
    res.status(404).type("text/plain").send("Unknown doc");
    return;
  }
  try {
    const raw = await fs.readFile(path.join(DOCS_DIR, name), "utf8");
    res.type("text/plain").send(raw);
  } catch {
    res.status(404).type("text/plain").send("Not written yet");
  }
});

app.post("/api/scope", async (req, res) => {
  const body = req.body ?? {};
  const projectName = (body.projectName || "").trim();
  const companyUrl = (body.companyUrl || "").trim();
  const repoUrl = (body.repoUrl || "").trim();
  const level = body.level;
  const coreLoop = (body.coreLoop || "").trim();
  const excludes = (body.excludes || "").trim();

  if (!companyUrl) return res.status(400).send("companyUrl is required");
  if (!["clickable", "MVP", "Prod"].includes(level))
    return res.status(400).send("level must be clickable, MVP, or Prod");
  if (!coreLoop) return res.status(400).send("coreLoop is required");

  const companyUrlNormalized = ensureScheme(companyUrl);
  const repoUrlNormalized = repoUrl ? ensureScheme(repoUrl) : "";

  const levelDescriptions = {
    clickable: "Walkthrough with fake data, no backend. For pitching and flow reviews.",
    MVP: "Real Supabase, real auth, one core loop working end-to-end.",
    Prod: "MVP plus error states, validation, loading states; ready for 5–10 real users.",
  };

  const excludeLines = excludes
    ? excludes
        .split(/\n+/)
        .map((s) => s.trim())
        .filter(Boolean)
        .map((s) => `- ${s.replace(/^[-*•]\s*/, "")}`)
        .join("\n")
    : "None specified.";

  const scopeMd = `# Sprint Zero — Scope

## Reference

- **Company URL:** ${companyUrlNormalized}
- **Repo URL:** ${repoUrlNormalized || "not provided"}

## Build level

**${level}**

${levelDescriptions[level]}

## Core loop

${coreLoop}

## Excludes

${excludeLines}
`;

  await fs.mkdir(DOCS_DIR, { recursive: true });
  await fs.writeFile(path.join(DOCS_DIR, "scope.md"), scopeMd, "utf8");

  // Stash project name into a meta file so the orchestrator can pick it up
  await fs.mkdir(STATUS_DIR, { recursive: true });
  await fs.writeFile(
    path.join(STATUS_DIR, "meta.json"),
    JSON.stringify({ projectName, companyUrl: companyUrlNormalized, repoUrl: repoUrlNormalized }, null, 2),
    "utf8"
  );

  // Optimistic status: advance UI immediately so the user doesn't stare at a loading state
  // waiting for the orchestrator to poll the filesystem.
  const existing = await readStatus();
  const optimistic = {
    ...existing,
    phase: "research",
    step: "reference-brief",
    stepNumber: 3,
    message: "Scope written. Waiting for the orchestrator to pick it up.",
    projectName,
    timestamp: new Date().toISOString(),
  };
  broadcast(optimistic);

  res.json({ ok: true });
});

/* ---------------------- static assets (prod) ----------------------- */

if (existsSync(DIST_DIR)) {
  app.use(express.static(DIST_DIR, { index: false, maxAge: "1h" }));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(DIST_DIR, "index.html"));
  });
} else {
  app.get("/", (_req, res) => {
    res.type("text/plain").send(
      "presenter/dist not found. Run `npm run build` in presenter/, or start the Vite dev server with `npm run dev:web` on port 4001."
    );
  });
}

/* ----------------------------- boot -------------------------------- */

function startOnPort(port, attemptsLeft = 20) {
  const server = createServer(app);
  server.on("error", (err) => {
    if (err.code === "EADDRINUSE" && attemptsLeft > 0) {
      startOnPort(port + 1, attemptsLeft - 1);
    } else {
      console.error("[presenter] fatal:", err);
      process.exit(1);
    }
  });
  server.listen(port, "127.0.0.1", () => {
    const url = `http://localhost:${port}`;
    console.log(`[presenter] serving ${url}`);
    // Stable marker other processes can read
    fs
      .mkdir(STATUS_DIR, { recursive: true })
      .then(() =>
        fs.writeFile(path.join(STATUS_DIR, "presenter.json"), JSON.stringify({ url, port }), "utf8")
      )
      .catch(() => {});
  });

  process.on("SIGINT", () => {
    server.close(() => process.exit(0));
  });
  process.on("SIGTERM", () => {
    server.close(() => process.exit(0));
  });
}

function ensureScheme(url) {
  if (/^https?:\/\//i.test(url)) return url;
  return `https://${url}`;
}

startWatcher();
startOnPort(Number(process.env.PORT) || 4000);
