from __future__ import annotations

from jobpilot.schemas.application import ApplicationAttempt, ApplicationPackage, WeeklyReport
from jobpilot.schemas.common import AgentEnvelope, ApplicationStatus, SchemaModel
from jobpilot.schemas.job import ExtractedRequirement, JobAnalysis, JobPosting, ScoutRequest
from jobpilot.schemas.match import GapItem, GapReport, MatchBreakdown, MatchReport, ResumeScores
from jobpilot.schemas.portfolio import PortfolioInventory, PortfolioProject, ProjectSpec

__all__ = [
    "AgentEnvelope",
    "ApplicationAttempt",
    "ApplicationPackage",
    "ApplicationStatus",
    "ExtractedRequirement",
    "GapItem",
    "GapReport",
    "JobAnalysis",
    "JobPosting",
    "MatchBreakdown",
    "MatchReport",
    "PortfolioInventory",
    "PortfolioProject",
    "ProjectSpec",
    "ResumeScores",
    "ScoutRequest",
    "WeeklyReport",
    "SchemaModel",
]
