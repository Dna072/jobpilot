from jobpilot.emailer import render_application_email, render_repo_request, render_weekly
from jobpilot.schemas.application import ApplicationPackage, WeeklyReport
from jobpilot.schemas.common import ResumeType


def test_human_action_email_contains_required_fields():
    package = ApplicationPackage(
        company="Klarna",
        role="Data Engineer",
        job_url="https://example.com/job",
        country="Sweden",
        location="Stockholm",
        match_score=88.0,
        selected_resume=ResumeType.DATA_ENGINEER,
        remaining_human_action="Complete CAPTCHA on Greenhouse.",
    )
    body = render_application_email(package, remaining=package.remaining_human_action or "")
    assert "Klarna" in body
    assert "Data Engineer" in body
    assert "88" in body
    assert "CAPTCHA" in body
    assert "DATA_ENGINEER" in body


def test_repo_request_template():
    body = render_repo_request(
        "Real-Time Event Processing and Analytics Platform",
        "eventpulse",
        "Streaming evidence",
        ["Data Engineer"],
        ["Kafka"],
        "Producers → Kafka → ...",
    )
    assert "ACTION REQUIRED — CREATE REPOSITORY" in body
    assert "eventpulse" in body
    assert "WAITING_FOR_REPOSITORY" in body
    assert "github.com/new" in body


def test_weekly_report_render():
    report = WeeklyReport(
        jobs_discovered=10,
        applications_submitted=2,
        most_requested_skills={"python": 0.81, "kafka": 0.41},
        quality_notes="Quality over volume.",
        strategy="Sweden first.",
    )
    text = render_weekly(report)
    assert "WEEKLY JOB APPLICATION REPORT" in text
    assert "python" in text
    assert "Quality over volume" in text
