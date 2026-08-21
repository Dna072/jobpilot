from __future__ import annotations

from pydantic import BaseModel, Field

from jobpilot.schemas.common import ProjectStatus


class PortfolioProject(BaseModel):
    name: str
    repository: str | None = None
    url: str | None = None
    kind: str = "portfolio"
    technologies: list[str] = Field(default_factory=list)
    architecture: str = ""
    system_design: str = ""
    deployment: str = ""
    tests: str = ""
    documentation_quality: str = ""
    evidence_strength: str = "moderate"
    skills_demonstrated: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    qa_passed: bool = False


class PortfolioInventory(BaseModel):
    github_username: str
    projects: list[PortfolioProject] = Field(default_factory=list)


class ProjectSpec(BaseModel):
    title: str
    repository_name: str
    problem: str
    objective: str
    target_jobs: list[str] = Field(default_factory=list)
    skills_demonstrated: list[str] = Field(default_factory=list)
    architecture: str
    system_design: str
    technology_choices: list[str] = Field(default_factory=list)
    data_flow: str = ""
    apis: str = ""
    database: str = ""
    infrastructure: str = ""
    security: str = ""
    scalability: str = ""
    observability: str = ""
    testing: str = ""
    cicd: str = ""
    deployment: str = ""
    repository_structure: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    definition_of_done: list[str] = Field(default_factory=list)
    visibility: str = "public"
    status: ProjectStatus = ProjectStatus.PROPOSED
