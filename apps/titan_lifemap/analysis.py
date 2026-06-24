"""
Titan LifeMap - Analysis Engine

Runs after a session is complete. Sends the full session data to Claude
with the scoring rules from scoring_rules.yaml, and gets back:
  - Titan Clarity Score (0-100)
  - Titan Momentum Plan (up to 5 actions)
  - Behavioural Friction Profile scores (6 patterns)
  - Internal AI Profile (never client-visible)

No weights or thresholds are hardcoded here. All scoring parameters come
from config/scoring_rules.yaml via config_loader.

The Internal AI Profile is stored in titan_internal_profiles and is not
returned from any client-facing endpoint. Ever.
"""

import json
import logging
import re

import anthropic

from apps.titan_lifemap.config import ANTHROPIC_API_KEY
from apps.titan_lifemap.config_loader import get_scoring_rules, get_prompt
from apps.titan_lifemap.db import (
    get_connection, get_session,
    save_scores, save_internal_profile,
)

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


def _build_session_summary(session: dict, soft_facts: dict, hard_facts: dict) -> str:
    lines = ["=== SESSION SUMMARY ==="]

    lines.append("\n-- Soft Facts --")
    field_labels = {
        "future_vision_statement": "Future Vision Statement",
        "personal_enough_statement": "Personal Enough Statement",
        "top_five_values": "Top Five Values",
        "family_impact_summary": "Family Impact Summary",
        "money_story_summary": "Money Story Summary",
        "behavioural_friction_profile": "Behavioural Friction Profile (raw)",
        "health_wealth_happiness_scorecard": "Health-Wealth-Happiness Scorecard",
        "legacy_statement": "Legacy Statement",
    }
    for field, label in field_labels.items():
        value = soft_facts.get(field)
        if value:
            lines.append(f"{label}: {value}")

    lines.append("\n-- Hard Facts (self-reported) --")
    hf_labels = {
        "income": "Income",
        "expenses": "Expenses",
        "assets": "Assets",
        "liabilities": "Liabilities",
        "existing_arrangements": "Existing Arrangements",
        "dependants": "Dependants",
    }
    has_hard_facts = False
    for field, label in hf_labels.items():
        value = hard_facts.get(field)
        if value:
            lines.append(f"{label}: {value}")
            has_hard_facts = True
    if not has_hard_facts:
        lines.append("(No financial data provided)")

    return "\n".join(lines)


def _build_prompt(session_summary: str, scoring_rules: dict, prompt_config: dict) -> str:
    rules_json = json.dumps(scoring_rules, indent=2)
    return f"""{prompt_config['system_prompt']}

SCORING RULES (apply these weights exactly — do not substitute your own):
{rules_json}

{session_summary}

{prompt_config.get('internal_profile_instruction', '')}

Return your response as two clearly separated JSON blocks:

BLOCK 1 — SCORES (for the client-facing reports and database):
```json
{{
  "clarity_score": <float 0-100>,
  "core_transition": "<short memorable phrase, e.g. 'From operator to mentor'>",
  "momentum_plan": [<up to 5 action strings>],
  "behavioural_friction_scores": {{
    "procrastination": <float 0-10>,
    "avoidance": <float 0-10>,
    "overthinking": <float 0-10>,
    "impulsiveness": <float 0-10>,
    "delegation": <float 0-10>,
    "lack_of_confidence": <float 0-10>
  }},
  "behavioural_friction_insights": {{
    "procrastination": "<one insight sentence>",
    "avoidance": "<one insight sentence>",
    "overthinking": "<one insight sentence>",
    "impulsiveness": "<one insight sentence>",
    "delegation": "<one insight sentence>",
    "lack_of_confidence": "<one insight sentence>"
  }},
  "friction_diagnosis": {{
    "primary_friction": {{"name": "<named pattern>", "how_it_shows_up": "<1-2 sentences>"}},
    "secondary_frictions": [{{"name": "<named>", "note": "<short note>"}}],
    "cost": "<what these frictions concretely cost them>",
    "behavioural_shift": "From <old behaviour> to <new behaviour>",
    "holding_you_back": "<one sentence answering 'what is actually holding me back?'>"
  }}
}}
```

BLOCK 2 — INTERNAL AI PROFILE (never shown to client):
```json
{{
  "psychological_summary": "<text>",
  "core_tensions": ["<tension 1>", "<tension 2>", ...],
  "what_they_need": "<text>",
  "gaps_and_inconsistencies": ["<gap 1>", ...],
  "behavioural_friction_deep": "<text>",
  "adviser_briefing": "<text>",
  "gaia_memory_tags": ["category:value", ...]
}}
```
"""


def _parse_scores(response_text: str) -> dict:
    blocks = re.findall(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if not blocks:
        raise ValueError("No JSON blocks found in analysis response")
    return json.loads(blocks[0])


def _parse_internal_profile(response_text: str) -> dict:
    blocks = re.findall(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if len(blocks) < 2:
        # Return a minimal profile if Claude didn't produce the second block
        logger.warning("Internal AI Profile block missing from analysis response")
        return {"note": "Internal profile not generated — analysis response had only one JSON block"}
    return json.loads(blocks[1])


def run_analysis(session_id: str) -> dict:
    """Run the post-session analysis for a completed session.

    Returns the scores dict (clarity_score, momentum_plan, behavioural_friction_scores).
    The Internal AI Profile is stored but never returned from this function.
    """
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        if not session["completed"]:
            raise ValueError(f"Session {session_id} is not yet complete")

        soft_row = conn.execute(
            "SELECT * FROM titan_soft_facts WHERE session_id = ?", (session_id,)
        ).fetchone()
        hard_row = conn.execute(
            "SELECT * FROM titan_hard_facts WHERE session_id = ?", (session_id,)
        ).fetchone()

        soft_facts = dict(soft_row) if soft_row else {}
        hard_facts = dict(hard_row) if hard_row else {}

        session_summary = _build_session_summary(session, soft_facts, hard_facts)
        scoring_rules = get_scoring_rules()
        prompt_config = get_prompt("analysis")

        prompt = _build_prompt(session_summary, scoring_rules, prompt_config)

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text

        scores = _parse_scores(response_text)
        internal_profile = _parse_internal_profile(response_text)

        save_scores(
            conn,
            session_id,
            clarity_score=float(scores["clarity_score"]),
            momentum_plan=scores["momentum_plan"],
            behavioural_friction_scores=scores["behavioural_friction_scores"],
            core_transition=scores.get("core_transition"),
            behavioural_friction_insights=scores.get("behavioural_friction_insights"),
            friction_diagnosis=scores.get("friction_diagnosis"),
        )

        # Store Internal AI Profile — no endpoint exposes this
        save_internal_profile(conn, session_id, internal_profile)

        diag = scores.get("friction_diagnosis") or {}
        primary = (diag.get("primary_friction") or {}).get("name")
        logger.info(
            "Analysis complete for session %s: clarity_score=%.1f core_transition=%r primary_friction=%r",
            session_id, scores["clarity_score"], scores.get("core_transition"), primary
        )

        return {
            "clarity_score": scores["clarity_score"],
            "core_transition": scores.get("core_transition"),
            "momentum_plan": scores["momentum_plan"],
            "behavioural_friction_scores": scores["behavioural_friction_scores"],
            "friction_diagnosis": scores.get("friction_diagnosis"),
        }

    finally:
        conn.close()
