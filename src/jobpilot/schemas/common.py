from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid4())


class RequirementLevel(str, Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"
    NICE_TO_HAVE = "NICE_TO_HAVE"


class ResumeType(str, Enum):
    DATA_ENGINEER = "DATA_ENGINEER"
    BACKEND_ENGINEER = "BACKEND_ENGINEER"
    FRONTEND_ENGINEER = "FRONTEND_ENGINEER"


class MatchRecommendation(str, Enum):
    APPLY_NOW = "APPLY_NOW"
    APPLY_AFTER_PROJECT = "APPLY_AFTER_PROJECT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    LOW_PRIORITY = "LOW_PRIORITY"
    DO_NOT_APPLY = "DO_NOT_APPLY"


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    ANALYZED = "ANALYZED"
    MATCHED = "MATCHED"
    REJECTED = "REJECTED"
    PROJECT_REQUIRED = "PROJECT_REQUIRED"
    WAITING_FOR_REPOSITORY = "WAITING_FOR_REPOSITORY"
    PROJECT_BUILDING = "PROJECT_BUILDING"
    PROJECT_COMPLETE = "PROJECT_COMPLETE"
    CV_GENERATED = "CV_GENERATED"
    READY_TO_APPLY = "READY_TO_APPLY"
    APPLICATION_IN_PROGRESS = "APPLICATION_IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    HUMAN_ACTION_REQUIRED = "HUMAN_ACTION_REQUIRED"
    FAILED = "FAILED"
    WITHDRAWN = "WITHDRAWN"


class ProjectStatus(str, Enum):
    PROPOSED = "PROPOSED"
    WAITING_FOR_REPOSITORY = "WAITING_FOR_REPOSITORY"
    REPOSITORY_FOUND = "REPOSITORY_FOUND"
    PROJECT_BUILDING = "PROJECT_BUILDING"
    QA = "QA"
    PROJECT_COMPLETE = "PROJECT_COMPLETE"
    REJECTED_IDEA = "REJECTED_IDEA"


class WorkMode(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class GapVerdict(str, Enum):
    EXISTING_SUFFICIENT = "EXISTING_SUFFICIENT"
    UPGRADE_EXISTING = "UPGRADE_EXISTING"
    NEW_PROJECT = "NEW_PROJECT"
    NO_PROJECT_NEEDED = "NO_PROJECT_NEEDED"


class ApplyMechanism(str, Enum):
    COMPANY_API = "COMPANY_API"
    ATS_API = "ATS_API"
    GREENHOUSE = "GREENHOUSE"
    LEVER = "LEVER"
    OTHER_ATS = "OTHER_ATS"
    CAREER_PAGE = "CAREER_PAGE"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"


ALLOWED_TRANSITIONS: dict[ApplicationStatus, set[ApplicationStatus]] = {
    ApplicationStatus.DISCOVERED: {ApplicationStatus.ANALYZED, ApplicationStatus.REJECTED},
    ApplicationStatus.ANALYZED: {
        ApplicationStatus.MATCHED,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.MATCHED: {
        ApplicationStatus.REJECTED,
        ApplicationStatus.PROJECT_REQUIRED,
        ApplicationStatus.CV_GENERATED,
        ApplicationStatus.HUMAN_ACTION_REQUIRED,
    },
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.PROJECT_REQUIRED: {
        ApplicationStatus.WAITING_FOR_REPOSITORY,
        ApplicationStatus.PROJECT_BUILDING,
        ApplicationStatus.PROJECT_COMPLETE,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.WAITING_FOR_REPOSITORY: {
        ApplicationStatus.ANALYZED,
        ApplicationStatus.PROJECT_BUILDING,
        ApplicationStatus.PROJECT_COMPLETE,
        ApplicationStatus.CV_GENERATED,
        ApplicationStatus.REJECTED,
    },
    ApplicationStatus.PROJECT_BUILDING: {
        ApplicationStatus.PROJECT_COMPLETE,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.PROJECT_COMPLETE: {
        ApplicationStatus.ANALYZED,
        ApplicationStatus.CV_GENERATED,
    },
    ApplicationStatus.CV_GENERATED: {ApplicationStatus.READY_TO_APPLY},
    ApplicationStatus.READY_TO_APPLY: {
        ApplicationStatus.APPLICATION_IN_PROGRESS,
        ApplicationStatus.HUMAN_ACTION_REQUIRED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.APPLICATION_IN_PROGRESS: {
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.HUMAN_ACTION_REQUIRED,
        ApplicationStatus.FAILED,
    },
    ApplicationStatus.SUBMITTED: {ApplicationStatus.WITHDRAWN},
    ApplicationStatus.HUMAN_ACTION_REQUIRED: {
        ApplicationStatus.APPLICATION_IN_PROGRESS,
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.FAILED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.FAILED: {
        ApplicationStatus.READY_TO_APPLY,
        ApplicationStatus.HUMAN_ACTION_REQUIRED,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.WITHDRAWN: set(),
}

# MATCHED may also go to LOW_PRIORITY conceptually via REJECTED + recommendation.
ALLOWED_TRANSITIONS[ApplicationStatus.ANALYZED].add(ApplicationStatus.MATCHED)
ALLOWED_TRANSITIONS[ApplicationStatus.MATCHED].add(ApplicationStatus.READY_TO_APPLY)


def can_transition(current: ApplicationStatus, target: ApplicationStatus) -> bool:
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: ApplicationStatus, target: ApplicationStatus) -> None:
    if not can_transition(current, target):
        raise ValueError(f"Illegal application transition {current.value} → {target.value}")


def require_submission_evidence(evidence: dict[str, Any] | None) -> None:
    if not evidence:
        raise ValueError("SUBMITTED requires confirmation evidence")
    keys = {"confirmation_id", "confirmation_url", "confirmation_text", "ats_status", "http_status"}
    if not keys.intersection(evidence.keys()):
        raise ValueError("SUBMITTED evidence must include a confirmation signal")
    if evidence.get("http_status") and int(evidence["http_status"]) >= 400:
        raise ValueError("HTTP error cannot be treated as submission evidence")


class AgentEnvelope(BaseModel):
    agent: str
    job_id: str | None = None
    action: str
    result: str = "ok"
    duration_ms: int = 0
    error: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SchemaModel(BaseModel):
    model_config = {"extra": "forbid"}

    id: str = Field(default_factory=new_id)
