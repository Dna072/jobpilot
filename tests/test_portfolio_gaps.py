from jobpilot.analyst import analyze_job
from jobpilot.matching import analyze_gaps
from jobpilot.schemas.common import GapVerdict, WorkMode
from jobpilot.schemas.job import JobPosting


def test_streaming_gap_recommends_new_project():
    posting = JobPosting(
        source="manual",
        company="Nordic Data AB",
        title="Data Platform Engineer",
        location="Stockholm, Sweden",
        work_mode=WorkMode.HYBRID,
        job_url="https://example.com/stream",
        description="Required: Kafka, Python, Spark, AWS, Kubernetes, real-time streaming.",
    )
    gap = analyze_gaps(analyze_job(posting))
    assert gap.verdict == GapVerdict.NEW_PROJECT
    assert gap.proposed_project and "Real-Time" in gap.proposed_project


def test_covered_skills_are_sufficient():
    posting = JobPosting(
        source="manual",
        company="Example",
        title="Data Engineer",
        location="Stockholm, Sweden",
        job_url="https://example.com/ok",
        description="Required: Python, SQL, PostgreSQL, AWS, Airflow, Redshift.",
    )
    gap = analyze_gaps(analyze_job(posting))
    assert gap.verdict in {GapVerdict.EXISTING_SUFFICIENT, GapVerdict.NO_PROJECT_NEEDED}


def test_dbt_prefers_upgrade():
    posting = JobPosting(
        source="manual",
        company="Example",
        title="Analytics Engineer",
        location="Stockholm, Sweden",
        job_url="https://example.com/dbt",
        description="Required: dbt, SQL, Python, Airflow.",
    )
    gap = analyze_gaps(analyze_job(posting))
    assert gap.verdict in {GapVerdict.UPGRADE_EXISTING, GapVerdict.NO_PROJECT_NEEDED, GapVerdict.EXISTING_SUFFICIENT}
