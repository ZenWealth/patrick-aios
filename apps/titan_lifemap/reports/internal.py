"""
Titan LifeMap - Internal AI Profile

Generated automatically on every session completion. NEVER shown to clients.
NO API endpoint returns this. Stored only in titan_internal_profiles.

"The client sees the report. GAIA sees the person."

This module reads from titan_internal_profiles (written by analysis.py) and
renders it into a structured document for internal GAIA use. The profile is
generated during the analysis pass — this module formats the stored profile
for any internal tooling that needs to read it (future GAIA integrations).
"""

import json
import logging

from apps.titan_lifemap.db import get_connection

logger = logging.getLogger(__name__)


def get_profile(session_id: str) -> dict:
    """Retrieve the Internal AI Profile for a session.

    This function exists for internal GAIA use only. It must never be called
    from any endpoint exposed to clients or external systems.

    Returns the profile dict, or raises ValueError if not found.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT profile_json FROM titan_internal_profiles WHERE session_id = ?",
            (session_id,)
        ).fetchone()
        if not row:
            raise ValueError(f"No internal profile found for session: {session_id}")
        return json.loads(row["profile_json"])
    finally:
        conn.close()


def get_gaia_tags(session_id: str) -> list[str]:
    """Return only the GAIA memory tags from the Internal AI Profile.

    Tags are in format 'category:value' (e.g. 'friction:procrastination').
    Used by future GAIA memory layer to build context across sessions.
    """
    profile = get_profile(session_id)
    return profile.get("gaia_memory_tags", [])
