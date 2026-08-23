from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


def utcnow() -> datetime:
    return datetime.now(UTC)


def uid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class CandidateProfileRow(Base):
    __tablename__ = "candidate_profile"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    version: Mapped[int] = mapped_column(Integer, default=1)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(64))
    location: Mapped[str | None] = mapped_column(String(200))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(300))
    name_normalized: Mapped[str] = mapped_column(String(300), unique=True)
    website: Mapped[str | None] = mapped_column(String(500))
    careers_url: Mapped[str | None] = mapped_column(String(500))
    greenhouse_board: Mapped[str | None] = mapped_column(String(200))
    lever_site: Mapped[str | None] = mapped_column(String(200))
    country: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    jobs: Mapped[list[Job]] = relationship(back_populates="company")


class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    kind: Mapped[str] = mapped_column(String(50), default="api")
    base_url: Mapped[str | None] = mapped_column(String(500))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=30)
    jobs: Mapped[list[Job]] = relationship(back_populates="source")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source_id", "source_job_id", name="uq_source_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    company_id: Mapped[str | None] = mapped_column(ForeignKey("companies.id"))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("job_sources.id"))
    source_job_id: Mapped[str | None] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(400))
    title_normalized: Mapped[str] = mapped_column(String(400), default="")
    location: Mapped[str] = mapped_column(String(300), default="")
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    work_mode: Mapped[str] = mapped_column(String(32), default="unknown")
    job_url: Mapped[str] = mapped_column(String(1000))
    canonical_url: Mapped[str | None] = mapped_column(String(1000))
    description: Mapped[str] = mapped_column(Text, default="")
    salary_min: Mapped[float | None] = mapped_column(Float)
    salary_max: Mapped[float | None] = mapped_column(Float)
    salary_currency: Mapped[str | None] = mapped_column(String(16))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seniority: Mapped[str | None] = mapped_column(String(64))
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    company: Mapped[Company | None] = relationship(back_populates="jobs")
    source: Mapped[JobSource | None] = relationship(back_populates="jobs")
    requirements: Mapped[list[JobRequirement]] = relationship(back_populates="job")
    application: Mapped[Application | None] = relationship(back_populates="job")


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    category: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    normalized: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(32))
    years: Mapped[float | None] = mapped_column(Float)
    raw_span: Mapped[str | None] = mapped_column(Text)
    job: Mapped[Job] = relationship(back_populates="requirements")


class PortfolioProjectRow(Base):
    __tablename__ = "portfolio_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(300), unique=True)
    kind: Mapped[str] = mapped_column(String(32), default="portfolio")
    repository: Mapped[str | None] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    architecture: Mapped[str] = mapped_column(Text, default="")
    evidence_strength: Mapped[str] = mapped_column(String(32), default="moderate")
    documentation_quality: Mapped[str] = mapped_column(String(32), default="moderate")
    qa_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    target_roles: Mapped[list[Any]] = mapped_column(JSON, default=list)
    technologies: Mapped[list[Any]] = mapped_column(JSON, default=list)
    skills: Mapped[list[Any]] = mapped_column(JSON, default=list)


class PortfolioSkill(Base):
    __tablename__ = "portfolio_skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(ForeignKey("portfolio_projects.id"))
    skill: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(64), default="other")
    evidence_strength: Mapped[str] = mapped_column(String(32), default="moderate")


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(String(300))
    spec: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(64), default="PROPOSED")
    rejected_reason: Mapped[str | None] = mapped_column(Text)


class ProjectRepository(Base):
    __tablename__ = "project_repositories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    requested_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(64), default="WAITING_FOR_REPOSITORY")
    github_url: Mapped[str | None] = mapped_column(String(500))
    local_path: Mapped[str | None] = mapped_column(String(500))
    spec: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    resume_type: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(32))
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"))
    tex_path: Mapped[str] = mapped_column(String(500))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    page_count: Mapped[int | None] = mapped_column(Integer)
    validation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), unique=True)
    status: Mapped[str] = mapped_column(String(64), default="DISCOVERED")
    match_score: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str | None] = mapped_column(String(64))
    selected_resume_type: Mapped[str | None] = mapped_column(String(64))
    mechanism: Mapped[str | None] = mapped_column(String(64))
    confirmation_id: Mapped[str | None] = mapped_column(String(200))
    confirmation_evidence: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    human_action: Mapped[str | None] = mapped_column(Text)
    approval_token: Mapped[str | None] = mapped_column(String(80))
    match_report: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    job: Mapped[Job] = relationship(back_populates="application")
    materials: Mapped[list[ApplicationMaterial]] = relationship(back_populates="application")


class ApplicationMaterial(Base):
    __tablename__ = "application_materials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"))
    resume_version_id: Mapped[str | None] = mapped_column(ForeignKey("resume_versions.id"))
    cover_letter: Mapped[str | None] = mapped_column(Text)
    screening: Mapped[list[Any]] = mapped_column(JSON, default=list)
    portfolio_links: Mapped[list[Any]] = mapped_column(JSON, default=list)
    package: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    application: Mapped[Application] = relationship(back_populates="materials")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    agent: Mapped[str] = mapped_column(String(64))
    job_id: Mapped[str | None] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(100))
    result: Mapped[str] = mapped_column(String(32), default="ok")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(64))
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WeeklyReportRow(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


_engine = None
_Session = None


def get_engine(url: str | None = None):
    global _engine, _Session
    if _engine is None:
        from jobpilot.config import get_settings

        url = url or get_settings().database_url
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, connect_args=connect_args)
        _Session = sessionmaker(_engine, expire_on_commit=False)
    return _engine


def reset_engine() -> None:
    global _engine, _Session
    _engine = None
    _Session = None


def get_session():
    get_engine()
    assert _Session is not None
    return _Session()


def init_db(url: str | None = None) -> None:
    engine = get_engine(url)
    Base.metadata.create_all(engine)
    _ensure_columns(engine)


def _ensure_columns(engine) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "applications" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("applications")}
    if "approval_token" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE applications ADD COLUMN approval_token VARCHAR(80)"))
    with engine.begin() as conn:
        conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS ix_applications_approval_token ON applications (approval_token)")
        )
