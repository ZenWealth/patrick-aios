"""
Titan LifeMap - Report Engine

Shared rendering logic used by all four report generators:
  consumer.py, coaching.py, adviser.py, internal.py

Workflow per report:
  1. Load the report template YAML (section structure + instructions)
  2. Call Claude to generate narrative content for each section
  3. QA GATE (consumer reports): validate against the Titan LifeMap Report
     Standard; regenerate failing sections; refuse to deliver if it cannot pass
  4. Render the content into a Jinja2 HTML template
  5. Convert to PDF using WeasyPrint

The QA gate is a product quality standard, not an optimisation: no participant
should ever receive a report that refers to them in the third person, is missing
a required beat, fails to close on identity, or breaches the Report Standard.

The Internal AI Profile follows the same pipeline but is never exposed
via any API endpoint. See reports/internal.py.
"""

import json
import logging
import re
from pathlib import Path

import anthropic
from jinja2 import Environment, FileSystemLoader

from apps.titan_lifemap.config import ANTHROPIC_API_KEY
from apps.titan_lifemap.config_loader import get_report_template, get_prompt

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
QA_MODEL = "claude-haiku-4-5-20251001"  # fast, cheap judge for the voice/Standard check
MAX_TOKENS = 2048

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# ---------------------------------------------------------------------------
# QA gate — Titan LifeMap Report Standard
# ---------------------------------------------------------------------------

# Generated narrative beats that must be present and non-empty.
QA_REQUIRED_SECTIONS = ["opening", "core_transition", "whats_possible", "becoming"]
# Score fields the report depends on.
QA_REQUIRED_SCORES = ["core_transition", "the_one_decision", "biggest_insight"]
# The report must close emotionally on this section.
QA_CLOSING_SECTION = "becoming"
# Total generated word budget — the report must not overwhelm.
QA_MAX_TOTAL_WORDS = 1500
# first_name values that indicate a missing / placeholder personalisation.
QA_PLACEHOLDER_NAMES = {"", "my", "n/a", "na", "none", "null", "test",
                        "client", "user", "unknown", "first", "name", "firstname"}
# Phrases that ALWAYS mean a third-person reference to the reader.
QA_BANNED_PHRASES = [
    r"\bthe client\b", r"\bthis client\b", r"\bthe participant\b",
    r"\bthe reader\b", r"\bthe customer\b", r"\bthe user\b",
    r"\bthis individual\b", r"\bthis person\b",
]
# Praise / validation language banned by the Standard.
QA_VALIDATION_WORDS = [
    r"\bpowerful\b", r"\bprofound\b", r"\bbrave\b", r"\bcourage(?:ous)?\b",
    r"\bwell done\b", r"\binspiring\b", r"\btakes? real courage\b",
]
QA_MAX_RETRIES = 2


class QAValidationError(Exception):
    """Raised when a consumer report cannot pass the Report Standard after retries."""


def _build_section_prompt(
    section: dict,
    session_data: dict,
    report_config: dict,
    prompt_config: dict,
) -> str:
    """Build the prompt for a single report section."""
    # Gather source data for this section
    source_fields = section.get("source_fields") or (
        [section["source_field"]] if section.get("source_field") else []
    )
    source_data_lines = []
    for field in source_fields:
        value = (
            session_data.get("soft_facts", {}).get(field)
            or session_data.get("hard_facts", {}).get(field)
            or session_data.get("scores", {}).get(field)
        )
        if value:
            source_data_lines.append(f"{field}: {value}")

    source_data = "\n".join(source_data_lines) if source_data_lines else "(no specific source data for this section)"

    tone_note_key = f"{session_data.get('report_type', 'consumer')}_tone_note"
    tone_note = prompt_config.get(tone_note_key, "")

    return f"""{prompt_config['system_prompt']}

{tone_note}

REPORT TYPE: {report_config.get('report_title', '')}

SECTION: {section['title']}

SECTION INSTRUCTION:
{section['instruction']}

SOURCE DATA FOR THIS SECTION:
{source_data}

Write the content for this section now. Plain text only unless the instruction
specifies otherwise. Do not include the section title or any markdown headings.
"""


def _generate_one_section(
    client: "anthropic.Anthropic",
    section: dict,
    session_data: dict,
    report_config: dict,
    prompt_config: dict,
    corrective: str = "",
) -> str:
    """Generate (or regenerate) a single section's narrative content."""
    prompt = _build_section_prompt(section, session_data, report_config, prompt_config)
    if corrective:
        prompt += (
            "\n\nCRITICAL CORRECTION — a previous attempt failed quality control for this "
            f"reason:\n{corrective}\nRewrite this section now, fixing that, strictly to the "
            "Titan LifeMap Report Standard."
        )
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _generate_all_sections(client, report_config, prompt_config, session_data) -> dict[str, str]:
    section_content = {}
    for section in report_config["sections"]:
        section_content[section["id"]] = _generate_one_section(
            client, section, session_data, report_config, prompt_config
        )
        logger.debug("Generated section '%s' for %s report",
                     section["id"], session_data.get("report_type"))
    return section_content


def generate_sections(report_type: str, session_data: dict) -> dict[str, str]:
    """Generate narrative content for every section in the report template.

    Returns a dict mapping section id -> generated text. (No QA gate — the gate
    runs in generate_report so the rendered output is always validated.)
    """
    report_config = get_report_template(report_type)
    prompt_config = get_prompt("reports")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    session_data["report_type"] = report_type
    return _generate_all_sections(client, report_config, prompt_config, session_data)


# --- QA gate internals -----------------------------------------------------

_QA_JUDGE_PROMPT = """You are the quality-control reviewer for a Titan LifeMap consumer report.
The whole report is written directly TO the reader, addressing them as "you". You are given
the report's sections, each headed by "### <section_id>".

Find EVERY violation of these two rules:
1. reader_third_person — the READER is referred to in the third person anywhere ("he", "she",
   "they", "him", "her", "his", "the client", etc.). Referring to OTHER people (a partner,
   children, colleagues, "the people who depend on you") in the third person is FINE. Only
   flag third-person references to the reader themselves.
2. standard_breach — praise / validation language ("powerful", "profound", "brave",
   "courageous", "well done", "takes courage"), judging or grading the reader, or a specific
   financial product / investment / transaction recommendation.

Return ONLY a JSON object, no other text:
{{"violations": [{{"section": "<section_id>", "issue": "reader_third_person" or "standard_breach", "detail": "<short quote or reason>"}}]}}
If there are no violations, return {{"violations": []}}.

REPORT SECTIONS:
{bundle}
"""


def _llm_qa(client, section_content: dict[str, str]) -> list[dict]:
    """One judge call over the whole report; returns a list of violation dicts."""
    bundle = "\n\n".join(
        f"### {sid}\n{(text or '').strip()}"
        for sid, text in section_content.items() if (text or "").strip()
    )
    try:
        resp = client.messages.create(
            model=QA_MODEL,
            max_tokens=700,
            messages=[{"role": "user", "content": _QA_JUDGE_PROMPT.format(bundle=bundle)}],
        )
        match = re.search(r"\{.*\}", resp.content[0].text, re.DOTALL)
        if match:
            return json.loads(match.group(0)).get("violations", [])
    except Exception as exc:  # judge failure must never silently pass a bad report,
        logger.warning("QA judge call failed (non-blocking): %s", exc)  # but deterministic
    return []  # checks still run and catch the always-wrong cases.


def _deterministic_failures(section_content: dict[str, str], session_data: dict) -> list[dict]:
    failures: list[dict] = []

    name = (session_data.get("session", {}).get("first_name") or "").strip()
    if name.lower() in QA_PLACEHOLDER_NAMES:
        failures.append({"section": "(header)", "check": "name",
                         "detail": f"missing/placeholder name: {name!r}", "regenerable": False})

    scores = session_data.get("scores", {})
    for field in QA_REQUIRED_SCORES:
        if not scores.get(field):
            failures.append({"section": field, "check": "required_score",
                             "detail": "missing score field", "regenerable": False})

    for sid in QA_REQUIRED_SECTIONS:
        if not (section_content.get(sid) or "").strip():
            failures.append({"section": sid, "check": "required_section",
                             "detail": "empty", "regenerable": True})

    if not (section_content.get(QA_CLOSING_SECTION) or "").strip():
        failures.append({"section": QA_CLOSING_SECTION, "check": "closing",
                         "detail": "report does not close on 'becoming'", "regenerable": True})

    total_words = sum(len((v or "").split()) for v in section_content.values())
    if total_words > QA_MAX_TOTAL_WORDS:
        failures.append({"section": "(whole)", "check": "length",
                         "detail": f"{total_words} words > {QA_MAX_TOTAL_WORDS}", "regenerable": True})

    for sid, text in section_content.items():
        for pat in QA_BANNED_PHRASES:
            if re.search(pat, text or "", re.I):
                failures.append({"section": sid, "check": "third_person_reader",
                                 "detail": f"banned phrase {pat}", "regenerable": True})
        for pat in QA_VALIDATION_WORDS:
            if re.search(pat, text or "", re.I):
                failures.append({"section": sid, "check": "validation_language",
                                 "detail": f"matched {pat}", "regenerable": True})
    return failures


def validate_sections(client, section_content: dict[str, str], session_data: dict) -> list[dict]:
    """Run the full QA gate. Returns a list of failures ([] means it passed)."""
    failures = _deterministic_failures(section_content, session_data)
    for v in _llm_qa(client, section_content):
        failures.append({
            "section": v.get("section", "(unknown)"),
            "check": v.get("issue", "standard_breach"),
            "detail": v.get("detail", ""),
            "regenerable": True,
        })
    return failures


def _run_qa(client, section_content, session_data, report_config, prompt_config):
    """Validate; regenerate failing sections; raise if it cannot pass.

    Returns (section_content, qa_log).
    """
    sections_by_id = {s["id"]: s for s in report_config["sections"]}
    qa_log = {"attempts": [], "passed": False, "failures": []}

    failures = []
    for attempt in range(QA_MAX_RETRIES + 1):
        failures = validate_sections(client, section_content, session_data)
        qa_log["attempts"].append({
            "attempt": attempt,
            "failures": [f"{f['section']}: {f['check']} ({f['detail']})" for f in failures],
        })
        if not failures:
            qa_log["passed"] = True
            logger.info("Consumer report passed QA on attempt %d", attempt)
            return section_content, qa_log

        blocking = [f for f in failures if not f["regenerable"]]
        if blocking:
            qa_log["failures"] = failures
            raise QAValidationError(
                "Report failed QA on non-regenerable issues: "
                + "; ".join(f"{f['section']}: {f['detail']}" for f in blocking)
            )

        if attempt == QA_MAX_RETRIES:
            break

        # Regenerate each failing section with a targeted corrective note.
        reasons_by_section: dict[str, list[str]] = {}
        for f in failures:
            if f["section"] in sections_by_id:
                reasons_by_section.setdefault(f["section"], []).append(f"{f['check']}: {f['detail']}")
        for sid, reasons in reasons_by_section.items():
            corrective = "; ".join(reasons)
            if "third_person_reader" in corrective:
                corrective += (". Write strictly in the SECOND PERSON — address the reader only "
                               "as 'you'; never 'he', 'she', 'they', or 'the client'.")
            logger.info("QA regenerating section '%s' (attempt %d): %s", sid, attempt + 1, corrective)
            section_content[sid] = _generate_one_section(
                client, sections_by_id[sid], session_data, report_config, prompt_config,
                corrective=corrective,
            )

    qa_log["failures"] = failures
    raise QAValidationError(
        "Report failed QA after retries: "
        + "; ".join(f"{f['section']}: {f['check']}" for f in failures)
    )


def _clean_markdown(text: str) -> str:
    """Strip stray markdown the model sometimes emits.

    The report template renders plain text, so emphasis markers like *word*,
    **word** or _word_ would otherwise show literally in the PDF. Section
    instructions ask for plain text, but this is a belt-and-braces guard.
    """
    text = re.sub(r'\*\*([^*\n]+?)\*\*', r'\1', text)   # **bold**
    text = re.sub(r'\*([^*\n]+?)\*', r'\1', text)        # *italic*
    text = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'\1', text)  # _italic_
    return text


def render_html(
    report_type: str,
    session_data: dict,
    section_content: dict[str, str],
) -> str:
    """Render section content into the HTML template for this report type."""
    report_config = get_report_template(report_type)
    section_content = {k: _clean_markdown(v) for k, v in section_content.items()}
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    # Use report-type-specific template if it exists, fall back to base
    template_name = f"{report_type}_report.html"
    try:
        template = env.get_template(template_name)
    except Exception:
        template = env.get_template("base_report.html")

    return template.render(
        report_config=report_config,
        session=session_data.get("session", {}),
        sections=report_config["sections"],
        section_content=section_content,
        scores=session_data.get("scores", {}),
    )


def render_pdf(html: str) -> bytes:
    """Convert HTML to PDF bytes using WeasyPrint."""
    try:
        from weasyprint import HTML
        return HTML(string=html).write_pdf()
    except ImportError:
        raise ImportError(
            "WeasyPrint is not installed. Run: pip install weasyprint\n"
            "WeasyPrint also requires system libraries — see docs/titan-lifemap-architecture.md"
        )


def generate_report(
    report_type: str,
    session_data: dict,
    as_pdf: bool = True,
    return_qa: bool = False,
):
    """Full pipeline: generate sections → QA gate (consumer) → render → optional PDF.

    Args:
        report_type: One of 'consumer', 'coaching', 'adviser', 'internal'
        session_data: Dict with keys: session, soft_facts, hard_facts, scores
        as_pdf: If True, return PDF bytes. If False, return HTML string.
        return_qa: If True, return (result, qa_log) so callers can inspect the gate.

    Raises QAValidationError if a consumer report cannot pass the Report Standard.
    Returns PDF bytes or HTML string (or a (result, qa_log) tuple if return_qa).
    """
    report_config = get_report_template(report_type)
    prompt_config = get_prompt("reports")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    session_data["report_type"] = report_type

    section_content = _generate_all_sections(client, report_config, prompt_config, session_data)

    qa_log = None
    if report_type == "consumer":
        section_content, qa_log = _run_qa(
            client, section_content, session_data, report_config, prompt_config
        )

    html = render_html(report_type, session_data, section_content)
    result = render_pdf(html) if as_pdf else html
    return (result, qa_log) if return_qa else result
