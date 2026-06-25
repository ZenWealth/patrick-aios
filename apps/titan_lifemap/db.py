"""
Titan LifeMap - Database

Writes into the same shared data/data.db that DataOS uses (one source of
truth across the whole AIOS workspace), in dedicated Titan-prefixed tables.

Tables:
    titan_sessions          - one row per session, current state
    titan_soft_facts        - the 8 soft-fact category outputs, one row per session
    titan_hard_facts        - financial data, one row per session
    titan_scores            - analysis layer output, one row per session
    titan_internal_profiles - the Internal AI Profile (never client-visible), one row per session
    titan_leads             - contact details + routing decision, for the workflow layer
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = WORKSPACE_ROOT / "data" / "data.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS titan_sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    current_stage TEXT NOT NULL DEFAULT 'visionary',
    completed INTEGER NOT NULL DEFAULT 0,
    route TEXT,
    first_name TEXT,
    email TEXT,
    conversation_history TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS titan_soft_facts (
    session_id TEXT PRIMARY KEY,
    future_vision_statement TEXT,
    personal_enough_statement TEXT,
    top_five_values TEXT,
    family_impact_summary TEXT,
    money_story_summary TEXT,
    behavioural_friction_profile TEXT,
    health_wealth_happiness_scorecard TEXT,
    legacy_statement TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES titan_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS titan_hard_facts (
    session_id TEXT PRIMARY KEY,
    income TEXT,
    expenses TEXT,
    assets TEXT,
    liabilities TEXT,
    existing_arrangements TEXT,
    dependants TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES titan_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS titan_scores (
    session_id TEXT PRIMARY KEY,
    clarity_score REAL,
    clarity_components TEXT,
    core_transition TEXT,
    the_one_decision TEXT,
    biggest_insight TEXT,
    the_conversation TEXT,
    momentum_plan TEXT,
    behavioural_friction_scores TEXT,
    behavioural_friction_insights TEXT,
    friction_diagnosis TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES titan_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS titan_internal_profiles (
    session_id TEXT PRIMARY KEY,
    profile_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES titan_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS titan_leads (
    session_id TEXT PRIMARY KEY,
    first_name TEXT,
    email TEXT,
    route TEXT,
    report_sent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES titan_sessions(session_id)
);
"""


def init_db() -> sqlite3.Connection:
    """Initialize the database. Creates the Titan LifeMap tables if missing."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    # Add conversation_history if it was not in the original schema
    cols = [r[1] for r in conn.execute("PRAGMA table_info(titan_sessions)").fetchall()]
    if "conversation_history" not in cols:
        conn.execute("ALTER TABLE titan_sessions ADD COLUMN conversation_history TEXT")
    # Step 8: Core Transition (the LifeMap centrepiece) + per-pattern friction
    # insights added to the scores table. Migrate existing databases in place.
    score_cols = [r[1] for r in conn.execute("PRAGMA table_info(titan_scores)").fetchall()]
    if "core_transition" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN core_transition TEXT")
    if "behavioural_friction_insights" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN behavioural_friction_insights TEXT")
    if "friction_diagnosis" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN friction_diagnosis TEXT")
    if "clarity_components" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN clarity_components TEXT")
    if "the_one_decision" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN the_one_decision TEXT")
    if "biggest_insight" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN biggest_insight TEXT")
    if "the_conversation" not in score_cols:
        conn.execute("ALTER TABLE titan_scores ADD COLUMN the_conversation TEXT")
    conn.commit()
    return conn


def get_connection() -> sqlite3.Connection:
    """Get a database connection. Initializes tables if needed."""
    return init_db()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute(
        "INSERT INTO titan_sessions (session_id, started_at, updated_at) VALUES (?, ?, ?)",
        (session_id, _now(), _now())
    )
    conn.commit()


def get_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM titan_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    return dict(row) if row else None


def update_session(conn: sqlite3.Connection, session_id: str, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE titan_sessions SET {set_clause}, updated_at = ? WHERE session_id = ?",
        (*fields.values(), _now(), session_id)
    )
    conn.commit()


def upsert_soft_facts(conn: sqlite3.Connection, session_id: str, **fields) -> None:
    existing = conn.execute(
        "SELECT 1 FROM titan_soft_facts WHERE session_id = ?", (session_id,)
    ).fetchone()
    if existing:
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE titan_soft_facts SET {set_clause}, updated_at = ? WHERE session_id = ?",
                (*fields.values(), _now(), session_id)
            )
    else:
        columns = ["session_id", *fields.keys(), "updated_at"]
        placeholders = ", ".join("?" * len(columns))
        conn.execute(
            f"INSERT INTO titan_soft_facts ({', '.join(columns)}) VALUES ({placeholders})",
            (session_id, *fields.values(), _now())
        )
    conn.commit()


def upsert_hard_facts(conn: sqlite3.Connection, session_id: str, **fields) -> None:
    existing = conn.execute(
        "SELECT 1 FROM titan_hard_facts WHERE session_id = ?", (session_id,)
    ).fetchone()
    if existing:
        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE titan_hard_facts SET {set_clause}, updated_at = ? WHERE session_id = ?",
                (*fields.values(), _now(), session_id)
            )
    else:
        columns = ["session_id", *fields.keys(), "updated_at"]
        placeholders = ", ".join("?" * len(columns))
        conn.execute(
            f"INSERT INTO titan_hard_facts ({', '.join(columns)}) VALUES ({placeholders})",
            (session_id, *fields.values(), _now())
        )
    conn.commit()


def save_scores(conn: sqlite3.Connection, session_id: str, clarity_score: float,
                 momentum_plan: list, behavioural_friction_scores: dict,
                 core_transition: str | None = None,
                 behavioural_friction_insights: dict | None = None,
                 friction_diagnosis: dict | None = None,
                 clarity_components: dict | None = None,
                 the_one_decision: str | None = None,
                 biggest_insight: str | None = None,
                 the_conversation: str | None = None) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO titan_scores "
        "(session_id, clarity_score, clarity_components, core_transition, the_one_decision, "
        "biggest_insight, the_conversation, momentum_plan, behavioural_friction_scores, "
        "behavioural_friction_insights, friction_diagnosis, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, clarity_score, json.dumps(clarity_components or {}), core_transition,
         the_one_decision, biggest_insight, the_conversation, json.dumps(momentum_plan),
         json.dumps(behavioural_friction_scores),
         json.dumps(behavioural_friction_insights or {}),
         json.dumps(friction_diagnosis or {}), _now())
    )
    conn.commit()


def save_internal_profile(conn: sqlite3.Connection, session_id: str, profile: dict) -> None:
    """Write the Internal AI Profile. This table is never read by any
    client-facing report query - see reports/internal.py."""
    conn.execute(
        "INSERT OR REPLACE INTO titan_internal_profiles (session_id, profile_json, created_at) "
        "VALUES (?, ?, ?)",
        (session_id, json.dumps(profile), _now())
    )
    conn.commit()


def save_lead(conn: sqlite3.Connection, session_id: str, first_name: str,
              email: str, route: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO titan_leads (session_id, first_name, email, route, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, first_name, email, route, _now())
    )
    conn.commit()


if __name__ == "__main__":
    conn = init_db()
    print(f"Database initialized at: {DB_PATH}")
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'titan_%' ORDER BY name"
    ).fetchall()
    print(f"Titan LifeMap tables: {[t['name'] for t in tables]}")
    conn.close()
