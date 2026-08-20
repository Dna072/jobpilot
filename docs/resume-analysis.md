# Resume Analysis

**Generated:** 2026-08-20  
**Found in workspace:** none of the three LaTeX masters.  
**Found elsewhere:** one PDF, data-engineer oriented.

Path copied for reference (read-only source, not a master to overwrite):

```text
cv/source/Derrick_Adjei_Resume.pdf
```

The implementation phase recreates three **separate** LaTeX masters from this PDF plus the candidate profile. It does not merge them into one generic CV.

## Data Engineer Resume (existing PDF)

**File:** `Derrick_Adjei_Resume.pdf` (1 page)

### Strengths

- Tight one-page layout; Swedish-market friendly length
- Clear Data Engineer headline and NTC warehouse story (Glue, PostgreSQL, Redshift, star schema, 500k users, DQ, “up to 50%” query improvement)
- Skills row covers Python, Airflow, Spark, SQL, PostgreSQL, MongoDB, AWS (S3, Glue, Redshift, Athena), Elasticsearch, Redis, REST, Docker, CI/CD
- Three relevant data projects: STEDI, Airflow Pipelines, Redshift Warehouse
- Education matches Stockholm targeting (Uppsala MSc)

### Weaknesses

- KPMG bullets are Power Platform / Power BI — weak as *data platform* evidence and slightly repetitive
- No Kafka, dbt, Snowflake, Spark streaming, or data contracts
- Portfolio projects are one-liners; no GitHub URLs in the extracted text
- Does not mention TPG, MedLink, RenderFlow, Kubernetes
- NTC title on this PDF is “Data Engineer (Contract)” only — backend/lead-IT story is suppressed
- Contact line is icon-heavy (risk of ATS/text extraction issues)

### Target roles

Data Engineer, Analytics Engineer, Data Platform / Warehouse / Infrastructure Engineer, ETL/ELT Engineer.

### Strongest projects on this resume

STEDI lakehouse, Airflow pipelines, Sparkify Redshift warehouse, plus NTC production ELT.

### Missing evidence

Kafka/streaming, dbt, Snowflake/Databricks, orchestration at KPMG (if any), infrastructure-as-code beyond boto3, tests/CI mentioned only as skills.

---

## Backend Engineer Resume

**Status at discovery:** does not exist as a separate document.

### Strengths available to build from

- NTC nationwide systems, APIs, PostgreSQL, TPG production platform
- Candidate brief: Lead IT Officer / Software Engineer, IAM, Docker, Kubernetes, HA
- Portfolio: ClipForge, MediaVault, RenderFlow (queues, RBAC, workers, K8s)
- Node/TypeScript products: MedLink, Arctiq, BookingApp-Api

### Weaknesses

- Current PDF does not sell backend seniority (Java/Node/microservices/distributed systems)
- Kubernetes evidence is portfolio (RenderFlow), not KPMG/NTC named on the PDF
- No public TPG source
- Java/C# claims are thin (old academic Java)

### Target roles

Backend Engineer, Python/Node backend, Platform Engineer, API Engineer, Distributed Systems (mid, not staff-level without more evidence).

### Strongest projects for this resume

MediaVault, RenderFlow, ClipForge, TPG, StreamPulse API layer.

### Missing evidence

Public microservice mesh, Kafka, gRPC, deep Java, production k8s at an employer.

---

## Frontend Engineer Resume

**Status at discovery:** does not exist as a separate document.

### Strengths available to build from

- Backend & frontend practice since 2017 (portfolio bio)
- Live UIs: MedLink, Arctiq, TPG, Portfolio site (Next.js + TypeScript)
- Media SaaS SPAs: ClipForge, MediaVault, StreamPulse (React + Vite + Tailwind)
- Stack: React, Next.js, TypeScript, JavaScript, Tailwind, Vite, REST

### Weaknesses

- No dedicated frontend CV; current PDF is almost entirely data engineering
- Accessibility, design systems, performance budgets not documented
- Older demos (`robo-friends`, `nextjs-blog`) are too junior to lead with
- Risk of looking like a data engineer applying sideways unless product work is prominent

### Target roles

Frontend Engineer, React/Next Engineer, Full Stack (frontend-significant).

### Strongest projects for this resume

MedLink, Arctiq, dna072.github.io/Portfolio, StreamPulse UI, MediaVault UI.

### Missing evidence

Design-system ownership, a11y audits, SSR/RSC performance write-ups, test IDs / visual regression.

---

## Comparison

| Dimension | Data (existing) | Backend (to create) | Frontend (to create) |
|---|---|---|---|
| Exists today | Yes (PDF) | No | No |
| Employment proof | NTC warehouse + KPMG automation | NTC/TPG + brief lead-IT | Thin; products carry the story |
| Portfolio proof | Sparkify, Airflow, STEDI | MediaVault, RenderFlow, ClipForge | MedLink, Arctiq, Portfolio, SPAs |
| Main gap | Streaming / dbt / modern AE tools | Kafka + employer k8s | Dedicated FE narrative + a11y/perf |
| Default for Tier 1 DE jobs | **Select** | Only if role is platform/API-heavy | No |
| Default for backend jobs | If data platform backend | **Select** | Full-stack with FE bias |
| Default for FE jobs | No | Full-stack with BE bias | **Select** |

**Selection rule for JobPilot:** score all three against *responsibilities and tech distribution*, not title keywords alone. Store the decision and reasoning. Never overwrite these masters; emit copies under `cv/generated/<company-role-date>/`.
