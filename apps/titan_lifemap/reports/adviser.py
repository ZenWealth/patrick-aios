"""
Titan LifeMap - Adviser Report

Generated for sessions routed to adviser introduction. Clinical, precise,
complete. Includes all hard facts and behavioural context for the adviser.
Written for a Chartered Financial Planner.
"""

import json

from apps.titan_lifemap.db import get_connection, get_session
from apps.titan_lifemap.reports.engine import generate_report


def build(session_id: str, as_pdf: bool = True) -> bytes | str:
    """Generate the adviser briefing report for a completed session."""
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        soft_row = conn.execute(
            "SELECT * FROM titan_soft_facts WHERE session_id = ?", (session_id,)
        ).fetchone()
        hard_row = conn.execute(
            "SELECT * FROM titan_hard_facts WHERE session_id = ?", (session_id,)
        ).fetchone()
        score_row = conn.execute(
            "SELECT * FROM titan_scores WHERE session_id = ?", (session_id,)
        ).fetchone()

        scores = {}
        if score_row:
            scores = {
                "clarity_score": score_row["clarity_score"],
                "momentum_plan": json.loads(score_row["momentum_plan"] or "[]"),
                "behavioural_friction_scores": json.loads(
                    score_row["behavioural_friction_scores"] or "{}"
                ),
            }

        session_data = {
            "session": dict(session),
            "soft_facts": dict(soft_row) if soft_row else {},
            "hard_facts": dict(hard_row) if hard_row else {},
            "scores": scores,
        }

        return generate_report("adviser", session_data, as_pdf=as_pdf)
    finally:
        conn.close()
