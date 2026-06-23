# Config Guide: Titan LifeMap

> Reference for every YAML file under `apps/titan_lifemap/config/`.
> Read this before editing any config file.

**Core rule:** Application code (`conversation.py`, `analysis.py`, `reports/`) contains only structural logic. All content — questions, scoring weights, report section instructions, Claude prompts — lives here. Changing behaviour means changing YAML, not Python.

**After any config edit:** run `python apps/titan_lifemap/config_loader.py` to validate. The loader fails loudly on missing/malformed files.

---

## stages.yaml

Controls the five-stage discovery sequence.

**Location:** `apps/titan_lifemap/config/stages.yaml`

**Schema per stage:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `name` | string | Yes | Internal identifier (used in DB, code). Lowercase. |
| `titan` | string | Yes | Which of the Seven Titans this stage embodies (display value). |
| `display_name` | string | No | Human-readable name for any future UI. |
| `framing` | string | Yes | The intro Claude reads when entering this stage. |
| `questions` | list[string] | Yes | The original open questions for this stage. Claude may ask follow-ups — see `prompts/conversation.yaml`. |
| `soft_fact_outputs` | list[string] | No | Which `SoftFacts` model fields this stage populates. Must match field names in `models.py`. |
| `output_name` | string | Yes | Named artifact(s) produced by this stage (for display/documentation). |
| `requests_contact` | bool | No | Set to `true` for the Steward stage only — this is where first name + email are requested. |
| `captures_hard_facts` | bool | No | Set to `true` for Steward and Guardian stages. |

**Stage order matters** — conversation.py reads them in sequence: Visionary → Sage → Builder → Steward → Guardian.

**IP boundary:** All question content must be original. See `context/titan-lifemap/ip-boundary.md` before adding or rewriting questions. CEG's Total Client Profile questions (Prince & Associates research) are protected and must not be quoted or closely paraphrased.

---

## scoring_rules.yaml

Controls the analysis layer: Clarity Score, Momentum Plan, Behavioural Friction Profile.

**Location:** `apps/titan_lifemap/config/scoring_rules.yaml`

**Top-level keys (all required):**

| Key | Description |
|-----|-------------|
| `behavioural_friction` | Pattern definitions, labels, and weights for the six BFP patterns. |
| `clarity_score` | Component weights and scale thresholds for the Titan Clarity Score. |
| `momentum_plan` | Rules for generating the Momentum Plan (max actions, categories). |

**Behavioural Friction patterns** (six fixed patterns — these are diagnostic categories, not a framework):
`procrastination`, `avoidance`, `overthinking`, `impulsiveness`, `delegation`, `lack_of_confidence`

The BFP is diagnosis only, kept explicitly separate from BEA (intervention framework). Do not add intervention language here.

**Clarity Score components** must sum weights to 1.0. Current: vision_clarity (0.25), values_alignment (0.20), legacy_intention (0.20), money_relationship (0.20), friction_awareness (0.15).

---

## prompts/conversation.yaml

Claude's system prompt and instructions for the conversation engine.

**Location:** `apps/titan_lifemap/config/prompts/conversation.yaml`

**Keys:**

| Key | Description |
|-----|-------------|
| `system_prompt` | The main system prompt given to Claude at session start. Sets tone, role, approach. |
| `stage_transition_instruction` | How Claude should handle moving between stages. |
| `contact_request_instruction` | When and how to ask for first name + email (Steward stage only). |
| `completion_instruction` | How to close the session after the Guardian stage. |

**Tone principle:** warm, unhurried, non-judgmental. One question at a time. Never formulaic.

---

## prompts/analysis.yaml

Claude's system prompt for the post-session scoring pass.

**Location:** `apps/titan_lifemap/config/prompts/analysis.yaml`

**Keys:**

| Key | Description |
|-----|-------------|
| `system_prompt` | Instructs Claude to produce Clarity Score, Momentum Plan, and Behavioural Friction scores. |
| `output_schema` | JSON schema definition for the required output. |
| `internal_profile_instruction` | Additional instruction for the Internal AI Profile section of the analysis pass. |

Analysis.py passes the session data + scoring_rules.yaml weights to Claude. Weights never appear in Python code.

---

## prompts/reports.yaml

Claude's system prompt and tone guidance for the report generation pass.

**Location:** `apps/titan_lifemap/config/prompts/reports.yaml`

**Keys:**

| Key | Description |
|-----|-------------|
| `system_prompt` | Core instruction for report writing: voice, tone, how to use client's own words. |
| `consumer_tone_note` | Specific tone guidance for the consumer report. |
| `adviser_tone_note` | Specific tone guidance for the adviser briefing. |
| `internal_tone_note` | Specific tone guidance for the Internal AI Profile. |

---

## report_templates/

Four report template files, one per report type.

**Location:** `apps/titan_lifemap/config/report_templates/`

**Files:**
- `consumer.yaml` — client-facing personal report
- `coaching.yaml` — coaching engagement report
- `adviser.yaml` — adviser pre-meeting briefing
- `internal.yaml` — Internal AI Profile (never client-visible)

**Schema per template:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `report_title` | string | Yes | Report heading. |
| `subtitle` | string | No | Secondary heading. |
| `sections` | list | Yes | Ordered list of report sections. |

**Schema per section:**

| Key | Type | Description |
|-----|------|-------------|
| `id` | string | Internal identifier for this section. |
| `title` | string | Section heading shown in the report. |
| `instruction` | string | Instruction to Claude for generating this section's content. |
| `source_field` | string | (Optional) Single `SoftFacts` or `HardFacts` field that feeds this section. |
| `source_fields` | list[string] | (Optional) Multiple fields that feed this section. |

**Internal AI Profile access restriction:**
The `internal.yaml` template carries an `access_restriction` key. This is documentation only — enforcement is in `reports/internal.py`, which has no API endpoint. The restriction must never be loosened.

---

## History

| Date | Change |
|------|--------|
| 2026-06-23 | Initial config guide — all five config categories documented. |
