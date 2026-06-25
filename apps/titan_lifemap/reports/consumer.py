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

            def _col(name, default=None):
                return score_row[name] if name in score_keys else default

            scores = {
                "clarity_score": score_row["clarity_score"],
                "clarity_components": json.loads(_col("clarity_components") or "{}"),
                "core_transition": _col("core_transition"),
                "the_one_decision": _col("the_one_decision"),
                "biggest_insight": _col("biggest_insight"),
                "the_conversation": _col("the_conversation"),
                "momentum_plan": json.loads(score_row["momentum_plan"] or "[]"),
                "behavioural_friction_scores": json.loads(
                    score_row["behavioural_friction_scores"] or "{}"
                ),
                "friction_diagnosis": json.loads(_col("friction_diagnosis") or "{}"),
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
