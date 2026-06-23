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
    """Fetch yesterday's stats for every connected Simple Analytics site."""
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
            yesterday = histogram[-2] if len(histogram) >= 2 else (histogram[-1] if histogram else None)

            results[site_name] = {
                "hostname": hostname,
                "date": yesterday["date"] if yesterday else None,
                "visitors": yesterday["visitors"] if yesterday else 0,
                "pageviews": yesterday["pageviews"] if yesterday else 0,
            }
    except Exception as e:
        return {"source": "simple_analytics", "status": "error", "reason": str(e)}

    return {"source": "simple_analytics", "status": "success", "data": results}


def write(conn, result, date):
    """Write Simple Analytics daily snapshots to database. Returns records written."""
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
        record_date = stats["date"] or date
        conn.execute(
            "INSERT OR REPLACE INTO simple_analytics_daily "
            "(date, site, hostname, visitors, pageviews, collected_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (record_date, site_name, stats["hostname"], stats["visitors"],
             stats["pageviews"], collected_at)
        )
        records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        for site, stats in result["data"].items():
            print(f"{site} ({stats['hostname']}): {stats['visitors']} visitors, "
                  f"{stats['pageviews']} pageviews on {stats['date']}")
    else:
        print(f"{result['status']}: {result.get('reason', '')}")
