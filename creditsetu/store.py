"""Application store (SQLite) shared by owners and the bank-officer dashboard.

Owners submit only files they have approved. Officers move a file through statuses
and leave notes the owner can see. Every change is kept as an event, so the owner
gets a timeline.

The database path comes from ``CREDITSETU_DB`` (default ``.data/creditsetu.db``).
On Streamlit Community Cloud the disk is temporary, which is fine for a demo; a
real deployment would point this at Postgres.
"""

from __future__ import annotations

import json
import os
import random
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

STATUSES = ["received", "under_review", "documents_requested", "sanctioned", "not_sanctioned"]
STATUS_LABELS = {
    "en": {"received": "Received", "under_review": "Under review", "documents_requested": "Documents requested",
           "sanctioned": "Sanctioned", "not_sanctioned": "Not sanctioned"},
    "hi": {"received": "मिल गया", "under_review": "जाँच चल रही है", "documents_requested": "दस्तावेज़ माँगे गए",
           "sanctioned": "मंज़ूर", "not_sanctioned": "मंज़ूर नहीं"},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    ref TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    business_name TEXT, owner_name TEXT, trade TEXT, district TEXT, state TEXT,
    amount INTEGER, score INTEGER, band TEXT,
    plan_json TEXT, file_json TEXT, draft_md TEXT, documents_json TEXT,
    status TEXT NOT NULL DEFAULT 'received',
    officer_note TEXT DEFAULT '',
    source TEXT DEFAULT 'owner'
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT NOT NULL,
    at TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT DEFAULT '',
    actor TEXT DEFAULT ''
);
"""


def db_path() -> Path:
    return Path(os.environ.get("CREDITSETU_DB", ".data/creditsetu.db"))


@contextmanager
def connect(path: Optional[Path] = None):
    p = Path(path or db_path())
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(p)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_ref(rng: Optional[random.Random] = None) -> str:
    rng = rng or random.Random()
    return "CS-" + datetime.now().strftime("%y%m") + "-" + "".join(rng.choices(string.digits, k=5))


def submit(*, business_name: str, owner_name: str, trade: str, district: str, state: str, amount: int,
           score: int, band: str, plan: list, file_json: str, draft_md: str, documents: list,
           source: str = "owner", created_at: Optional[str] = None, path: Optional[Path] = None,
           ref: Optional[str] = None) -> str:
    ref = ref or new_ref()
    at = created_at or _now()
    with connect(path) as con:
        con.execute(
            "INSERT INTO applications (ref, created_at, updated_at, business_name, owner_name, trade, district, state,"
            " amount, score, band, plan_json, file_json, draft_md, documents_json, status, source)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ref, at, at, business_name, owner_name, trade, district, state, amount, score, band,
             json.dumps(plan, ensure_ascii=False), file_json, draft_md, json.dumps(documents, ensure_ascii=False),
             "received", source))
        con.execute("INSERT INTO events (ref, at, status, note, actor) VALUES (?,?,?,?,?)",
                    (ref, at, "received", "Owner-approved file received via CreditSetu.", "system"))
    return ref


def update_status(ref: str, status: str, note: str = "", actor: str = "officer", path: Optional[Path] = None,
                  at: Optional[str] = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"Unknown status {status}")
    at = at or _now()
    with connect(path) as con:
        con.execute("UPDATE applications SET status=?, officer_note=?, updated_at=? WHERE ref=?",
                    (status, note, at, ref))
        con.execute("INSERT INTO events (ref, at, status, note, actor) VALUES (?,?,?,?,?)",
                    (ref, at, status, note, actor))


def get(ref: str, path: Optional[Path] = None) -> Optional[dict]:
    with connect(path) as con:
        row = con.execute("SELECT * FROM applications WHERE ref=?", (ref.strip().upper(),)).fetchone()
        if not row:
            return None
        app = dict(row)
        app["events"] = [dict(e) for e in con.execute(
            "SELECT * FROM events WHERE ref=? ORDER BY at, id", (app["ref"],))]
    app["plan"] = json.loads(app["plan_json"] or "[]")
    app["documents"] = json.loads(app["documents_json"] or "[]")
    app["file"] = json.loads(app["file_json"] or "{}")
    return app


def list_all(path: Optional[Path] = None) -> list[dict]:
    with connect(path) as con:
        rows = [dict(r) for r in con.execute("SELECT * FROM applications ORDER BY created_at DESC")]
    for r in rows:
        docs = json.loads(r.get("documents_json") or "[]")
        r["missing_docs"] = sum(1 for d in docs if d.get("status") == "missing")
    return rows


def count(path: Optional[Path] = None) -> int:
    with connect(path) as con:
        return con.execute("SELECT COUNT(*) FROM applications").fetchone()[0]


def reset(path: Optional[Path] = None) -> None:
    with connect(path) as con:
        con.execute("DELETE FROM applications")
        con.execute("DELETE FROM events")


def backdate(ref: str, days: int, path: Optional[Path] = None) -> None:
    """Demo helper: make a seeded file look like it arrived ``days`` ago."""
    at = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with connect(path) as con:
        con.execute("UPDATE applications SET created_at=?, updated_at=? WHERE ref=?", (at, at, ref))
        con.execute("UPDATE events SET at=? WHERE ref=? AND status='received'", (at, ref))
