from __future__ import annotations

from pydantic import BaseModel, Field

from jobpilot.schemas.common import GapVerdict, MatchRecommendation, ResumeType


class MatchBreakdown(BaseModel):
    technical_skills: float
    relevant_experience: float
    portfolio_evidence: float
    seniority: float
    education: float
    location: float
    industry: float
    other: float


class MatchReport(BaseModel):
    score: float
    breakdown: MatchBreakdown
    strong_matches: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    transferable_experience: list[str] = Field(default_factory=list)
    portfolio_evidence: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: MatchRecommendation
    rationale: str = ""


class ResumeScores(BaseModel):
    DATA_ENGINEER: float
    BACKEND_ENGINEER: float
    FRONTEND_ENGINEER: float
    selected: ResumeType
    reasoning: str


class GapItem(BaseModel):
    skill: str
    in_experience: bool = False
    in_portfolio: bool = False
    evidence: str | None = None


class GapReport(BaseModel):
    verdict: GapVerdict
    items: list[GapItem] = Field(default_factory=list)
    upgrade_target: str | None = None
    proposed_project: str | None = None
    rationale: str = ""
