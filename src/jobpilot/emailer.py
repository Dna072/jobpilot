from __future__ import annotations

import smtplib
from email.message import EmailMessage

from jobpilot.config import get_settings
from jobpilot.schemas.application import ApplicationPackage, WeeklyReport


def _send(subject: str, body: str, attachments: list[tuple[str, bytes, str]] | None = None) -> dict:
    settings = get_settings()
    if not settings.smtp_host or not settings.email_to:
        return {"sent": False, "reason": "smtp_not_configured", "subject": subject, "body": body}
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.email_from or settings.smtp_username
    msg["To"] = settings.email_to
    msg.set_content(body)
    for name, data, mime in attachments or []:
        main, _, sub = mime.partition("/")
        msg.add_attachment(data, maintype=main or "application", subtype=sub or "octet-stream", filename=name)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
    return {"sent": True, "subject": subject}


def email_create_repository(project: str, body: str) -> dict:
    return _send(f"ACTION REQUIRED — Create Repository: {project}", body)


def email_project_complete(project: str, body: str) -> dict:
    return _send(f"PROJECT COMPLETE — {project}", body)


def email_human_action(package: ApplicationPackage) -> dict:
    subject = f"ACTION REQUIRED — {package.company} — {package.role}"
    body = render_application_email(package, remaining=package.remaining_human_action or "")
    return _send(subject, body)


def email_submitted(package: ApplicationPackage, confirmation: str) -> dict:
    subject = f"APPLICATION SUBMITTED — {package.company} — {package.role}"
    body = render_application_email(package, remaining=f"Confirmation: {confirmation}")
    return _send(subject, body)


def email_failed(package: ApplicationPackage, reason: str) -> dict:
    subject = f"APPLICATION FAILED — {package.company} — {package.role}"
    return _send(subject, render_application_email(package, remaining=f"Failure: {reason}"))


def email_weekly(report: WeeklyReport) -> dict:
    return _send("WEEKLY JOB APPLICATION REPORT", render_weekly(report))


def render_application_email(package: ApplicationPackage, remaining: str = "") -> str:
    return "\n".join(
        [
            f"Company: {package.company}",
            f"Role: {package.role}",
            f"Country: {package.country or ''}",
            f"Location: {package.location}",
            f"Match score: {package.match_score}",
            f"Selected resume: {package.selected_resume.value}",
            f"Application URL: {package.job_url}",
            f"Resume PDF: {package.resume_pdf_path or 'pending'}",
            f"Projects used: {', '.join(package.portfolio_links) or 'see package'}",
            "",
            remaining,
            "",
            "Cover letter:",
            package.cover_letter or "(not required / not generated)",
            "",
            "Screening answers:",
            *[f"Q: {a.question}\nA: {a.answer}" for a in package.screening_answers],
        ]
    )


def render_weekly(report: WeeklyReport) -> str:
    skills = "\n".join(f"{k:20} {v:.0%}" for k, v in report.most_requested_skills.items()) or "(none yet)"
    return "\n".join(
        [
            "WEEKLY JOB APPLICATION REPORT",
            "",
            f"Jobs discovered:              {report.jobs_discovered}",
            f"Jobs analyzed:                {report.jobs_analyzed}",
            f"Jobs rejected:                {report.jobs_rejected}",
            f"Strong matches:               {report.strong_matches}",
            f"Applications submitted:       {report.applications_submitted}",
            f"Human actions required:       {report.human_actions_required}",
            f"Failed applications:          {report.failed_applications}",
            f"Projects created:             {report.projects_created}",
            f"Projects upgraded:            {report.projects_upgraded}",
            f"Resumes generated:            {report.resumes_generated}",
            f"Average match score:          {report.average_match_score}",
            f"Highest match score:          {report.highest_match_score}",
            "",
            "Applications by country:",
            *([f"  {k}: {v}" for k, v in report.applications_by_country.items()] or ["  (none)"]),
            "",
            "Applications by role:",
            *([f"  {k}: {v}" for k, v in report.applications_by_role.items()] or ["  (none)"]),
            "",
            "Companies applied to:",
            ", ".join(report.companies_applied) or "(none)",
            "",
            "Most Requested Skills",
            skills,
            "",
            "Portfolio Gaps",
            *([f"- {g}" for g in report.portfolio_gaps] or ["- (none recorded)"]),
            "",
            "Recommended Projects",
            *([f"- {p}" for p in report.recommended_projects] or ["- (none)"]),
            "",
            "Application Quality",
            report.quality_notes,
            "",
            "Strategy Recommendations",
            report.strategy,
        ]
    )


def render_repo_request(spec_title: str, repo: str, purpose: str, jobs: list[str], skills: list[str], architecture: str) -> str:
    return "\n".join(
        [
            "ACTION REQUIRED — CREATE REPOSITORY",
            "",
            f"Project name: {spec_title}",
            f"Repository name: {repo}",
            f"Purpose: {purpose}",
            f"Target jobs: {', '.join(jobs)}",
            f"Missing skills: {', '.join(skills)}",
            f"Architecture:\n{architecture}",
            "",
            "Visibility recommendation: public",
            "",
            "Exact GitHub instructions:",
            "1. Open https://github.com/new",
            "2. Owner: Dna072",
            f"3. Repository name: {repo}",
            "4. Public",
            "5. Do not initialize with README if JobPilot will scaffold the repo",
            "6. Create repository",
            "7. Clone it into a workspace path listed in config.project_strategy.project_roots",
            "",
            "JobPilot will detect the repository and continue automatically.",
            "PROJECT_STATUS = WAITING_FOR_REPOSITORY",
        ]
    )
