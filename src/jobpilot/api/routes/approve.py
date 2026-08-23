from __future__ import annotations

import html
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response

from jobpilot.apply.submit import attempt_application
from jobpilot.db.models import Application, ApplicationMaterial, Job, get_session
from jobpilot.resume.tailor import display_company_name
from jobpilot.schemas.application import ApplicationPackage
from jobpilot.schemas.common import ApplicationStatus, assert_transition, require_submission_evidence
from jobpilot.schemas.job import JobPosting
from jobpilot.storage import read_bytes

router = APIRouter(tags=["approve"])


def _esc(value: str | None) -> str:
    return html.escape(value or "", quote=True)


def _load_by_token(token: str) -> tuple[Application, ApplicationPackage]:
    session = get_session()
    try:
        app = session.query(Application).filter_by(approval_token=token).first()
        if not app:
            raise HTTPException(404, "This review link is not valid.")
        material = (
            session.query(ApplicationMaterial)
            .filter_by(application_id=app.id)
            .order_by(ApplicationMaterial.id.desc())
            .first()
        )
        raw = (material.package if material else {}) or {}
        package = ApplicationPackage.model_validate(raw) if raw else None
        if not package:
            raise HTTPException(404, "The application draft is missing.")
        return app, package
    finally:
        session.close()


@router.get("/apply/{token}", response_class=HTMLResponse)
def preview(token: str) -> str:
    app, package = _load_by_token(token)
    company = _esc(display_company_name(package.company))
    answers = "".join(
        f"<li><strong>{_esc(a.question)}</strong> {_esc(a.answer)}</li>" for a in package.screening_answers
    ) or "<li>No extra answers prepared.</li>"
    links = "".join(
        f'<li><a href="{_esc(link)}">{_esc(link)}</a></li>'
        for link in [*package.portfolio_links, *package.github_links]
    )
    links_block = f"<h2>Links that would be included</h2><ul>{links}</ul>" if links else ""
    letter = _esc(package.cover_letter)
    sent = app.status == ApplicationStatus.SUBMITTED.value
    disabled = "disabled" if sent else ""
    status_note = "This application has already been sent." if sent else "Nothing has been sent yet."
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Review application — {company}</title>
<style>
body {{ font-family: Georgia, serif; max-width: 720px; margin: 40px auto; line-height: 1.5; color: #111; }}
.btn {{ display: inline-block; margin-right: 12px; padding: 10px 16px; text-decoration: none; border-radius: 4px; }}
.send {{ background: #0D47A1; color: white; border: 0; }}
.manual {{ background: #eee; color: #111; border: 0; }}
pre {{ white-space: pre-wrap; background: #f6f6f6; padding: 16px; }}
</style></head><body>
<h1>Review this application</h1>
<p>{status_note}</p>
<p><strong>Role:</strong> {_esc(package.role)}<br>
<strong>Company:</strong> {company}<br>
<strong>Location:</strong> {_esc(package.location)} {_esc(package.country)}</p>
<p><a href="{_esc(package.job_url)}">Open the company application page</a> ·
<a href="/apply/{_esc(token)}/resume">Download the CV</a></p>
<h2>Cover letter</h2>
<pre>{letter}</pre>
<h2>Answers prepared for the form</h2>
<ul>{answers}</ul>
{links_block}
<form method="post" action="/apply/{_esc(token)}/approve" style="display:inline">
  <button class="btn send" {disabled} type="submit">Send this application</button>
</form>
<form method="post" action="/apply/{_esc(token)}/manual" style="display:inline">
  <button class="btn manual" {disabled} type="submit">I'll submit it myself</button>
</form>
</body></html>"""


@router.get("/apply/{token}/resume")
def download_resume(token: str) -> Response:
    _app, package = _load_by_token(token)
    data = read_bytes(package.resume_pdf_path)
    if not data:
        raise HTTPException(404, "The CV file is not available yet.")
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=resume.pdf"})


@router.post("/apply/{token}/approve", response_class=HTMLResponse)
def approve(token: str) -> str:
    session = get_session()
    try:
        app = session.query(Application).filter_by(approval_token=token).first()
        if not app:
            raise HTTPException(404, "This review link is not valid.")
        if app.status == ApplicationStatus.SUBMITTED.value:
            return _message("This application was already sent.")
        material = (
            session.query(ApplicationMaterial)
            .filter_by(application_id=app.id)
            .order_by(ApplicationMaterial.id.desc())
            .first()
        )
        if not material:
            raise HTTPException(404, "The application draft is missing.")
        package = ApplicationPackage.model_validate(material.package)
        job = session.get(Job, app.job_id)
        posting = JobPosting(
            source=job.source.name if job and job.source else "manual",
            company=package.company,
            title=package.role,
            job_url=package.job_url,
            location=package.location,
            country=package.country,
            description="",
        )
        assert_transition(ApplicationStatus(app.status), ApplicationStatus.APPLICATION_IN_PROGRESS)
        app.status = ApplicationStatus.APPLICATION_IN_PROGRESS.value
        attempt = attempt_application(posting, package, approved=True)
        if attempt.status == ApplicationStatus.SUBMITTED:
            require_submission_evidence(attempt.evidence)
            app.status = ApplicationStatus.SUBMITTED.value
            app.confirmation_id = attempt.confirmation_id
            app.confirmation_evidence = attempt.evidence
            app.submitted_at = datetime.now(UTC)
            session.commit()
            return _message("The application was sent. You should hear from the company on their usual channel.")
        app.status = ApplicationStatus.HUMAN_ACTION_REQUIRED.value
        app.human_action = attempt.human_action
        app.error = attempt.error
        session.commit()
        return _message(
            attempt.human_action
            or "The form could not be completed automatically. Please submit it yourself on the company page."
        )
    finally:
        session.close()


@router.post("/apply/{token}/manual", response_class=HTMLResponse)
def manual(token: str) -> str:
    session = get_session()
    try:
        app = session.query(Application).filter_by(approval_token=token).first()
        if not app:
            raise HTTPException(404, "This review link is not valid.")
        app.status = ApplicationStatus.HUMAN_ACTION_REQUIRED.value
        app.human_action = "You chose to submit this one yourself."
        session.commit()
        _, package = _load_by_token(token)
        return _message(
            f"Nothing was sent. Open the company page and paste the cover letter yourself: {package.job_url}"
        )
    finally:
        session.close()


def _message(text: str) -> str:
    return (
        "<!doctype html><html><body style='font-family:Georgia;max-width:640px;margin:40px auto'>"
        f"<p>{_esc(text)}</p></body></html>"
    )
