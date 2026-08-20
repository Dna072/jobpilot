from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from jobpilot.schemas.common import ApplicationStatus, ApplyMechanism, ResumeType


class ScreeningAnswer(BaseModel):
    question: str
    answer: str
    invented: bool = False


class ApplicationPackage(BaseModel):
    company: str
    role: str
    job_url: str
    country: str | None = None
    location: str = ""
    match_score: float
    selected_resume: ResumeType
    resume_tex_path: str | None = None
    resume_pdf_path: str | None = None
    cover_letter: str | None = None
    screening_answers: list[ScreeningAnswer] = Field(default_factory=list)
    portfolio_links: list[str] = Field(default_factory=list)
    github_links: list[str] = Field(default_factory=list)
    remaining_human_action: str | None = None


class ApplicationAttempt(BaseModel):
    mechanism: ApplyMechanism
    status: ApplicationStatus
    dry_run: bool = True
    confirmation_id: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    human_action: str | None = None


class WeeklyReport(BaseModel):
    jobs_discovered: int = 0
    jobs_analyzed: int = 0
    jobs_rejected: int = 0
    strong_matches: int = 0
    applications_submitted: int = 0
    human_actions_required: int = 0
    failed_applications: int = 0
    applications_by_country: dict[str, int] = Field(default_factory=dict)
    applications_by_role: dict[str, int] = Field(default_factory=dict)
    average_match_score: float = 0.0
    highest_match_score: float = 0.0
    companies_applied: list[str] = Field(default_factory=list)
    projects_created: int = 0
    projects_upgraded: int = 0
    resumes_generated: int = 0
    most_requested_skills: dict[str, float] = Field(default_factory=dict)
    portfolio_gaps: list[str] = Field(default_factory=list)
    recommended_projects: list[str] = Field(default_factory=list)
    quality_notes: str = ""
    strategy: str = ""
