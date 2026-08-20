from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jobpilot import __version__
from jobpilot.api.routes import applications, jobs, projects, reports, status
from jobpilot.db.models import init_db

app = FastAPI(title="JobPilot", version=__version__, description="Career-engineering control plane")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(status.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.on_event("startup")
def startup() -> None:
    init_db()
    from jobpilot.agents.orchestrator import seed_knowledge

    seed_knowledge()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}
