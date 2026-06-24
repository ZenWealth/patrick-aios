"""
Titan LifeMap - Consumer Report

The report a client receives after their discovery session. Warm, personal,
non-technical. Delivered via email (routing.py) or available at a session
summary URL. Never includes raw hard financial data.
"""

from apps.titan_lifemap.db import get_connection, get_session
from apps.titan_lifemap.reports.engine import generate_report


def build(session_id: str, as_pdf: bool = True) -> bytes | str:
    """Generate the consumer report for a completed session."""
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        soft_row = conn.execute(
            "SELECT * FROM titan_soft_facts WHERE session_id = ?", (session_id,)
        ).fetchone()
        score_row = conn.execute(
            "SELECT * FROM titan_scores WHERE session_id = ?", (session_id,)
        ).fetchone()

        import json
        scores = {}
        if score_row:
            score_keys = score_row.keys()
            scores = {
                "clarity_score": score_row["clarity_score"],
                "core_transition": score_row["core_transition"] if "core_transition" in score_keys else None,
                "momentum_plan": json.loads(score_row["momentum_plan"] or "[]"),
                "behavioural_friction_scores": json.loads(
                    score_row["behavioural_friction_scores"] or "{}"
                ),
                "friction_diagnosis": json.loads(
                    score_row["friction_diagnosis"] or "{}"
                ) if "friction_diagnosis" in score_keys else {},
            }

        session_data = {
            "session": dict(session),
            "soft_facts": dict(soft_row) if soft_row else {},
            "hard_facts": {},
            "scores": scores,
        }

        return generate_report("consumer", session_data, as_pdf=as_pdf)
    finally:
        conn.close()
