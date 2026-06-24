"""
Titan LifeMap - Rescue a stalled session and generate its report

For a real session that concluded the discovery but never completed (because the
old engine relied on an inline token), this extracts its soft facts from the
transcript, marks it complete, runs the real analysis (capturing the Core
Transition + scores), renders the consumer report, and prints it.

No email is sent (the workflow's email step is not invoked here, and these
sessions have no address anyway). This DOES mark the real session completed=1
and writes its soft facts / scores.

Usage (from the repo root):
    .venv/bin/python scripts/rescue_session.py <session_id_or_prefix>
"""

import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.titan_lifemap.db import get_connection, upsert_soft_facts, update_session
from apps.titan_lifemap import conversation as C
from apps.titan_lifemap.analysis import run_analysis
from apps.titan_lifemap.reports import consumer
from apps.titan_lifemap.reports.engine import render_pdf

if len(sys.argv) < 2:
    print("usage: rescue_session.py <session_id_or_prefix>")
    sys.exit(1)
key = sys.argv[1]

conn = get_connection()
row = conn.execute(
    "SELECT session_id, conversation_history, completed, email, first_name "
    "FROM titan_sessions WHERE session_id = ? OR session_id LIKE ?",
    (key, key + "%"),
).fetchone()
conn.close()
if not row:
    print("No session matching:", key)
    sys.exit(1)

sid = row["session_id"]
hist = json.loads(row["conversation_history"] or "[]")
turns = sum(1 for m in hist if m.get("role") == "user")
print(f"Rescuing {sid}  (name={row['first_name']} email={row['email']} "
      f"completed={row['completed']} turns={turns})")

# 1. Confirm it really concluded
print("detector discovery_complete:", C._detect_completion(hist))

# 2. Extract soft facts from the full transcript and persist
facts = C._extract_all_soft_facts(hist)
print(f"extracted {len(facts)}/{len(C.SOFT_FACT_FIELDS)} soft-fact fields")
conn = get_connection()
if facts:
    upsert_soft_facts(conn, sid, **facts)
update_session(conn, sid, completed=1, route="consumer")
conn.close()

# 3. Real analysis pass -> Core Transition + scores
print("\nrunning analysis ...")
scores = run_analysis(sid)
print("core_transition:", scores.get("core_transition"))
print("clarity_score  :", scores.get("clarity_score"))

# 4. Render the report once and print it
html = consumer.build(sid, as_pdf=False)
open(f"/tmp/lifemap-{sid[:8]}.html", "w").write(html)
open(f"/tmp/lifemap-{sid[:8]}.pdf", "wb").write(render_pdf(html))
print(f"PDF -> /tmp/lifemap-{sid[:8]}.pdf\n")

body = html.split("<body>", 1)[-1].split("</body>", 1)[0]
body = re.sub(r"<style.*?</style>", "", body, flags=re.DOTALL)
text = re.sub(r"<[^>]+>", "", body)
text = re.sub(r"[ \t]+", " ", text)
text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
print("=" * 72)
print(text.strip())
