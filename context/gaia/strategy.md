# GAIA — Strategy

> Development priorities and next steps for the AI financial planning platform.

---

## Current Stage

**Active build.** Titan LifeMap (see `context/titan-lifemap/overview.md` and `plans/2026-06-23-titan-lifemap-discovery-engine.md`) is GAIA's first product, currently being implemented as a standalone FastAPI backend on the existing VPS.

## Immediate Priorities

- ~~Define the core proposition precisely~~ — **Resolved**: Titan LifeMap, a Behavioural Discovery Engine, consumer-facing first.
- ~~Identify the most compelling first use case~~ — **Resolved**: life clarity before financial planning, via the Seven Titans sequencing (Visionary → Sage → Builder → Steward → Guardian).
- Build vs. partner strategy: building in-house on existing AIOS infrastructure (Claude Agent SDK, VPS), no external platform dependency.
- Regulatory boundary: Titan LifeMap stays explicitly non-regulated — goal-setting, values, life clarity, cash-flow understanding — never specific investment/insurance recommendations. The IFA Referral route is where regulated advice begins, handled by a human adviser, not by Titan LifeMap itself.
- GAIA currently builds within the existing AIOS workspace; whether it needs a separate legal vehicle remains open and is not blocking development.
- Frontend embed into sustain-momentum.com (10Web/WordPress) is a deliberately separate follow-up plan, not yet started.
- Real CRM/adviser-routing integration deferred until Titan LifeMap proves demand with real users (current stack: Google Workspace + Make.com, no CRM).

## Open Questions

- What is the commercialisation model? Subscription, B2B licensing, white-label for advice firms? — Still open; Titan LifeMap's three routes (self-guided, coaching, IFA referral) suggest multiple monetisation paths once usage data exists.
- ~~What is the role of behavioural finance as a differentiator?~~ — **Resolved**: the Behavioural Friction Profile (diagnostic) is a core differentiator, explicitly separate from BEA (intervention) — see `context/titan-lifemap/overview.md`.
- What funding or partnership is needed to move from concept to prototype? — Largely answered: built in-house, no external funding required for v1.
- How does the Internal AI Profile (permanent memory layer) eventually power personalization across repeat visits, coaching engagements, and future GAIA products? Not addressed in this build — flagged in the Titan LifeMap plan's Notes as the natural next architectural question once v1 is proven.

## Longer-Term Vision

GAIA becomes a recognised AI-powered financial planning platform, operating at the intersection of consumer need, regulatory design (AGBR/TS), and AI capability. It serves as the scalable, high-value exit or licensing asset in Patrick's portfolio.

---

_Update as the concept develops and key decisions are made._
