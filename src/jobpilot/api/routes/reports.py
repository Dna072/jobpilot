from __future__ import annotations

from fastapi import APIRouter

from jobpilot.agents.status import build_weekly_report
from jobpilot.db.models import WeeklyReportRow, get_session
from jobpilot.emailer import render_weekly

router = APIRouter(tags=["reports"])


@router.get("/reports/weekly")
def latest_weekly() -> dict:
    session = get_session()
    try:
        row = session.query(WeeklyReportRow).order_by(WeeklyReportRow.created_at.desc()).first()
        if not row:
            report = build_weekly_report()
            return {"report": report.model_dump(), "text": render_weekly(report)}
        return {"report": row.payload}
    finally:
        session.close()


@router.post("/reports/weekly")
def generate_weekly() -> dict:
    report = build_weekly_report()
    return {"report": report.model_dump(), "text": render_weekly(report)}
