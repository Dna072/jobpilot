from __future__ import annotations

from fastapi import APIRouter, HTTPException

from jobpilot.db.models import Application, Job, get_session

router = APIRouter(tags=["jobs"])


@router.get("/jobs")
def list_jobs(limit: int = 50) -> list[dict]:
    session = get_session()
    try:
        rows = session.query(Job).order_by(Job.first_seen_at.desc()).limit(limit).all()
        out = []
        for job in rows:
            app = session.query(Application).filter_by(job_id=job.id).first()
            out.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company.name if job.company else None,
                    "location": job.location,
                    "country": job.country,
                    "url": job.job_url,
                    "status": app.status if app else None,
                    "match_score": app.match_score if app else None,
                }
            )
        return out
    finally:
        session.close()


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    session = get_session()
    try:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(404, "job not found")
        app = session.query(Application).filter_by(job_id=job.id).first()
        return {
            "id": job.id,
            "title": job.title,
            "company": job.company.name if job.company else None,
            "description": job.description,
            "url": job.job_url,
            "application": {
                "status": app.status if app else None,
                "match_score": app.match_score if app else None,
                "recommendation": app.recommendation if app else None,
                "match_report": app.match_report if app else None,
            },
        }
    finally:
        session.close()
