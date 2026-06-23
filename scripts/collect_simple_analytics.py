"""
DataOS - Simple Analytics Collector

Pulls daily visitor/pageview stats from Simple Analytics' free public JSON
endpoint. Requires the site's stats to be set to "public" (Settings ->
Change visibility) - no API key needed, no paid plan required.

Supports multiple sites via SIMPLE_ANALYTICS_SITE_<NAME> entries in .env,
each holding the bare hostname (e.g. targeted.support).

Tables created: simple_analytics_daily
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_env_prefixed  # noqa: E402

try:
    import requests
except ImportError:
    raise ImportError("Missing 'requests' - run: pip install requests")

API_URL_TEMPLATE = "https://simpleanalytics.com/{hostname}.json"


def collect():
    """Fetch the full available history (~30 days) for every connected Simple Analytics site.

    Each run re-fetches and upserts the whole window, so historical days stay
    correct (e.g. if Simple Analytics back-fills bot-filtered traffic) and a
    missed collection day doesn't leave a permanent gap.
    """
    sites = get_env_prefixed("SIMPLE_ANALYTICS_SITE_")
    if not sites:
        return {
            "source": "simple_analytics", "status": "skipped",
            "reason": "No SIMPLE_ANALYTICS_SITE_* entries set in .env"
        }

    results = {}
    try:
        for site_name, hostname in sites.items():
            resp = requests.get(
                API_URL_TEMPLATE.format(hostname=hostname),
                params={"version": 6, "fields": "pageviews,visitors,histogram", "info": "false"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                return {"source": "simple_analytics", "status": "error",
                        "reason": f"{hostname}: API returned ok=false"}

            histogram = data.get("histogram", [])
            # Drop the final entry - it's the current (incomplete) day
            history = histogram[:-1] if len(histogram) > 1 else histogram

            results[site_name] = {"hostname": hostname, "history": history}
    except Exception as e:
        return {"source": "simple_analytics", "status": "error", "reason": str(e)}

    return {"source": "simple_analytics", "status": "success", "data": results}


def write(conn, result, date):
    """Write Simple Analytics daily history to database. Returns records written."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS simple_analytics_daily (
            date TEXT NOT NULL,
            site TEXT NOT NULL,
            hostname TEXT,
            visitors INTEGER,
            pageviews INTEGER,
            collected_at TEXT,
            PRIMARY KEY (date, site)
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0
    for site_name, stats in result["data"].items():
        for day in stats["history"]:
            conn.execute(
                "INSERT OR REPLACE INTO simple_analytics_daily "
                "(date, site, hostname, visitors, pageviews, collected_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (day["date"], site_name, stats["hostname"], day["visitors"],
                 day["pageviews"], collected_at)
            )
            records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        for site, stats in result["data"].items():
            print(f"{site} ({stats['hostname']}): {len(stats['history'])} days of history")
            for day in stats["history"][-7:]:
                print(f"  {day['date']}: {day['visitors']} visitors, {day['pageviews']} pageviews")
    else:
        print(f"{result['status']}: {result.get('reason', '')}")
