/*
 * FDE · Assignment 1 · Node Gateway  (the "software backend")
 * ==========================================================
 * This is the ONLY server the browser widget talks to. Its jobs:
 *   - serve the widget file at /widget.js
 *   - accept translation requests from the widget (CORS, validation)
 *   - forward them to the Python AI service
 *   - expose /health and /stats
 *   - log every request
 *
 * It is ~90% done. Find the two `TODO (YOU)` blocks and implement them.
 * Everything else works out of the box.
 *
 * Run:  npm install && npm start      (needs Node 18+ for global fetch)
 */
const express = require("express");
const cors = require("cors");
const rateLimit = require("express-rate-limit");
const path = require("path");
const crypto = require("crypto");
require("dotenv").config();

const PORT = process.env.PORT || 8787;
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8000";
const WIDGET_PATH = path.join(__dirname, "..", "..", "widget", "translation-widget.js");

// Spend guards. Every translate request that misses the cache costs money, and
// this gateway is public with no auth — the widget has to run on any page, so
// there is no user to authorise. These three bound what one caller can spend:
// how much text per request, how many strings per batch, and how many requests
// per minute. None of them is a substitute for a budget cap in the Anthropic
// console, which is the only hard ceiling.
const BODY_LIMIT = process.env.BODY_LIMIT || "128kb";
const MAX_BATCH = Number(process.env.MAX_BATCH || 50);
const RATE_LIMIT_PER_MIN = Number(process.env.RATE_LIMIT_PER_MIN || 60);

const app = express();
const startedAt = Date.now();

// --- middleware ----------------------------------------------------------
// One hop: Caddy terminates TLS on the host and forwards X-Forwarded-For.
// Without this every request would look like it came from 127.0.0.1 and the
// limiter below would throttle all callers as one.
app.set("trust proxy", 1);
app.use(cors()); // dev: allow every origin so the widget works on any page
app.use(express.json({ limit: BODY_LIMIT }));

// --- request id + structured request logging ----------------------------
// Reuse an inbound X-Request-Id if the caller set one, else generate a fresh
// UUID. The id is echoed back to the browser, forwarded to the AI service, and
// logged by both — so one request is greppable end-to-end across both services.
app.use((req, res, next) => {
  const t0 = Date.now();
  const requestId = req.headers["x-request-id"] || crypto.randomUUID();
  req.requestId = requestId;
  res.setHeader("X-Request-Id", requestId);
  res.on("finish", () => {
    console.log(
      JSON.stringify({
        ts: new Date().toISOString(),
        service: "gateway",
        requestId,
        method: req.method,
        url: req.originalUrl,
        status: res.statusCode,
        ms: Date.now() - t0,
      })
    );
  });
  next();
});

// --- rate limit, on the money-spending routes only -----------------------
// /health, /stats and /widget.js stay free: they cost nothing and throttling
// them would only break monitoring and the demo page.
app.use(
  ["/translate", "/translate/batch"],
  rateLimit({
    windowMs: 60_000,
    limit: RATE_LIMIT_PER_MIN,
    standardHeaders: "draft-7",
    legacyHeaders: false,
    message: { error: "rate limit exceeded — try again in a minute" },
  })
);

// --- serve the widget to the console loader ------------------------------
app.get("/widget.js", (req, res) => {
  res.type("application/javascript");
  res.sendFile(WIDGET_PATH);
});

// --- helper: forward a request to the Python AI service ------------------
// POSTs `body` as JSON and forwards the trace id so the AI service logs the
// same request id. Throws on a non-2xx so callers can turn it into a 502.
async function callAiService(path, body, requestId) {
  const headers = { "Content-Type": "application/json" };
  if (requestId) headers["X-Request-Id"] = requestId;
  const res = await fetch(AI_SERVICE_URL + path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("AI service " + res.status);
  return res.json();
}

// --- routes the widget calls ---------------------------------------------
app.post("/translate", async (req, res) => {
  const { text, target } = req.body || {};
  if (typeof text !== "string") return res.status(400).json({ error: "`text` (string) is required" });
  try {
    const data = await callAiService("/translate", { text, target: target || "es-MX" }, req.requestId);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: "AI service error: " + err.message });
  }
});

app.post("/translate/batch", async (req, res) => {
  const { texts, target } = req.body || {};
  if (!Array.isArray(texts)) return res.status(400).json({ error: "`texts` (array) is required" });
  // A batch of distinct strings misses the cache by definition and fans out to
  // one LLM call each, so the array length is the real cost multiplier.
  if (texts.length > MAX_BATCH)
    return res.status(400).json({ error: `at most ${MAX_BATCH} texts per request, got ${texts.length}` });
  try {
    const data = await callAiService("/translate/batch", { texts, target: target || "es-MX" }, req.requestId);
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: "AI service error: " + err.message });
  }
});

app.get("/health", async (req, res) => {
  const uptimeSec = Math.round((Date.now() - startedAt) / 1000);
  let ai = "unreachable";
  try {
    const r = await fetch(AI_SERVICE_URL + "/health");
    ai = r.ok ? await r.json() : "error";
  } catch (_) {}
  res.json({ status: "ok", gatewayUptimeSec: uptimeSec, aiService: ai });
});

app.get("/stats", async (req, res) => {
  try {
    const r = await fetch(AI_SERVICE_URL + "/stats");
    res.json(await r.json());
  } catch (err) {
    res.status(502).json({ error: "AI service error: " + err.message });
  }
});

app.listen(PORT, () => {
  console.log(`FDE gateway on http://localhost:${PORT}  →  AI service ${AI_SERVICE_URL}`);
  console.log(`Widget served at http://localhost:${PORT}/widget.js`);
});
