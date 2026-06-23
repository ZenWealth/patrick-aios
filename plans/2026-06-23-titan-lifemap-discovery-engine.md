# Plan: Titan LifeMap — AIOS Discovery & Planning Engine

**Created:** 2026-06-23
**Status:** Implemented
**Request:** Build a structured, modular conversational discovery system (Titan LifeMap™) branded under Patrick's trademarked Titan Mindset framework, replacing the original Chatbase-based fact-find idea, and serving as the first concrete expression of the GAIA proposition.

---

## Overview

### What This Plan Accomplishes

This plan builds **Titan LifeMap™** — a multi-stage, AI-guided discovery conversation that helps consumers gain clarity on their life and finances before any regulated advice is given. It replaces the "ask about pensions and ISAs first" model of a traditional fact-find with a sequence rooted in Patrick's own trademarked Seven Titans framework (Visionary → Sage → Builder → Steward → Guardian), captures both soft facts (values, life vision, behavioural patterns) and hard facts (income, assets, goals), and produces **four** outputs from every completed session: a self-guided consumer report, a Sustain Momentum coaching baseline, an adviser-ready referral pack (only the relevant one of these three is shown to the client depending on their route), and — generated every time, for every session, regardless of route — an **Internal AI Profile** that is never client-visible and becomes the permanent memory layer behind GAIA.

**Built for rapid iteration, not for being right the first time.** Every stage, prompt, scoring rule, and report template is stored as external configuration (YAML), not hardcoded in Python. The application code is a thin, stable engine that loads and executes configuration — so Patrick can change questions, scoring weights, or report wording during testing without needing a code change or redeploy logic rewrite.

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
- **Externalize everything that's likely to change during testing into YAML configuration**: stages and questions, scoring rules, report templates, and Claude prompts. Application code loads and executes this configuration; it does not embed it.
- Build the **analysis layer** (Phase 3): behavioural profiling, friction identification, Clarity Score and Momentum Plan scoring, driven by configurable scoring rules and using Claude via the Agent SDK.
- Build **four report generators** (Phase 4): Consumer Report, Sustain Momentum Coaching Report, Adviser Referral Pack, and **Internal AI Profile** (generated every time, never client-visible) — reusing the existing WeasyPrint PDF pipeline already proven in CommandOS, driven by configurable templates.
- Build the **(deliberately simple) workflow integration layer** (Phase 5): lead storage, email delivery via Google Workspace, and a Make.com webhook — no CRM.
- Document **Phase 6 (future expansion)** as a forward-looking section in context, not built now.
- Update `context/gaia/overview.md` and `strategy.md` to reflect that GAIA now has a defined first product.
- Update `gtd/projects.md` to mark progress on the "Develop D2C financial guidance process" project.
- Create a new context folder `context/titan-lifemap/` documenting the framework, the soft-fact categories, and the IP boundary (what's safe to use vs. what must stay original).
- Create a `docs/` entry for every major component as it's built, following the existing `docs/_index.md` routing pattern from InfraOS — so future Claude sessions (or developers) can find and understand any piece without re-reading all the code.

### Configuration-Over-Code Architecture

This is the central architectural principle for this build, set by Patrick before implementation began: **Titan LifeMap, GAIA, and the Behavioural Discovery Engine will evolve significantly during testing, so nothing that's likely to change should require a code change to update.**

| What | Stored As | Location | Why |
|---|---|---|---|
| Titan stages (questions, framing, sequencing) | YAML | `apps/titan_lifemap/config/stages.yaml` | Patrick will want to reword, reorder, add, or remove stages/questions after watching real users go through them |
| Scoring rules (Clarity Score, Momentum Plan, Behavioural Friction weights) | YAML | `apps/titan_lifemap/config/scoring_rules.yaml` | Scoring logic is exactly the kind of thing that needs tuning after seeing real distributions of real answers |
| Report templates (section structure, headings, what each report type includes) | YAML + Jinja2 HTML templates | `apps/titan_lifemap/config/report_templates/` | The four report types' content and structure will likely be revised heavily once Patrick sees first drafts against real sessions |
| Claude prompts (system prompts for conversation, analysis, each report generator) | YAML/text files | `apps/titan_lifemap/config/prompts/` | Prompts are the most iteration-prone part of any Claude-driven system — must be editable without touching Python |

**The rule for implementation:** if a future change to wording, weighting, sequencing, or report content would require editing a `.py` file, that's a sign something should have been a config file instead. Application code should only contain logic that is genuinely structural (how to load config, how to call Claude, how to write to the database, how to render a PDF) — never the content itself.

### New Files to Create

| File Path | Purpose |
|---|---|
| `context/titan-lifemap/overview.md` | Titan LifeMap product overview — Seven Titans framework, discovery sequencing, soft-fact categories, output names |
| `context/titan-lifemap/ip-boundary.md` | Explicit record of the CEG IP concern and how this design avoids it — for Patrick's own reference and for any future contributor/developer who touches this code |
| `apps/titan_lifemap/__init__.py` | Package init |
| `apps/titan_lifemap/main.py` | FastAPI app entry point — serves the conversation API |
| `apps/titan_lifemap/config.py` | Env/config loader (`.env` vars), reusing `scripts/config.py` patterns — distinct from the `config/` YAML directory below |
| `apps/titan_lifemap/config/stages.yaml` | The five discovery stages, their framing, and original questions — **content, not code** |
| `apps/titan_lifemap/config/scoring_rules.yaml` | Clarity Score, Momentum Plan, and Behavioural Friction Profile scoring weights/rules — **content, not code** |
| `apps/titan_lifemap/config/prompts/conversation.yaml` | System prompts driving the conversation engine's Claude calls |
| `apps/titan_lifemap/config/prompts/analysis.yaml` | System prompts driving the analysis layer's Claude calls |
| `apps/titan_lifemap/config/prompts/reports.yaml` | System prompts driving each of the four report generators |
| `apps/titan_lifemap/config/report_templates/consumer.yaml` | Consumer Report structure/sections |
| `apps/titan_lifemap/config/report_templates/coaching.yaml` | Coaching Report structure/sections |
| `apps/titan_lifemap/config/report_templates/adviser.yaml` | Adviser Referral Pack structure/sections |
| `apps/titan_lifemap/config/report_templates/internal.yaml` | Internal AI Profile structure/sections |
| `apps/titan_lifemap/config_loader.py` | Loads and validates all YAML config files at startup; the only module that knows about file paths/YAML parsing — everything else asks this module for config objects |
| `apps/titan_lifemap/models.py` | Data model: TitanProfile, Session, SoftFact, HardFact, ScoringResult (Pydantic models) |
| `apps/titan_lifemap/db.py` | SQLite table definitions and query helpers for Titan LifeMap tables in `data/data.db` |
| `apps/titan_lifemap/conversation.py` | Conversation orchestration — stage progression (driven by `stages.yaml` via `config_loader.py`), session state, completion logic, wraps Claude Agent SDK calls |
| `apps/titan_lifemap/analysis.py` | Analysis layer — behavioural friction identification, Clarity Score, Momentum Plan scoring, all driven by `scoring_rules.yaml` |
| `apps/titan_lifemap/reports/engine.py` | Shared report rendering engine — loads a report template YAML + Jinja2 HTML template, renders, converts to PDF via WeasyPrint. All four report generators below are thin callers of this engine, not separate rendering logic |
| `apps/titan_lifemap/reports/consumer.py` | Consumer Report generator — calls `engine.py` with `consumer.yaml` |
| `apps/titan_lifemap/reports/coaching.py` | Sustain Momentum Coaching Report generator — calls `engine.py` with `coaching.yaml` |
| `apps/titan_lifemap/reports/adviser.py` | Adviser Referral Pack generator — calls `engine.py` with `adviser.yaml` |
| `apps/titan_lifemap/reports/internal.py` | **Internal AI Profile generator** — calls `engine.py` with `internal.yaml`. Never exposed via any client-facing endpoint. See dedicated section below. |
| `apps/titan_lifemap/reports/templates/report.css` | Shared PDF stylesheet, adapted from `apps/command/templates/report.css` |
| `apps/titan_lifemap/reports/templates/*.html` | Jinja2 HTML templates (one per report type) — structure driven by the corresponding `report_templates/*.yaml` |
| `apps/titan_lifemap/routing.py` | Workflow integration — lead storage, Google Workspace email, Make.com webhook (Phase 5, built for real per Patrick's confirmed stack, not stubbed) |
| `scripts/run_titan_lifemap.sh` | VPS startup script for the FastAPI service (mirrors `apps/command/main.py` deployment pattern) |
| `outputs/titan-lifemap-vps-deployment.md` | VPS deployment guide, modeled on `outputs/commandos-vps-deployment.md` |
| `reference/titan-lifemap-data-access.md` | Schema reference for the new Titan LifeMap tables, modeled on `reference/data-access.md` |
| `docs/titan-lifemap-architecture.md` | Component-level documentation of the whole system — see Documentation section below |
| `docs/titan-lifemap-config-guide.md` | Plain-language guide to every config file: what it controls, how to safely edit it, what NOT to put in code instead |

### The Internal AI Profile (Fourth Report)

Per Patrick's explicit instruction, every completed session generates a fourth output that is **never shown to the client, the adviser, or anyone outside Patrick/GAIA**:

> "The client sees the report. GAIA sees the person."

**Contents:** all soft facts in full, all behavioural observations, friction scores, the complete values hierarchy, and Titan archetype insights (which Titans/stages produced the richest or most revealing responses) — essentially the maximum-fidelity capture of the session, written for machine and future-AI consumption rather than human readability.

**Purpose:** this becomes the **permanent memory layer** — when this person returns (to Titan LifeMap again, to a Sustain Momentum coaching engagement, to a future GAIA product), this profile is what lets the system recognize and build on what's already known about them, rather than starting from zero. This is explicitly designed to be the most valuable long-term asset in the platform, not a byproduct.

**Implementation implications:**
- Stored in its own table, `titan_internal_profiles`, never joined into any client-facing report query path.
- No endpoint in `main.py` ever returns this report to an external caller — it is written to the database and optionally to a PDF/JSON file in a directory not exposed by the API, for Patrick's own reference.
- Its YAML template (`internal.yaml`) and prompt (in `prompts/reports.yaml`) explicitly instruct Claude to maximize information capture and analytical depth rather than client-friendly framing — this is the one report where verbosity and clinical precision are good, not bad.

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
7. **Configuration-over-code, set before implementation began (2026-06-23)**: Patrick explicitly instructed that stages, prompts, scoring rules, and report templates must be stored separately from application logic, anticipating significant change during testing. This is treated as a hard constraint on every step below, not a nice-to-have — see the "Configuration-Over-Code Architecture" section above.
8. **Internal AI Profile as a fourth, permanent, non-optional report**: Added per Patrick's explicit instruction after the initial plan was drafted. Generated for every session unconditionally (not just for certain routes), stored separately from client-facing data, intended as the long-term memory substrate for GAIA. This is treated as core to Phase 4, not an afterthought bolted onto the original three reports.
9. **Document each component as it is built, not retrospectively**: Each major file/module gets a corresponding entry in `docs/_index.md` (the existing InfraOS documentation routing system) at the time it's created, not as a cleanup pass at the end — so the documentation accurately reflects the reasoning present at build time.

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

### Step 4: Build the config loader and data model (Phase 1)

**Actions:**
- Create the `apps/titan_lifemap/config/` directory structure (`config/`, `config/prompts/`, `config/report_templates/`).
- Create `apps/titan_lifemap/config_loader.py`: a single module responsible for finding, parsing, and validating every YAML file under `config/`. Exposes functions like `get_stages()`, `get_scoring_rules()`, `get_prompt(name)`, `get_report_template(name)` — every other module gets configuration through these functions, never by reading YAML directly itself. Validates required keys are present at startup and fails loudly (not silently) if a config file is malformed, since a broken config should never reach a live session.
- Create `apps/titan_lifemap/models.py` with Pydantic models: `TitanProfile` (top-level container), `Session` (session_id, started_at, current_stage, completed flag, route — consumer/coaching/adviser), `SoftFacts` (one field per of the 8 categories), `HardFacts` (income, expenses, assets, liabilities, existing arrangements), `ScoringResult` (clarity_score, momentum_score, behavioural_friction_profile).
- Create `apps/titan_lifemap/db.py` following the `scripts/db.py` pattern: `init_db()`, `get_connection()`, and table creation SQL for `titan_sessions`, `titan_soft_facts`, `titan_hard_facts`, `titan_scores`, `titan_internal_profiles`, `titan_leads` — all keyed by `session_id`, written into the existing `data/data.db`.
- Write a quick test script (`apps/titan_lifemap/db.py`'s `if __name__ == "__main__"` block) that initializes the tables and confirms they exist, mirroring `scripts/db.py`'s self-test pattern.
- **Documentation**: create `docs/titan-lifemap-architecture.md` now (don't wait until the end) and add its first entries: data model and config loader. Add a row to `docs/_index.md` pointing to it.

**Files affected:**
- `apps/titan_lifemap/config/` (new directory)
- `apps/titan_lifemap/config_loader.py` (new)
- `apps/titan_lifemap/models.py` (new)
- `apps/titan_lifemap/db.py` (new)
- `docs/titan-lifemap-architecture.md` (new)
- `docs/_index.md` (add entry)

---

### Step 5: Write the five discovery stages as configuration, with original content (Phase 2a)

**Actions:**
- Create `apps/titan_lifemap/config/stages.yaml` defining the five stages in order (Visionary, Sage, Builder, Steward, Guardian) as **data**, not code: each stage has a name, a short framing intro (in Titan Mindset's voice, not CEG's), 3-5 original open questions covering the relevant soft-fact categories (Visionary → Life Vision + Definition of Enough; Sage → Purpose & Legacy + Health-Wealth-Happiness; Builder → Core Values + Family & Relationships; Steward → Relationship With Money + hard facts intro; Guardian → Behavioural Patterns + protection-related hard facts), and the named output artifact it produces.
- Explicitly write every question fresh — do not consult or paraphrase the CEG PDF content while writing this file. Use only the category concepts already documented in `context/titan-lifemap/overview.md`.
- Cross-check each written question against `context/titan-lifemap/ip-boundary.md`'s rule before finalizing.
- Add a `get_stages()` function to `config_loader.py` (if not already stubbed in Step 4) that parses this file into a list of stage objects the conversation engine can iterate.
- **Documentation**: add a "Stages Configuration" section to `docs/titan-lifemap-config-guide.md` (create the file now) explaining the YAML schema and how to safely add/reorder/edit a stage without touching Python.

**Files affected:**
- `apps/titan_lifemap/config/stages.yaml` (new)
- `apps/titan_lifemap/config_loader.py` (extend)
- `docs/titan-lifemap-config-guide.md` (new)

---

### Step 6: Build the conversation orchestration engine (Phase 2b)

**Actions:**
- Create `apps/titan_lifemap/config/prompts/conversation.yaml`: the system prompt(s) used to run the Claude-driven conversation — framing for how Claude should ask questions, follow up, and decide when a stage is sufficiently captured. Written as configuration so Patrick can tune Claude's conversational tone/behaviour without a code change.
- Create `apps/titan_lifemap/conversation.py`: wraps the Claude Agent SDK (same pattern as `apps/command/agent_sdk.py`) to run a guided conversation through the five stages loaded via `config_loader.get_stages()`. Each turn: load session state from `db.py`, determine current stage, build the Claude prompt from `config_loader.get_prompt("conversation")` + the current stage's question + conversation history, capture the user's response, decide (via Claude) whether enough has been captured for that stage's soft-fact category or another follow-up question is needed, advance stage when complete.
- Reuse `apps/command/session_manager.py`'s persistence pattern, adapted for web sessions (session_id from a cookie/token rather than a Telegram chat_id).
- Create `apps/titan_lifemap/config.py`, copying `scripts/config.py`'s `.env` loading and cert-fix pattern (this is the `.env` loader, distinct from `config_loader.py` which handles the YAML content config).
- Create `apps/titan_lifemap/main.py`: a FastAPI app with endpoints `POST /session/start`, `POST /session/{id}/message`, `GET /session/{id}/status`. Implement the friction-free session flow confirmed by Patrick: session starts anonymously with a server-generated token (cookie-based), Visionary and Sage stages proceed without contact details, first name + email are requested by the conversation engine (per `conversation.yaml`'s prompt) at the start of the Steward stage (i.e. just before financial data and well before report generation) — if the session expires before contact details are captured, the user simply restarts (no resume-by-email flow, per Patrick's "don't over-engineer this initially").
- Run locally first (`uvicorn apps.titan_lifemap.main:app --reload`) to verify the conversation flow works end-to-end via curl/Postman before any frontend work.
- **Documentation**: extend `docs/titan-lifemap-architecture.md` with the conversation engine and session-handling sections.

**Files affected:**
- `apps/titan_lifemap/config/prompts/conversation.yaml` (new)
- `apps/titan_lifemap/conversation.py` (new)
- `apps/titan_lifemap/config.py` (new)
- `apps/titan_lifemap/main.py` (new)
- `apps/titan_lifemap/__init__.py` (new)
- `requirements.txt` (add `fastapi`, `uvicorn`)
- `docs/titan-lifemap-architecture.md` (extend)

---

### Step 7: Build the analysis layer, driven by configurable scoring rules (Phase 3)

**Actions:**
- Create `apps/titan_lifemap/config/scoring_rules.yaml`: defines, as data, how the Behavioural Friction Profile is scored (the six diagnostic patterns — procrastination, avoidance, overthinking, impulsiveness, excessive delegation, lack of confidence — and what signals/weights map to each), how the Titan Clarity Score is composed (which stages/answers contribute, and how), and how the Titan Momentum Plan is ranked (priority/urgency weighting). Per Patrick's confirmed decision, this file does **not** reference or embed BEA — Behavioural Friction Profile is diagnosis-only; BEA-based intervention recommendations are explicitly out of scope for this plan and may be addressed in a future plan that consumes this profile.
- Create `apps/titan_lifemap/config/prompts/analysis.yaml`: the system prompt(s) for the Claude-driven analysis pass.
- Create `apps/titan_lifemap/analysis.py`: once a session's soft facts and hard facts are complete, loads `scoring_rules.yaml` and `prompts/analysis.yaml` via `config_loader.py`, runs a Claude-driven analysis pass producing the Behavioural Friction Profile, Titan Clarity Score, and Titan Momentum Plan. The Python code here should contain no hardcoded scoring weights or thresholds — every number that could plausibly need retuning lives in `scoring_rules.yaml`.
- Store results via `db.py` into the `titan_scores` table.
- Write a test using a sample completed session (mock data) to confirm scoring runs without errors before relying on real conversation data.
- **Documentation**: extend `docs/titan-lifemap-config-guide.md` with the scoring rules schema, and `docs/titan-lifemap-architecture.md` with the analysis layer.

**Files affected:**
- `apps/titan_lifemap/config/scoring_rules.yaml` (new)
- `apps/titan_lifemap/config/prompts/analysis.yaml` (new)
- `apps/titan_lifemap/analysis.py` (new)
- `docs/titan-lifemap-config-guide.md` (extend)
- `docs/titan-lifemap-architecture.md` (extend)

---

### Step 8: Build the shared report engine and four report generators, including the Internal AI Profile (Phase 4)

**Actions:**
- Create `apps/titan_lifemap/reports/templates/report.css`, adapting `apps/command/templates/report.css` for Titan LifeMap branding (colors/fonts can be placeholder until Patrick provides brand guidelines).
- Create the four `apps/titan_lifemap/config/report_templates/*.yaml` files (`consumer.yaml`, `coaching.yaml`, `adviser.yaml`, `internal.yaml`), each defining as data: section order, section headings, which data fields populate each section, and tone/framing notes. Per the Guiding Design Principle, the consumer/coaching/adviser templates must lead with "where you are / where you want to go / what is stopping you / what should happen next," with financial data appearing as supporting evidence, never the headline. `internal.yaml` is the exception — it should specify maximal detail and clinical precision, since it is written for machine/future-AI consumption, not human comfort.
- Create `apps/titan_lifemap/config/prompts/reports.yaml`: system prompts for each of the four report generators' Claude-driven narrative writing.
- Create `apps/titan_lifemap/reports/engine.py`: the **shared rendering engine** — given a report-type name, loads the corresponding template YAML and prompt, asks Claude to draft the narrative content per the template's section structure, renders into the corresponding Jinja2 HTML template, converts to PDF via WeasyPrint (reusing `apps/command/pdf_generator.py`'s pattern). This is the only place PDF-rendering logic lives.
- Create thin generator modules that call `engine.py` with the right template name:
  - `apps/titan_lifemap/reports/consumer.py` — Consumer Report (Titan LifeMap Profile, Clarity Score, Momentum Plan, educational guidance, explicitly no regulated advice language).
  - `apps/titan_lifemap/reports/coaching.py` — Sustain Momentum Coaching Report (coaching baseline, accountability framework, progress measurement tool, for Patrick and Avdokia's use).
  - `apps/titan_lifemap/reports/adviser.py` — Adviser Referral Pack (Personal Profile, Financial Snapshot, Planning Priorities, Behavioural Insights).
  - `apps/titan_lifemap/reports/internal.py` — **Internal AI Profile**. Always generated on session completion regardless of route (called directly by the completion logic in `conversation.py`, not exposed via any API endpoint). Writes to the `titan_internal_profiles` table and to a PDF/JSON file in a directory the API never serves. Maximizes information capture per the Guiding Design Principle's exception for this report type.
- Add a `POST /session/{id}/report?route={consumer|coaching|adviser}` endpoint to `main.py` for the three client-facing reports only — there is deliberately no endpoint that can return the Internal AI Profile to any external caller.
- **Documentation**: extend `docs/titan-lifemap-architecture.md` with the report engine and all four generators, being explicit in the docs about why `internal.py` has no API exposure (so a future developer doesn't "fix" this as an oversight).

**Files affected:**
- `apps/titan_lifemap/reports/templates/report.css` (new)
- `apps/titan_lifemap/reports/templates/*.html` (new, one per report type)
- `apps/titan_lifemap/config/report_templates/consumer.yaml` (new)
- `apps/titan_lifemap/config/report_templates/coaching.yaml` (new)
- `apps/titan_lifemap/config/report_templates/adviser.yaml` (new)
- `apps/titan_lifemap/config/report_templates/internal.yaml` (new)
- `apps/titan_lifemap/config/prompts/reports.yaml` (new)
- `apps/titan_lifemap/reports/engine.py` (new)
- `apps/titan_lifemap/reports/consumer.py` (new)
- `apps/titan_lifemap/reports/coaching.py` (new)
- `apps/titan_lifemap/reports/adviser.py` (new)
- `apps/titan_lifemap/reports/internal.py` (new)
- `apps/titan_lifemap/main.py` (add report endpoint)
- `docs/titan-lifemap-architecture.md` (extend)

---

### Step 9: Build the (deliberately simple) workflow integration layer (Phase 5)

**Actions:**
- Create `apps/titan_lifemap/routing.py` implementing the confirmed Phase 1 stack — no CRM:
  - `store_lead(profile)` — writes the completed profile/lead into the `titan_leads` table in `data/data.db`.
  - `send_report_email(profile, report_pdf_path)` — sends the generated report to the user's email via Google Workspace (SMTP with an app password initially, matching the "don't over-engineer" instruction).
  - `notify_make_webhook(profile, event_type)` — fires a webhook to Make.com so Patrick can build his own downstream automations (e.g. notify him by Telegram via the existing CommandOS bot, or anything else) without that logic living in this codebase.
  - `route_to_adviser(profile)` / `route_to_coaching(profile)` — for now, both simply call `notify_make_webhook` with a distinct event type; real adviser/coaching system integration is deferred until Phase 1 demand is proven, per Patrick's explicit instruction not to add CRM complexity yet.
- The webhook URL and email sender address are read from `.env` via `apps/titan_lifemap/config.py` — never hardcoded.
- Document the Make.com webhook payload shape in `reference/titan-lifemap-data-access.md` so Patrick can build the Make.com scenario independently.
- **Documentation**: extend `docs/titan-lifemap-architecture.md` with the routing/workflow layer.

**Files affected:**
- `apps/titan_lifemap/routing.py` (new)
- `reference/titan-lifemap-data-access.md` (new)
- `docs/titan-lifemap-architecture.md` (extend)

---

### Step 10: Deploy to the VPS

**Actions:**
- SSH/terminal into the VPS (same one running CommandOS).
- `git pull` to bring the new `apps/titan_lifemap/` code (including the `config/` YAML files, which are committed to the repo like any other source file) over.
- Install new dependencies: `pip install fastapi uvicorn pyyaml jinja2` (plus anything else added to `requirements.txt`).
- Test the FastAPI app runs manually: `uvicorn apps.titan_lifemap.main:app --host 0.0.0.0 --port 8001`.
- Create `scripts/run_titan_lifemap.sh` and a systemd service file (mirroring `module-installs/command-os-v1/.../config/command-bot.service`), running as the `patrick` user, auto-restart, logging to `data/titan-lifemap.stdout.log` / `.stderr.log`.
- Set up the `api.sustain-momentum.com` subdomain: DNS A record pointing to the VPS IP, then SSL via Certbot/Let's Encrypt, then an nginx (or equivalent) reverse proxy from port 443 to the FastAPI app's port (8001).
- Enable and start the service; verify with `systemctl status titan-lifemap`.
- Document the full deployment process in `outputs/titan-lifemap-vps-deployment.md`, modeled on the existing `outputs/commandos-vps-deployment.md` — including the subdomain/SSL/reverse-proxy steps, since CommandOS's deployment guide didn't need this (Telegram doesn't need a public HTTPS endpoint).
- **Note for the implementer**: since `config/*.yaml` files are committed to git and deployed via `git pull` just like code, **editing a config file still requires Patrick (or Claude) to commit, push, and pull on the VPS, then restart the service** — config-over-code avoids Python changes, but does not eliminate the deploy step entirely. If Patrick wants true zero-deploy config edits later, a future plan could move config files outside the git-deployed path (e.g. a VPS-local `config_overrides/` directory checked first) — explicitly out of scope for this plan, noted for the future.

**Files affected:**
- `scripts/run_titan_lifemap.sh` (new)
- `outputs/titan-lifemap-vps-deployment.md` (new)
- VPS: `/etc/systemd/system/titan-lifemap.service` (new, not in this repo)
- VPS: nginx/reverse-proxy config for `api.sustain-momentum.com` (new, not in this repo)

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
- [ ] Database tables (`titan_sessions`, `titan_soft_facts`, `titan_hard_facts`, `titan_scores`, `titan_internal_profiles`, `titan_leads`) created successfully in `data/data.db`
- [ ] All five discovery stages exist in `config/stages.yaml` (not in Python) and contain only original content (manually cross-checked against `ip-boundary.md`)
- [ ] Scoring weights/rules exist in `config/scoring_rules.yaml` (not in Python) — confirm by grep: no numeric scoring thresholds appear in `analysis.py` itself
- [ ] All four report structures exist in `config/report_templates/*.yaml` (not in Python)
- [ ] All Claude system prompts exist in `config/prompts/*.yaml` (not inline string literals in Python)
- [ ] `config_loader.py` fails loudly (raises, doesn't silently default) if a required config file is missing or malformed — verified by deliberately breaking one YAML file and confirming startup fails with a clear error
- [ ] Conversation engine runs end-to-end locally via curl/Postman test (start session anonymously, proceed through Visionary/Sage without contact details, contact details requested entering Steward, continue through Guardian, reach completion)
- [ ] Analysis layer produces a Clarity Score, Momentum Plan, and Behavioural Friction Profile from test session data without errors
- [ ] All three client-facing report generators (consumer, coaching, adviser) produce valid PDFs from the same test session data
- [ ] **Internal AI Profile is generated automatically on every session completion** (test by completing a session via any route and confirming a `titan_internal_profiles` row exists) **and is not reachable via any API endpoint** (confirm by checking `main.py`'s route list)
- [ ] FastAPI service deployed and running as a systemd service on the VPS, `systemctl status titan-lifemap` shows active
- [ ] `api.sustain-momentum.com` resolves and serves the API over HTTPS
- [ ] `docs/titan-lifemap-architecture.md` and `docs/titan-lifemap-config-guide.md` exist and cover every component built in Steps 4-9
- [ ] `docs/_index.md` has an entry routing to the new docs
- [ ] `CLAUDE.md` updated with Titan LifeMap section
- [ ] `HISTORY.md` updated, all changes committed and pushed to GitHub

---

## Success Criteria

The implementation is complete when:

1. A test user can complete a full Titan LifeMap conversation (all five stages) via the API and receive a session marked complete.
2. Each of the three client-facing report types (consumer, coaching, adviser) can be generated as a PDF from a completed test session — **and** the Internal AI Profile is generated automatically alongside them, every time, without being requested.
3. **Patrick can change a stage's question wording, a scoring weight, or a report section heading by editing a YAML file and redeploying — with no Python file needing to change.** This is the single most important test of whether the configuration-over-code goal was actually achieved, and should be demonstrated with at least one real example before this plan is considered done (e.g., reword one Visionary-stage question and confirm it shows up in the next test conversation).
4. The service runs continuously on the VPS as a systemd service, independent of CommandOS, and survives a server reboot.
5. `context/gaia/` and `gtd/projects.md` accurately reflect that this work is done and what remains (frontend embed, real CRM/email integration is built per the confirmed simple stack, BEA-intervention layer — Phase 5/6).
6. No content in `config/stages.yaml` can be traced to CEG's Total Client Profile guide, Covey's 7 Habits, or ActionCoach materials — verified by Patrick's own review, since he is the one with direct knowledge of those source materials.
7. A future Claude session (or human developer) with no memory of this conversation could read `docs/titan-lifemap-architecture.md` and `docs/titan-lifemap-config-guide.md` and understand how to safely modify the system without re-reading every line of code.

---

## Notes

- **Frontend embed (website widget) is explicitly out of scope for this plan.** This plan builds and deploys the backend API only, reachable at `api.sustain-momentum.com`. A follow-up plan should cover the WordPress/10Web-side JavaScript widget — the technical path (website as presentation layer calling the API) is confirmed feasible, but the specific embed mechanism is deferred.
- **Phase 5 (workflow integration) is now built for real** against Patrick's confirmed simple stack (Google Workspace + Make.com + database, no CRM) — not stubbed, per the revised plan. **Phase 6** (cashflow modelling, full GAIA platform, BEA accountability/intervention engine) remains documented-only, not built, since it depends on Phases 1-4 being proven with real usage first.
- **Branding/visual design is placeholder.** Report styling, color scheme, and any logo usage should be revisited once Patrick has Titan Mindset brand guidelines to share — not blocking for functional completion of this plan.
- This plan deliberately avoided reading deeper into the Titan Mindset manuscript PDFs beyond what Patrick already typed directly in conversation, since his direct description is authoritative and avoids any risk of the plan itself being built from a hard-to-parse or incomplete extraction.
- **Configuration-over-code is a constraint added before implementation began**, per Patrick's explicit instruction: "Build for adaptability rather than optimisation... create Version 1 quickly, test it with real users, then iterate rapidly." Every step above was rewritten against this constraint rather than treating it as a later refactor — this matters because retrofitting config-driven architecture onto already-hardcoded logic is significantly more expensive than building it that way from the start.
- **The Internal AI Profile is the most architecturally significant addition.** Per Patrick: "The client sees the report. GAIA sees the person." Any future plan involving personalization, returning users, or cross-session memory should treat `titan_internal_profiles` as the foundational data source — this is explicitly designed to outlast any individual report format or even the Titan LifeMap product itself.

---

## Implementation Notes

**Implemented:** 2026-06-23

### Summary

- Steps 1-4 (context docs, IP boundary, data model, DB schema): committed during initial implementation pass
- Steps 5-6 (all config YAML files, conversation engine, FastAPI app): committed in one batch — pyyaml install unblocked after PowerShell `| tail` issue resolved
- Steps 7-9 (analysis engine, four report generators, routing layer): committed together
- Steps 10-12 (VPS deployment doc, CLAUDE.md, HISTORY.md, plan status): final wrap-up commit

Config validated at every step: `python apps/titan_lifemap/config_loader.py` outputs "All config valid. 5 stages loaded: ['visionary', 'sage', 'builder', 'steward', 'guardian']"

All imports verified in .venv. DB migration for `conversation_history` column handled via ALTER TABLE on first connect.

### Deviations from Plan

- `conversation.py` uses the Anthropic messages API directly rather than the Claude Agent SDK — the Agent SDK is designed for agentic file-reading tasks, not real-time chat. This is the correct architecture for a user-facing conversation.
- `reports/internal.py` is a read/formatting module (reads from titan_internal_profiles written by analysis.py) rather than a report generator — the Internal AI Profile is produced entirely in analysis.py as the second JSON block of the analysis pass, which is cleaner than a separate generation call.
- Stage completion detection uses `[STAGE_COMPLETE]` sentinel in Claude's response. This is a simple, reliable convention documented in `prompts/conversation.yaml`.
- WeasyPrint system library installation (libpango etc.) deferred to VPS deployment step — not blocking for local import validation.

### Issues Encountered

- pyyaml not installed in .venv: resolved by running `pip install -q pyyaml` without PowerShell's `| tail` pipe (which caused silent failure)
- DB already existed without `conversation_history` column: resolved with ALTER TABLE migration in `init_db()` on first connect
