from __future__ import annotations

import json

import typer
from rich.console import Console

from jobpilot.agents.repo_watch import watch_repositories
from jobpilot.agents.status import format_status, send_weekly_report
from jobpilot.db.models import init_db

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


@app.command()
def status() -> None:
    """Print pipeline counters."""
    init_db()
    console.print(format_status())


@app.command("init-db")
def init_db_cmd() -> None:
    init_db()
    console.print("Database tables created.")


@app.command()
def seed() -> None:
    from jobpilot.agents.orchestrator import seed_knowledge

    seed_knowledge()
    console.print("Candidate profile and portfolio inventory seeded.")


@app.command()
def scout(limit: int = 40) -> None:
    from jobpilot.agents.orchestrator import ingest_postings, seed_knowledge
    from jobpilot.sources.jobs import discover_jobs

    seed_knowledge()
    postings = discover_jobs(limit)
    created = ingest_postings(postings)
    console.print(f"Fetched {len(postings)} postings, inserted {created} new jobs.")


@app.command()
def cycle(limit: int = 15, no_scout: bool = False) -> None:
    from jobpilot.agents.orchestrator import run_cycle

    result = run_cycle(limit=limit, scout=not no_scout)
    console.print_json(data=json.loads(json.dumps(result, default=str)))


@app.command()
def process(job_id: str) -> None:
    from jobpilot.agents.orchestrator import process_job, seed_knowledge

    seed_knowledge()
    console.print_json(data=process_job(job_id))


@app.command("watch-repos")
def watch_repos() -> None:
    init_db()
    updates = watch_repositories()
    console.print_json(data=updates)


@app.command()
def report() -> None:
    init_db()
    result = send_weekly_report()
    console.print_json(data={k: v for k, v in result.items() if k != "body"})
    if result.get("body"):
        console.print(result["body"])


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run("jobpilot.api.main:app", host=host, port=port, reload=False)


@app.command()
def worker() -> None:
    from jobpilot.workers.celery_app import celery

    celery.worker_main(["worker", "--loglevel=info"])


def main() -> None:
    app()


if __name__ == "__main__":
    main()
