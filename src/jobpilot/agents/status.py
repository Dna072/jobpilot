from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta

from jobpilot.db.models import (
    Application,
    Job,
    JobRequirement,
    ProjectRepository,
    ResumeVersion,
    WeeklyReportRow,
    get_session,
)
from jobpilot.emailer import email_weekly
from jobpilot.schemas.application import WeeklyReport
from jobpilot.schemas.common import ApplicationStatus


def collect_status() -> dict:
    session = get_session()
    try:
        jobs = session.query(Job).count()
        analyzed = session.query(JobRequirement.job_id).distinct().count()
        apps = session.query(Application).all()
        submitted = sum(1 for a in apps if a.status == ApplicationStatus.SUBMITTED.value)
        human = sum(1 for a in apps if a.status == ApplicationStatus.HUMAN_ACTION_REQUIRED.value)
        failed = sum(1 for a in apps if a.status == ApplicationStatus.FAILED.value)
        strong = sum(1 for a in apps if (a.match_score or 0) >= 85)
        projects = session.query(ProjectRepository).count()
        upgrades = session.query(ProjectRepository).filter(ProjectRepository.status == "PROJECT_COMPLETE").count()
        return {
            "jobs_discovered": jobs,
            "jobs_analyzed": analyzed,
            "strong_matches": strong,
            "applications_submitted": submitted,
            "human_actions_required": human,
            "projects_created": projects,
            "projects_upgraded": upgrades,
            "failed_applications": failed,
        }
    finally:
        session.close()


def format_status(stats: dict | None = None) -> str:
    stats = stats or collect_status()
    return "\n".join(
        [
            f"Jobs discovered:              {stats['jobs_discovered']:>6}",
            f"Jobs analyzed:                {stats['jobs_analyzed']:>6}",
            f"Strong matches:               {stats['strong_matches']:>6}",
            f"Applications submitted:       {stats['applications_submitted']:>6}",
            f"Human actions required:       {stats['human_actions_required']:>6}",
            f"Projects created:             {stats['projects_created']:>6}",
            f"Projects upgraded:            {stats['projects_upgraded']:>6}",
            f"Failed applications:          {stats['failed_applications']:>6}",
        ]
    )


def build_weekly_report() -> WeeklyReport:
    session = get_session()
    try:
        since = datetime.now(UTC) - timedelta(days=7)
        jobs = session.query(Job).filter(Job.first_seen_at >= since).all()
        apps = session.query(Application).all()
        week_apps = [a for a in apps if a.updated_at and a.updated_at >= since]
        by_country: Counter[str] = Counter()
        by_role: Counter[str] = Counter()
        companies: list[str] = []
        scores = [a.match_score or 0 for a in week_apps if a.match_score]
        for app in week_apps:
            job = session.get(Job, app.job_id)
            if not job:
                continue
            by_country[job.country or "unknown"] += 1
            by_role[job.title] += 1
            if app.status == ApplicationStatus.SUBMITTED.value and job.company:
                companies.append(job.company.name if job.company else "")
        skill_counts: Counter[str] = Counter()
        reqs = session.query(JobRequirement).all()
        for req in reqs:
            skill_counts[req.normalized] += 1
        total = sum(skill_counts.values()) or 1
        most = {k: v / total for k, v in skill_counts.most_common(12)}
        report = WeeklyReport(
            jobs_discovered=len(jobs),
            jobs_analyzed=len({r.job_id for r in reqs}),
            jobs_rejected=sum(1 for a in apps if a.status == ApplicationStatus.REJECTED.value),
            strong_matches=sum(1 for a in apps if (a.match_score or 0) >= 85),
            applications_submitted=sum(1 for a in apps if a.status == ApplicationStatus.SUBMITTED.value),
            human_actions_required=sum(
                1 for a in apps if a.status == ApplicationStatus.HUMAN_ACTION_REQUIRED.value
            ),
            failed_applications=sum(1 for a in apps if a.status == ApplicationStatus.FAILED.value),
            applications_by_country=dict(by_country),
            applications_by_role=dict(by_role),
            average_match_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
            highest_match_score=max(scores) if scores else 0.0,
            companies_applied=[c for c in companies if c],
            projects_created=session.query(ProjectRepository).count(),
            projects_upgraded=0,
            resumes_generated=session.query(ResumeVersion).filter(ResumeVersion.kind == "tailored").count(),
            most_requested_skills=most,
            portfolio_gaps=["Kafka / real-time streaming", "dbt analytics layer"],
            recommended_projects=["Real-Time Event Processing and Analytics Platform"],
            quality_notes=(
                "Applications are only marked sent when there is a confirmation. "
                "Portfolio work is not described as employment."
            ),
            strategy=(
                "Keep looking first in Uppsala, Stockholm, Gothenburg and Malmö, then other Sweden, "
                "then the rest of Europe."
            ),
        )
        session.add(WeeklyReportRow(payload=report.model_dump()))
        session.commit()
        return report
    finally:
        session.close()


def send_weekly_report() -> dict:
    report = build_weekly_report()
    return email_weekly(report)
