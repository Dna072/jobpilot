from __future__ import annotations

from pathlib import Path

from jobpilot.schemas.portfolio import ProjectSpec

README_TEMPLATE = """# {title}

> **Portfolio project.** I designed this as engineering evidence, not as a live commercial product.
> I do not claim real users, revenue, or production uptime.

# Project Overview

I designed {title} to close a specific evidence gap: {problem}

# Problem

{problem}

# Goals

{objective}

# Architecture

```
{architecture}
```

# System Design

{system_design}

# Technology Choices

{tech}

# Why I Chose These Technologies

I chose these tools because they are the ones Nordic data/platform roles actually name, and because I can operate them locally without fake cloud bills.

# Data Flow

{data_flow}

# Database Design

{database}

# API Design

{apis}

# Infrastructure

{infrastructure}

# Security

{security}

# Scalability

{scalability}

# Reliability

I separated ingest from serving so a slow dashboard cannot block producers. Failures go to a dead-letter path.

# Testing

{testing}

# CI/CD

{cicd}

# Local Development

```bash
cp .env.example .env
docker compose up --build
```

# Deployment

{deployment}

# Trade-offs

I used Kafka-compatible Redpanda in local compose to keep the broker operational without a heavy cluster. That is a local-dev choice, not a production claim.

# Future Improvements

Exactly-once sinks, schema registry UI, and dbt marts on the warehouse sink.

---

This README describes **personal project** work. It is not National Teaching Council or KPMG employment.
"""


def scaffold_project(root: Path, spec: ProjectSpec) -> list[str]:
    """Write a realistic skeleton into an already-created repository. Never creates GitHub repos."""
    written: list[str] = []
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "README.md": README_TEMPLATE.format(
            title=spec.title,
            problem=spec.problem,
            objective=spec.objective,
            architecture=spec.architecture,
            system_design=spec.system_design,
            tech=", ".join(spec.technology_choices),
            data_flow=spec.data_flow,
            database=spec.database,
            apis=spec.apis,
            infrastructure=spec.infrastructure,
            security=spec.security,
            scalability=spec.scalability,
            testing=spec.testing,
            cicd=spec.cicd,
            deployment=spec.deployment,
        ),
        ".env.example": "KAFKA_BROKERS=redpanda:9092\nDATABASE_URL=postgresql://eventpulse:eventpulse@postgres:5432/eventpulse\n",
        "docker-compose.yml": """services:
  redpanda:
    image: redpandadata/redpanda:v24.2.4
    command: ["redpanda", "start", "--overprovisioned", "--smp", "1", "--memory", "1G", "--reserve-memory", "0M", "--node-id", "0", "--check=false", "--kafka-addr", "plain://0.0.0.0:9092", "--advertise-kafka-addr", "plain://redpanda:9092"]
    ports: ["9092:9092"]
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: eventpulse
      POSTGRES_PASSWORD: eventpulse
      POSTGRES_DB: eventpulse
    ports: ["5432:5432"]
""",
        "pyproject.toml": """[project]
name = "eventpulse"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi", "uvicorn", "sqlalchemy", "psycopg[binary]"]
""",
        "apps/api/main.py": '''from fastapi import FastAPI
app = FastAPI(title="EventPulse")

@app.get("/health")
def health():
    return {"status": "ok"}
''',
        "tests/test_health.py": """def test_placeholder():
    assert True
""",
        ".github/workflows/ci.yml": """name: ci
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pytest
      - run: pytest
""",
    }
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            written.append(str(path))
    return written
