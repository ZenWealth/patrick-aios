"""
Titan LifeMap - Data Models

Pydantic models describing the shape of a Titan LifeMap session. These
are the structural contracts between the conversation engine, the
analysis layer, and the report generators - they do not contain any
content (questions, scoring weights, report wording all live in config/).
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

Route = Literal["consumer", "coaching", "adviser"]
StageName = Literal["visionary", "sage", "builder", "steward", "guardian"]


class Session(BaseModel):
    """A single Titan LifeMap conversation session."""
    session_id: str
    started_at: datetime
    current_stage: StageName = "visionary"
    completed: bool = False
    route: Optional[Route] = None
    first_name: Optional[str] = None
    email: Optional[str] = None


class SoftFacts(BaseModel):
    """The eight soft-fact category outputs. Free text - Claude writes
    these during the conversation based on the stage answers."""
    future_vision_statement: Optional[str] = None        # A. Life Vision
    personal_enough_statement: Optional[str] = None       # B. Definition of Enough
    top_five_values: Optional[list[str]] = None           # C. Core Values
    family_impact_summary: Optional[str] = None           # D. Family and Relationships
    money_story_summary: Optional[str] = None             # E. Relationship With Money
    behavioural_friction_profile: Optional[str] = None    # F. Behavioural Patterns (narrative; numeric scores live in ScoringResult)
    health_wealth_happiness_scorecard: Optional[str] = None  # G. Health, Wealth and Happiness
    legacy_statement: Optional[str] = None                 # H. Purpose and Legacy


class HardFacts(BaseModel):
    """Financial data, captured from the Steward stage onward."""
    income: Optional[str] = None
    expenses: Optional[str] = None
    assets: Optional[str] = None
    liabilities: Optional[str] = None
    existing_arrangements: Optional[str] = None
    dependants: Optional[str] = None


class ScoringResult(BaseModel):
    """Output of the analysis layer (apps/titan_lifemap/analysis.py)."""
    clarity_score: float = Field(ge=0, le=100)
    momentum_plan: list[str] = Field(default_factory=list)  # ranked priority actions
    behavioural_friction_scores: dict[str, float] = Field(default_factory=dict)
    # e.g. {"procrastination": 0.7, "avoidance": 0.2, ...} - keys come from scoring_rules.yaml


class TitanProfile(BaseModel):
    """Top-level container - everything captured/derived for one session."""
    session: Session
    soft_facts: SoftFacts = Field(default_factory=SoftFacts)
    hard_facts: HardFacts = Field(default_factory=HardFacts)
    scoring: Optional[ScoringResult] = None
