from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from jobpilot.config import get_settings

router = APIRouter(tags=["ops"])


def authorize_ops(
    authorization: str | None = Header(default=None),
    x_jobpilot_ops_token: str | None = Header(default=None, alias="X-Jobpilot-Ops-Token"),
) -> None:
    token = get_settings().jobpilot_ops_token
    if not token:
        raise HTTPException(status_code=503, detail="JOBPILOT_OPS_TOKEN is not configured")
    provided = x_jobpilot_ops_token
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization.split(" ", 1)[1].strip()
    if provided != token:
        raise HTTPException(status_code=401, detail="unauthorized")


@router.post("/ops/cycle")
def ops_cycle(
    authorization: str | None = Header(default=None),
    x_jobpilot_ops_token: str | None = Header(default=None, alias="X-Jobpilot-Ops-Token"),
    limit: int = 15,
) -> dict:
    authorize_ops(authorization, x_jobpilot_ops_token)
    from jobpilot.agents.orchestrator import run_cycle

    return run_cycle(limit=limit, scout=True)


@router.post("/ops/watch-repos")
def ops_watch(
    authorization: str | None = Header(default=None),
    x_jobpilot_ops_token: str | None = Header(default=None, alias="X-Jobpilot-Ops-Token"),
) -> dict:
    authorize_ops(authorization, x_jobpilot_ops_token)
    from jobpilot.agents.repo_watch import watch_repositories

    return {"updates": watch_repositories()}


@router.post("/ops/weekly-report")
def ops_report(
    authorization: str | None = Header(default=None),
    x_jobpilot_ops_token: str | None = Header(default=None, alias="X-Jobpilot-Ops-Token"),
) -> dict:
    authorize_ops(authorization, x_jobpilot_ops_token)
    from jobpilot.agents.status import send_weekly_report

    result = send_weekly_report()
    return {k: v for k, v in result.items() if k != "body"}
