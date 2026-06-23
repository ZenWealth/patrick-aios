"""
Titan LifeMap - Report Engine

Shared rendering logic used by all four report generators:
  consumer.py, coaching.py, adviser.py, internal.py

Workflow per report:
  1. Load the report template YAML (section structure + instructions)
  2. Call Claude to generate narrative content for each section
  3. Render the content into a Jinja2 HTML template
  4. Convert to PDF using WeasyPrint

The Internal AI Profile follows the same pipeline but is never exposed
via any API endpoint. See reports/internal.py.
"""

import logging
from pathlib import Path

import anthropic
from jinja2 import Environment, FileSystemLoader

from apps.titan_lifemap.config import ANTHROPIC_API_KEY
from apps.titan_lifemap.config_loader import get_report_template, get_prompt

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


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


def generate_sections(
    report_type: str,
    session_data: dict,
) -> dict[str, str]:
    """Generate narrative content for every section in the report template.

    Returns a dict mapping section id -> generated text.
    """
    report_config = get_report_template(report_type)
    prompt_config = get_prompt("reports")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    session_data["report_type"] = report_type
    section_content = {}

    for section in report_config["sections"]:
        section_id = section["id"]
        prompt = _build_section_prompt(section, session_data, report_config, prompt_config)

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        section_content[section_id] = response.content[0].text
        logger.debug("Generated section '%s' for %s report", section_id, report_type)

    return section_content


def render_html(
    report_type: str,
    session_data: dict,
    section_content: dict[str, str],
) -> str:
    """Render section content into the HTML template for this report type."""
    report_config = get_report_template(report_type)
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
) -> bytes | str:
    """Full pipeline: generate sections → render HTML → optionally convert to PDF.

    Args:
        report_type: One of 'consumer', 'coaching', 'adviser', 'internal'
        session_data: Dict with keys: session, soft_facts, hard_facts, scores
        as_pdf: If True, return PDF bytes. If False, return HTML string.

    Returns PDF bytes or HTML string.
    """
    section_content = generate_sections(report_type, session_data)
    html = render_html(report_type, session_data, section_content)
    if as_pdf:
        return render_pdf(html)
    return html
