# Plan: Titan LifeMap — AIOS Discovery & Planning Engine

**Created:** 2026-06-23
**Status:** Draft
**Request:** Build a structured, modular conversational discovery system (Titan LifeMap™) branded under Patrick's trademarked Titan Mindset framework, replacing the original Chatbase-based fact-find idea, and serving as the first concrete expression of the GAIA proposition.

---

## Overview

### What This Plan Accomplishes

This plan builds **Titan LifeMap™** — a multi-stage, AI-guided discovery conversation that helps consumers gain clarity on their life and finances before any regulated advice is given. It replaces the "ask about pensions and ISAs first" model of a traditional fact-find with a sequence rooted in Patrick's own trademarked Seven Titans framework (Visionary → Sage → Builder → Steward → Guardian), captures both soft facts (values, life vision, behavioural patterns) and hard facts (income, assets, goals), and produces one of three tailored outputs depending on where the user is routed: a self-guided consumer report, a Sustain Momentum coaching baseline, or an adviser-ready referral pack.

### Why This Matters

This is not a standalone feature — it is the first buildable expression of **GAIA**, which has sat at "concept stage" with no defined product since this workspace was set up. It also directly answers the "Develop D2C financial guidance process" project already tracked in `gtd/projects.md` under Sustain Momentum. Crucially, it resolves Patrick's repeated IP concern (first raised with Covey/ActionCoach, now with CEG Worldwide's Total Client Profile) by building entirely original content under his own trademark rather than adapting anyone else's proprietary methodology — the architecture itself (Visionary/Sage-first, financial-data-last) is what makes this legally and philosophically distinct from CEG's Discovery process, not just different wording.

---

## Current State

### Relevant Existing Structure

- **`context/gaia/overview.md` / `strategy.md`** — describes GAIA as "concept stage," no product, open questions about primary user and use case. This plan answers several of those open questions directly.
- **`context/sustain-momentum/overview.md` / `strategy.md`** — describes the consumer-facing "Clarity Check / Personal Clarity Review / Clarity Call" services and the B2B AGBR/TS consulting work. Titan LifeMap sits upstream of (and eventually replaces/powers) the Clarity Check.
- **`gtd/projects.md`** — has an open project "Develop D2C financial guidance process" under Sustain Momentum with a `@think` next action. This plan supersedes that next action with a concrete build plan.
- **`apps/command/`** — existing CommandOS Telegram bot, running on the same Hostinger VPS this plan will use. Contains reusable patterns: `agent_sdk.py` (Claude Agent SDK wrapper), `session_manager.py` (persistent session storage), `config.py` (env loading), `worker.py` (system prompts), `logger.py`. These patterns are directly reusable for Titan LifeMap's conversation engine — same underlying SDK, different orchestration target (web API, not Telegram).
- **`data/data.db`** — existing SQLite warehouse (DataOS), with `collect_*.py` / `db.py` patterns for table creation and querying. Titan LifeMap's profile data will live in this same database.
- **`scripts/config.py`** — existing `.env` loader with `get_env` / `get_env_prefixed` helpers, plus the cert-fix pattern for this network's TLS interception. Reusable as-is.
- **VPS infrastructure** — Hostinger VPS (Ubuntu 24.04), already running CommandOS as a systemd service under user `patrick`, Python 3.13 venv, Claude Code CLI installed. Titan LifeMap's backend API will run here as a second systemd service.
- **Website** — sustain-momentum.com on WordPress (10Web), with Chatbase, Vapi, Make.com, Google Sheets/Docs already in use. Titan LifeMap embeds as a standalone conversational experience on this site, separate from Chatbase.

### Gaps or Problems Being Addressed

- GAIA has no defined product — this plan gives it one.
- The original "Chatbase as fact-find" idea is being replaced with a system Patrick fully controls (memory, scoring, profiling, report generation) — Chatbase cannot do this.
- No existing mechanism captures soft facts (values, behavioural patterns, life vision) anywhere in the current Sustain Momentum service stack — only the AGBR/TS consulting and basic Clarity services exist today.
- No adviser-referral or coaching-baseline output exists today — referrals and coaching engagements currently start from nothing structured.

---

## Proposed Changes

### Summary of Changes

- Build a new **Titan LifeMap backend** (FastAPI-based, Python) deployed on the existing VPS, alongside CommandOS, as Phase 1-2 of this plan (data model + conversation engine).
- Build the **analysis layer** (Phase 3): behavioural profiling, friction identification, Clarity Score and Momentum Plan scoring, using Claude via the Agent SDK.
- Build **three report generators** (Phase 4): Consumer Report, Sustain Momentum Coaching Report, Adviser Referral Pack — reusing the existing WeasyPrint PDF pipeline already proven in CommandOS.
- Stub out **workflow integration hooks** (Phase 5) for CRM/email/routing — implemented as extensible interfaces now, wired to real systems later once Patrick confirms which CRM/email tools he'll use.
- Document **Phase 6 (future expansion)** as a forward-looking section in context, not built now.
- Update `context/gaia/overview.md` and `strategy.md` to reflect that GAIA now has a defined first product.
- Update `gtd/projects.md` to mark progress on the "Develop D2C financial guidance process" project.
- Create a new context folder `context/titan-lifemap/` documenting the framework, the soft-fact categories, and the IP boundary (what's safe to use vs. what must stay original).

### New Files to Create

| File Path | Purpose |
|---|---|
| `context/titan-lifemap/overview.md` | Titan LifeMap product overview — Seven Titans framework, discovery sequencing, soft-fact categories, output names |
| `context/titan-lifemap/ip-boundary.md` | Explicit record of the CEG IP concern and how this design avoids it — for Patrick's own reference and for any future contributor/developer who touches this code |
| `apps/titan_lifemap/__init__.py` | Package init |
| `apps/titan_lifemap/main.py` | FastAPI app entry point — serves the conversation API |
| `apps/titan_lifemap/config.py` | Env/config loader, reusing `scripts/config.py` patterns |
| `apps/titan_lifemap/models.py` | Data model: TitanProfile, Session, SoftFact, HardFact, ScoringResult (Pydantic models) |
| `apps/titan_lifemap/db.py` | SQLite table definitions and query helpers for Titan LifeMap tables in `data/data.db` |
| `apps/titan_lifemap/stages.py` | The five discovery stages (Visionary, Sage, Builder, Steward, Guardian) — original questions per stage, written fresh (not derived from CEG) |
| `apps/titan_lifemap/conversation.py` | Conversation orchestration — stage progression, session state, completion logic, wraps Claude Agent SDK calls |
| `apps/titan_lifemap/analysis.py` | Analysis layer — behavioural friction identification, Clarity Score, Momentum Plan scoring |
| `apps/titan_lifemap/reports/consumer.py` | Consumer Report generator (Titan LifeMap Profile, Clarity Score, Momentum Plan) |
| `apps/titan_lifemap/reports/coaching.py` | Sustain Momentum Coaching Report generator (coaching baseline, accountability framework) |
| `apps/titan_lifemap/reports/adviser.py` | Adviser Referral Pack generator (profile + financial snapshot + priorities + behavioural insights) |
| `apps/titan_lifemap/reports/templates/report.css` | Shared PDF stylesheet, adapted from `apps/command/templates/report.css` |
| `apps/titan_lifemap/routing.py` | Workflow integration stubs — CRM, email, adviser routing, coaching routing (interfaces only, Phase 5) |
| `scripts/run_titan_lifemap.sh` | VPS startup script for the FastAPI service (mirrors `apps/command/main.py` deployment pattern) |
| `module-installs/titan-lifemap-v1/...` (optional) | If Patrick wants this packaged as a reusable AIOS module later — deferred, not part of this build |
| `outputs/titan-lifemap-vps-deployment.md` | VPS deployment guide, modeled on `outputs/commandos-vps-deployment.md` |
| `reference/titan-lifemap-data-access.md` | Schema reference for the new Titan LifeMap tables, modeled on `reference/data-access.md` |

### Files to Modify

| File Path | Changes |
|---|---|
| `context/gaia/overview.md` | Update "Stage" and "Vision" sections to reflect that GAIA's first product (Titan LifeMap) is now defined and in build |
| `context/gaia/strategy.md` | Update "Immediate Priorities" and "Open Questions" — several are now answered (primary user, first use case, differentiation via behavioural finance) |
| `context/sustain-momentum/overview.md` | Add Titan LifeMap as the evolution of the Clarity Check service |
| `gtd/projects.md` | Update the "Develop D2C financial guidance process" project with the new plan reference and updated next action |
| `CLAUDE.md` | Add a "Titan LifeMap" section (mirroring the "CommandOS" section) once Phase 1-2 are deployed |
| `requirements.txt` | Add `fastapi`, `uvicorn` (or similar ASGI server) for the new backend service |
| `.env` (local only, not committed) | Add Titan LifeMap-specific config vars as they're identified during implementation |

### Files to Delete (if any)

None.

---

## Design Decisions

### Key Decisions Made

1. **Original content only, no CEG derivation**: All discovery questions are written fresh for this plan. The category *concepts* (values, goals, relationships, money history) are universal and not protectable, but no question wording, category labels, or sequencing from CEG's Total Client Profile guide is reused. The Seven Titans sequencing (Visionary/Sage-first) is itself the differentiator, not a cosmetic rename of CEG's structure.
2. **Standalone backend, not Chatbase-hosted**: Per Patrick's explicit preference (Option B) — a dedicated FastAPI service on the VPS, embedded in the WordPress site via API calls from a custom frontend widget. Chatbase remains untouched, serving marketing/FAQ/lead-gen only.
3. **Reuse CommandOS's proven patterns**: The Claude Agent SDK wrapper, session management, and PDF generation pipeline already work in production (CommandOS). Titan LifeMap's conversation engine and report generators are built on the same proven primitives rather than reinventing them, reducing risk.
4. **Shared database, new tables**: Titan LifeMap profile data lives in the existing `data/data.db` rather than a separate database, keeping one source of truth and allowing future cross-referencing (e.g., correlating Titan Clarity Scores with website traffic or consulting pipeline data already in this database).
5. **Phases 1-4 are this plan's scope; Phases 5-6 are stubbed/deferred**: CRM, email, and adviser-routing integrations depend on tools Patrick hasn't yet chosen (which CRM? which email platform?). Building speculative integrations now would be premature. Phase 5 ships as clean interfaces ready to wire up once those tools are chosen. Phase 6 (cashflow modelling, full GAIA platform) is explicitly out of scope — documented as future direction only.
6. **New FastAPI service, not folded into CommandOS**: Titan LifeMap serves website visitors (B2C, public-facing, no Telegram/admin context), while CommandOS serves Patrick privately via Telegram. Different audiences, different trust boundaries — kept as separate services on the same VPS rather than merged, so a bug in one cannot take down the other.

### Alternatives Considered

- **Extend Chatbase with custom actions/webhooks**: Rejected per Patrick's explicit preference — Chatbase's webhook/action model would give less control over memory, scoring, and profiling than a standalone service, and Patrick stated wanting to avoid dependence on Chatbase limitations.
- **Build directly into WordPress (PHP plugin)**: Rejected — would duplicate the Python/Claude Agent SDK logic already proven in CommandOS, and Patrick is not a developer who could maintain PHP code. A thin JavaScript widget calling out to the Python API (which Claude maintains) is more sustainable.
- **Single combined report instead of three**: Rejected — the three audiences (consumer, coach, adviser) need fundamentally different framing and detail level; combining them would either overwhelm consumers or underserve advisers.

### Resolved Decisions (formerly Open Questions)

All five were resolved by Patrick on 2026-06-23:

1. **Hosting/domain**: VPS-hosted, not WordPress-coupled. Structure: `sustain-momentum.com` (marketing website, WordPress/10Web) → `api.sustain-momentum.com` (Titan LifeMap / GAIA API, VPS) → `app.sustain-momentum.com` (future client portal, VPS, not built in this plan). This keeps GAIA decoupled from the website so it can become a standalone commercial platform later without a migration. DNS for `api.sustain-momentum.com` needs to point to the VPS IP; SSL via Let's Encrypt/Certbot during deployment (Step 10).
2. **Frontend widget**: 10Web supports custom HTML/JS/iframe embeds — exact method decided later. Architecture principle: **the website is a presentation layer, the VPS is the application layer**. Website page embeds the Titan LifeMap experience, which calls the API on `api.sustain-momentum.com`. WordPress performs no application logic. (Frontend embed itself remains out of scope for this plan, per the original Notes section — this just confirms the technical path is feasible.)
3. **Session handling**: Friction-free start — no contact details required upfront. Flow: visitor starts immediately, completes Visionary and Sage stages anonymously under a server-generated session token (cookie-based), contact details (first name + email) requested at an appropriate point — typically just before report generation. Server-side session storage in `data/data.db`; if a session expires, the user restarts (no complex resume-by-email flow needed initially).
4. **Behavioural Friction vs. BEA**: Kept explicitly separate, not merged. **Behavioural Friction Profile = diagnosis** (what we observe: procrastination, avoidance, overthinking, impulsiveness, excessive delegation, lack of confidence). **BEA = intervention** (how we respond, per the existing BEA framework from Patrick's white paper). The relationship is one-directional: diagnosis feeds into which BEA intervention gets recommended, but the two frameworks are not collapsed into one. `analysis.py` produces the Behavioural Friction Profile only — BEA-based recommendations are a downstream consumer of that profile, not part of the scoring itself, and may be addressed in a future plan once Titan LifeMap's diagnostic side is proven.
5. **CRM and email**: No CRM in Phase 1 — deliberately deferred until demand is proven. Stack: **Google Workspace** for email delivery, **Make.com** for workflow automation, **database within GAIA** (i.e. `data/data.db`) for lead/profile storage. Flow: complete Titan LifeMap → report generated → email delivered (via Google Workspace, likely triggered through Make.com) → lead stored in the database. `routing.py` (Step 9) should be built against this simpler stack, not speculative CRM interfaces.

### Guiding Design Principle (added 2026-06-23)

Patrick set this as the philosophy that should drive every design decision in this build:

> "The objective is not to build a better fact-find. The objective is to build a Behavioural Discovery Engine. Most systems ask 'what do you own?' Titan LifeMap should ask 'what matters most?' Most systems gather data. Titan LifeMap should generate clarity. Financial information supports the conversation. It does not lead it."

Practical implications for implementation:
- In `stages.py`, every stage's framing and questions should orient toward clarity and meaning before any financial detail — this is already the Visionary→Sage→Builder→Steward→Guardian sequence, but the *tone* of the writing (Step 5) must reinforce it, not just the ordering.
- In `analysis.py` and the report generators (Step 7-8), lead every output with "where you are / where you want to go / what is stopping you / what should happen next" — not with net worth or asset summaries.
- Financial data (hard facts) should read as supporting evidence within the narrative, never as the headline.

---

## Step-by-Step Tasks

### Step 1: Create Titan LifeMap context documentation

Document the framework and the IP boundary before writing any code, so the reasoning is preserved and any future session (or developer) understands why the system is built this way.

**Actions:**
- Create `context/titan-lifemap/overview.md` covering: the Seven Titans framework (Visionary, Warrior, Scholar, Steward, Guardian, Builder, Sage), the five-stage discovery sequence (Visionary → Sage → Builder → Steward → Guardian, financial data last), the eight soft-fact categories with their named outputs (Future Vision Statement, Personal Enough Statement, Top Five Values, Family Impact Summary, Money Story Summary, Behavioural Friction Profile, Health-Wealth-Happiness Scorecard, Legacy Statement), the three handoff routes, and the output naming (Titan LifeMap Profile, Titan Clarity Score, Titan Momentum Plan).
- Create `context/titan-lifemap/ip-boundary.md` explicitly recording: what CEG's Total Client Profile guide contains (category list only, no verbatim content), why Titan LifeMap's architecture is distinct (sequencing philosophy, original questions, different category set), and the rule for any future content additions ("never copy or closely paraphrase CEG, Covey, or ActionCoach source material — use only the universal underlying concept").

**Files affected:**
- `context/titan-lifemap/overview.md` (new)
- `context/titan-lifemap/ip-boundary.md` (new)

---

### Step 2: Update GAIA and Sustain Momentum context to reflect this build

**Actions:**
- Edit `context/gaia/overview.md`: change "Stage" from "Early development / concept phase" to note that Titan LifeMap is GAIA's first defined product, now in active build. Update "Vision" to reference Titan LifeMap by name.
- Edit `context/gaia/strategy.md`: update "Immediate Priorities" — mark "define the core proposition" and "identify the most compelling first use case" as resolved by Titan LifeMap. Update "Open Questions" — note that "primary user" is now answered (consumer-first, with adviser/coaching as downstream routes) and "role of behavioural finance as differentiator" is now answered (BEA-aligned Behavioural Friction Profile).
- Edit `context/sustain-momentum/overview.md`: add a short paragraph under the "Consumer-Facing" section noting that Titan LifeMap is the evolution of the Clarity Check service.

**Files affected:**
- `context/gaia/overview.md`
- `context/gaia/strategy.md`
- `context/sustain-momentum/overview.md`

---

### Step 3: Update the GTD project tracking this work

**Actions:**
- Edit `gtd/projects.md`: update the "Develop D2C financial guidance process" project under Sustain Momentum — change next action from the `@think` reflection (already completed via this planning conversation) to a new next action referencing this plan file, e.g. "@claude — Implement Phase 1 of Titan LifeMap per plans/2026-06-23-titan-lifemap-discovery-engine.md."
- Run `python scripts/refresh_dashboard.py` after the edit to update the dashboard.

**Files affected:**
- `gtd/projects.md`
- `gtd/dashboard.md` (auto-regenerated)

---

### Step 4: Build the data model (Phase 1)

**Actions:**
- Create `apps/titan_lifemap/models.py` with Pydantic models: `TitanProfile` (top-level container), `Session` (session_id, started_at, current_stage, completed flag, route — consumer/coaching/adviser), `SoftFacts` (one field per of the 8 categories), `HardFacts` (income, expenses, assets, liabilities, existing arrangements), `ScoringResult` (clarity_score, momentum_score, behavioural_friction_profile).
- Create `apps/titan_lifemap/db.py` following the `scripts/db.py` pattern: `init_db()`, `get_connection()`, and table creation SQL for `titan_sessions`, `titan_soft_facts`, `titan_hard_facts`, `titan_scores` — all keyed by `session_id`, written into the existing `data/data.db`.
- Write a quick test script (`apps/titan_lifemap/db.py`'s `if __name__ == "__main__"` block) that initializes the tables and confirms they exist, mirroring `scripts/db.py`'s self-test pattern.

**Files affected:**
- `apps/titan_lifemap/models.py` (new)
- `apps/titan_lifemap/db.py` (new)

---

### Step 5: Build the five discovery stages with original content (Phase 2a)

**Actions:**
- Create `apps/titan_lifemap/stages.py` defining the five stages in order (Visionary, Sage, Builder, Steward, Guardian), each with: a short framing intro (in Titan Mindset's voice, not CEG's), 3-5 original open questions per stage covering the relevant soft-fact categories (Visionary → Life Vision + Definition of Enough; Sage → Purpose & Legacy + Health-Wealth-Happiness; Builder → Core Values + Family & Relationships; Steward → Relationship With Money + hard facts intro; Guardian → Behavioural Patterns + protection-related hard facts), and the named output artifact each stage produces.
- Explicitly write every question fresh — do not consult or paraphrase the CEG PDF content while writing this file. Use only the category concepts already documented in `context/titan-lifemap/overview.md`.
- Cross-check each written question against `context/titan-lifemap/ip-boundary.md`'s rule before finalizing.

**Files affected:**
- `apps/titan_lifemap/stages.py` (new)

---

### Step 6: Build the conversation orchestration engine (Phase 2b)

**Actions:**
- Create `apps/titan_lifemap/conversation.py`: wraps the Claude Agent SDK (same pattern as `apps/command/agent_sdk.py`) to run a guided conversation through the five stages. Each turn: load session state from `db.py`, determine current stage from `stages.py`, prompt Claude with the stage's framing + question + conversation history, capture the user's response, decide (via Claude) whether enough has been captured for that stage's soft-fact category or another follow-up question is needed, advance stage when complete.
- Reuse `apps/command/session_manager.py`'s persistence pattern, adapted for web sessions (session_id from a cookie/token rather than a Telegram chat_id).
- Create `apps/titan_lifemap/config.py`, copying `scripts/config.py`'s `.env` loading and cert-fix pattern.
- Create `apps/titan_lifemap/main.py`: a FastAPI app with endpoints `POST /session/start`, `POST /session/{id}/message`, `GET /session/{id}/status`. Run locally first (`uvicorn apps.titan_lifemap.main:app --reload`) to verify the conversation flow works end-to-end via curl/Postman before any frontend work.

**Files affected:**
- `apps/titan_lifemap/conversation.py` (new)
- `apps/titan_lifemap/config.py` (new)
- `apps/titan_lifemap/main.py` (new)
- `apps/titan_lifemap/__init__.py` (new)
- `requirements.txt` (add `fastapi`, `uvicorn`)

---

### Step 7: Build the analysis layer (Phase 3)

**Actions:**
- Create `apps/titan_lifemap/analysis.py`: once a session's soft facts and hard facts are complete, run a Claude-driven analysis pass that produces: a Behavioural Friction Profile (scoring procrastination, avoidance, overthinking, impulsiveness, delegation, lack of confidence — referencing the BEA framework's six components per Open Question #4), a Titan Clarity Score (a single composite score reflecting how clear the user's life vision and definition of "enough" are), and a Titan Momentum Plan (a ranked set of priority actions bridging current state to stated goals).
- Store results via `db.py` into the `titan_scores` table.
- Write a test using a sample completed session (mock data) to confirm scoring runs without errors before relying on real conversation data.

**Files affected:**
- `apps/titan_lifemap/analysis.py` (new)

---

### Step 8: Build the three report generators (Phase 4)

**Actions:**
- Create `apps/titan_lifemap/reports/templates/report.css`, adapting `apps/command/templates/report.css` for Titan LifeMap branding (colors/fonts can be placeholder until Patrick provides brand guidelines).
- Create `apps/titan_lifemap/reports/consumer.py`: generates the **Consumer Report** — Titan LifeMap Profile (all soft facts), Titan Clarity Score, Titan Momentum Plan, educational guidance, explicitly no regulated advice language. Output as PDF via WeasyPrint, reusing `apps/command/pdf_generator.py`'s pattern.
- Create `apps/titan_lifemap/reports/coaching.py`: generates the **Sustain Momentum Coaching Report** — coaching baseline, accountability framework, progress measurement tool, formatted for Patrick and Avdokia's use.
- Create `apps/titan_lifemap/reports/adviser.py`: generates the **Adviser Referral Pack** — Personal Profile (values, goals, family situation, behavioural observations), Financial Snapshot (income, assets, liabilities, cashflow, existing arrangements), Planning Priorities (ranked objectives, time horizons, urgency scores), Behavioural Insights (execution risks, decision-making style, areas requiring support).
- Add a `POST /session/{id}/report?route={consumer|coaching|adviser}` endpoint to `main.py` that calls the appropriate generator based on which route the session was assigned.

**Files affected:**
- `apps/titan_lifemap/reports/templates/report.css` (new)
- `apps/titan_lifemap/reports/consumer.py` (new)
- `apps/titan_lifemap/reports/coaching.py` (new)
- `apps/titan_lifemap/reports/adviser.py` (new)
- `apps/titan_lifemap/main.py` (add report endpoint)

---

### Step 9: Build the (deliberately simple) workflow integration layer (Phase 5)

**Actions:**
- Create `apps/titan_lifemap/routing.py` implementing the confirmed Phase 1 stack — no CRM:
  - `store_lead(profile)` — writes the completed profile/lead into a `titan_leads` table in `data/data.db`.
  - `send_report_email(profile, report_pdf_path)` — sends the generated report to the user's email via Google Workspace (SMTP or Gmail API — use SMTP with an app password initially for simplicity, matching the "don't over-engineer" instruction).
  - `notify_make_webhook(profile, event_type)` — fires a webhook to Make.com so Patrick can build his own downstream automations (e.g. notify him by Telegram via the existing CommandOS bot, or anything else) without that logic living in this codebase.
  - `route_to_adviser(profile)` / `route_to_coaching(profile)` — for now, both simply call `notify_make_webhook` with a distinct event type; real adviser/coaching system integration is deferred until Phase 1 demand is proven, per Patrick's explicit instruction not to add CRM complexity yet.
- Document the Make.com webhook payload shape in `reference/titan-lifemap-data-access.md` so Patrick can build the Make.com scenario independently.

**Files affected:**
- `apps/titan_lifemap/routing.py` (new)
- `reference/titan-lifemap-data-access.md` (new)

---

### Step 10: Deploy to the VPS

**Actions:**
- SSH/terminal into the VPS (same one running CommandOS).
- `git pull` to bring the new `apps/titan_lifemap/` code over.
- Install new dependencies: `pip install fastapi uvicorn` (plus anything else added to `requirements.txt`).
- Test the FastAPI app runs manually: `uvicorn apps.titan_lifemap.main:app --host 0.0.0.0 --port 8001`.
- Create `scripts/run_titan_lifemap.sh` and a systemd service file (mirroring `module-installs/command-os-v1/.../config/command-bot.service`), running as the `patrick` user, auto-restart, logging to `data/titan-lifemap.stdout.log` / `.stderr.log`.
- Enable and start the service; verify with `systemctl status titan-lifemap`.
- Document the full deployment process in `outputs/titan-lifemap-vps-deployment.md`, modeled on the existing `outputs/commandos-vps-deployment.md`.

**Files affected:**
- `scripts/run_titan_lifemap.sh` (new)
- `outputs/titan-lifemap-vps-deployment.md` (new)
- VPS: `/etc/systemd/system/titan-lifemap.service` (new, not in this repo)

---

### Step 11: Update CLAUDE.md

**Actions:**
- Add a "Titan LifeMap" section to `CLAUDE.md`, mirroring the existing "CommandOS" section: what it is, where the code lives, how to deploy changes, and a note that this is GAIA's first concrete product.
- Update the workspace structure diagram to include `apps/titan_lifemap/`.

**Files affected:**
- `CLAUDE.md`

---

### Step 12: Update HISTORY.md and commit

**Actions:**
- Add a dated entry to `HISTORY.md` summarizing what was built (data model, conversation engine, analysis layer, report generators, VPS deployment).
- Commit all new and modified files with a clear message (e.g. `feat: build Titan LifeMap discovery engine - GAIA's first product`).
- Push to GitHub.

**Files affected:**
- `HISTORY.md`
- All files from Steps 1-11 (git add/commit)

---

## Connections & Dependencies

### Files That Reference This Area

- `gtd/projects.md` and `gtd/dashboard.md` already reference the "Develop D2C financial guidance process" project that this plan fulfills.
- `context/sustain-momentum/overview.md` references the Clarity Check service that Titan LifeMap evolves.
- `context/gaia/overview.md` and `strategy.md` reference GAIA's undefined product status, resolved by this plan.

### Updates Needed for Consistency

- `CLAUDE.md`'s workspace structure diagram and Commands section (Step 11).
- `reference/data-access.md` should get a cross-reference note pointing to the new `reference/titan-lifemap-data-access.md` once that exists, since both describe tables in the same `data/data.db`.

### Impact on Existing Workflows

- No impact on CommandOS, DataOS, IntelOS, or ProductivityOS — Titan LifeMap is additive, running as a separate service on the same VPS.
- `/prime` does not need to change for this plan (Titan LifeMap is consumer-facing infrastructure, not something Patrick interacts with each session) — though Patrick may want a future `/titan-status` command to check on submissions; not in scope for this plan.

---

## Validation Checklist

- [ ] `context/titan-lifemap/overview.md` and `ip-boundary.md` created and reviewed by Patrick for accuracy
- [ ] `context/gaia/overview.md` and `strategy.md` updated to reflect Titan LifeMap as GAIA's first product
- [ ] `gtd/projects.md` updated with new next action referencing this plan
- [ ] Database tables (`titan_sessions`, `titan_soft_facts`, `titan_hard_facts`, `titan_scores`) created successfully in `data/data.db`
- [ ] All five discovery stages in `stages.py` contain only original content (manually cross-checked against `ip-boundary.md`)
- [ ] Conversation engine runs end-to-end locally via curl/Postman test (start session, send messages through all 5 stages, reach completion)
- [ ] Analysis layer produces a Clarity Score, Momentum Plan, and Behavioural Friction Profile from test session data without errors
- [ ] All three report generators (consumer, coaching, adviser) produce valid PDFs from the same test session data
- [ ] FastAPI service deployed and running as a systemd service on the VPS, `systemctl status titan-lifemap` shows active
- [ ] `CLAUDE.md` updated with Titan LifeMap section
- [ ] `HISTORY.md` updated, all changes committed and pushed to GitHub

---

## Success Criteria

The implementation is complete when:

1. A test user can complete a full Titan LifeMap conversation (all five stages) via the API and receive a session marked complete.
2. Each of the three report types (consumer, coaching, adviser) can be generated as a PDF from a completed test session.
3. The service runs continuously on the VPS as a systemd service, independent of CommandOS, and survives a server reboot.
4. `context/gaia/` and `gtd/projects.md` accurately reflect that this work is done and what remains (frontend embed, real CRM/email integration — Phase 5/6).
5. No content in `apps/titan_lifemap/stages.py` can be traced to CEG's Total Client Profile guide, Covey's 7 Habits, or ActionCoach materials — verified by Patrick's own review, since he is the one with direct knowledge of those source materials.

---

## Notes

- **Frontend embed (website widget) is explicitly out of scope for this plan.** This plan builds and deploys the backend API only. A follow-up plan should cover the WordPress/10Web-side JavaScript widget once Open Questions #1-3 (hosting, frontend tech, session/auth handling) are answered.
- **Phase 5 (real CRM/email integration) and Phase 6 (cashflow modelling, full GAIA platform, BEA accountability engine) are intentionally deferred** — stubbed cleanly in Phase 5, documented only (not built) for Phase 6. Revisit once Phases 1-4 are proven with real usage.
- **Branding/visual design is placeholder.** Report styling, color scheme, and any logo usage should be revisited once Patrick has Titan Mindset brand guidelines to share — not blocking for functional completion of this plan.
- This plan deliberately avoided reading deeper into the Titan Mindset manuscript PDFs beyond what Patrick already typed directly in conversation, since his direct description is authoritative and avoids any risk of the plan itself being built from a hard-to-parse or incomplete extraction.
