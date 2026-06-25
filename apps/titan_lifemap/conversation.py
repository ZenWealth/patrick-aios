"""
Titan LifeMap - Conversation Engine

Manages the five-stage Titan LifeMap discovery conversation.
Uses the Anthropic messages API (not the Agent SDK - this is real-time chat).

Stage sequencing: Visionary → Sage → Builder → Steward → Guardian

Conversation history is persisted in titan_sessions.conversation_history so
that stateless FastAPI workers can resume any session.
"""

import json
import logging
import re
import sqlite3
from dataclasses import dataclass

import anthropic

from apps.titan_lifemap.config import ANTHROPIC_API_KEY
from apps.titan_lifemap.config_loader import get_stages, get_prompt
from apps.titan_lifemap.db import (
    get_connection, get_session, update_session,
    upsert_soft_facts, upsert_hard_facts,
)

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

STAGE_ORDER = ["visionary", "sage", "builder", "steward", "guardian"]

# Completion is detected by a separate, cheap monitor pass rather than by the chat
# model emitting an inline [DISCOVERY_COMPLETE] token — which, in practice, it does
# not do reliably (it concludes the discovery in prose but omits the marker).
DETECTOR_MODEL = "claude-haiku-4-5-20251001"
MIN_TURNS_BEFORE_COMPLETION = 6

SOFT_FACT_FIELDS = [
    "future_vision_statement", "personal_enough_statement", "top_five_values",
    "family_impact_summary", "money_story_summary", "behavioural_friction_profile",
    "health_wealth_happiness_scorecard", "legacy_statement",
]


@dataclass
class ConversationResponse:
    message: str
    stage: str
    stage_complete: bool
    session_complete: bool
    requests_contact: bool


def _get_stage(name: str) -> dict:
    stages = {s["name"]: s for s in get_stages()}
    if name not in stages:
        raise ValueError(f"Unknown stage: {name}")
    return stages[name]


def _next_stage(current: str) -> str | None:
    idx = STAGE_ORDER.index(current)
    if idx + 1 < len(STAGE_ORDER):
        return STAGE_ORDER[idx + 1]
    return None


def _build_system_prompt(current_stage_name: str) -> str:
    prompt_config = get_prompt("conversation")
    stage = _get_stage(current_stage_name)
    stages_overview = "\n".join(
        f"- {s['name']}: {s['titan']} — {s['output_name']}" for s in get_stages()
    )

    return f"""{prompt_config['system_prompt']}

CURRENT STAGE: {stage['name']} ({stage['titan']})

Stage framing (read this naturally as you enter the stage, don't quote it verbatim):
{stage['framing']}

Questions to explore in this stage:
{chr(10).join(f'- {q}' for q in stage['questions'])}

What this stage produces: {stage['output_name']}

All five stages (for context):
{stages_overview}

{prompt_config.get('stage_transition_instruction', '')}

{prompt_config.get('contact_request_instruction', '') if stage.get('requests_contact') else ''}
"""


def _load_history(conn: sqlite3.Connection, session_id: str) -> list[dict]:
    row = conn.execute(
        "SELECT conversation_history FROM titan_sessions WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    if not row or not row["conversation_history"]:
        return []
    return json.loads(row["conversation_history"])


def _save_history(conn: sqlite3.Connection, session_id: str, history: list[dict]) -> None:
    conn.execute(
        "UPDATE titan_sessions SET conversation_history = ?, updated_at = datetime('now') "
        "WHERE session_id = ?",
        (json.dumps(history), session_id)
    )
    conn.commit()


def _format_transcript(history: list[dict]) -> str:
    """Render the conversation history as a plain transcript for monitor passes."""
    lines = []
    for m in history:
        who = "CLIENT" if m.get("role") == "user" else "GUIDE"
        lines.append(f"{who}: {m.get('content', '').strip()}")
    return "\n\n".join(lines)


def _strip_signals(text: str) -> str:
    """Remove any stray control markers so they never reach the client."""
    return text.replace("[STAGE_COMPLETE]", "").replace("[DISCOVERY_COMPLETE]", "").strip()


def _detect_completion(history: list[dict]) -> bool:
    """Decide whether the discovery has genuinely concluded.

    A separate, cheap monitor pass (not part of the conversation) — far more reliable
    than asking the chat model to emit an inline token. Returns False on any error so
    a transient failure never falsely ends a session.
    """
    instruction = get_prompt("conversation").get("completion_detector_prompt", "")
    if not instruction:
        return False
    transcript = _format_transcript(history)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        resp = client.messages.create(
            model=DETECTOR_MODEL,
            max_tokens=150,
            messages=[{"role": "user", "content": f"{instruction}\n\nTRANSCRIPT:\n{transcript}"}],
        )
        match = re.search(r'\{.*\}', resp.content[0].text, re.DOTALL)
        if not match:
            return False
        return bool(json.loads(match.group(0)).get("discovery_complete"))
    except Exception as e:
        logger.warning("Completion detector failed: %s", e)
        return False


def _extract_all_soft_facts(history: list[dict]) -> dict:
    """One pass over the full transcript to populate all eight soft-fact fields.

    Replaces the old per-stage JSON-block mechanism (which depended on the chat model
    emitting structured blocks mid-conversation and never fired in practice).
    """
    instruction = get_prompt("conversation").get("extraction_prompt", "")
    if not instruction:
        return {}
    transcript = _format_transcript(history)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": f"{instruction}\n\nTRANSCRIPT:\n{transcript}"}],
        )
        text = resp.content[0].text
        match = (re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
                 or re.search(r'(\{.*\})', text, re.DOTALL))
        if not match:
            return {}
        data = json.loads(match.group(1))
        return {k: v for k, v in data.items() if k in SOFT_FACT_FIELDS and v}
    except Exception as e:
        logger.error("Soft-fact extraction failed: %s", e)
        return {}


def start_session(session_id: str) -> str:
    """Open the conversation for a new session with the Visionary stage intro."""
    conn = get_connection()
    try:
        prompt_config = get_prompt("conversation")
        stage = _get_stage("visionary")

        system = _build_system_prompt("visionary")
        first_message = (
            "Hello! I've just started the Titan LifeMap Discovery Session."
        )

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": first_message}],
        )
        assistant_text = response.content[0].text

        history = [
            {"role": "user", "content": first_message},
            {"role": "assistant", "content": assistant_text},
        ]
        _save_history(conn, session_id, history)
        update_session(conn, session_id, current_stage="visionary")

        return assistant_text
    finally:
        conn.close()


def send_message(session_id: str, user_message: str) -> ConversationResponse:
    """Process one user turn and return the assistant response."""
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        if session["completed"]:
            return ConversationResponse(
                message="This discovery session is already complete.",
                stage=session["current_stage"],
                stage_complete=False,
                session_complete=True,
                requests_contact=False,
            )

        current_stage_name = session["current_stage"]
        history = _load_history(conn, session_id)

        # Capture contact details whenever the client provides them. The discovery asks
        # for first name + email near the end (see conversation.yaml); this records them
        # on whichever turn they actually appear, independent of stage.
        if not session.get("email"):
            _capture_contact_if_present(conn, session_id, user_message)
            session = get_session(conn, session_id)  # reload after possible update

        history.append({"role": "user", "content": user_message})

        system = _build_system_prompt(current_stage_name)
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=history,
        )
        assistant_text = response.content[0].text

        history.append({"role": "assistant", "content": assistant_text})
        _save_history(conn, session_id, history)

        # Completion is judged by a separate monitor pass once the conversation has had
        # room to develop — not by an inline token from the chat model. On completion we
        # extract all soft facts from the full transcript in a single pass.
        session_complete = False
        user_turns = sum(1 for m in history if m.get("role") == "user")
        if user_turns >= MIN_TURNS_BEFORE_COMPLETION and _detect_completion(history):
            soft_facts = _extract_all_soft_facts(history)
            if soft_facts:
                upsert_soft_facts(conn, session_id, **soft_facts)
            update_session(conn, session_id, completed=1)
            session_complete = True
            logger.info(
                "Discovery complete for session %s (monitor); extracted %d soft-fact fields",
                session_id, len(soft_facts),
            )

        stage_config = _get_stage(current_stage_name)
        return ConversationResponse(
            message=_strip_signals(assistant_text),
            stage=current_stage_name,
            stage_complete=False,
            session_complete=session_complete,
            requests_contact=stage_config.get("requests_contact", False),
        )
    finally:
        conn.close()


def _capture_contact_if_present(
    conn: sqlite3.Connection, session_id: str, user_message: str
) -> None:
    """Best-effort email extraction from a user message at the Steward stage.

    This is a lightweight heuristic — the conversation.py logic treats contact
    capture as a natural part of the conversation, not a form. If the user typed
    an email address anywhere in their message, we record it.
    """
    # Match the full domain including multi-part TLDs (e.g. zen.co.uk, not just zen.co).
    email_match = re.search(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', user_message, re.IGNORECASE)
    if not email_match:
        return

    email = email_match.group(0)
    first_name = _extract_first_name(user_message, email)
    update_session(conn, session_id, email=email, first_name=first_name)
    logger.info("Contact captured for session %s: %s (name=%r)", session_id, email, first_name)


# Capitalised words that are never a first name (avoids "My name is" → "My").
_NAME_STOPWORDS = {
    "My", "Me", "I", "Im", "Hi", "Hello", "Hey", "The", "Yes", "No", "Ok", "Okay",
    "It", "Its", "This", "That", "Email", "Name", "Sure", "Thanks", "Thank", "And", "So",
}


def _extract_first_name(text: str, email: str) -> str | None:
    """Best-effort first name. Prefer explicit cues; return None rather than guess wrong."""
    # Explicit introductions — require a capitalised name so "i'm ready" doesn't match.
    for pattern in (
        r"[Mm]y name(?:'s| is)?\s+([A-Z][a-z]+)",
        r"\bI(?:'m| am)\s+([A-Z][a-z]+)",
        r"[Cc]all me\s+([A-Z][a-z]+)",
        r"[Tt]his is\s+([A-Z][a-z]+)",
    ):
        m = re.search(pattern, text)
        if m and m.group(1) not in _NAME_STOPWORDS:
            return m.group(1)

    # A capitalised name sitting right next to the email ("Sarah - sarah@x.com").
    m = re.search(r"\b([A-Z][a-z]{1,20})\b[\s,\-–]*" + re.escape(email), text)
    if m and m.group(1) not in _NAME_STOPWORDS:
        return m.group(1)

    # Fall back to an alphabetic email local part that looks like a name.
    local = email.split("@")[0]
    if local.isalpha() and 2 <= len(local) <= 20:
        return local.capitalize()
    return None
