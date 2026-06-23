# System: Titan LifeMap

> A configuration-driven, multi-stage AI discovery engine for GAIA. Backend API serving Sustain Momentum's website.

## Architecture

```
[Website widget] --> [FastAPI app: main.py] --> [conversation.py] --> [Claude Agent SDK]
                                                       |
                                                       v
                                              [config_loader.py] <-- [config/*.yaml]
                                                       |
                                                       v
                                                   [db.py] --> data/data.db (titan_* tables)
                                                       |
                          (on completion)              v
                            +----------------- [analysis.py] -- scoring_rules.yaml
                            |                          |
                            v                          v
                   [reports/engine.py] <----- [config/report_templates/*.yaml]
                            |
        +-------------------+-------------------+----------------------+
        v                   v                   v                      v
  reports/consumer.py  reports/coaching.py  reports/adviser.py   reports/internal.py
   (client-facing,      (client-facing,      (client-facing,      (NEVER client-facing,
    via API endpoint)    via API endpoint)    via API endpoint)    no API exposure at all)
                            |
                            v
                      [routing.py] --> Google Workspace email, Make.com webhook, titan_leads table
```

**Core principle:** content (questions, scoring weights, report structure, prompts) lives in `config/*.yaml`. Application code only contains structural logic (loading config, calling Claude, writing to DB, rendering PDFs). See `docs/titan-lifemap-config-guide.md` for the config schema reference.

## Key Files

| File | Purpose |
|------|---------|
| `apps/titan_lifemap/config_loader.py` | The only module that reads YAML directly. Exposes `get_stages()`, `get_scoring_rules()`, `get_prompt(name)`, `get_report_template(name)`. Fails loudly on missing/malformed config. |
| `apps/titan_lifemap/models.py` | Pydantic models: `Session`, `SoftFacts`, `HardFacts`, `ScoringResult`, `TitanProfile`. Structural contracts only, no content. |
| `apps/titan_lifemap/db.py` | SQLite tables in the shared `data/data.db`: `titan_sessions`, `titan_soft_facts`, `titan_hard_facts`, `titan_scores`, `titan_internal_profiles`, `titan_leads`. |
| `apps/titan_lifemap/config/stages.yaml` | The five discovery stages (data, not code) |
| `apps/titan_lifemap/conversation.py` | Conversation orchestration engine *(built in a later implementation step)* |
| `apps/titan_lifemap/analysis.py` | Scoring/analysis layer *(built in a later implementation step)* |
| `apps/titan_lifemap/reports/` | Four report generators (consumer, coaching, adviser, internal) *(built in a later implementation step)* |
| `apps/titan_lifemap/routing.py` | Email/webhook/lead-storage workflow *(built in a later implementation step)* |
| `apps/titan_lifemap/main.py` | FastAPI app entry point *(built in a later implementation step)* |

## How It Works

1. A website visitor starts a Titan LifeMap session anonymously (no contact details required).
2. `conversation.py` walks them through five stages, loaded from `config/stages.yaml` via `config_loader.get_stages()`: Visionary → Sage → Builder → Steward → Guardian. First name + email are requested entering the Steward stage, not before.
3. Each stage's answers are written to `titan_soft_facts` (or `titan_hard_facts` from Steward onward) via `db.py`.
4. On completion, `analysis.py` runs a Claude-driven pass — using `config/scoring_rules.yaml` for weights, never hardcoded — producing the Behavioural Friction Profile, Titan Clarity Score, and Titan Momentum Plan, saved to `titan_scores`.
5. Four reports are generated: three client-facing (consumer/coaching/adviser, depending on the session's `route`) via API-exposed endpoints, and **one Internal AI Profile generated automatically every time, with no API endpoint that can return it** — see `reports/internal.py`.
6. `routing.py` stores the lead, emails the appropriate client-facing report via Google Workspace, and fires a Make.com webhook for any downstream automation Patrick wants to build himself.

## Configuration

See `docs/titan-lifemap-config-guide.md` for the full schema of every YAML file. Quick reference:

| File | Controls |
|------|----------|
| `config/stages.yaml` | The five discovery stages, questions, framing |
| `config/scoring_rules.yaml` | Clarity Score, Momentum Plan, Behavioural Friction weights |
| `config/prompts/*.yaml` | Claude system prompts for conversation/analysis/reports |
| `config/report_templates/*.yaml` | Section structure for each of the four report types |

`.env` variables (loaded via `apps/titan_lifemap/config.py`, not yet built as of this doc entry): Anthropic API key (reused from the workspace `.env`), Google Workspace SMTP credentials, Make.com webhook URL.

## Common Operations

**Initialize/verify the database:**
```bash
python apps/titan_lifemap/db.py
```

**Validate all config files:**
```bash
python apps/titan_lifemap/config_loader.py
```

**Run the API locally** *(once main.py exists)*:
```bash
uvicorn apps.titan_lifemap.main:app --reload
```

## Dependencies

- **Depends on:** the shared `data/data.db` (DataOS), the Claude Agent SDK patterns proven in `apps/command/` (CommandOS), `scripts/config.py`'s `.env`/cert-fix pattern.
- **Used by:** the Sustain Momentum website (via a future frontend embed, not yet built) and, eventually, the broader GAIA platform via the Internal AI Profile memory layer.

## History

| Date | Change |
|------|--------|
| 2026-06-23 | Initial documentation — data model, db schema, and config loader built and tested. Six tables confirmed created in `data/data.db`. |
