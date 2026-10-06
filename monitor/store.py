import re
import sqlite3
from pathlib import Path

from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT DEFAULT '',
  city TEXT DEFAULT '',
  url TEXT DEFAULT '',
  salary_raw TEXT DEFAULT '',
  posted_at TEXT DEFAULT '',
  deadline TEXT DEFAULT '',
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  is_new INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  UNIQUE(source, external_id)
);
"""


def open_db(path: str | None = None) -> sqlite3.Connection:
    p = Path(path or DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.execute(SCHEMA)
    con.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    cols = {r[1] for r in con.execute("PRAGMA table_info(jobs)")}
    for c in ("posted_at", "deadline", "misses"):
        if c not in cols:
            con.execute(f"ALTER TABLE jobs ADD COLUMN {c} TEXT DEFAULT ''")
    con.commit()
    con.row_factory = sqlite3.Row
    return con


def get_meta(con: sqlite3.Connection, key: str) -> str | None:
    row = con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def set_meta_now(con: sqlite3.Connection, key: str) -> None:
    con.execute(
        "INSERT INTO meta (key, value) VALUES (?, datetime('now')) "
        "ON CONFLICT(key) DO UPDATE SET value = datetime('now')",
        (key,),
    )
    con.commit()


def upsert(con: sqlite3.Connection, source: str, job: dict) -> bool:
    """Zwraca True jesli to nowe ogloszenie (pierwsze wstawienie)."""
    cur = con.execute(
        """INSERT INTO jobs (source, external_id, title, company, city, url, salary_raw,
                             posted_at, deadline,
                             first_seen_at, last_seen_at, is_new, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1, 'active')
           ON CONFLICT(source, external_id) DO UPDATE SET
             last_seen_at = datetime('now'),
             misses = 0,
             title = excluded.title,
             company = excluded.company,
             url = excluded.url,
             posted_at = COALESCE(NULLIF(excluded.posted_at, ''), jobs.posted_at),
             deadline = COALESCE(NULLIF(excluded.deadline, ''), jobs.deadline),
             status = CASE WHEN jobs.status = 'expired' THEN 'active' ELSE jobs.status END
        """,
        (
            source,
            job["external_id"],
            job.get("title", ""),
            job.get("company", ""),
            job.get("city", ""),
            job.get("url", ""),
            job.get("salary_raw", ""),
            job.get("posted_at", ""),
            job.get("deadline", ""),
        ),
    )
    return cur.rowcount == 1


DEAD_AFTER_MISSES = 2  # ile kolejnych skanow ogloszenie zniknac musi, zanim sprawdzimy link


def mark_missed(con: sqlite3.Connection, source: str, present_ids: list[str]) -> int:
    """Nie ubijamy od razu: liczymy pominięcia. Wygaśnięcie potwierdza probe linku.

    Każdy skraper zwraca tylko podzbiór listy (jedna strona, własne słowa kluczowe),
    wiec "nie widziałem w tym skanie" != "oferta zniknęła"."""
    if not present_ids:
        return 0  # skraper nic nie zwrócił -> nie ruszamy statusów
    placeholders = ",".join("?" * len(present_ids))
    cur = con.execute(
        f"""UPDATE jobs SET misses = CAST(COALESCE(misses, 0) AS INTEGER) + 1
            WHERE source = ? AND status = 'active'
              AND external_id NOT IN ({placeholders})""",
        [source, *present_ids],
    )
    return cur.rowcount


def dead_candidates(con: sqlite3.Connection, limit: int = 80) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT * FROM jobs
           WHERE status = 'active' AND CAST(COALESCE(misses, 0) AS INTEGER) >= ?
           ORDER BY last_seen_at LIMIT ?""",
        (DEAD_AFTER_MISSES, limit),
    ).fetchall()


def expire(con: sqlite3.Connection, source: str, external_id: str) -> None:
    con.execute(
        "UPDATE jobs SET status = 'expired', is_new = 0 WHERE source = ? AND external_id = ?",
        (source, external_id),
    )


def touch(con: sqlite3.Connection, source: str, external_id: str) -> None:
    """Oferta zniknela z listy, ale link zyje -> zostaje i zerujemy licznik."""
    con.execute(
        """UPDATE jobs SET misses = 0, last_seen_at = datetime('now')
           WHERE source = ? AND external_id = ?""",
        (source, external_id),
    )


DEAD_MARKS = (
    "oferta zakończona", "oferta zakończyl", "oferta nieaktywna", "ogłoszenie nieaktywne",
    "nie istnieje", "wygasła", "wygasla", "strona nie istnieje", "oferta usunięta",
)


def probe_alive(url: str) -> bool:
    """Czy oferta wciaz istnieje? Blad sieci = wierzymy, ze zyje (nie ubijamy na slepo)."""
    if not url:
        return False
    try:
        from curl_cffi import requests as creq

        r = creq.get(url, impersonate="chrome", timeout=20)
    except Exception:
        return True
    if r.status_code >= 400:
        return False
    low = re.sub(r"<[^>]+>", " ", (r.text or "")[:120000]).lower()
    return not any(k in low for k in DEAD_MARKS)


def new_jobs(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute(
        "SELECT * FROM jobs WHERE is_new = 1 AND status = 'active' ORDER BY source, title"
    ).fetchall()


def recent_jobs(
    con: sqlite3.Connection, days: int = 3, since: str | None = None
) -> list[sqlite3.Row]:
    return con.execute(
        """SELECT * FROM jobs
           WHERE status = 'active'
             AND (is_new = 1
                  OR COALESCE(NULLIF(posted_at, ''), first_seen_at) >= datetime('now', ?)
                  OR (? IS NOT NULL AND first_seen_at >= ?))
           ORDER BY COALESCE(NULLIF(posted_at, ''), first_seen_at) DESC,
                    title COLLATE NOCASE""",
        (f"-{days} days", since, since),
    ).fetchall()


def active_jobs(con: sqlite3.Connection) -> list[sqlite3.Row]:
    """Wszystkie aktywne oferty (do index.html)."""
    return con.execute(
        "SELECT * FROM jobs WHERE status = 'active' ORDER BY title COLLATE NOCASE"
    ).fetchall()


def mark_notified(con: sqlite3.Connection) -> None:
    con.execute("UPDATE jobs SET is_new = 0 WHERE is_new = 1")
    con.commit()
