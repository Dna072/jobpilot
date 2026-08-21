# JobPilot

Autonomous **career-engineering** system for Derrick Adjei: discover European jobs (Sweden first), score them honestly, close portfolio gaps, tailor one of three LaTeX resumes, and apply only through legitimate channels.

This is not a spray-and-pray auto-apply bot. It maximizes *quality-adjusted* applications and **never** marks an application `SUBMITTED` without confirmation evidence.

## What discovery found

The `jobpilot` workspace started empty. Candidate evidence was loaded from:

- Existing PDF resume (`cv/source/Derrick_Adjei_Resume.pdf`)
- GitHub [`Dna072`](https://github.com/Dna072)
- Portfolio site [`dna072.github.io`](https://dna072.github.io)

The three LaTeX masters did **not** exist; they were created from that evidence under `cv/` and must not be overwritten by tailoring.

Full write-up: [`docs/candidate-profile.md`](docs/candidate-profile.md).

## Architecture

```
Job Scout → Analyst → Match → Gap / Project → CV select & tailor → Apply
                                                              ↘ Human action email
```

Agents speak **Pydantic schemas**, not chat. LLM providers are swappable (`LLM_PROVIDER=heuristic|openai`). The heuristic provider keeps tests and offline use deterministic.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
jobpilot init-db
jobpilot seed
jobpilot status
pytest -q
```

Run the control plane:

```bash
jobpilot serve          # FastAPI on :8000
cd frontend && npm install && npm run dev
```

Or: `docker compose up --build` (Postgres, Redis, API, worker, beat, web).

## CLI

```bash
jobpilot status          # pipeline counters
jobpilot scout           # permitted job feeds only
jobpilot cycle           # scout + process
jobpilot cycle --no-scout
jobpilot watch-repos     # detect human-created GitHub repos
jobpilot report          # weekly performance email
```

## Applying

Live HTTP apply is **off** until you set:

```text
JOBPILOT_ALLOW_LIVE_APPLY=true
```

and `applications.dry_run: false` in `config/jobpilot.yaml`.

Even then JobPilot will **not**:

- bypass CAPTCHA or bot detection
- automate LinkedIn
- steal cookies or rotate identities
- reverse-engineer private ATS APIs
- claim success without a confirmation id / page / ATS status

If a human step is required you get:

```text
ACTION REQUIRED — [COMPANY] — [ROLE]
```

with the tailored CV, cover letter, and screening answers attached in the package.

## New repositories

Cursor cannot create GitHub repositories. If a streaming/Kafka (or other) project is justified, JobPilot emails:

```text
ACTION REQUIRED — Create Repository: [PROJECT]
```

and sets `PROJECT_STATUS = WAITING_FOR_REPOSITORY` until the repo appears.

## GCP (always-on)

A laptop is enough for `jobpilot cycle`. Continuous scout / repo-watch / weekly email needs a host.

GCP config lives in [`infra/gcp`](infra/gcp) and is documented in [`docs/gcp.md`](docs/gcp.md):

```bash
export GCP_PROJECT=your-project-id
./scripts/gcp-deploy.sh
```

That provisions Cloud Run (API + dashboard), Cloud SQL, Cloud Scheduler jobs, Secret Manager, and a GCS bucket for generated CVs. Redis/Celery are not used in GCP — Scheduler runs `jobpilot cycle` every six hours.

## Configuration

All targeting, weights, and caps live in [`config/jobpilot.yaml`](config/jobpilot.yaml). Do not hard-code them.

## Honesty rules

- Portfolio repos are never rewritten as KPMG/NTC employment.
- NexDev / SIMSGH / MedLink / Arctiq are product work without a fabricated job title.
- NTC titles/dates differ across resume, LinkedIn, and the candidate brief; all variants are stored, not blended into a new title.
