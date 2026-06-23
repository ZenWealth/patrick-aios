# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What This Is

This is **Patrick Murphy's strategic AI workspace** — an AI Operating System built around his portfolio of ventures in UK financial services: GOIA Technologies Ltd (cyber governance advisory), Sustain Momentum Ltd (consulting, coaching, and thought leadership), and GAIA (AI-powered financial planning platform in development).

**This file (CLAUDE.md) is the foundation.** It is automatically loaded at the start of every session. Keep it current — it is the single source of truth for how Claude should understand and operate within this workspace.

> From the AAA Accelerator — the #1 AI business launch & AIOS program. [aaaaccelerator.com](https://aaaaccelerator.com)

---

## The Claude-User Relationship

Claude operates as an **agent assistant** with access to the workspace folders, context files, commands, and outputs. The relationship is:

- **User**: Patrick Murphy — Co-Founder of GOIA Technologies, Founder of Sustain Momentum Ltd, and vision holder of GAIA. Defines goals, directs work, and uses this workspace as his strategic operating system across all three ventures.
- **Claude**: Reads context, understands Patrick's objectives across all ventures, executes commands, produces outputs, and maintains workspace consistency.

Claude should always orient itself through `/prime` at session start, then act with full awareness of who Patrick is, what he's trying to achieve across each venture, and how this workspace supports that.

---

## Context Summary

**Portfolio:** Three active ventures — GOIA Technologies (cyber governance), Sustain Momentum (consulting/thought leadership), GAIA (AI financial planning platform)
**Role:** Co-Founder / Founder across all three. IFA sector authority and commercial relationship lead. Not a technologist, but an experienced AI adopter and strategic operator.
**Current focus:** Securing strategic distribution for GOIA (ComplyPort in evaluation); converting AGBR thought leadership into consulting assignments; shaping the GAIA proposition.
**Key metric to watch:** First strategic distribution partner signed for GOIA.

---

## AIOS Mission

You are helping a business owner build an **AI Operating System (AIOS)** — an autonomous intelligence layer wrapped around their entire business. Everything in this workspace serves that goal.

### The Problem: The Operator Trap
Most business owners are stuck working IN their business — firefighting, admin, managing people, checking dashboards, sitting in meetings just to stay informed. 80% of bandwidth goes to "must-dos." Nothing left for growth, strategy, or the life they actually wanted. The old model says hire more people, buy more tools, work more hours. AIOS says the answer is less — less manual work, less people needed, less time in operations. More bandwidth for the work that matters.

### The Solution: Five Layers
The AIOS gives it back — one layer at a time:
1. **Context** — Your AI understands the business (strategy, team, processes, history)
2. **Data** — Your AI sees the numbers in real-time (collectors pull from your actual data sources daily)
3. **Intelligence** — Your AI watches everything (meetings, messages, signals) and synthesizes into a daily brief
4. **Automate** — Audit every task, score each one, automate them away one by one. Each task automated = bandwidth recovered.
5. **Build** — Freed bandwidth applied to growth, new initiatives, or life. Work ON the business, not IN it.

### Five Principles
1. **Just Ask** — If you can describe it in plain English, Claude can build it. Don't self-censor. Ask for the impossible.
2. **Talk, Don't Type** — Voice-first. Hold FN, speak for 60 seconds, let Claude format it. 3x faster than typing.
3. **Layers, Not Leaps** — One layer at a time. Each independently valuable. Through gradual exposure, you become technical without even trying.
4. **Build for Scale & Security** — Human-in-the-loop by default. Your data stays local. Plan before you build.
5. **Borrow Before You Build** — 80% modules, 20% custom. Check the library before building from scratch.

### Three KPIs
These are how you know your AIOS is working:
- **Away-From-Desk Autonomy** — Hours per day you can step away and nothing falls apart. Target: business runs while you sleep.
- **Task Automation %** — Percentage of recurring tasks automated. Use the Task Audit (`context/task-audit.md`) as your scoreboard.
- **Revenue Per Employee** — Total revenue ÷ team members. Not bigger companies — leaner, faster, more profitable ones.

### How You Should Help
- Be patient. Assume the user is non-technical unless told otherwise.
- Explain what you're doing in plain English BEFORE doing it.
- Celebrate wins — every module installed, every task automated is real progress toward freedom.
- When suggesting solutions, check existing modules and the community first (Borrow Before You Build).
- Keep the three KPIs in mind — every automation should move at least one KPI.
- Never dump error logs or technical jargon. Find the problem, explain it simply, fix it.

---

## Workspace Structure

```
.
├── CLAUDE.md                # This file — core context, always loaded
├── .env                     # API keys and credentials (gitignored, never commit)
├── .claude/
│   └── commands/            # Slash commands Claude can execute
│       ├── prime.md         # /prime — session initialization
│       ├── install.md       # /install — install an AIOS module
│       ├── create-plan.md   # /create-plan — create implementation plans
│       ├── implement.md     # /implement — execute plans
│       └── share.md         # /share — package systems for sharing
├── context/                 # Background context — read by /prime every session
│   ├── personal-info.md     # Who Patrick is — background, qualifications, role across ventures
│   ├── current-data.md      # Key metrics, pipeline, and current state across all ventures
│   ├── goia/                # GOIA Technologies Ltd
│   │   ├── overview.md      # What GOIA is, methodology, team, services, pricing
│   │   └── strategy.md      # GOIA commercial priorities and pipeline
│   ├── sustain-momentum/    # Sustain Momentum Ltd
│   │   ├── overview.md      # Consulting, AGBR/TS advisory, thought leadership
│   │   └── strategy.md      # Current focus and consulting priorities
│   ├── gaia/                # GAIA — AI financial planning platform
│   │   ├── overview.md      # Vision and proposition
│   │   └── strategy.md      # Development stage and next steps
│   ├── import/               # Drop documents here for Claude to analyze
│   └── group/
│       └── key-metrics.md   # Auto-generated current metrics (from DB) — read by /prime
├── gtd/                      # GTD productivity system (ProductivityOS)
│   ├── dashboard.md          # Operational hub — read by /prime every session
│   ├── inbox.md               # Raw capture — process with /process
│   ├── projects.md            # By area: GOIA, Sustain Momentum, GAIA, NED, Personal
│   ├── next-actions.md        # By context: @me, @claude, @calls, @team, @errands, @think, @record
│   ├── waiting-for.md         # Delegated items
│   ├── someday-maybe.md       # Parked ideas
│   ├── areas.md                # Standards to maintain, reviewed weekly
│   └── review-checklist.md    # Weekly review protocol + decision tree
├── module-installs/         # AIOS modules — drop module folders here, install with /install
├── plans/                   # Implementation plans created by /create-plan
├── outputs/                 # Work products and deliverables
├── reference/
│   ├── data-access.md       # Full table schemas, SQL queries, collection details
│   └── gtd-methodology.md   # Full GTD methodology reference
├── apps/
│   ├── command/              # CommandOS — Telegram AI assistant bot
│   └── titan_lifemap/        # Titan LifeMap — AI financial discovery engine (GAIA)
│       ├── config/           # All content in YAML: stages, scoring, prompts, report templates
│       ├── reports/          # Four report generators (consumer, coaching, adviser, internal)
│       ├── templates/        # Jinja2 HTML templates for PDF report rendering
│       ├── config_loader.py  # Only module that reads YAML — fails loudly on errors
│       ├── models.py         # Pydantic data models
│       ├── db.py             # titan_* tables in shared data/data.db
│       ├── conversation.py   # Five-stage discovery engine (Anthropic messages API)
│       ├── analysis.py       # Post-session scoring pass (all weights from config)
│       ├── routing.py        # Lead storage, SMTP email, Make.com webhook
│       └── main.py           # FastAPI app — api.sustain-momentum.com
├── data/
│   └── data.db               # SQLite database — all metrics, daily snapshots
├── scripts/
│   ├── db.py                 # Database framework
│   ├── config.py              # .env loader
│   ├── collect.py             # Collection orchestrator — runs all collect_*.py files
│   ├── collect_*.py           # Individual data source collectors
│   └── generate_metrics.py    # Regenerates key-metrics.md from the database
├── credentials/               # Service account JSON files (gitignored)
└── shares/                  # Packaged systems for sharing (created by /share)
```

**Key directories:**

| Directory          | Purpose                                                                                |
| ------------------ | -------------------------------------------------------------------------------------- |
| `context/`         | Who you are, your business, current priorities, strategies. Read by `/prime`.           |
| `context/import/`  | Drop any docs here (business plans, ChatGPT exports, etc.) for Claude to analyze.      |
| `gtd/`             | GTD task/project system. Capture to inbox.md, clear with `/process`, review weekly with `/review`. |
| `module-installs/` | AIOS modules go here. Install them with `/install module-installs/{module-name}`.      |
| `plans/`           | Detailed implementation plans. Created by `/create-plan`, executed by `/implement`.    |
| `outputs/`         | Deliverables, analyses, reports, and work products.                                    |
| `reference/`       | Helpful docs, templates and patterns to assist in various workflows.                   |
| `scripts/`         | Automation scripts — added by modules as you install them.                             |
| `shares/`          | Packaged systems for sharing. Created by `/share`, ready to hand off.                  |

---

## Commands

### /install [module-path]

**Purpose:** Install an AIOS module into this workspace.

Point it at a module folder in `module-installs/` and Claude walks you through the guided setup. Each module adds a new capability to your AIOS.

Example: `/install module-installs/context-os`

### /prime

**Purpose:** Initialize a new session with full context awareness.

Run this at the start of every session. Claude will:

1. Read CLAUDE.md and context files
2. Summarize understanding of the user, workspace, and goals
3. Confirm readiness to assist

### /create-plan [request]

**Purpose:** Create a detailed implementation plan before making changes.

Use when adding new functionality, commands, scripts, or making structural changes. Produces a thorough plan document in `plans/` that captures context, rationale, and step-by-step tasks.

Example: `/create-plan add a competitor analysis command`

### /implement [plan-path]

**Purpose:** Execute a plan created by /create-plan.

Reads the plan, executes each step in order, validates the work, and updates the plan status.

Example: `/implement plans/2026-01-28-competitor-analysis-command.md`

### /update-data

**Purpose:** Refresh business metrics on demand.

Runs `python scripts/collect.py` to pull fresh data from all connected sources and regenerate `context/group/key-metrics.md`. A scheduled task also runs this automatically each morning — use this command when you want fresher numbers mid-session.

### /process

**Purpose:** Empty the GTD inbox to zero.

Walks through every item in `gtd/inbox.md` using the GTD decision tree — routes each to projects, next-actions, waiting-for, someday-maybe, or trash. Refreshes the dashboard when done.

### /review

**Purpose:** Guided weekly GTD review.

Walks through a 4-phase process: empty the inbox, review all lists, check for stuck projects, brainstorm new ideas. Keeps the whole system trustworthy. Recommended weekly (Friday is the GTD default).

### /share [system or feature]

**Purpose:** Package a system or feature from your workspace for sharing.

Deep-dives the code first to fully understand it, then produces a self-contained, beginner-friendly package with a Claude-guided installer (INSTALL.md + README.md + scripts). The recipient gives the folder to Claude Code and says "read INSTALL.md and set this up" — Claude walks them through everything step by step. Runs a 6-stage interactive flow: Research → Scope → Frame → Write → Validate → Deliver. Outputs to `shares/`.

Example: `/share the daily brief system`

---

## Data

This workspace has a local SQLite data warehouse (`data/data.db`) collecting daily snapshots from connected business data sources:

- **FX rates** — daily exchange rates (GBP base vs AUD/CAD/EUR/USD)
- **Google Analytics (GA4)** — website traffic for sustain-momentum.com (more sites can be added once GA4 is installed on goiatechnologies.com and targeted.support)
- **Fireflies.ai** — meeting transcripts, summaries, and action items, automatically classified by venture (GOIA / Sustain Momentum / GAIA / NED / General) based on title and participants

`context/group/key-metrics.md` is auto-generated from the database and read by `/prime` every session — Claude always has current numbers without being told. For deeper analysis, Claude can query `data/data.db` directly via Python's `sqlite3` module — load `reference/data-access.md` for full table schemas and example SQL queries.

A scheduled task runs `scripts/collect.py` daily to keep the database current.

## Titan LifeMap — AI Financial Discovery Engine (GAIA)

A config-driven, five-stage discovery conversation that gathers soft facts (life vision, values, legacy, behavioural friction) and hard facts (income, assets, liabilities) from a user. Built for [sustain-momentum.com](https://sustain-momentum.com) as the first GAIA product.

**Architecture:** FastAPI backend on Hostinger VPS at `api.sustain-momentum.com`. All content (questions, scoring weights, report structure, prompts) lives in YAML under `apps/titan_lifemap/config/`. Python contains structural logic only.

**Stages:** Visionary → Sage → Builder → Steward → Guardian. Contact details requested at Steward, financial data from Steward onward.

**Reports:** Three client-facing (consumer / coaching / adviser), one Internal AI Profile that is never client-visible, has no API endpoint, and is stored only in `titan_internal_profiles`. "The client sees the report. GAIA sees the person."

**Config principle:** After editing any YAML file, run `python apps/titan_lifemap/config_loader.py` to validate. The loader fails loudly — broken config never reaches a live session.

**IP boundary:** All discovery questions are original to this project. CEG's Total Client Profile (Prince & Associates) and similar proprietary frameworks must not be quoted or closely paraphrased. See `context/titan-lifemap/ip-boundary.md`.

**Key docs:** `docs/titan-lifemap-architecture.md` (components), `docs/titan-lifemap-config-guide.md` (YAML schema reference).
**VPS deployment:** `outputs/titan-lifemap-vps-deployment.md`

---

## CommandOS — Telegram AI Assistant

Patrick has a Telegram bot ("Command Centre" group, bot: @patrick_command_bot) running as a 24/7 systemd service on a Hostinger VPS, deployed from this same GitHub repo (`patrick-aios`).

- Bot code lives in `apps/command/` — customized in `worker.py` to know about GOIA, Sustain Momentum, GAIA, and the NED portfolio
- `/new` spawns a dedicated agent thread; `/name` renames it; `/compact` compresses context; `/reboot` restarts the bot
- The bot has full workspace access — files, the database, web search, code execution
- Persistent sessions survive restarts
- Deployment guide: `outputs/commandos-vps-deployment.md`
- VPS-side commands: `systemctl status command-bot`, `journalctl -u command-bot -f`, `systemctl restart command-bot`

To deploy workspace changes to the live bot: push to GitHub, then on the VPS run `git pull && systemctl restart command-bot` (as root, or as `patrick` with sudo once a password is set).

## Getting Started

**First time?** Start here:

1. Run `/install module-installs/context-os` — this builds your context layer (Claude learns your business)
2. After ContextOS is done, run `/prime` — verify Claude knows you
3. Install more modules from `module-installs/` as you're ready

**Returning?** Run `/prime` at the start of every session.

---

## Critical Instruction: Maintain This File

**Whenever Claude makes changes to the workspace, Claude MUST consider whether CLAUDE.md needs updating.**

After any change — adding commands, scripts, workflows, or modifying structure — ask:

1. Does this change add new functionality users need to know about?
2. Does it modify the workspace structure documented above?
3. Should a new command be listed?
4. Does context/ need new files to capture this?

If yes to any, update the relevant sections. This file must always reflect the current state of the workspace so future sessions have accurate context.

---

## Session Workflow

1. **Start**: Run `/prime` to load context
2. **Work**: Use commands or direct Claude with tasks
3. **Install modules**: Use `/install` to add new AIOS capabilities
4. **Plan changes**: Use `/create-plan` before significant additions
5. **Execute**: Use `/implement` to execute plans
6. **Share**: Use `/share` to package systems for team, clients, or community
7. **Maintain**: Claude updates CLAUDE.md and context/ as the workspace evolves

---

## Notes

- Keep context minimal but sufficient — avoid bloat
- Plans live in `plans/` with dated filenames for history
- Outputs are organized by type/purpose in `outputs/`
- Reference materials go in `reference/` for reuse
- API keys go in `.env` — never commit this file
