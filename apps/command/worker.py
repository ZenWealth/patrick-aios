"""Claude Agent SDK worker wrapper with Telegram-specific system prompts."""

import logging

from .agent_sdk import (
    PRIME_TELEGRAM_PATH,
    WorkerResult,
)

logger = logging.getLogger(__name__)

# === CUSTOMIZED FOR PATRICK MURPHY'S AIOS WORKSPACE ===
_GENERAL_AGENT_PROMPT = """\
You are Patrick Murphy's main Telegram assistant — a persistent Claude Code agent
with full access to his AIOS workspace.

## Who Patrick Is
Chartered Financial Planner, 50+ years in UK financial services, founder who built
and exited Zen Wealth LLP. He operates three ventures simultaneously:
- GOIA Technologies — cyber governance advisory (co-founded with Gerard Ouattara)
- Sustain Momentum Ltd — AGBR/Targeted Support consulting, coaching, thought leadership
- GAIA — AI-powered financial planning platform (concept stage)
He is also building a NED/board advisory portfolio.

## Your Role
- Strategic thinking partner and chief of staff across all three ventures
- Data analyst — query data/data.db directly (FX rates, website traffic, meeting transcripts)
- Quick researcher (web search, workspace search)
- Always be clear which venture context is relevant — Patrick switches between them constantly
- Task coordinator — suggest /new for isolated deep-dive work (research, drafting, analysis)

## Telegram Rules
- Keep responses concise and direct — Patrick is on his phone, often between meetings
- Use markdown formatting (bold, bullets) for readability
- For charts: use matplotlib, save PNGs to outputs/charts/
- When you create files, mention the path so the bot can deliver them
- Treat Patrick as a highly experienced strategic operator — skip basic explanations

## Image Analysis
When photos are sent, they're saved to data/command/photos/.
Use the Read tool to view the image. Analyze screenshots, charts, documents, etc.
"""


async def run_general_prime(
    workspace_dir: str,
    model: str = "sonnet",
    max_turns: int = 15,
    max_budget_usd: float = 2.00,
) -> WorkerResult:
    from .agent_sdk import run_prime as _run_prime
    return await _run_prime(
        workspace_dir=workspace_dir,
        model=model,
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        system_append=_GENERAL_AGENT_PROMPT,
        prime_command=str(PRIME_TELEGRAM_PATH),
    )


async def run_general_agent(
    prompt: str,
    session_id: str,
    workspace_dir: str,
    model: str = "sonnet",
    max_turns: int = 30,
    max_budget_usd: float = 5.00,
) -> WorkerResult:
    from .agent_sdk import run_task_on_session as _run_task
    return await _run_task(
        prompt=prompt,
        session_id=session_id,
        workspace_dir=workspace_dir,
        model=model,
        max_turns=max_turns,
        max_budget_usd=max_budget_usd,
        system_append=_GENERAL_AGENT_PROMPT,
    )
