# GCP deployment

JobPilot does **not** have to run on a server for a one-off cycle on your laptop.

It **does** need a long-lived environment if you want it to keep discovering jobs, watching for repositories you create, emailing human-action packages, and sending the Monday report. Leaving a laptop on is enough technically; GCP is the production home.

## Recommended shape (this repo)

Redis/Celery are for local Docker Compose. On GCP they are replaced by **Cloud Scheduler + Cloud Run Jobs**.

```text
Cloud Scheduler (Europe/Stockholm)
  0 */6 * * *     → Cloud Run Job jobpilot-cycle
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

## After deploy

```bash
# Dashboard / API URLs
terraform -chdir=infra/gcp/terraform output

# Ops token (protects POST /api/v1/ops/*)
gcloud secrets versions access latest --secret=jobpilot-ops-token

# Run a cycle now (does not wait for the 6-hour tick)
gcloud run jobs execute jobpilot-cycle --region=europe-north1
```

Live apply stays **off** (`JOBPILOT_ALLOW_LIVE_APPLY=false`).

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

## Tear-down

```bash
terraform -chdir=infra/gcp/terraform apply -var=deletion_protection=false
terraform -chdir=infra/gcp/terraform destroy
```

Cloud SQL deletion protection is on by default so a stray destroy cannot drop the application history.
