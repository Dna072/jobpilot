from __future__ import annotations

from fastapi import APIRouter

from jobpilot.db.models import PortfolioProjectRow, ProjectRepository, get_session

router = APIRouter(tags=["projects"])


@router.get("/projects")
def list_projects() -> dict:
    session = get_session()
    try:
        inventory = session.query(PortfolioProjectRow).all()
        waiting = session.query(ProjectRepository).all()
        return {
            "inventory": [
                {
                    "name": p.name,
                    "kind": p.kind,
                    "repository": p.repository,
                    "evidence_strength": p.evidence_strength,
                    "qa_passed": p.qa_passed,
                    "target_roles": p.target_roles,
                }
                for p in inventory
            ],
            "requests": [
                {
                    "name": r.requested_name,
                    "status": r.status,
                    "github_url": r.github_url,
                    "local_path": r.local_path,
                }
                for r in waiting
            ],
        }
    finally:
        session.close()
