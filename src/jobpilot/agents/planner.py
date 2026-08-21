from __future__ import annotations

from jobpilot.schemas.common import ProjectStatus
from jobpilot.schemas.match import GapReport, GapVerdict
from jobpilot.schemas.portfolio import ProjectSpec

STREAMING_SPEC = ProjectSpec(
    title="Real-Time Event Processing and Analytics Platform",
    repository_name="eventpulse",
    problem=(
        "Batch warehouses in the existing portfolio do not demonstrate convincing "
        "real-time streaming evidence (Kafka, schema validation, stream processing)."
    ),
    objective=(
        "Build a realistic event platform: producers → Kafka → schema validation → "
        "stream processing → lake/warehouse → analytics API → dashboard."
    ),
    target_jobs=["Data Engineer", "Data Platform Engineer", "Backend Engineer"],
    skills_demonstrated=["Kafka", "Python", "Stream Processing", "PostgreSQL", "Docker", "SQL"],
    architecture=(
        "Producers\n   ↓\nKafka\n   ↓\nSchema Validation\n   ↓\nStream Processing\n   ↓\n"
        "Data Lake / Warehouse\n   ↓\nAnalytics API\n   ↓\nDashboard"
    ),
    system_design=(
        "Bounded contexts: ingest, streaming, serving, analytics. At-least-once processing "
        "with idempotent sinks. No fake production traffic claims."
    ),
    technology_choices=["Kafka", "Python", "FastAPI", "PostgreSQL", "Docker Compose"],
    data_flow="JSON events with versioned schemas; late-arriving data windowed in the processor.",
    apis="REST analytics API for KPIs and recent events; health/ready probes.",
    database="PostgreSQL serving store plus object-storage-style lake sink (local/MinIO).",
    infrastructure="Docker Compose locally; optional Kubernetes later — not required for v1.",
    security="No secrets in git; schema validation rejects unknown producers; least-privilege local creds.",
    scalability="Partitioned topics; horizontally scalable stream workers.",
    observability="Structured logs, consumer lag metric, dead-letter topic.",
    testing="Unit tests for schema/idempotency; integration with Redpanda/Kafka testcontainer or compose.",
    cicd="GitHub Actions: lint, test, docker build.",
    deployment="docker compose up --build",
    repository_structure="apps/producer, apps/processor, apps/api, apps/web, infra/, tests/",
    acceptance_criteria=[
        "End-to-end event from producer to dashboard",
        "Schema validation failures go to DLQ",
        "README is first-person and labels this as a portfolio system",
        "Tests and Docker succeed",
    ],
    definition_of_done=[
        "QA agent passes",
        "No secrets committed",
        "Eligible for Data and Backend resumes only after QA",
    ],
    status=ProjectStatus.PROPOSED,
)


def plan_from_gap(gap: GapReport) -> ProjectSpec | None:
    if gap.verdict == GapVerdict.NEW_PROJECT and gap.proposed_project:
        if "real-time" in gap.proposed_project.lower() or "event" in gap.proposed_project.lower():
            return STREAMING_SPEC.model_copy(update={"title": gap.proposed_project})
        return STREAMING_SPEC
    return None
