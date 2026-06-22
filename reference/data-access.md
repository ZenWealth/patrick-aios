# Data Access Reference

> How to query the DataOS database directly. Loaded on demand when deeper
> analysis is needed beyond what's in `context/group/key-metrics.md`.

---

## SQLite Data Warehouse

**Location:** `data/data.db`

**Connect from Python:**
```python
import sqlite3
conn = sqlite3.connect("data/data.db")
conn.row_factory = sqlite3.Row
```

Claude can run SQL directly in sessions using this pattern — no need to go through the collectors.

---

## Connected Data Sources

| Source | Table | Collection Script | What It Tracks |
|---|---|---|---|
| FX Rates (Frankfurter API) | `fx_rates` | `scripts/collect_fx_rates.py` | Daily exchange rates, GBP base, vs AUD/CAD/EUR/USD |
| Google Analytics (GA4) | `ga4_daily` | `scripts/collect_ga4.py` | Daily website traffic per site — sessions, users, page views, bounce rate |
| Fireflies.ai | `meetings` | `scripts/collect_fireflies.py` | Meeting transcripts, summaries, action items — classified by venture (GOIA/SUSTAIN_MOMENTUM/GAIA/NED/GENERAL) via keyword matching |

**Not yet connected:** GOIA (goiatechnologies.com) and Targeted Support (targeted.support) don't have GA4 installed yet. Once they do, add `GA4_PROPERTY_ID_GOIA` and `GA4_PROPERTY_ID_TARGETED_SUPPORT` to `.env` — the collector auto-discovers any `GA4_PROPERTY_ID_*` entry, no code changes needed.

---

## Table Schemas

### fx_rates
| Column | Type | Description |
|---|---|---|
| date | TEXT | Rate date (YYYY-MM-DD) |
| currency | TEXT | Currency code (AUD, CAD, EUR, USD) |
| rate | REAL | Exchange rate from GBP |
| base | TEXT | Base currency, always 'GBP' |
| collected_at | TEXT | UTC timestamp of collection |

Primary key: (date, currency)

### ga4_daily
| Column | Type | Description |
|---|---|---|
| date | TEXT | Snapshot date (YYYY-MM-DD) |
| site | TEXT | Site label (e.g. SUSTAIN_MOMENTUM) — derived from the `GA4_PROPERTY_ID_<SITE>` env var suffix |
| sessions | INTEGER | Total sessions that day |
| users | INTEGER | Total users that day |
| new_users | INTEGER | New users that day |
| page_views | INTEGER | Total page views that day |
| bounce_rate | REAL | Bounce rate as a percentage |
| collected_at | TEXT | UTC timestamp of collection |

Primary key: (date, site)

### meetings
| Column | Type | Description |
|---|---|---|
| meeting_id | TEXT | Unique ID, prefixed `fireflies_` |
| title | TEXT | Meeting title |
| date | TEXT | Meeting date (YYYY-MM-DD) |
| start_time | TEXT | Start time (HH:MM:SS UTC) |
| duration_minutes | INTEGER | Length of meeting |
| participants | TEXT | JSON array of `{name, email}` |
| transcript_text | TEXT | Full transcript, `[Speaker] text` per line |
| summary | TEXT | Fireflies-generated summary |
| action_items_raw | TEXT | JSON array of action items, if any |
| venture | TEXT | GOIA / SUSTAIN_MOMENTUM / GAIA / NED / GENERAL — classified by keyword match against title + participants |
| external_url | TEXT | Link to the Fireflies recording |
| collected_at | TEXT | UTC timestamp of collection |

Primary key: `meeting_id`. Collection looks back 7 days each run (`LOOKBACK_DAYS` in `collect_fireflies.py`) — safe to run daily without gaps.

**Multiple Fireflies accounts:** the collector reads `FIREFLIES_API_KEY` (Patrick's own account) plus any `FIREFLIES_API_KEY_<NAME>` entries (e.g. `FIREFLIES_API_KEY_GERARD`), merging and de-duplicating by transcript ID. Useful when a meeting is organized and recorded on someone else's Fireflies account — like the weekly GOIA call, which Gerard organizes.

**Venture classification keywords** (edit `VENTURE_KEYWORDS` in `scripts/collect_fireflies.py` to adjust):
- GOIA: goia, gerard, ouattara, boardsignal, complyport, cyber governance
- SUSTAIN_MOMENTUM: sustain momentum, targeted support, agbr, clarity call/review
- GAIA: gaia
- NED: ned, non-exec, board advisory, nurole, criticaleye, headhunter
- Anything else falls into GENERAL

### collection_log
Tracks every collection run (success/skipped/error) across all sources. Columns: `id`, `collected_at`, `source`, `status`, `reason`, `records_written`.

---

## Common Queries

**Latest snapshot per source:**
```sql
SELECT * FROM ga4_daily WHERE date = (SELECT MAX(date) FROM ga4_daily);
SELECT * FROM fx_rates WHERE date = (SELECT MAX(date) FROM fx_rates);
```

**Website traffic trend, last 30 days:**
```sql
SELECT date, site, sessions, users
FROM ga4_daily
WHERE date >= date('now', '-30 days')
ORDER BY date;
```

**Month-over-month traffic comparison:**
```sql
SELECT
  strftime('%Y-%m', date) AS month,
  site,
  SUM(sessions) AS total_sessions,
  SUM(page_views) AS total_page_views
FROM ga4_daily
GROUP BY month, site
ORDER BY month DESC;
```

**GBP to EUR/USD trend:**
```sql
SELECT date, currency, rate
FROM fx_rates
WHERE currency IN ('EUR', 'USD')
ORDER BY date DESC
LIMIT 30;
```

**Check collection health (any failures?):**
```sql
SELECT * FROM collection_log
WHERE status != 'success'
ORDER BY collected_at DESC
LIMIT 20;
```

**Find a meeting by keyword (title or transcript):**
```sql
SELECT date, title, venture, summary FROM meetings
WHERE title LIKE '%ComplyPort%' OR transcript_text LIKE '%ComplyPort%'
ORDER BY date DESC;
```

**Meetings by venture, last 30 days:**
```sql
SELECT venture, COUNT(*) AS meeting_count, SUM(duration_minutes) AS total_minutes
FROM meetings
WHERE date >= date('now', '-30 days')
GROUP BY venture;
```

---

## Running Collection Manually

```bash
# Windows (from workspace root)
.venv\Scripts\python.exe scripts\collect.py              # all sources
.venv\Scripts\python.exe scripts\collect.py --sources ga4 # one source only
.venv\Scripts\python.exe scripts\generate_metrics.py       # regenerate key-metrics.md only
```

Logs from automated runs live at `data/collect.log` once the scheduled task is set up.

---

## A Note on Network/SSL

This machine sits behind a network (antivirus or corporate-style) that intercepts HTTPS with its own root certificate. Two things were configured to make data collection work:

1. **`pip-system-certs`** is installed in the venv — patches Python's `requests`/`urllib3`-based calls to trust the Windows certificate store.
2. **`credentials/combined-roots.pem`** — a combined bundle of certifi's public CAs plus Windows' trusted roots, referenced via `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` in `scripts/config.py`. This is needed because gRPC-based clients (Google Analytics, and any future Google Cloud API) don't use the Windows certificate store automatically.

If a *new* collector using gRPC-based libraries fails with `CERTIFICATE_VERIFY_FAILED`, this is already handled — `config.py` sets the env var as long as the collector imports it. If a *new* collector uses plain `requests`, it should work automatically via `pip-system-certs`.
