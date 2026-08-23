from pathlib import Path

from fastapi.testclient import TestClient

from jobpilot.apply.ats import parse_greenhouse, parse_lever, submit_official
from jobpilot.apply.submit import attempt_application
from jobpilot.config import get_settings
from jobpilot.db.models import Application, ApplicationMaterial, get_session
from jobpilot.emailer import render_application_email
from jobpilot.schemas.application import ApplicationPackage, ScreeningAnswer
from jobpilot.schemas.common import ApplicationStatus, ResumeType
from jobpilot.schemas.job import JobPosting


def _package(**kwargs) -> ApplicationPackage:
    data = dict(
        company="Klarna",
        role="Data Engineer",
        job_url="https://boards.greenhouse.io/klarna/jobs/12345",
        location="Stockholm",
        country="Sweden",
        match_score=88.0,
        selected_resume=ResumeType.DATA_ENGINEER,
        cover_letter="Dear Hiring Team,\n\nI am writing to apply.\n",
        screening_answers=[
            ScreeningAnswer(question="Located in Europe?", answer="I live in Stockholm, Sweden."),
        ],
        approval_token="preview-token",
        preview_url="https://jobpilot-api.example/apply/preview-token",
    )
    data.update(kwargs)
    return ApplicationPackage(**data)


def test_greenhouse_and_lever_urls_parse():
    assert parse_greenhouse("https://boards.greenhouse.io/spotify/jobs/123") == ("spotify", "123")
    assert parse_greenhouse("https://job-boards.greenhouse.io/klarna/jobs/456") == ("klarna", "456")
    assert parse_greenhouse("https://boards.eu.greenhouse.io/company/jobs/9") == ("company", "9")
    assert parse_lever("https://jobs.lever.co/tretton37/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee") == (
        "tretton37",
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )
    assert parse_greenhouse("https://example.com/jobs/1") is None


def test_unapproved_apply_never_submits_even_when_live(monkeypatch):
    monkeypatch.setenv("JOBPILOT_ALLOW_LIVE_APPLY", "true")
    get_settings.cache_clear()
    posting = JobPosting(
        source="greenhouse",
        company="Klarna",
        title="Data Engineer",
        job_url="https://boards.greenhouse.io/klarna/jobs/12345",
    )
    attempt = attempt_application(posting, _package(), approved=False)
    assert attempt.status == ApplicationStatus.HUMAN_ACTION_REQUIRED
    assert attempt.evidence.get("policy_reason") == "awaiting_approval"


def test_official_submit_stays_human_for_unknown_boards():
    result = submit_official("https://jobs.example.com/apply/1", _package(job_url="https://jobs.example.com/apply/1"))
    assert result["ok"] is False
    assert result.get("human") is True


def test_preview_page_does_not_send_on_get(tmp_path):
    session = get_session()
    app = Application(
        job_id="missing-job",
        status=ApplicationStatus.HUMAN_ACTION_REQUIRED.value,
        approval_token="review-me",
    )
    session.add(app)
    session.flush()
    pdf = tmp_path / "resume.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    package = _package(resume_pdf_path=str(pdf), preview_url="https://example/apply/review-me")
    session.add(
        ApplicationMaterial(
            application_id=app.id,
            cover_letter=package.cover_letter,
            package=package.model_dump(),
        )
    )
    session.commit()
    session.close()

    from jobpilot.api.main import app as fastapi_app

    client = TestClient(fastapi_app)
    page = client.get("/apply/review-me")
    assert page.status_code == 200
    assert "Nothing has been sent yet" in page.text
    assert "Send this application" in page.text
    assert "I'll submit it myself" in page.text
    assert "88" not in page.text
    assert "DATA_ENGINEER" not in page.text
    assert "JobPilot" not in page.text

    forbidden = client.get("/apply/review-me/approve")
    assert forbidden.status_code == 405

    session = get_session()
    still = session.query(Application).filter_by(approval_token="review-me").one()
    assert still.status == ApplicationStatus.HUMAN_ACTION_REQUIRED.value
    session.close()

    resume = client.get("/apply/review-me/resume")
    assert resume.status_code == 200
    assert resume.content.startswith(b"%PDF")

    manual = client.post("/apply/review-me/manual")
    assert manual.status_code == 200
    assert "Nothing was sent" in manual.text


def test_application_email_includes_preview_and_materials():
    body = render_application_email(_package(resume_pdf_path="/tmp/resume.pdf"))
    assert "https://jobpilot-api.example/apply/preview-token" in body
    assert "send the application automatically" in body
    assert "submit it yourself" in body
    assert "Dear Hiring Team" in body
    assert "Located in Europe?" in body
    assert "resume.pdf" in body
    assert "88" not in body
    assert "JobPilot" not in body
    assert "DATA_ENGINEER" not in body
