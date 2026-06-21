"""
DataOS/IntelOS - Fireflies.ai Meeting Collector

Pulls meeting transcripts from Fireflies and classifies each one by venture
(GOIA, Sustain Momentum, GAIA, NED, or general) using keyword matching
against the meeting title and participant names/emails.

Requires:
    FIREFLIES_API_KEY - from app.fireflies.ai/integrations

Tables created: meetings
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_env  # noqa: E402

try:
    import requests
except ImportError:
    raise ImportError("Missing 'requests' - run: pip install requests")

FIREFLIES_ENDPOINT = "https://api.fireflies.ai/graphql"
LOOKBACK_DAYS = 7

TRANSCRIPTS_QUERY = """
query GetTranscripts($fromDate: DateTime, $limit: Int, $skip: Int) {
    transcripts(fromDate: $fromDate, limit: $limit, skip: $skip) {
        id
        title
        date
        duration
        meeting_attendees {
            displayName
            email
        }
        sentences {
            text
            speaker_name
        }
        summary {
            action_items
            short_summary
            overview
        }
    }
}
"""

# Venture classification - keyword matching against title + participant text.
# Order matters: first match wins.
VENTURE_KEYWORDS = {
    "GOIA": ["goia", "gerard", "ouattara", "boardsignal", "complyport", "cyber governance"],
    "SUSTAIN_MOMENTUM": ["sustain momentum", "targeted support", "targeted.support",
                         "agbr", "clarity call", "clarity review"],
    "GAIA": ["gaia"],
    "NED": ["ned ", "non-exec", "non exec", "board advisory", "nurole",
            "criticaleye", "headhunter"],
}


def _classify_venture(title, participants_text):
    haystack = f"{title} {participants_text}".lower()
    for venture, keywords in VENTURE_KEYWORDS.items():
        for kw in keywords:
            if kw in haystack:
                return venture
    return "GENERAL"


def _build_transcript_text(sentences):
    lines = []
    for s in sentences:
        speaker = s.get("speaker_name", "Unknown")
        text = (s.get("text") or "").strip()
        if text:
            lines.append(f"[{speaker}] {text}")
    return "\n".join(lines)


def _build_participants(attendees):
    participants = []
    for a in attendees:
        p = {}
        if a.get("displayName"):
            p["name"] = a["displayName"]
        if a.get("email"):
            p["email"] = a["email"]
        if p:
            participants.append(p)
    return participants


def collect():
    """Collect Fireflies transcripts from the last LOOKBACK_DAYS days."""
    api_key = get_env("FIREFLIES_API_KEY")
    if not api_key:
        return {
            "source": "fireflies", "status": "skipped",
            "reason": "Missing FIREFLIES_API_KEY in .env"
        }

    since_dt = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    since_date = since_dt.strftime("%Y-%m-%dT00:00:00Z")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    all_transcripts = []
    skip = 0
    limit = 50

    try:
        while True:
            variables = {"fromDate": since_date, "limit": limit, "skip": skip}
            resp = requests.post(
                FIREFLIES_ENDPOINT, headers=headers,
                json={"query": TRANSCRIPTS_QUERY, "variables": variables},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                return {"source": "fireflies", "status": "error",
                        "reason": data["errors"][0].get("message", "Unknown error")}

            transcripts = data.get("data", {}).get("transcripts", [])
            if not transcripts:
                break
            all_transcripts.extend(transcripts)
            if len(transcripts) < limit:
                break
            skip += limit
    except Exception as e:
        return {"source": "fireflies", "status": "error", "reason": str(e)}

    meetings = []
    for t in all_transcripts:
        transcript_id = t.get("id")
        if not transcript_id:
            continue

        sentences = t.get("sentences") or []
        attendees = t.get("meeting_attendees") or []
        summary_data = t.get("summary") or {}
        participants = _build_participants(attendees)
        participants_text = " ".join(
            f"{p.get('name', '')} {p.get('email', '')}" for p in participants
        )

        title = t.get("title", "Untitled Meeting")
        transcript_text = _build_transcript_text(sentences)

        summary_parts = []
        if summary_data.get("overview"):
            summary_parts.append(summary_data["overview"])
        if summary_data.get("short_summary"):
            summary_parts.append(summary_data["short_summary"])
        summary = "\n\n".join(summary_parts)

        action_items = summary_data.get("action_items")
        action_items_raw = json.dumps(action_items) if action_items else None

        meeting_date_raw = t.get("date", "")
        start_time = None
        if meeting_date_raw:
            try:
                dt = datetime.fromtimestamp(int(meeting_date_raw) / 1000, tz=timezone.utc)
                date_str = dt.strftime("%Y-%m-%d")
                start_time = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError, OSError):
                date_str = str(meeting_date_raw)[:10]
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        duration = t.get("duration")
        duration_minutes = round(float(duration) / 60) if duration is not None else None

        venture = _classify_venture(title, participants_text)

        meetings.append({
            "meeting_id": f"fireflies_{transcript_id}",
            "title": title,
            "date": date_str,
            "start_time": start_time,
            "duration_minutes": duration_minutes,
            "participants": json.dumps(participants),
            "transcript_text": transcript_text,
            "summary": summary,
            "action_items_raw": action_items_raw,
            "venture": venture,
            "external_url": f"https://app.fireflies.ai/view/{transcript_id}",
        })

    return {"source": "fireflies", "status": "success", "data": meetings}


def write(conn, result, date):
    """Write meeting records to database. Returns count written."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            meeting_id TEXT PRIMARY KEY,
            title TEXT,
            date TEXT NOT NULL,
            start_time TEXT,
            duration_minutes INTEGER,
            participants TEXT,
            transcript_text TEXT,
            summary TEXT,
            action_items_raw TEXT,
            venture TEXT,
            external_url TEXT,
            collected_at TEXT
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0
    for m in result["data"]:
        conn.execute(
            "INSERT OR REPLACE INTO meetings "
            "(meeting_id, title, date, start_time, duration_minutes, participants, "
            "transcript_text, summary, action_items_raw, venture, external_url, collected_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (m["meeting_id"], m["title"], m["date"], m["start_time"], m["duration_minutes"],
             m["participants"], m["transcript_text"], m["summary"], m["action_items_raw"],
             m["venture"], m["external_url"], collected_at)
        )
        records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        for m in result["data"]:
            print(f"{m['date']} [{m['venture']}] {m['title']} ({m['duration_minutes']} min)")
        print(f"\nTotal: {len(result['data'])} meetings")
    else:
        print(f"{result['status']}: {result.get('reason', '')}")
