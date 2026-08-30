# GCP deployment

JobPilot does **not** have to run on a server for a one-off cycle on your laptop.

It **does** need a long-lived environment if you want it to keep discovering jobs, watching for repositories you create, emailing human-action packages, and sending the Monday report. Leaving a laptop on is enough technically; GCP is the production home.

## Recommended shape (this repo)

Redis/Celery are for local Docker Compose. On GCP they are replaced by **Cloud Scheduler + Cloud Run Jobs**.

```text
Cloud Scheduler (Europe/Stockholm)
  */15 * * * *    → Cloud Run Job jobpilot-cycle
  */15 * * * *    → Cloud Run Job jobpilot-watch
  0 7 * * 1       → Cloud Run Job jobpilot-report

Browser  →  Cloud Run jobpilot-web  →  Cloud Run jobpilot-api
                                         │
                         Cloud SQL Postgres (db-f1-micro)
                         Secret Manager
                         GCS (generated CVs)
```

Region default: **europe-north1** (Finland). Cloud Scheduler itself is created in **europe-west1** because Scheduler is not available in every region.

Estimated cost at idle: Cloud SQL f1-micro dominates (~USD 7–12/month). Cloud Run scales to zero.

The API image installs Tectonic so tailored CVs compile with the same Fira Sans / navy-bar look as `cv/source/*.pdf`.

## Prerequisites

1. A GCP project with billing enabled
2. `gcloud` and real Terraform **1.15.9** (latest stable as of 2026-08-19). Cloud Shell’s `terraform` is a stub. There is no 1.59.9.
3. You can create Cloud SQL and Cloud Run resources (Owner or a custom role with those APIs)

```bash
gcloud auth login
gcloud auth application-default login
export GCP_PROJECT=your-project-id
export GCP_REGION=europe-north1
```

Fill SMTP in `.env` (same keys as local). Deploy:

```bash
chmod +x scripts/gcp-deploy.sh scripts/gcp-secrets.sh
./scripts/gcp-deploy.sh
```

The script builds images with Cloud Build, applies Terraform, and uploads SMTP/GitHub secrets from `.env`.

### Secret `NOT_FOUND` / `Listed 0 items`

`gcloud secrets list --filter="name~jobpilot"` showing nothing means Terraform has not created the Secret Manager containers yet. `gcp-secrets.sh` now creates those secrets if they are missing, then writes your `.env` values.

```bash
export GCP_PROJECT=skandix-app
./scripts/gcp-secrets.sh
gcloud secrets list --filter="name~jobpilot"
```

That only loads mail settings. Cloud Run / Cloud SQL still require `./scripts/gcp-deploy.sh` after Terraform is installed.

### Cloud Build `PERMISSION_DENIED`

`gcloud builds submit` needs **Cloud Build Editor** (or Owner) on the project. Creating an Artifact Registry repo is a different permission, so that step can succeed while the build still fails.

```bash
ACCOUNT="$(gcloud config get-value account)"
gcloud services enable cloudbuild.googleapis.com --project="$GCP_PROJECT"
gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
  --member="user:${ACCOUNT}" \
  --role="roles/cloudbuild.builds.editor"
```

If that binding itself is denied, the project Owner must grant you `roles/cloudbuild.builds.editor` or `roles/editor`. Wait 1–2 minutes, then re-run `./scripts/gcp-deploy.sh`.

### Artifact Registry `409 already exists`

`gcp-deploy.sh` creates the `jobpilot` Docker repo so Cloud Build can push, then Terraform also declares that repo. Re-run after pull — the script imports the existing repo so apply does not try to create it again.

### Cloud SQL `Invalid Tier (db-f1-micro) for (ENTERPRISE_PLUS)`

PostgreSQL 16 defaults to Enterprise Plus, which only accepts `db-perf-optimized-N-*` machines. The Terraform now sets `edition = "ENTERPRISE"` so `db-f1-micro` is valid. If a failed `jobpilot` instance is stuck, delete it before re-applying:

```bash
gcloud sql instances delete jobpilot --project=skandix-app
```

### Cloud Run `reserved env names: PORT`

Cloud Run sets `PORT` itself (this repo listens on 8080 via `container_port`). Do not put `PORT` in Terraform `env` blocks. Pull and re-apply if you hit this error.

## After deploy

```bash
# Dashboard / API URLs
terraform -chdir=infra/gcp/terraform output

# Ops token (protects POST /api/v1/ops/*)
gcloud secrets versions access latest --secret=jobpilot-ops-token

# Run a cycle or repo watch now (does not wait for the 15-minute tick)
gcloud run jobs execute jobpilot-cycle --region=europe-north1
gcloud run jobs execute jobpilot-watch --region=europe-north1
```

Live apply is **on**, but nothing is sent until you open the review email and choose **Send this application**. Greenhouse uses the official Job Board API. Lever stays manual unless `LEVER_API_KEY` is set.

### Empty GitHub repo, no code

The watch job can see a public repo without a token, but it cannot push files until Secret Manager `jobpilot-github-token` is a GitHub personal access token with the `repo` scope (not `unset`).

```bash
# after putting GITHUB_TOKEN=ghp_... in .env
export GCP_PROJECT=skandix-app
./scripts/gcp-secrets.sh
gcloud run jobs execute jobpilot-watch --region=europe-north1
```

## Manual Terraform

```bash
cp infra/gcp/terraform/terraform.tfvars.example infra/gcp/terraform/terraform.tfvars
# edit project_id and image URIs after the first Cloud Build
terraform -chdir=infra/gcp/terraform init
terraform -chdir=infra/gcp/terraform apply
```

## What is not automated

- Creating the GCP project / attaching billing
- Creating GitHub repositories for portfolio work
- LinkedIn or CAPTCHA
- Marking applications `SUBMITTED` without confirmation evidence

## Pause without deleting data

To stop scout, repo-watch, emails, and the public site **for now** (Cloud SQL data stays):

```bash
export GCP_PROJECT=skandix-app
./scripts/gcp-stop.sh
```

That pauses the three Scheduler jobs, sets Cloud Run max instances to 0, and stops the Cloud SQL instance (`activation-policy=NEVER`). Add `--keep-sql` if you only want to pause jobs.

Start it again later:

```bash
export GCP_PROJECT=skandix-app
./scripts/gcp-resume.sh
```

Do **not** run `./scripts/gcp-deploy.sh` while you want it paused — deploy writes `paused = false` and would start the jobs again.

## Tear-down

```bash
terraform -chdir=infra/gcp/terraform apply -var=deletion_protection=false
terraform -chdir=infra/gcp/terraform destroy
```

Cloud SQL deletion protection is on by default so a stray destroy cannot drop the application history.
