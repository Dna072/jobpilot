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
    subject = f"Please review the application to {package.role} at {company}"
    body = render_application_email(package)
    return _send(subject, body, attachments=_resume_attachments(package))


def email_submitted(package: ApplicationPackage, confirmation: str) -> dict:
    company = display_company_name(package.company)
    subject = f"Application sent: {package.role} at {company}"
    extra = f"The company should have a record of this application. Reference: {confirmation}." if confirmation else ""
    body = render_application_email(package, extra=extra)
    return _send(subject, body, attachments=_resume_attachments(package))


def email_github_token_needed(repo: str, github_url: str) -> dict:
    url = github_url or f"https://github.com/Dna072/{repo}"
    body = "\n".join(
        [
            "Hi Derrick,",
            "",
            f"The {repo} repository exists ({url}), but the starter code cannot be added yet.",
            "A GitHub personal access token with access to your repositories is missing or still set to a placeholder.",
            "",
            "Please:",
            "1. Open https://github.com/settings/tokens",
            '2. Create a token with the "repo" scope',
            "3. Store it as the jobpilot-github-token secret in Google Cloud, or as GITHUB_TOKEN in .env",
            "4. Run the repository watch again (or wait for the next 15-minute check)",
            "",
            "After that, the starter files will be committed to the empty repository.",
        ]
    )
    return _send(f"A GitHub token is needed to add code to {repo}", body)


def email_failed(package: ApplicationPackage, reason: str) -> dict:
    company = display_company_name(package.company)
    subject = f"Could not finish applying to {package.role} at {company}"
    body = render_application_email(
        package,
        extra="The form could not be completed automatically. Please submit it yourself using the link and cover letter below.",
    )
    return _send(subject, body, attachments=_resume_attachments(package))


def email_weekly(report: WeeklyReport) -> dict:
    return _send("Your weekly job search update", render_weekly(report))


def render_application_email(package: ApplicationPackage, extra: str = "") -> str:
    company = display_company_name(package.company)
    place = ", ".join(p for p in (package.location, package.country) if p)
    lines = [
        "Hi Derrick,",
        "",
        f"There is a role at {company} that looks like a good fit. Nothing has been sent to the company yet. Please review the CV, cover letter, and answers first.",
        "",
        f"Role: {package.role}",
        f"Company: {company}",
    ]
    if place:
        lines.append(f"Location: {place}")
    lines.append(f"Company application page: {package.job_url}")
    if package.preview_url:
        lines.extend(
            [
                "",
                "Review the CV, cover letter, and answers here:",
                package.preview_url,
                "",
                "On that page you can send the application automatically, or keep the draft and submit it yourself on the company site.",
            ]
        )
    if extra:
        lines.extend(["", extra])
    lines.extend(
        [
            "",
            "Cover letter that would be sent:",
            "",
            package.cover_letter or "(cover letter not generated)",
        ]
    )
    if package.resume_pdf_path:
        lines.extend(
            [
                "",
                "The tailored CV is attached to this email as resume.pdf.",
            ]
        )
    if package.portfolio_links or package.github_links:
        lines.extend(["", "Links that would be included:"])
        for link in [*package.portfolio_links, *package.github_links]:
            lines.append(f"- {link}")
    if package.screening_answers:
        lines.extend(["", "Answers that would be used if the form asks:"])
        for answer in package.screening_answers:
            lines.append(f"- {answer.question} {answer.answer}")
    return "\n".join(lines)


def _resume_attachments(package: ApplicationPackage) -> list[tuple[str, bytes, str]]:
    from jobpilot.storage import read_bytes

    data = read_bytes(package.resume_pdf_path)
    if not data:
        return []
    return [("resume.pdf", data, "application/pdf")]


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
            "If a role is sitting in your inbox, open the review link, check the CV and cover letter, then either send it or submit it yourself on the company's site.",
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
            "",
            "Leave the repository empty. You do not need to clone it or add files yourself.",
            "Once the empty repository exists on GitHub, the starter code will be added automatically.",
        ]
    )
