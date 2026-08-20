from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from jobpilot.schemas.common import RequirementLevel, WorkMode


class JobPosting(BaseModel):
    source: str
    source_job_id: str | None = None
    company: str
    title: str
    location: str = ""
    country: str | None = None
    city: str | None = None
    work_mode: WorkMode = WorkMode.UNKNOWN
    job_url: str
    description: str = ""
    requirements_raw: str = ""
    preferred_raw: str = ""
    salary_raw: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    posted_at: datetime | None = None
    closing_at: datetime | None = None
    seniority: str | None = None
    language_requirements: list[str] = Field(default_factory=list)
    work_authorization: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ExtractedRequirement(BaseModel):
    name: str
    normalized: str
    category: str
    level: RequirementLevel
    years: float | None = None
    raw_span: str | None = None


class JobAnalysis(BaseModel):
    job_url: str
    title: str
    company: str
    seniority: str | None = None
    years_required: float | None = None
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    location: str = ""
    country: str | None = None
    city: str | None = None
    work_mode: WorkMode = WorkMode.UNKNOWN
    work_authorization: str | None = None
    industry: str | None = None
    requirements: list[ExtractedRequirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    leadership_required: bool = False
    tech_distribution: dict[str, int] = Field(default_factory=dict)


class ScoutRequest(BaseModel):
    roles: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    limit: int = 80
