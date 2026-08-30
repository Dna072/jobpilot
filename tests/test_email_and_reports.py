from jobpilot.analyst import analyze_job
from jobpilot.emailer import render_application_email, render_repo_request, render_weekly
from jobpilot.matching import match_job
from jobpilot.resume.tailor import cover_letter, display_company_name
from jobpilot.schemas.application import ApplicationPackage, WeeklyReport
from jobpilot.schemas.common import ResumeType
from jobpilot.schemas.job import JobPosting


FORBIDDEN_OUTBOUND = (
    "JobPilot",
    "jobpilot",
    "match score",
    "Match score",
    "transparent rubric",
    "JOBPILOT_",
    "DATA_ENGINEER",
    "BACKEND_ENGINEER",
    "WAITING_FOR_REPOSITORY",
    "Live apply",
)


def test_human_action_email_is_plain_english():
    package = ApplicationPackage(
        company="Klarna",
        role="Data Engineer",
        job_url="https://example.com/job",
        country="Sweden",
        location="Stockholm",
        match_score=88.0,
        selected_resume=ResumeType.DATA_ENGINEER,
        cover_letter="Dear Hiring Team,\n\nI am writing to apply.\n",
        remaining_human_action="Open the job link, attach the CV, paste the cover letter, and submit the form.",
        preview_url="https://example.com/apply/review-token",
    )
    body = render_application_email(package)
    assert "Klarna" in body
    assert "Data Engineer" in body
    assert "https://example.com/job" in body
    assert "https://example.com/apply/review-token" in body
    assert "Dear Hiring Team" in body
    assert "88" not in body
    assert "DATA_ENGINEER" not in body
    for token in FORBIDDEN_OUTBOUND:
        assert token not in body


def test_cover_letter_has_no_system_voice():
    posting = JobPosting(
        source="arbeitnow",
        company="autonomous-teaming",
        title="Robotics Software Engineer - Generalist (mid-level)",
        location="Munich (DEU)",
        country="Germany",
        city="Munich",
        job_url="https://www.arbeitnow.com/jobs/x",
        description="Required: Python, software engineering, APIs. Build reliable services.",
    )
    analysis = analyze_job(posting)
    letter = cover_letter(analysis, match_job(analysis), ResumeType.BACKEND_ENGINEER)
    assert "Autonomous Teaming" in letter
    assert "Robotics Software Engineer" in letter
    assert "Stockholm" in letter
    assert "National Teaching Council" in letter or "KPMG" in letter
    for token in FORBIDDEN_OUTBOUND + ("76%", "75.5", "rubric", "Selected resume", "portfolio repositories"):
        assert token not in letter


def test_display_company_name_humanizes_slugs():
    assert display_company_name("autonomous-teaming") == "Autonomous Teaming"
    assert display_company_name("KPMG Sweden") == "KPMG Sweden"


def test_repo_request_template():
    body = render_repo_request(
        "Real-Time Event Processing and Analytics Platform",
        "eventpulse",
        "Streaming evidence",
        ["Data Engineer"],
        ["Kafka"],
        "Producers → Kafka → ...",
    )
    assert "eventpulse" in body
    assert "github.com/new" in body
    assert "WAITING_FOR_REPOSITORY" not in body
    assert "JobPilot" not in body


def test_weekly_report_render():
    report = WeeklyReport(
        jobs_discovered=10,
        applications_submitted=2,
        most_requested_skills={"python": 0.81, "kafka": 0.41},
        quality_notes="Quality over volume.",
        strategy="Sweden first.",
    )
    text = render_weekly(report)
    assert "Hi Derrick" in text
    assert "python" in text
    assert "JobPilot" not in text
    assert "match score" not in text.lower()
