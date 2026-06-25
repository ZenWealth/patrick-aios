"""
Titan LifeMap - Seed & render a test report (verification helper)

Seeds a synthetic *completed* session (test-pdf-0001) with representative
soft facts + scores (including a Core Transition), then renders the consumer
report to /tmp and prints it as plain text for review.

Usage (from the repo root):
    .venv/bin/python scripts/seed_test_report.py            # consumer report
    .venv/bin/python scripts/seed_test_report.py coaching   # other report type

Only touches the test-pdf-0001 row — real sessions are untouched. Makes one
batch of Claude calls (one per report section) on each run.
"""

import os
import re
import sys
import traceback

# Allow `import apps.titan_lifemap...` when run as a loose script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.titan_lifemap.db import (
    get_connection, create_session, update_session, upsert_soft_facts, save_scores,
)

SID = "test-pdf-0001"
REPORT_TYPE = sys.argv[1] if len(sys.argv) > 1 else "consumer"

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

MOMENTUM_PLAN = [
    "Define 'enough' as a specific number with your adviser, then stop moving it.",
    "Hand one strategic decision per quarter fully to your leadership team and do not review it.",
    "Book the health screening you keep deferring — this quarter, not 'soon'.",
    "Write the one-page letter to your children about judgement over money.",
    "Schedule the first winter writing block now, before the calendar fills.",
]

FRICTION_SCORES = {
    "procrastination": 4.0, "avoidance": 6.0, "overthinking": 8.0,
    "impulsiveness": 2.0, "delegation": 5.0, "lack_of_confidence": 3.0,
}

FRICTION_INSIGHTS = {
    "procrastination": "Acts decisively in business but stalls on personal decisions that have no external deadline.",
    "avoidance": "Avoids the health question precisely because it is the one risk he cannot delegate.",
    "overthinking": "Researches personal decisions to the point where analysis becomes a way of not choosing.",
    "impulsiveness": "Rarely impulsive; if anything, too deliberate.",
    "delegation": "Delegates operations easily but keeps strategic control close — the bottleneck to stepping back.",
    "lack_of_confidence": "Confident externally; the private doubt is whether enough will ever feel like enough.",
}

FRICTION_DIAGNOSIS = {
    "primary_friction": {
        "name": "Identity Attachment",
        "what": "Your sense of self is bound to being the one everything runs through.",
        "how": "You keep making yourself necessary — holding the strategic decisions you could hand over — because stepping back feels less like freedom than like disappearing.",
        "cost": "It defers the winters-writing life you have already described and keeps you on a finish line you quietly keep moving.",
    },
    "secondary_frictions": [
        {"name": "Over-responsibility",
         "what": "You carry decisions that are no longer yours to carry.",
         "how": "You review what you have delegated; little stays fully handed over.",
         "cost": "It caps the freedom the whole plan is meant to buy."},
        {"name": "Avoidance",
         "what": "You sidestep the one risk you cannot delegate.",
         "how": "You keep postponing the health question while optimising everything else.",
         "cost": "The unhedged health risk compounds in the background."},
    ],
    "holding_you_back": "What's holding you back isn't money — it's that stepping back still feels like disappearing, so you keep making yourself indispensable.",
}

CLARITY_COMPONENTS = {
    "vision": 82,
    "values": 78,
    "execution": 58,
    "health_alignment": 54,
    "legacy_clarity": 80,
}

THE_ONE_DECISION = (
    "Hand over one strategic decision completely — and do not review it — so the thing you "
    "built can prove it runs without you. Almost everything else you want depends on first "
    "believing that it can."
)


def seed():
    conn = get_connection()
    for t in ("titan_soft_facts", "titan_scores", "titan_internal_profiles",
              "titan_leads", "titan_hard_facts"):
        conn.execute(f"DELETE FROM {t} WHERE session_id = ?", (SID,))
    conn.execute("DELETE FROM titan_sessions WHERE session_id = ?", (SID,))
    conn.commit()
    conn.close()

    conn = get_connection()
    create_session(conn, SID)
    update_session(conn, SID, completed=1, current_stage="guardian", route=REPORT_TYPE,
                   first_name="Patrick", email="patrickmurphyzen@gmail.com")
    conn.close()

    conn = get_connection()
    upsert_soft_facts(conn, SID, **SOFT_FACTS)
    conn.close()

    conn = get_connection()
    save_scores(conn, SID, clarity_score=70.4, momentum_plan=MOMENTUM_PLAN,
                behavioural_friction_scores=FRICTION_SCORES,
                core_transition="From building to entrusting",
                behavioural_friction_insights=FRICTION_INSIGHTS,
                friction_diagnosis=FRICTION_DIAGNOSIS,
                clarity_components=CLARITY_COMPONENTS,
                the_one_decision=THE_ONE_DECISION)
    conn.close()
    print("Seeded:", SID, "| report type:", REPORT_TYPE)


def to_text(html: str) -> str:
    body = html.split("<body>", 1)[-1].split("</body>", 1)[0]
    body = re.sub(r"<style.*?</style>", "", body, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "", body)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def main():
    seed()
    try:
        from apps.titan_lifemap.reports import consumer, coaching, adviser
        builder = {"consumer": consumer, "coaching": coaching, "adviser": adviser}.get(REPORT_TYPE, consumer)
        html = builder.build(SID, as_pdf=False)
        open("/tmp/lifemap-test.html", "w").write(html)
        from apps.titan_lifemap.reports.engine import render_pdf
        open("/tmp/lifemap-test.pdf", "wb").write(render_pdf(html))
        print(f"HTML {len(html)} bytes; PDF -> /tmp/lifemap-test.pdf\n")
        print("=" * 70)
        print(to_text(html))
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
