# System Architecture

JobPilot is an **AI career-engineering system**, not a spray-and-pray auto-apply bot. It maximizes quality-adjusted applications: match quality × interview probability, under a daily cap, with truthful claims and a hard stop at human-only steps.

## Context

```text
                    ┌──────────────────────────────────────────┐
                    │           Operator (Derrick)             │
                    │  email · GitHub repos · human CAPTCHA    │
                    └───────────────┬──────────────────────────┘
                                    │ SMTP / dashboard
                    ┌───────────────▼──────────────────────────┐
                    │              JOB ORCHESTRATOR            │
                    │     FastAPI + Celery + PostgreSQL        │
                    └─┬────────┬────────┬────────┬─────────┬───┘
                      │        │        │        │         │
                 Job Scout  Analyst  Match   Portfolio  Application
                                           Planner/Builder/QA/Docs
                                                CV select/tailor
                                             Notify · Weekly report
```

## Containers (Docker Compose)

| Service | Role |
|---|---|
| `postgres` | System of record (jobs, applications, portfolio, agent runs) |
| `redis` | Celery broker + result backend + rate-limit counters |
| `api` | FastAPI control plane + `jobpilot` CLI inside the image |
| `worker` | Celery workers executing agents |
| `beat` | Periodic scout, repo watch, weekly report |
| `web` | Next.js operator dashboard |
| `tex` (optional profile) | Tectonic/LaTeX compile for resume PDFs |

## Agent communication

Agents never pass free-form chat as control messages. Every hop is a Pydantic schema (see `agent-specifications.md`). The orchestrator persists each hop to `agent_runs` with:

```text
agent, job_id, timestamp, action, result, duration, error
```

## LLM abstraction

```text
LLMProvider (protocol)
    ├── HeuristicProvider     # no network; tests + offline
    ├── OpenAICompatibleProvider
    └── AnthropicProvider
```

Structured outputs are validated with Pydantic. If the LLM fails validation, the heuristic parser is the fallback. The provider is selected by `LLM_PROVIDER` and never hard-coded.

## Data flow (happy path)

1. **Scout** pulls *permitted* feeds (Arbeitnow, Greenhouse boards, Lever postings, optional Adzuna). Respects rate limits. No aggressive scraping, no LinkedIn automation.
2. **Dedup** on job key: source+id, URL, and `(company, normalized title, location)`.
3. **Analyst** extracts required / preferred / nice-to-have skills and constraints.
4. **Match** scores against the candidate profile + portfolio inventory (transparent weights).
5. Below `minimum_match_score` → `REJECTED` / `LOW_PRIORITY`.
6. **Gap agent** decides: evidence sufficient, upgrade existing project, or new project.
7. New project → email `ACTION REQUIRED — CREATE REPOSITORY`, status `WAITING_FOR_REPOSITORY`. JobPilot **does not** create GitHub repos.
8. When the repo appears (workspace path or GitHub list) → Planner → Builder → QA → Documentation. Project may not be cited on a CV until QA passes.
9. **Resume selector** scores the three masters; **tailor** writes `cv/generated/...` without touching masters; compile + visual/text PDF QA.
10. **Application agent** tries legitimate mechanisms in order: official API → ATS API → Greenhouse → Lever → other ATS with a public apply interface → career page form. Stops for CAPTCHA, auth walls, ToS bans, or bot checks.
11. `SUBMITTED` only with evidence (HTTP success body, confirmation id, confirmation page text). Otherwise `FAILED` or `HUMAN_ACTION_REQUIRED`.
12. Email + dashboard + weekly report.

## Security

- Secrets only via environment / `.env` (never committed)
- No session-cookie theft, no identity/IP rotation, no CAPTCHA bypass
- Application HTTP client uses a single configured identity and polite rate limits
- Secret scanning in project QA
- `.gitignore` covers `.env`, tokens, generated PDFs with PII if needed (generated CVs are local artifacts)

## Observability

- Structured JSON logs per agent action
- `GET /api/v1/status` and CLI `jobpilot status`
- `agent_runs` table for audit

## GCP production

Local Docker Compose uses Celery + Redis. GCP replaces the always-on worker with Cloud Scheduler and Cloud Run Jobs so the control plane can scale to zero between ticks.

See [`docs/gcp.md`](gcp.md).

```text
Cloud Scheduler → Cloud Run Job (cycle / watch / report)
Browser → Cloud Run web → Cloud Run api → Cloud SQL + GCS + Secret Manager
```


- LinkedIn Easy Apply bots
- Residential proxy pools / captcha farms
- Reverse-engineered private ATS APIs
- Fake confirmation of applications
