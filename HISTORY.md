# Workspace History

> Chronological log of all work done in this workspace. Updated every session.
> Most recent entries at the top. Each entry has a date, title, and bullet points.
>
> **How it works:** When you run `/commit` after meaningful work, Claude adds an entry here
> automatically. You don't need to write this file yourself.

---

## 2026-06-23

### Titan LifeMap v1 — Full Implementation (Steps 1-12)

**What was built:**
- Config-driven AI discovery engine: five stages (Visionary → Sage → Builder → Steward → Guardian), all content in YAML under `apps/titan_lifemap/config/` — questions, scoring weights, report section instructions, Claude system prompts
- FastAPI backend (`apps/titan_lifemap/main.py`): `/session/start`, `/session/{id}/message`, `/session/{id}/status`, `/session/{id}/complete`
- Conversation engine (`conversation.py`): Anthropic messages API, stage sequencing, contact capture at Steward stage, conversation history persisted in DB
- Analysis engine (`analysis.py`): post-session Claude scoring pass — Clarity Score, Momentum Plan, Behavioural Friction Profile; all weights from scoring_rules.yaml
- Four report generators (`reports/`): consumer, coaching, adviser, Internal AI Profile — Jinja2 HTML → WeasyPrint PDF
- Internal AI Profile: auto-generated on every completion, stored in `titan_internal_profiles`, NO API endpoint, never client-visible. "The client sees the report. GAIA sees the person."
- Routing layer (`routing.py`): lead storage, Google Workspace SMTP, Make.com webhook
- Six Titan LifeMap tables in shared `data/data.db`: sessions, soft_facts, hard_facts, scores, internal_profiles, leads
- IP boundary documented (`context/titan-lifemap/ip-boundary.md`): all questions are original to this project
- Full documentation: architecture doc, config schema guide, VPS deployment guide
- CLAUDE.md and docs/_index.md updated

**Architecture principle:** Content is YAML, code is structure. Changing behaviour = changing config, not Python.

**VPS deployment:** `outputs/titan-lifemap-vps-deployment.md` — systemd service `titan-lifemap`, nginx reverse proxy, Certbot SSL for api.sustain-momentum.com

---

## 2026-06-21

### Initial Setup
- Initialized workspace with ContextOS and InfraOS
- Set up Git tracking and connected to GitHub
- Created documentation system (docs/ folder with routing index)
- Installed /commit command for structured commits with auto-documentation

### InfraOS Test
- Testing the /commit workflow

### DataOS
- Built SQLite data warehouse (data/data.db) with daily collection pipeline
- Connected FX rates (zero-auth starter) and Google Analytics (sustain-momentum.com)
- key-metrics.md auto-generates each run, loaded by /prime
- Daily 6 AM Windows Task Scheduler job runs collection automatically
- Fixed local network TLS interception issue via pip-system-certs + combined cert bundle

### IntelOS
- Added Fireflies.ai meeting collector, classified by venture (GOIA/SUSTAIN_MOMENTUM/GAIA/NED/GENERAL)
- Folded into the existing DataOS pipeline — runs on the same 6 AM schedule, no separate cron
- Recent Meetings section added to key-metrics.md

### CommandOS
- Built Telegram AI assistant ("Command Centre" group) with full workspace access
- Customized worker.py system prompt for Patrick's three ventures and NED work
- PDF (WeasyPrint) and chart (matplotlib) generation enabled, voice notes skipped
- Deployed to Hostinger VPS (Ubuntu 24.04) as a systemd service — runs 24/7, auto-restarts
- Resolved: root-user restriction on --dangerously-skip-permissions (created non-root `patrick` user)
- Resolved: invalid Anthropic API key (was copied from masked key-list view, not the one-time reveal)
- Deployment guide saved to outputs/commandos-vps-deployment.md
