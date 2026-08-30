# JobPilot

Autonomous **career-engineering** system for Derrick Adjei: discover European jobs (Sweden first), score them honestly, close portfolio gaps, tailor one of three LaTeX resumes, and apply only through legitimate channels.

This is not a spray-and-pray auto-apply bot. It maximizes *quality-adjusted* applications and **never** marks an application `SUBMITTED` without confirmation evidence.

## What discovery found

The `jobpilot` workspace started empty. Candidate evidence was loaded from:

- Official resumes: `cv/source/Derrick_Adjei_Data_Engineer.pdf` and `cv/source/Derrick_Adjei_Backend_Engineer.pdf`
- GitHub [`Dna072`](https://github.com/Dna072)
- Portfolio site [`dna072.github.io`](https://dna072.github.io)

The three LaTeX masters under `cv/` use the same Leslie Cheng template as those PDFs (Fira Sans, navy bars) and must not be overwritten by tailoring. Compile with `./scripts/compile-resumes.sh`.

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
jobpilot scout           # JobTech + ATS boards + EU remote (not LinkedIn/Indeed scrape)
jobpilot cycle           # scout + process
jobpilot cycle --no-scout
jobpilot watch-repos     # detect human-created GitHub repos
jobpilot report          # weekly performance email
```

## Applying

Live apply is on for official Greenhouse Job Board and Lever Postings APIs, **only after you approve**.

Every draft is emailed first: tailored CV (`resume.pdf`), cover letter, screening answers, and a review link. Opening the link does not send anything. On that page you can:

- **Send this application** — submit through the official Greenhouse / Lever endpoint
- **I'll submit it myself** — keep the draft and apply on the company site

JobPilot will **not**:

- send an application without that approval
- bypass CAPTCHA or bot detection
- automate LinkedIn
- steal cookies or rotate identities
- reverse-engineer private ATS APIs
- claim success without a confirmation id / page / ATS status

## New repositories

Cursor cannot create GitHub repositories. If a streaming/Kafka (or other) project is justified, JobPilot emails:

```text
ACTION REQUIRED — Create Repository: [PROJECT]
```

and sets `PROJECT_STATUS = WAITING_FOR_REPOSITORY` until the empty repo appears. Create it on GitHub (no README needed). A token with the `repo` scope (`jobpilot-github-token` / `GITHUB_TOKEN`) is required so the starter code can be pushed. Without that token the dashboard stays at **Repository found — starter code not pushed yet**.

## GCP (always-on)

A laptop is enough for `jobpilot cycle`. Continuous scout / repo-watch / weekly email needs a host.

GCP config lives in [`infra/gcp`](infra/gcp) and is documented in [`docs/gcp.md`](docs/gcp.md):

```bash
export GCP_PROJECT=your-project-id
./scripts/gcp-deploy.sh
```

That provisions Cloud Run (API + dashboard), Cloud SQL, Cloud Scheduler jobs, Secret Manager, and a GCS bucket for generated CVs. Redis/Celery are not used in GCP — Scheduler runs `jobpilot cycle` and `jobpilot-watch` every 15 minutes.

To pause everything without deleting data:

```bash
export GCP_PROJECT=skandix-app
./scripts/gcp-stop.sh
```

Resume with `./scripts/gcp-resume.sh`.

## Configuration

All targeting, weights, and caps live in [`config/jobpilot.yaml`](config/jobpilot.yaml). Do not hard-code them.

## Honesty rules

- Portfolio repos are never rewritten as KPMG/NTC employment.
- NexDev / SIMSGH / MedLink / Arctiq are product work without a fabricated job title.
- NTC titles/dates differ across resume, LinkedIn, and the candidate brief; all variants are stored, not blended into a new title.
