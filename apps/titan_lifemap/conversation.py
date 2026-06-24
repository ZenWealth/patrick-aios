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


def _extract_soft_facts(response_text: str, stage_name: str) -> dict:
    """Attempt to extract soft-fact fields from Claude's response using stage config.

    Claude is instructed to include a JSON block with structured outputs at stage
    completion. This parser handles both clean JSON and embedded JSON in prose.
    Returns an empty dict if no structured data is found - soft facts can be
    populated retrospectively during the analysis pass.
    """
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if not json_match:
        return {}
    try:
        data = json.loads(json_match.group(1))
        stage = _get_stage(stage_name)
        allowed_fields = set(stage.get("soft_fact_outputs", []))
        return {k: v for k, v in data.items() if k in allowed_fields}
    except (json.JSONDecodeError, KeyError):
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

        # Detect contact details if we're at Steward stage and don't have them yet
        if current_stage_name == "steward" and not session.get("email"):
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

        discovery_complete = _detect_discovery_complete(assistant_text)
        stage_complete = _detect_stage_complete(assistant_text, current_stage_name)
        session_complete = False
        next_stage = _next_stage(current_stage_name)

        if discovery_complete:
            # Full discovery complete — synthesise and close regardless of stage
            soft_facts = _extract_soft_facts(assistant_text, current_stage_name)
            if soft_facts:
                upsert_soft_facts(conn, session_id, **soft_facts)
            update_session(conn, session_id, completed=1)
            session_complete = True

        elif stage_complete:
            soft_facts = _extract_soft_facts(assistant_text, current_stage_name)
            if soft_facts:
                upsert_soft_facts(conn, session_id, **soft_facts)

            if next_stage:
                update_session(conn, session_id, current_stage=next_stage)
                current_stage_name = next_stage
            else:
                update_session(conn, session_id, completed=1)
                session_complete = True

        stage_config = _get_stage(current_stage_name)
        return ConversationResponse(
            message=assistant_text,
            stage=current_stage_name,
            stage_complete=stage_complete,
            session_complete=session_complete,
            requests_contact=stage_config.get("requests_contact", False),
        )
    finally:
        conn.close()


def _detect_stage_complete(text: str, stage_name: str) -> bool:
    """Claude signals stage completion with [STAGE_COMPLETE].
    Not used when [DISCOVERY_COMPLETE] is present — that supersedes it.
    """
    return "[STAGE_COMPLETE]" in text and "[DISCOVERY_COMPLETE]" not in text


def _detect_discovery_complete(text: str) -> bool:
    """Claude signals the full discovery is complete with [DISCOVERY_COMPLETE].
    This fires after the Verbal Synthesis and Core Transition sequence,
    regardless of which stage we are in. It supersedes [STAGE_COMPLETE].
    """
    return "[DISCOVERY_COMPLETE]" in text


def _capture_contact_if_present(
    conn: sqlite3.Connection, session_id: str, user_message: str
) -> None:
    """Best-effort email extraction from a user message at the Steward stage.

    This is a lightweight heuristic — the conversation.py logic treats contact
    capture as a natural part of the conversation, not a form. If the user typed
    an email address anywhere in their message, we record it.
    """
    email_match = re.search(r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b', user_message, re.IGNORECASE)
    if not email_match:
        return

    # Extract first name: look for a name before or after the email
    email = email_match.group(0)
    name_match = re.search(r'\b([A-Z][a-z]{1,20})\b', user_message)
    first_name = name_match.group(1) if name_match else None

    update_session(conn, session_id, email=email, first_name=first_name)
    logger.info("Contact captured for session %s: %s", session_id, email)
