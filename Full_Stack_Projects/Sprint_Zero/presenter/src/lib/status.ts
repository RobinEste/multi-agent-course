import { useEffect, useRef, useState } from "react";
import type { Status } from "./types";

const EMPTY_STATUS: Status = {
  phase: "idle",
  docs: [],
};

export function useStatus(): Status {
  const [status, setStatus] = useState<Status>(EMPTY_STATUS);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let cancelled = false;

    // Hydrate from the server, then open SSE stream.
    fetch("/api/state")
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .catch(() => {
        /* server may not be up in dev with only the vite side — tolerate. */
      });

    const es = new EventSource("/api/stream");
    esRef.current = es;

    es.addEventListener("status", (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        setStatus(data);
      } catch {
        /* ignore */
      }
    });

    return () => {
      cancelled = true;
      es.close();
    };
  }, []);

  return status;
}

export async function submitScope(payload: unknown): Promise<{ ok: boolean; error?: string }> {
  try {
    const r = await fetch("/api/scope", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) {
      const text = await r.text();
      return { ok: false, error: text || `HTTP ${r.status}` };
    }
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : "Network error" };
  }
}

export async function fetchDoc(name: string): Promise<string> {
  const r = await fetch(`/api/doc/${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`Could not load ${name}`);
  return r.text();
}
