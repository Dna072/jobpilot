from celery import Celery

from jobpilot.config import get_settings

settings = get_settings()
celery = Celery("jobpilot", broker=settings.redis_url, backend=settings.redis_url)
celery.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json", timezone="UTC")


@celery.task(name="jobpilot.scout")
def task_scout() -> dict:
    from jobpilot.agents.orchestrator import run_cycle

    return run_cycle(limit=20, scout=True)


@celery.task(name="jobpilot.watch_repos")
def task_watch_repos() -> list:
    from jobpilot.agents.repo_watch import watch_repositories

    return watch_repositories()


@celery.task(name="jobpilot.weekly_report")
def task_weekly_report() -> dict:
    from jobpilot.agents.status import send_weekly_report

    return send_weekly_report()


@celery.on_after_configure.connect
def setup_periodic(sender, **kwargs) -> None:
    sender.add_periodic_task(15 * 60, task_scout.s(), name="scout-every-15m")
    sender.add_periodic_task(15 * 60, task_watch_repos.s(), name="repo-watch-15m")
    sender.add_periodic_task(7 * 24 * 3600, task_weekly_report.s(), name="weekly-report")
