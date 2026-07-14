"""
lib/cache.py — two-tier cache: memory + SQLite  (TODO: you implement)
=====================================================================
Why two tiers?
  - MEMORY (dict): instant, but lost on restart.
  - SQLite (disk): survives restarts, and is where you can inspect what your
    service has learned. Check memory first, then disk, then LLM.

The cache key must be deterministic for the same (text, target). Hashing the
input with sha256 gives you a compact, collision-safe key.

Fill in the TODOs. The method signatures and stats are laid out for you.
"""
import hashlib

import aiosqlite


def _key(text: str, target: str) -> str:
    return hashlib.sha256(f"{target}::{text}".encode("utf-8")).hexdigest()


class TwoTierCache:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._mem: dict[str, str] = {}
        self._stats = {"requests": 0, "memory_hits": 0, "db_hits": 0, "misses": 0}

    async def init(self) -> None:
        """Create the translations table if it doesn't exist.

        `key` is the PRIMARY KEY, so SQLite already maintains a unique index on
        it — no separate index needed for the lookups in get()/set().
        """
        async with aiosqlite.connect(self.db_path) as db:
            # WAL lets readers proceed while one writer commits — cuts
            # "database is locked" under concurrent batch writes. Persists on the file.
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS translations (
                    key          TEXT PRIMARY KEY,
                    source       TEXT NOT NULL,
                    target       TEXT NOT NULL,
                    translated   TEXT NOT NULL,
                    model        TEXT,
                    access_count INTEGER   DEFAULT 1,
                    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.commit()

    async def get(self, text: str, target: str, *, count: bool = True) -> str | None:
        """Return a cached translation or None. Check memory, then SQLite.

        Pass `count=False` for the single-flight re-check in app.translate_one, so
        one logical translate is tallied once in /stats instead of twice on the
        miss path (the re-check hit/miss is a cache-primitive detail, not a new
        request). Side effects (warming memory, bumping access_count) still happen.
        """
        def tally(metric: str) -> None:
            if count:
                self._stats[metric] += 1

        tally("requests")
        k = _key(text, target)

        # 1) memory tier
        if k in self._mem:
            tally("memory_hits")
            return self._mem[k]

        # 2) SQLite tier — survives restarts; warms the memory tier on a hit.
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT translated FROM translations WHERE key = ?", (k,)
            ) as cur:
                row = await cur.fetchone()
            if row is not None:
                await db.execute(
                    "UPDATE translations SET access_count = access_count + 1 WHERE key = ?",
                    (k,),
                )
                await db.commit()
                self._mem[k] = row[0]
                tally("db_hits")
                return row[0]

        tally("misses")
        return None

    async def set(self, text: str, target: str, translated: str, model: str) -> None:
        """Store a translation in both tiers (upsert on the key)."""
        k = _key(text, target)
        self._mem[k] = translated
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO translations (key, source, target, translated, model)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    translated   = excluded.translated,
                    model        = excluded.model,
                    access_count = access_count + 1
                """,
                (k, text, target, translated, model),
            )
            await db.commit()

    async def size(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM translations") as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def stats(self) -> dict:
        total = self._stats["memory_hits"] + self._stats["db_hits"] + self._stats["misses"]
        hits = self._stats["memory_hits"] + self._stats["db_hits"]
        hit_rate = round(100 * hits / total, 1) if total else 0.0
        return {**self._stats, "hit_rate_pct": hit_rate, "memory_entries": len(self._mem)}
