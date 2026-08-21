# Project Strategy

Do not create a project because a single posting mentions a tool. Recommend work only when:

1. Multiple desirable jobs require the skill, **or**
2. The skill is strategically important for the target career (Tier 1 data / Tier 2 backend), **or**
3. The project would materially strengthen candidacy.

Never duplicate Sparkify/STEDI/Airflow. Prefer **upgrades** when they produce stronger evidence.

## Current evidence vs Nordic market demand

| Skill | Candidate evidence | Typical DE demand | Action |
|---|---|---|---|
| Python / SQL / PostgreSQL | Strong (employment + portfolio) | Very high | Maintain |
| AWS Glue / Redshift / S3 | Strong (NTC + Sparkify/STEDI) | High in AWS shops | Maintain; name NTC carefully |
| Airflow | Portfolio + resume skill | High | Upgrade: add data-quality contracts / Great Expectations-style checks if missing |
| Spark / PySpark | STEDI | High | Upgrade STEDI or warehouse jobs with larger transforms — not a new toy repo |
| dbt | None | High for Analytics Engineer | **Candidate new project** if ≥N jobs ask |
| Kafka / streaming | None (Assess radar only) | High for platform DE | **Highest-value new project** |
| Snowflake / Databricks | None | High in some SE/NL/DE markets | Only if scout histogram shows demand; do not build two warehouses |
| Kubernetes | RenderFlow portfolio | Medium for DE, high for platform | Cite RenderFlow on backend CV; do not rebuild |
| React / Next | Products + SPAs | High for FE roles | Cite MedLink/Arctiq/Portfolio; no new todo-app |
| RL / PyTorch | Thesis | Low for DE | Keep on ML applications only |

## Ranked recommendations (discovery-time, pre-scout)

Scout will overwrite this ranking with real skill histograms. Until then, strategy rank is:

| Priority | Project | Skills covered | Expected application impact | Implementation cost | Jobs (est.) |
|---|---|---|---|---|---|
| P0 | **Real-Time Event Processing & Analytics Platform** (new repo; wait for human create) | Kafka, schema registry, stream processing, lake/warehouse sink, analytics API, dashboard | Unlocks many “streaming + Kafka” DE/platform roles without lying about NTC | High | Many Tier 1 |
| P1 | **dbt analytics layer on an existing warehouse repo** (upgrade Sparkify or a new `analytics` schema — prefer upgrade) | dbt, testing, docs, semantic marts | Analytics Engineer / modern DE | Medium | Many AE/DE |
| P2 | **Airflow reliability upgrade** (SLA, data contracts, lineage notes) | Airflow, DQ, observability | Strengthens existing DE resume bullets | Low–medium | Incremental |
| P3 | **Public architecture write-up for TPG/SIMSGH** (docs only, truthful, no fake metrics) | System design narrative | Backend/FE CVs | Low | Positioning |
| — | Another Redshift star schema | Warehouse | Low (duplicate) | — | Do not build |
| — | Kafka tutorial / “hello producer” | Keywords only | Harmful | — | Do not build |

## P0 sketch (if/when approved by gap agent)

```text
Producers
   ↓
Kafka
   ↓
Schema Validation
   ↓
Stream Processing
   ↓
Data Lake / Warehouse
   ↓
Analytics API
   ↓
Dashboard
```

Status if recommended: email `ACTION REQUIRED — Create Repository`, `PROJECT_STATUS = WAITING_FOR_REPOSITORY`. Do not pretend the repo exists.

## Resume placement after QA

| Project | Data CV | Backend CV | Frontend CV |
|---|---|---|---|
| Streaming platform | YES | YES | NO (unless dashboard is the story) |
| dbt upgrade | YES | NO | NO |
| RenderFlow | NO (unless infra DE) | YES | NO |
| MediaVault / ClipForge | NO | YES | YES (UI) |
| StreamPulse | YES (analytics SQL) | YES | YES |
| MedLink / Arctiq | NO | YES | YES |
| DRL-JSS | NO | NO | NO (ML CV/applications only) |
