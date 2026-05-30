import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "listings.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id           TEXT PRIMARY KEY,
                address      TEXT,
                rent         INTEGER,
                size_sqm     INTEGER,
                housing_type TEXT,
                url          TEXT,
                title        TEXT,
                first_seen   TEXT NOT NULL,
                last_seen    TEXT NOT NULL,
                is_new       INTEGER NOT NULL DEFAULT 1
            )
        """)
        conn.commit()


def mark_all_not_new():
    with connect() as conn:
        conn.execute("UPDATE listings SET is_new = 0")
        conn.commit()


def upsert(listing: dict) -> bool:
    """Insert new listing or update last_seen. Returns True if the listing is new."""
    now = datetime.utcnow().isoformat()
    with connect() as conn:
        existing = conn.execute(
            "SELECT id FROM listings WHERE id = ?", (listing["id"],)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE listings SET last_seen = ? WHERE id = ?",
                (now, listing["id"]),
            )
            return False
        conn.execute(
            """INSERT INTO listings
               (id, address, rent, size_sqm, housing_type, url, title, first_seen, last_seen, is_new)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                listing["id"], listing["address"], listing["rent"],
                listing["size_sqm"], listing["housing_type"],
                listing["url"], listing["title"], now, now,
            ),
        )
        return True


def get_all() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM listings ORDER BY rent ASC NULLS LAST"
        ).fetchall()
        return [dict(r) for r in rows]


def get_new() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM listings WHERE is_new = 1 ORDER BY first_seen DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def stats() -> dict:
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        new = conn.execute("SELECT COUNT(*) FROM listings WHERE is_new = 1").fetchone()[0]
        return {"total": total, "new": new}
