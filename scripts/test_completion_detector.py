"""
Titan LifeMap - Test the completion detector + soft-fact extraction (read-only)

Runs the new monitor passes against REAL stored sessions without modifying anything.
Confirms the detector marks the substantive (16-25 turn) sessions complete and the
abandoned (1-2 turn) ones not complete, and that extraction produces real soft facts.

Run from the repo root:
    .venv/bin/python scripts/test_completion_detector.py            # all real sessions
    .venv/bin/python scripts/test_completion_detector.py <id> ...   # specific sessions
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from apps.titan_lifemap.config import ANTHROPIC_API_KEY
from apps.titan_lifemap.db import get_connection
from apps.titan_lifemap import conversation as C

# Probe that the detector model is actually reachable on this account
print(f"Detector model: {C.DETECTOR_MODEL}")
try:
    anthropic.Anthropic(api_key=ANTHROPIC_API_KEY).messages.create(
        model=C.DETECTOR_MODEL, max_tokens=10,
        messages=[{"role": "user", "content": "Reply with OK"}],
    )
    print("  reachable: yes\n")
except Exception as e:
    print(f"  reachable: NO -> {e!r}\n  (detector will silently return False until this is fixed)\n")

ids = sys.argv[1:]
conn = get_connection()
if ids:
    rows = [conn.execute(
        "SELECT session_id, conversation_history FROM titan_sessions WHERE session_id = ?",
        (i,)).fetchone() for i in ids]
else:
    rows = conn.execute(
        "SELECT session_id, conversation_history FROM titan_sessions ORDER BY rowid DESC"
    ).fetchall()
conn.close()

for r in rows:
    if r is None:
        continue
    sid = r["session_id"]
    if not ids and sid.startswith("test-"):
        continue
    hist = json.loads(r["conversation_history"] or "[]")
    turns = sum(1 for m in hist if m.get("role") == "user")
    print("=" * 72)
    print(f"{sid[:8]}  user_turns={turns}")

    if turns < C.MIN_TURNS_BEFORE_COMPLETION:
        print(f"  below MIN_TURNS ({C.MIN_TURNS_BEFORE_COMPLETION}) — production skips the "
              f"detector here (treated as not complete)")
        continue

    complete = C._detect_completion(hist)
    print(f"  detector: discovery_complete = {complete}")
    if not complete:
        continue

    facts = C._extract_all_soft_facts(hist)
    print(f"  extraction: {len(facts)}/{len(C.SOFT_FACT_FIELDS)} fields populated")
    for k in C.SOFT_FACT_FIELDS:
        v = facts.get(k, "")
        shown = (v[:130] + "…") if len(v) > 130 else v
        print(f"    - {k}: {shown if v else '(empty)'}")
