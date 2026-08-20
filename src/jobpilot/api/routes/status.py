from __future__ import annotations

from fastapi import APIRouter

from jobpilot.agents.status import collect_status, format_status

router = APIRouter(tags=["status"])


@router.get("/status")
def status() -> dict:
    stats = collect_status()
    stats["text"] = format_status(stats)
    return stats
