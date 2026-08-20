# Portfolio Inventory

**Generated:** 2026-08-20  
**GitHub user:** [Dna072](https://github.com/Dna072) — 33 public repositories at discovery.  
**Classification:** professional product vs portfolio vs academic vs archival. Portfolio projects must never be listed as employers.

Evidence strength: `strong` (production-style code + tests + docs), `moderate` (working code, thinner ops), `weak` (demo/tutorial/old), `archival`.

## Matrix (target-role evidence)

| Project | Data | Backend | Frontend | ML | Kind |
|---|---|---|---|---|---|
| TPG (NTC) | ✓ | ✓ | ✓ | – | Professional product |
| NTC Redshift/Glue warehouse | ✓ | – | – | – | Professional (resume) |
| SIMSGH | ✓ | ✓ | ✓ | – | Product (NexDev; title not on resume) |
| MedLink | – | ✓ | ✓ | – | Product (NexDev) |
| Arctiq | – | ✓ | ✓ | – | Product (NexDev) |
| ClipForge | – | ✓ | ✓ | ✓ | Portfolio |
| MediaVault | – | ✓ | ✓ | – | Portfolio |
| StreamPulse | ✓ | ✓ | ✓ | – | Portfolio |
| RenderFlow | – | ✓ | ✓ | – | Portfolio (infra) |
| Sparkify Redshift DWH | ✓ | – | – | – | Portfolio / coursework-style |
| Airflow Pipelines | ✓ | – | – | – | Portfolio / coursework-style |
| STEDI Lakehouse | ✓ | – | – | ✓ | Portfolio / coursework-style |
| DRL-JSS | – | – | – | ✓ | Thesis |
| rl-cartpole | – | – | – | ✓ | Academic |
| Portfolio / dna072.github.io | – | – | ✓ | – | Personal site |
| BookingApp-Api | – | ✓ | – | – | Older backend |
| cert_generator | – | ✓ | – | – | NTC-adjacent utility |
| Older ML/Java/C demos | – | – | – | ✓ | Archival |

## Professional / live products

### TPG — Teacher Portal Ghana

- **URL:** https://tpg.ntc.gov.gh
- **Repo:** not public as a dedicated TPG repository
- **Stack (portfolio):** JavaScript, Node.js, Python, PostgreSQL
- **Skills:** nationwide public-sector workflows, APIs, PostgreSQL, production web
- **Target roles:** Backend, Full Stack, Data (as consuming/producing operational data)
- **Evidence strength:** strong as employment evidence (live gov platform); source code not inspectable here
- **Notes:** candidate brief adds licensing, digital certificates, IAM, HA. `cert_generator` supports certificates as a related artifact.

### SIMSGH

- **URL:** https://simsgh.com
- **Organization:** NexDev Technologies (candidate brief + NexDev public post)
- **Skills:** school operations, attendance, grades, fees, notifications
- **Evidence strength:** moderate (live product; no public source, no job title/dates on resume)
- **Target roles:** Full Stack, Backend

### MedLink

- **URL:** https://medlink.nexdev.tech
- **Stack:** TypeScript, React, Next.js, Vite, Node.js, Tailwind
- **Target roles:** Frontend, Full Stack, Backend
- **Evidence strength:** moderate (live URL; no public source in Dna072)

### Arctiq

- **URL:** https://arctiq.nexdev.tech
- **Stack:** TypeScript, JavaScript, React, Vite, Next.js, Express, Tailwind
- **Target roles:** Frontend, Full Stack
- **Evidence strength:** moderate (same caveat)

## Flagship portfolio repositories (inspectable)

### clipforge — AI Video Processing Platform

- **Repo:** https://github.com/Dna072/clipforge
- **Tech:** Python, FastAPI, Redis workers, React dashboard, Docker Compose, mockable AI provider
- **Architecture:** sync API vs async media/AI pipeline
- **Tests / Docker / docs:** yes (production-style README)
- **Skills:** APIs, queues, workers, auth, media pipeline, provider abstraction
- **Target roles:** Backend, Platform, ML-adjacent
- **Evidence:** strong portfolio — explicitly **not** a commercial product

### mediavault — DAM / media library

- **Repo:** https://github.com/Dna072/mediavault
- **Tech:** FastAPI, PostgreSQL FTS, RBAC, JWT rotation, S3/MinIO, React+TS
- **Skills:** auth, multi-tenant RBAC, search, signed URLs, layered architecture
- **Target roles:** Backend, Full Stack
- **Evidence:** strong portfolio

### streampulse — analytics dashboard

- **Repo:** https://github.com/Dna072/streampulse
- **Tech:** FastAPI, PostgreSQL aggregations, React+Recharts, JWT
- **Skills:** analytical SQL, API-backed charts, indexing
- **Target roles:** Analytics Engineer, Backend, Frontend
- **Evidence:** strong portfolio (synthetic data, honestly labelled)

### renderflow — distributed media workers

- **Repo:** https://github.com/Dna072/renderflow
- **Tech:** FastAPI, PostgreSQL, Redis queues, workers, Docker Compose, Kubernetes manifests, FFmpeg
- **Skills:** job state machines, heartbeats, retries, K8s, observability
- **Target roles:** Backend, Platform, Infra
- **Evidence:** strong portfolio (not production traffic)

### sparkify_dwh_aws_redshift

- **Repo:** https://github.com/Dna072/sparkify_dwh_aws_redshift
- **Tech:** Python, S3, Redshift COPY, star schema, boto3 IaC
- **Skills:** warehouse modelling, dist/sort keys, ELT
- **Target roles:** Data Engineer, Data Warehouse Engineer
- **Evidence:** moderate–strong as warehouse design evidence; dataset is Sparkify/Udacity-style

### airflow-pipelines

- **Repo:** https://github.com/Dna072/airflow-pipelines
- **Tech:** Airflow, Python, SQL, AWS, Docker, custom operators, DQ checks
- **Target roles:** Data Engineer, Analytics Engineer
- **Evidence:** moderate–strong orchestration evidence

### stedi-human-balance-analytics

- **Repo:** https://github.com/Dna072/stedi-human-balance-analytics
- **Tech:** Glue, S3, Athena, Spark/PySpark, medallion lakehouse, consent filters
- **Target roles:** Data Engineer, Data Platform, ML-adjacent data
- **Evidence:** moderate–strong lakehouse/governance evidence

### drl-jss — MSc thesis

- **Repo:** https://github.com/Dna072/drl-jss
- **Tech:** Python, deep RL, job-shop simulation (PyTorch / RL libraries)
- **Target roles:** ML Engineer (research-leaning), not a substitute for data-eng Kafka evidence
- **Evidence:** strong as thesis/ML research

## Secondary / older

| Repo | Notes | Strength |
|---|---|---|
| `rl-cartpole` | DQN on Gym CartPole | weak–moderate ML |
| `data-engineering` | Uppsala DE coursework | academic |
| `statistical-machine-learning` | film-dialogue ML notebook | academic |
| `BookingApp-Api` | Node API; thin README | weak backend |
| `cert_generator` | CSV → PDF certificates (JS) | moderate NTC-adjacent |
| `nextjs-blog`, `robo-friends` | intro React/Next | weak frontend |
| `Portfolio` / `dna072.github.io` | Next.js professional site | moderate frontend (the site itself) |
| Java ML / Traffic-Simulator / HashCode | pre-2018 / coursework | archival |

## Highest-value gaps (see also `project-strategy.md`)

1. **Kafka / real-time streaming** — radar says Assess; architecture page has a streaming diagram; no implemented streaming product.
2. **dbt / analytics engineering toolchain** — Airflow+SQL exist; dbt project does not.
3. **Snowflake / Databricks** — commonly requested in Nordic DE roles; not evidenced.
4. **Public TPG/SIMSGH engineering write-up** that carefully separates professional work from portfolio clones.
5. **Three specialized LaTeX resumes** — only one PDF exists.

## Dedup rule

Do not create another “S3 → Redshift star schema” or another “Glue medallion lakehouse.” Prefer **upgrading** Airflow/Sparkify/STEDI or building a **streaming** system that those warehouses currently lack.
