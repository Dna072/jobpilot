from __future__ import annotations

import json
import time
from datetime import UTC, datetime

from jobpilot.agents.cv import generate_package
from jobpilot.agents.planner import plan_from_gap
from jobpilot.analyst import analyze_job
from jobpilot.apply.submit import attempt_application
from jobpilot.config import load_app_config
from jobpilot.db.models import (
    AgentRun,
    Application,
    ApplicationMaterial,
    CandidateProfileRow,
    Company,
    Job,
    JobRequirement,
    JobSource,
    Notification,
    PortfolioProjectRow,
    ProjectRepository,
    get_session,
    init_db,
)
from jobpilot.dedup import job_fingerprint, normalize_company, normalize_title
from jobpilot.emailer import (
    email_create_repository,
    email_human_action,
    email_submitted,
    render_repo_request,
)
from jobpilot.knowledge import load_candidate_profile, load_inventory
from jobpilot.logging import agent_log
from jobpilot.matching import analyze_gaps, match_job
from jobpilot.schemas.common import (
    ApplicationStatus,
    ProjectStatus,
    assert_transition,
    require_submission_evidence,
)
from jobpilot.schemas.job import JobPosting
from jobpilot.sources.jobs import discover_jobs


def log_run(agent: str, action: str, job_id: str | None, result: str, duration_ms: int, error: str | None = None, payload: dict | None = None) -> None:
    session = get_session()
    try:
        session.add(
            AgentRun(
                agent=agent,
                job_id=job_id,
                action=action,
                result=result,
                duration_ms=duration_ms,
                error=error,
                payload=payload or {},
            )
        )
        session.commit()
    finally:
        session.close()
    agent_log(
        agent=agent,
        job_id=job_id,
        action=action,
        result=result,
        duration_ms=duration_ms,
        error=error,
    )


def seed_knowledge() -> None:
    init_db()
    session = get_session()
    try:
        profile = load_candidate_profile()
        if not session.query(CandidateProfileRow).first():
            session.add(
                CandidateProfileRow(
                    full_name=profile["full_name"],
                    email=profile["email"],
                    phone=profile.get("phone"),
                    location=profile.get("location"),
                    payload=profile,
                )
            )
        inventory = load_inventory()
        for project in inventory.projects:
            if session.query(PortfolioProjectRow).filter_by(name=project.name).first():
                continue
            session.add(
                PortfolioProjectRow(
                    name=project.name,
                    kind=project.kind,
                    repository=project.repository,
                    url=project.url,
                    description=project.architecture,
                    architecture=project.system_design,
                    evidence_strength=project.evidence_strength,
                    documentation_quality=project.documentation_quality,
                    qa_passed=project.kind == "professional",
                    target_roles=project.target_roles,
                    technologies=project.technologies,
                    skills=project.skills_demonstrated,
                )
            )
        for name in ("arbeitnow", "greenhouse", "lever", "manual"):
            if not session.query(JobSource).filter_by(name=name).first():
                session.add(JobSource(name=name, kind="api"))
        session.commit()
    finally:
        session.close()


def upsert_job(posting: JobPosting) -> tuple[Job, bool]:
    session = get_session()
    try:
        fp = job_fingerprint(posting.company, posting.title, posting.location, posting.job_url)
        existing = session.query(Job).filter_by(fingerprint=fp).first()
        if existing:
            existing.last_seen_at = datetime.now(UTC)
            session.commit()
            return existing, False
        if posting.source_job_id:
            source = session.query(JobSource).filter_by(name=posting.source).first()
            if source:
                existing = (
                    session.query(Job)
                    .filter_by(source_id=source.id, source_job_id=posting.source_job_id)
                    .first()
                )
                if existing:
                    existing.last_seen_at = datetime.now(UTC)
                    session.commit()
                    return existing, False
        company = session.query(Company).filter_by(name_normalized=normalize_company(posting.company)).first()
        if not company:
            company = Company(name=posting.company, name_normalized=normalize_company(posting.company), country=posting.country)
            session.add(company)
            session.flush()
        source = session.query(JobSource).filter_by(name=posting.source).first()
        job = Job(
            company_id=company.id,
            source_id=source.id if source else None,
            source_job_id=posting.source_job_id,
            title=posting.title,
            title_normalized=normalize_title(posting.title),
            location=posting.location,
            country=posting.country,
            city=posting.city,
            work_mode=posting.work_mode.value,
            job_url=posting.job_url,
            canonical_url=posting.job_url.split("?")[0],
            description=posting.description,
            salary_min=posting.salary_min,
            salary_max=posting.salary_max,
            salary_currency=posting.salary_currency,
            posted_at=posting.posted_at,
            closing_at=posting.closing_at,
            seniority=posting.seniority,
            fingerprint=fp,
            raw=posting.raw,
        )
        session.add(job)
        session.flush()
        session.add(Application(job_id=job.id, status=ApplicationStatus.DISCOVERED.value))
        session.commit()
        session.refresh(job)
        return job, True
    finally:
        session.close()


def ingest_postings(postings: list[JobPosting]) -> int:
    created = 0
    for posting in postings:
        _, is_new = upsert_job(posting)
        created += int(is_new)
    return created


def process_job(job_id: str) -> dict:
    t0 = time.perf_counter()
    session = get_session()
    try:
        job = session.get(Job, job_id)
        if not job:
            return {"error": "job not found"}
        app = session.query(Application).filter_by(job_id=job_id).first()
        if not app:
            app = Application(job_id=job_id, status=ApplicationStatus.DISCOVERED.value)
            session.add(app)
            session.flush()
        posting = JobPosting(
            source=job.source.name if job.source else "manual",
            source_job_id=job.source_job_id,
            company=job.company.name if job.company else "Unknown",
            title=job.title,
            location=job.location,
            country=job.country,
            city=job.city,
            job_url=job.job_url,
            description=job.description,
            seniority=job.seniority,
        )
        analysis = analyze_job(posting)
        session.query(JobRequirement).filter_by(job_id=job.id).delete()
        for req in analysis.requirements:
            session.add(
                JobRequirement(
                    job_id=job.id,
                    category=req.category,
                    name=req.name,
                    normalized=req.normalized,
                    level=req.level.value,
                    years=req.years,
                )
            )
        assert_transition(ApplicationStatus(app.status), ApplicationStatus.ANALYZED)
        app.status = ApplicationStatus.ANALYZED.value
        match = match_job(analysis)
        assert_transition(ApplicationStatus(app.status), ApplicationStatus.MATCHED)
        app.status = ApplicationStatus.MATCHED.value
        app.match_score = match.score
        app.recommendation = match.recommendation.value
        app.match_report = json.loads(match.model_dump_json())
        config = load_app_config()
        minimum = float(config.get("match", {}).get("minimum_match_score", 75))

        if match.recommendation.value in {"DO_NOT_APPLY", "LOW_PRIORITY"} or match.score < minimum:
            app.status = ApplicationStatus.REJECTED.value
            session.commit()
            log_run("match", "reject", job.id, "ok", int((time.perf_counter() - t0) * 1000), payload=app.match_report)
            return {"status": app.status, "score": match.score}

        gap = analyze_gaps(analysis)
        if gap.verdict.value == "NEW_PROJECT":
            spec = plan_from_gap(gap)
            app.status = ApplicationStatus.PROJECT_REQUIRED.value
            if spec:
                existing = session.query(ProjectRepository).filter_by(requested_name=spec.repository_name).first()
                if not existing:
                    session.add(
                        ProjectRepository(
                            requested_name=spec.repository_name,
                            status=ProjectStatus.WAITING_FOR_REPOSITORY.value,
                            spec=json.loads(spec.model_dump_json()),
                        )
                    )
                    body = render_repo_request(
                        spec.title,
                        spec.repository_name,
                        spec.objective,
                        spec.target_jobs,
                        spec.skills_demonstrated,
                        spec.architecture,
                    )
                    result = email_create_repository(spec.title, body)
                    session.add(
                        Notification(
                            kind="create_repository",
                            subject=f"ACTION REQUIRED — Create Repository: {spec.title}",
                            body=body,
                            sent=bool(result.get("sent")),
                        )
                    )
                app.status = ApplicationStatus.WAITING_FOR_REPOSITORY.value
            session.commit()
            return {"status": app.status, "gap": gap.verdict.value}

        package = generate_package(analysis, match)
        app.selected_resume_type = package.selected_resume.value
        app.status = ApplicationStatus.CV_GENERATED.value
        app.status = ApplicationStatus.READY_TO_APPLY.value
        session.add(
            ApplicationMaterial(
                application_id=app.id,
                cover_letter=package.cover_letter,
                screening=[a.model_dump() for a in package.screening_answers],
                portfolio_links=package.portfolio_links,
                package=json.loads(package.model_dump_json()),
            )
        )
        daily_cap = int(config.get("applications", {}).get("maximum_daily_applications", 8))
        today = datetime.now(UTC).date()
        submitted_today = 0
        for row in session.query(Application).filter(
            Application.status == ApplicationStatus.SUBMITTED.value
        ):
            if row.submitted_at and row.submitted_at.date() == today:
                submitted_today += 1
        in_progress = session.query(Application).filter(
            Application.status.in_(
                [
                    ApplicationStatus.APPLICATION_IN_PROGRESS.value,
                    ApplicationStatus.HUMAN_ACTION_REQUIRED.value,
                ]
            )
        ).count()
        if submitted_today + in_progress >= daily_cap:
            session.commit()
            return {"status": app.status, "deferred": "daily_cap"}

        app.status = ApplicationStatus.APPLICATION_IN_PROGRESS.value
        attempt = attempt_application(posting, package)
        app.mechanism = attempt.mechanism.value
        if attempt.status == ApplicationStatus.SUBMITTED:
            require_submission_evidence(attempt.evidence)
            app.status = ApplicationStatus.SUBMITTED.value
            app.confirmation_id = attempt.confirmation_id
            app.confirmation_evidence = attempt.evidence
            app.submitted_at = datetime.now(UTC)
            email_submitted(package, attempt.confirmation_id or "confirmed")
        else:
            app.status = attempt.status.value
            app.human_action = attempt.human_action
            app.confirmation_evidence = attempt.evidence
            app.error = attempt.error
            package.remaining_human_action = attempt.human_action
            if attempt.status == ApplicationStatus.HUMAN_ACTION_REQUIRED:
                result = email_human_action(package)
                session.add(
                    Notification(
                        kind="human_action",
                        subject=f"ACTION REQUIRED — {package.company} — {package.role}",
                        body=attempt.human_action or "",
                        sent=bool(result.get("sent")),
                    )
                )
        session.commit()
        log_run(
            "orchestrator",
            "process_job",
            job.id,
            "ok",
            int((time.perf_counter() - t0) * 1000),
            payload={"status": app.status, "score": match.score},
        )
        return {"status": app.status, "score": match.score, "mechanism": app.mechanism}
    except Exception as exc:
        session.rollback()
        log_run("orchestrator", "process_job", job_id, "error", int((time.perf_counter() - t0) * 1000), error=str(exc))
        raise
    finally:
        session.close()


def run_cycle(limit: int = 25, scout: bool = True) -> dict:
    seed_knowledge()
    discovered = 0
    if scout:
        t0 = time.perf_counter()
        try:
            postings = discover_jobs()
            discovered = ingest_postings(postings)
            log_run("scout", "discover", None, "ok", int((time.perf_counter() - t0) * 1000), payload={"count": discovered})
        except Exception as exc:
            log_run("scout", "discover", None, "error", int((time.perf_counter() - t0) * 1000), error=str(exc))
    session = get_session()
    processed = []
    try:
        pending = (
            session.query(Application)
            .filter(Application.status.in_([ApplicationStatus.DISCOVERED.value, ApplicationStatus.ANALYZED.value]))
            .limit(limit)
            .all()
        )
        ids = [a.job_id for a in pending]
    finally:
        session.close()
    for job_id in ids:
        processed.append(process_job(job_id))
    return {"discovered": discovered, "processed": processed}
