"""
DataOS - Google Analytics 4 Collector

Fetches daily website traffic for every connected GA4 property.
Supports multiple sites via GA4_PROPERTY_ID_* environment variables -
each suffix becomes the "site" label in the database.

Requires:
    GOOGLE_SERVICE_ACCOUNT_JSON - path to the service account JSON file
    GA4_PROPERTY_ID_<SITE> - one per site, e.g. GA4_PROPERTY_ID_SUSTAIN_MOMENTUM

Tables created: ga4_daily
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import get_env_prefixed, get_google_credentials_path  # noqa: E402

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Metric, RunReportRequest
    from google.oauth2.service_account import Credentials
except ImportError:
    raise ImportError(
        "Missing Google Analytics packages - run: "
        "pip install google-analytics-data google-auth"
    )

METRICS = ["sessions", "totalUsers", "newUsers", "screenPageViews", "bounceRate"]


def collect():
    """Fetch yesterday's traffic for every connected GA4 property.

    Note: a date-dimensioned multi-day query was tried for instant history
    backfill, but this GA4 property's regional data-residency settings reject
    that request shape (FAILED_PRECONDITION). Single-day, no-dimension
    queries work reliably, so history builds up naturally via daily runs."""
    creds_path = get_google_credentials_path()
    if not creds_path:
        return {
            "source": "ga4", "status": "skipped",
            "reason": "Missing GOOGLE_SERVICE_ACCOUNT_JSON or file not found"
        }

    properties = get_env_prefixed("GA4_PROPERTY_ID_")
    if not properties:
        return {
            "source": "ga4", "status": "skipped",
            "reason": "No GA4_PROPERTY_ID_* entries set in .env"
        }

    try:
        creds = Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
        client = BetaAnalyticsDataClient(credentials=creds)

        sites = {}
        for site_name, property_id in properties.items():
            resp = client.run_report(RunReportRequest(
                property=f"properties/{property_id}",
                date_ranges=[DateRange(start_date="yesterday", end_date="yesterday")],
                metrics=[Metric(name=m) for m in METRICS],
            ))
            yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
            if resp.rows:
                values = resp.rows[0].metric_values
                day = {
                    "date": yesterday,
                    "sessions": int(float(values[0].value)),
                    "users": int(float(values[1].value)),
                    "new_users": int(float(values[2].value)),
                    "page_views": int(float(values[3].value)),
                    "bounce_rate": float(values[4].value) * 100,
                }
            else:
                day = {"date": yesterday, "sessions": 0, "users": 0, "new_users": 0,
                       "page_views": 0, "bounce_rate": 0.0}
            sites[site_name] = [day]

        return {"source": "ga4", "status": "success", "data": sites}
    except Exception as e:
        return {"source": "ga4", "status": "error", "reason": str(e)}


def write(conn, result, date):
    """Write GA4 daily snapshots to database. Returns records written."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ga4_daily (
            date TEXT NOT NULL,
            site TEXT NOT NULL,
            sessions INTEGER,
            users INTEGER,
            new_users INTEGER,
            page_views INTEGER,
            bounce_rate REAL,
            collected_at TEXT,
            PRIMARY KEY (date, site)
        )
    """)

    if result.get("status") != "success":
        conn.commit()
        return 0

    collected_at = datetime.now(timezone.utc).isoformat()
    records = 0

    for site_name, history in result["data"].items():
        for day in history:
            conn.execute(
                "INSERT OR REPLACE INTO ga4_daily "
                "(date, site, sessions, users, new_users, page_views, bounce_rate, collected_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (day["date"], site_name, day["sessions"], day["users"], day["new_users"],
                 day["page_views"], day["bounce_rate"], collected_at)
            )
            records += 1

    conn.commit()
    return records


if __name__ == "__main__":
    result = collect()
    if result["status"] == "success":
        for site, history in result["data"].items():
            print(f"{site}: {len(history)} days of history")
            for day in history[-7:]:
                print(f"  {day['date']}: {day['sessions']} sessions, {day['users']} users, "
                      f"{day['page_views']} page views")
    else:
        print(f"{result['status']}: {result.get('reason', '')}")
