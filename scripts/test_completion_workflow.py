"""
Titan LifeMap - Test the full post-session workflow (the /complete trigger target)

Verifies the chain the frontend trigger fires, end-to-end and WITHOUT HTTP:
seeds a completed session with soft facts but NO scores, then runs
routing.run_completion_workflow — which runs the REAL analysis (generating the
Core Transition from the session record, not a hand-written one), stores the
scores, and renders the report. Email/webhook are skipped if unconfigured.

Run from the repo root:
    .venv/bin/python scripts/test_completion_workflow.py

Only touches the test-trigger-0002 row. Makes real Claude calls (analysis +
one per report section).
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.titan_lifemap.db import (
    get_connection, create_session, update_session, upsert_soft_facts,
)
from apps.titan_lifemap import routing

SID = "test-trigger-0002"

SOFT_FACTS = dict(
    future_vision_statement=(
        "By 65 he wants to have stepped back from day-to-day operations of the group, "
        "spending winters writing and mentoring two or three founders, with the family "
        "office running without him."),
    personal_enough_statement=(
        "A liquid net worth that throws off enough income to never check a share price "
        "out of fear — he suspects this number is far lower than what he is still "
        "driving toward."),
    top_five_values="Autonomy; Mastery; Family security; Intellectual honesty; Legacy through others",
    family_impact_summary=(
        "Worries his drive has modelled relentlessness rather than contentment for his "
        "children; wants them to inherit judgement, not just capital."),
    money_story_summary=(
        "Grew up watching a capable father stay trapped in a job he resented, for "
        "security. Money became proof he would never be trapped — which has made "
        "stopping feel like danger."),
    behavioural_friction_profile=(
        "Over-researches before acting on personal (not business) decisions; delegates "
        "operationally but hoards strategic decisions."),
    health_wealth_happiness_scorecard="Wealth 9/10, Health 6/10, Happiness 7/10 — aware health is the unhedged risk.",
    legacy_statement=(
        "To be remembered by a handful of people as the person who changed the trajectory "
        "of their thinking, not for the size of his estate."),
)


def main():
    conn = get_connection()
    for t in ("titan_soft_facts", "titan_scores", "titan_internal_profiles",
              "titan_leads", "titan_hard_facts"):
        conn.execute(f"DELETE FROM {t} WHERE session_id = ?", (SID,))
    conn.execute("DELETE FROM titan_sessions WHERE session_id = ?", (SID,))
    conn.commit()
    conn.close()

    conn = get_connection()
    create_session(conn, SID)
    update_session(conn, SID, completed=1, current_stage="guardian", route="consumer",
                   first_name="Patrick", email="patrickmurphyzen@gmail.com")
    conn.close()

    conn = get_connection()
    upsert_soft_facts(conn, SID, **SOFT_FACTS)
    conn.close()
    print("Seeded completed-unscored session:", SID)

    print("\nRunning run_completion_workflow (real analysis + report; "
          "email/webhook skip if unconfigured)...\n")
    result = routing.run_completion_workflow(SID)
    print("workflow result:", json.dumps(result, indent=2, default=str))

    conn = get_connection()
    row = conn.execute(
        "SELECT core_transition, clarity_score, behavioural_friction_insights "
        "FROM titan_scores WHERE session_id = ?", (SID,)
    ).fetchone()
    profile = conn.execute(
        "SELECT 1 FROM titan_internal_profiles WHERE session_id = ?", (SID,)
    ).fetchone()
    lead = conn.execute(
        "SELECT report_sent FROM titan_leads WHERE session_id = ?", (SID,)
    ).fetchone()
    conn.close()

    print("\n--- Persisted by the REAL analysis pass ---")
    if row:
        print("core_transition :", repr(row["core_transition"]))
        print("clarity_score   :", row["clarity_score"])
        insights = json.loads(row["behavioural_friction_insights"] or "{}")
        print("friction_insights:", "present" if insights else "MISSING",
              f"({len(insights)} patterns)")
    else:
        print("NO scores row created — analysis did not persist.")
    print("internal_profile:", "stored" if profile else "MISSING")
    print("lead row        :", "stored" if lead else "MISSING",
          f"(report_sent={lead['report_sent']})" if lead else "")


if __name__ == "__main__":
    main()
