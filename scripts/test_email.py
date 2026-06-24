"""
Titan LifeMap - Test email delivery

Verifies SMTP is configured correctly and sends a real Titan LifeMap report to
the session's email address. Order: check config -> probe SMTP login (surfaces
auth errors clearly) -> build report -> send.

Run from the repo root:
    .venv/bin/python scripts/test_email.py [session_id]

Default session: test-pdf-0001 (seeded; email = patrickmurphyzen@gmail.com).
Makes Claude calls to build the report only if SMTP login succeeds.
"""

import os
import sys
import smtplib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.titan_lifemap.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAKE_WEBHOOK_URL,
)
from apps.titan_lifemap.db import get_connection, get_session
from apps.titan_lifemap import routing
from apps.titan_lifemap.reports import consumer

sid = sys.argv[1] if len(sys.argv) > 1 else "test-pdf-0001"

print("=== SMTP config ===")
print("  SMTP_HOST     :", SMTP_HOST or "MISSING")
print("  SMTP_PORT     :", SMTP_PORT or "MISSING")
print("  SMTP_USER     :", SMTP_USER or "MISSING")
print("  SMTP_PASSWORD :", "set" if SMTP_PASSWORD else "MISSING")
print("  MAKE_WEBHOOK  :", "set" if MAKE_WEBHOOK_URL else "(not set)")

if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD]):
    print("\nSMTP not fully configured — add the keys to .env and restart. Aborting.")
    sys.exit(1)

print("\n=== SMTP login probe ===")
try:
    with smtplib.SMTP(SMTP_HOST, int(SMTP_PORT), timeout=20) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
    print("  login OK")
except Exception as e:
    print("  login FAILED:", repr(e))
    print("  (Google Workspace needs an App Password with 2FA enabled, port 587.)")
    sys.exit(1)

conn = get_connection()
session = get_session(conn, sid)
conn.close()
if not session:
    print("No session:", sid)
    sys.exit(1)
print("\nsession:", sid, "| email:", session.get("email"))
if not session.get("email"):
    print("Session has no email address — nothing to send to. Aborting.")
    sys.exit(1)

print("building report (Claude calls) ...")
pdf = consumer.build(sid, as_pdf=True)
print(f"report {len(pdf)} bytes; sending ...")
ok = routing.send_report_email(sid, session.get("route") or "consumer", pdf)
print("\nsend_report_email ->", ok)
print("Check the inbox for", session.get("email"))
