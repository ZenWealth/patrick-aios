"""
Titan LifeMap - Inspect live discovery sessions (diagnostic, read-only)

For each real (non-test) session, prints stage, completed flag, turn counts,
whether any assistant message emitted [STAGE_COMPLETE]/[DISCOVERY_COMPLETE],
and the last assistant message snippet. This distinguishes genuine abandonment
(few turns) from a signalling failure (many turns, no signal, still stuck).

Run from the repo root:  .venv/bin/python scripts/inspect_sessions.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.titan_lifemap.db import get_connection

conn = get_connection()
rows = conn.execute(
    "SELECT session_id, current_stage, completed, email, conversation_history, "
    "started_at, updated_at FROM titan_sessions ORDER BY rowid DESC"
).fetchall()
conn.close()

real = 0
for r in rows:
    sid = r["session_id"]
    if sid.startswith("test-"):
        continue
    real += 1
    hist = json.loads(r["conversation_history"] or "[]")
    users = [m for m in hist if m.get("role") == "user"]
    assts = [m for m in hist if m.get("role") == "assistant"]
    blob = "\n".join(m.get("content", "") for m in assts)
    stage_sig = blob.count("[STAGE_COMPLETE]")
    disc_sig = blob.count("[DISCOVERY_COMPLETE]")
    last = assts[-1]["content"].strip() if assts else "(none)"
    longest_user = max((len(m.get("content", "")) for m in users), default=0)

    print("=" * 72)
    print(f"{sid[:8]}  stage={r['current_stage']}  completed={r['completed']}  email={r['email']}")
    print(f"  turns: user={len(users)} assistant={len(assts)} | "
          f"longest user msg={longest_user} chars")
    print(f"  signals: [STAGE_COMPLETE] x{stage_sig}   [DISCOVERY_COMPLETE] x{disc_sig}")
    print(f"  started={r['started_at']}  updated={r['updated_at']}")
    print(f"  last assistant said:\n    {last[:320]}")

print("=" * 72)
print(f"Total real (non-test) sessions: {real}")
