"""
Titan LifeMap - Routing Layer

Called after session completion and report generation. Handles:
  1. Storing the lead in titan_leads
  2. Sending the client-facing report by email (Google Workspace SMTP)
  3. Firing the Make.com webhook for downstream automation
  4. Routing to the adviser/coaching/consumer flow based on session route

The Internal AI Profile is NOT routed here - it is stored by analysis.py
and never leaves the system via email or webhook.
"""

import json
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import urllib.request

from apps.titan_lifemap.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAKE_WEBHOOK_URL
from apps.titan_lifemap.db import get_connection, get_session, save_lead, update_session
from apps.titan_lifemap.analysis import run_analysis
from apps.titan_lifemap.reports import consumer, coaching, adviser

logger = logging.getLogger(__name__)

ROUTE_CONSUMER = "consumer"
ROUTE_COACHING = "coaching"
ROUTE_ADVISER = "adviser"


def determine_route(session_id: str) -> str:
    """Determine the routing for a completed session.

    Routing logic (Phase 1 — manual/default, no scoring-based auto-routing yet):
    - If session.route is already set, use it
    - Default to 'consumer' if no route has been set

    Future phases: scoring thresholds in scoring_rules.yaml can drive auto-routing.
    """
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        return session.get("route") or ROUTE_CONSUMER
    finally:
        conn.close()


def store_lead(session_id: str, route: str) -> None:
    """Store the lead record in titan_leads and update session route."""
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        first_name = session.get("first_name") or "Friend"
        email = session.get("email")

        if email:
            save_lead(conn, session_id, first_name, email, route)

        update_session(conn, session_id, route=route)
        logger.info("Lead stored for session %s: route=%s email=%s", session_id, route, email)
    finally:
        conn.close()


def send_report_email(session_id: str, route: str, report_bytes: bytes) -> bool:
    """Send the client-facing report PDF by email via Google Workspace SMTP.

    Returns True if sent, False if no email address or SMTP not configured.
    """
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        to_email = session.get("email") if session else None
    finally:
        conn.close()

    if not to_email:
        logger.info("No email address for session %s — skipping email send", session_id)
        return False

    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD]):
        logger.warning("SMTP not configured — skipping email send for session %s", session_id)
        return False

    first_name = session.get("first_name") or "there"

    subject_map = {
        ROUTE_CONSUMER: "Your Titan LifeMap Report",
        ROUTE_COACHING: "Your Titan LifeMap Report — Coaching Edition",
        ROUTE_ADVISER: "Your Titan LifeMap Report",
    }
    subject = subject_map.get(route, "Your Titan LifeMap Report")

    body = f"""Hi {first_name},

Thank you for completing your Titan LifeMap Discovery Session.

Please find your personalised Titan LifeMap report attached.

If you have any questions or would like to discuss what came up in your session,
you're welcome to get in touch directly.

With kind regards,
Patrick Murphy
Sustain Momentum
sustain-momentum.com
"""

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEApplication(report_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename="titan-lifemap-report.pdf")
    msg.attach(attachment)

    try:
        port = int(SMTP_PORT)
        with smtplib.SMTP(SMTP_HOST, port) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.sendmail(SMTP_USER, to_email, msg.as_string())
        logger.info("Report email sent to %s for session %s", to_email, session_id)

        conn = get_connection()
        try:
            conn.execute(
                "UPDATE titan_leads SET report_sent = 1 WHERE session_id = ?", (session_id,)
            )
            conn.commit()
        finally:
            conn.close()

        return True

    except Exception as e:
        logger.error("Failed to send report email for session %s: %s", session_id, e)
        return False


def notify_make_webhook(session_id: str, route: str) -> bool:
    """Fire a Make.com webhook with session metadata for downstream automation.

    Returns True if the webhook fired successfully.
    """
    if not MAKE_WEBHOOK_URL:
        logger.debug("MAKE_WEBHOOK_URL not set — skipping webhook for session %s", session_id)
        return False

    conn = get_connection()
    try:
        session = get_session(conn, session_id)
    finally:
        conn.close()

    if not session:
        return False

    payload = json.dumps({
        "session_id": session_id,
        "route": route,
        "first_name": session.get("first_name"),
        "email": session.get("email"),
        "completed_at": session.get("updated_at"),
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            MAKE_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
        logger.info("Make webhook fired for session %s: HTTP %s", session_id, status)
        return status < 300
    except Exception as e:
        logger.error("Make webhook failed for session %s: %s", session_id, e)
        return False


def run_completion_workflow(session_id: str) -> dict:
    """Full post-session workflow: analyse → route → generate report → email → webhook.

    Called by main.py when a session is marked complete.
    Returns a summary dict with what was done.
    """
    result = {
        "session_id": session_id,
        "analysis": False,
        "route": None,
        "report_generated": False,
        "email_sent": False,
        "webhook_fired": False,
    }

    # 1. Run analysis (scores + Internal AI Profile)
    try:
        scores = run_analysis(session_id)
        result["analysis"] = True
        result["clarity_score"] = scores["clarity_score"]
    except Exception as e:
        logger.error("Analysis failed for session %s: %s", session_id, e)
        return result

    # 2. Determine route and store lead
    route = determine_route(session_id)
    store_lead(session_id, route)
    result["route"] = route

    # 3. Generate the appropriate client-facing report
    try:
        report_builders = {
            ROUTE_CONSUMER: consumer.build,
            ROUTE_COACHING: coaching.build,
            ROUTE_ADVISER: adviser.build,
        }
        builder = report_builders.get(route, consumer.build)
        report_pdf = builder(session_id, as_pdf=True)
        result["report_generated"] = True
    except Exception as e:
        logger.error("Report generation failed for session %s: %s", session_id, e)
        return result

    # 4. Send email
    result["email_sent"] = send_report_email(session_id, route, report_pdf)

    # 5. Fire webhook
    result["webhook_fired"] = notify_make_webhook(session_id, route)

    logger.info("Completion workflow done for session %s: %s", session_id, result)
    return result
