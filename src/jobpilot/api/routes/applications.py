from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from jobpilot.config import public_base_url
from jobpilot.db.models import Application, ApplicationMaterial, get_session
from jobpilot.schemas.common import (
    ApplicationStatus,
    assert_transition,
    require_submission_evidence,
)

router = APIRouter(tags=["applications"])


class HumanCompleteBody(BaseModel):
    confirmation_id: str | None = None
    evidence: dict | None = None
    failed: bool = False
    reason: str | None = None


def _preview_link(token: str | None, request: Request | None = None) -> str | None:
    if not token:
        return None
    base = public_base_url()
    if not base and request is not None:
        base = str(request.base_url).rstrip("/")
    if not base:
        return None
    return f"{base}/apply/{token}"


@router.get("/applications")
def list_applications(request: Request, status: str | None = None, limit: int = 50) -> list[dict]:
    session = get_session()
    try:
        q = session.query(Application)
        if status:
            q = q.filter(Application.status == status)
        rows = q.order_by(Application.updated_at.desc()).limit(limit).all()
        return [
            {
                "id": a.id,
                "job_id": a.job_id,
                "status": a.status,
                "match_score": a.match_score,
                "recommendation": a.recommendation,
                "selected_resume_type": a.selected_resume_type,
                "human_action": a.human_action,
                "confirmation_id": a.confirmation_id,
                "preview_url": _preview_link(a.approval_token, request),
            }
            for a in rows
        ]
    finally:
        session.close()


@router.get("/applications/{application_id}")
def get_application(application_id: str, request: Request) -> dict:
    session = get_session()
    try:
        app = session.get(Application, application_id)
        if not app:
            raise HTTPException(404, "not found")
        materials = session.query(ApplicationMaterial).filter_by(application_id=app.id).all()
        return {
            "id": app.id,
            "status": app.status,
            "match_score": app.match_score,
            "match_report": app.match_report,
            "human_action": app.human_action,
            "preview_url": _preview_link(app.approval_token, request),
            "materials": [m.package for m in materials],
        }
    finally:
        session.close()


@router.post("/applications/{application_id}/human-complete")
def human_complete(application_id: str, body: HumanCompleteBody) -> dict:
    session = get_session()
    try:
        app = session.get(Application, application_id)
        if not app:
            raise HTTPException(404, "not found")
        current = ApplicationStatus(app.status)
        if body.failed:
            assert_transition(current, ApplicationStatus.FAILED)
            app.status = ApplicationStatus.FAILED.value
            app.error = body.reason
            session.commit()
            return {"status": app.status}
        evidence = body.evidence or {}
        if body.confirmation_id:
            evidence["confirmation_id"] = body.confirmation_id
        require_submission_evidence(evidence)
        assert_transition(current, ApplicationStatus.SUBMITTED)
        app.status = ApplicationStatus.SUBMITTED.value
        app.confirmation_id = body.confirmation_id
        app.confirmation_evidence = evidence
        app.submitted_at = datetime.now(UTC)
        session.commit()
        return {"status": app.status}
    finally:
        session.close()
