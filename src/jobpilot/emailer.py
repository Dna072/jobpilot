from __future__ import annotations

import smtplib
from email.message import EmailMessage

from jobpilot.config import get_settings
from jobpilot.resume.tailor import display_company_name
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
    return {"sent": True, "subject": subject, "body": body}


def email_create_repository(project: str, body: str) -> dict:
    return _send(f"Please create a GitHub repository for {project}", body)


def email_project_complete(project: str, body: str) -> dict:
    return _send(f"The {project} repository is ready to use", body)


def email_human_action(package: ApplicationPackage) -> dict:
    company = display_company_name(package.company)
    subject = f"Please apply to {package.role} at {company}"
    body = render_application_email(package)
    return _send(subject, body)


def email_submitted(package: ApplicationPackage, confirmation: str) -> dict:
    company = display_company_name(package.company)
    subject = f"Application sent: {package.role} at {company}"
    extra = f"The company should have a record of this application. Reference: {confirmation}." if confirmation else ""
    body = render_application_email(package, extra=extra)
    return _send(subject, body)


def email_failed(package: ApplicationPackage, reason: str) -> dict:
    company = display_company_name(package.company)
    subject = f"Could not finish applying to {package.role} at {company}"
    body = render_application_email(
        package,
        extra="The form could not be completed automatically. Please submit it yourself using the link and cover letter below.",
    )
    return _send(subject, body)


def email_weekly(report: WeeklyReport) -> dict:
    return _send("Your weekly job search update", render_weekly(report))


def render_application_email(package: ApplicationPackage, extra: str = "") -> str:
    company = display_company_name(package.company)
    place = ", ".join(p for p in (package.location, package.country) if p)
    next_step = package.remaining_human_action or (
        "Open the job link, attach the CV, paste the cover letter, and submit the form. "
        "If the site asks you to sign in or complete a check, do that there."
    )
    lines = [
        f"Hi Derrick,",
        "",
        f"There is a role at {company} that looks like a good fit. Please apply using the link and letter below.",
        "",
        f"Role: {package.role}",
        f"Company: {company}",
    ]
    if place:
        lines.append(f"Location: {place}")
    lines.extend(
        [
            f"Apply here: {package.job_url}",
            "",
            "What to do:",
            next_step,
        ]
    )
    if package.resume_pdf_path:
        lines.extend(["", f"CV to attach: {package.resume_pdf_path}"])
    if extra:
        lines.extend(["", extra])
    lines.extend(
        [
            "",
            "Cover letter (paste this into the application — do not add anything else):",
            "",
            package.cover_letter or "(cover letter not generated)",
        ]
    )
    if package.screening_answers:
        lines.extend(["", "If the form asks questions, you can use these answers:"])
        for answer in package.screening_answers:
            lines.append(f"- {answer.question} {answer.answer}")
    return "\n".join(lines)


def render_weekly(report: WeeklyReport) -> str:
    skills = ", ".join(k for k, _ in list(report.most_requested_skills.items())[:8]) or "none recorded yet"
    countries = ", ".join(f"{k} ({v})" for k, v in report.applications_by_country.items()) or "none yet"
    companies = ", ".join(report.companies_applied) or "none yet"
    return "\n".join(
        [
            "Hi Derrick,",
            "",
            "Here is a simple summary of this week's job search.",
            "",
            f"New roles found: {report.jobs_discovered}",
            f"Applications sent: {report.applications_submitted}",
            f"Applications still waiting for you to submit: {report.human_actions_required}",
            f"Applications that could not be finished: {report.failed_applications}",
            "",
            f"Where the roles were: {countries}",
            f"Companies applied to: {companies}",
            f"Skills that came up often: {skills}",
            "",
            "I will keep looking first in Uppsala, Stockholm, Gothenburg and Malmö, then the rest of Sweden, then other European countries.",
            "",
            "If a role is sitting in your inbox, please open the link, attach the CV, paste the cover letter, and submit it on the company's site.",
        ]
    )


def render_repo_request(spec_title: str, repo: str, purpose: str, jobs: list[str], skills: list[str], architecture: str) -> str:
    skill_list = ", ".join(skills) if skills else "the skills this kind of role usually asks for"
    job_list = ", ".join(jobs) if jobs else "related openings"
    return "\n".join(
        [
            "Hi Derrick,",
            "",
            f"Please create a public GitHub repository so we can build {spec_title}.",
            f"That project would help with roles such as {job_list}, especially around {skill_list}.",
            "",
            f"Repository name: {repo}",
            f"What it is for: {purpose}",
            "",
            "How to create it:",
            "1. Open https://github.com/new",
            "2. Owner: Dna072",
            f"3. Repository name: {repo}",
            "4. Make it public",
            "5. Create the repository",
            "6. Clone it onto this machine",
            "",
            "Once the repository exists, the rest of the work can continue.",
        ]
    )
