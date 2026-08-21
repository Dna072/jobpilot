# Database Design

PostgreSQL is the system of record. SQLAlchemy models live in `src/jobpilot/db/models.py`. Alembic migrations in `alembic/`.

## Tables

### candidate_profile

Single-row-capable profile store (versioned).

| Column | Type | Notes |
|---|---|---|
| id | uuid pk | |
| version | int | monotonic |
| full_name | text | |
| email | text | |
| phone | text | |
| location | text | |
| payload | jsonb | structured profile (experience, education, skills with sources) |
| created_at | timestamptz | |

### companies

| Column | Type |
|---|---|
| id | uuid pk |
| name | text |
| name_normalized | text unique |
| website | text |
| careers_url | text |
| greenhouse_board | text |
| lever_site | text |
| country | text |
| notes | text |

### job_sources

| Column | Type |
|---|---|
| id | uuid pk |
| name | text unique |
| kind | text |
| base_url | text |
| enabled | bool |
| rate_limit_per_min | int |

### jobs

| Column | Type |
|---|---|
| id | uuid pk |
| company_id | fk |
| source_id | fk |
| source_job_id | text |
| title | text |
| title_normalized | text |
| location | text |
| country | text |
| city | text |
| work_mode | text |
| job_url | text |
| canonical_url | text |
| description | text |
| salary_min/max | numeric |
| salary_currency | text |
| posted_at / closing_at | timestamptz |
| seniority | text |
| fingerprint | text unique |
| raw | jsonb |
| first_seen_at / last_seen_at | timestamptz |

Unique: `(source_id, source_job_id)` where source_job_id is not null.

### job_requirements

| Column | Type |
|---|---|
| id | uuid pk |
| job_id | fk |
| category | text |
| name | text |
| normalized | text |
| level | text |
| years | numeric |
| raw_span | text |

### portfolio_projects

| Column | Type |
|---|---|
| id | uuid pk |
| name | text unique |
| kind | text |
| repository | text |
| description | text |
| architecture | text |
| evidence_strength | text |
| documentation_quality | text |
| qa_passed | bool |
| target_roles | jsonb |
| technologies | jsonb |
| skills | jsonb |

### portfolio_skills

Join: project_id, skill, category, evidence_strength.

### project_requirements / project_repositories

Planner specs and repo watch records (`requested_name`, `status`, `github_url`, `local_path`, `detected_at`).

### resume_versions

| Column | Type |
|---|---|
| id | uuid pk |
| resume_type | text |
| kind | text (`master` / `tailored`) |
| job_id | fk nullable |
| tex_path | text |
| pdf_path | text |
| page_count | int |
| validation | jsonb |
| created_at | timestamptz |

### applications

| Column | Type |
|---|---|
| id | uuid pk |
| job_id | fk unique |
| status | text |
| match_score | numeric |
| recommendation | text |
| selected_resume_type | text |
| mechanism | text |
| confirmation_id | text |
| confirmation_evidence | jsonb |
| error | text |
| human_action | text |
| submitted_at | timestamptz |
| updated_at | timestamptz |

### application_materials

Resume version, cover letter, screening Q&A, portfolio links.

### agent_runs

| Column | Type |
|---|---|
| id | uuid pk |
| agent | text |
| job_id | uuid nullable |
| action | text |
| result | text |
| duration_ms | int |
| error | text |
| payload | jsonb |
| created_at | timestamptz |

### notifications / weekly_reports

Outbound email audit and stored weekly JSON reports.

## Indexes

- `jobs.fingerprint`
- `jobs.title_normalized, companies.name_normalized, jobs.location`
- `applications.status`
- `agent_runs(agent, created_at)`
