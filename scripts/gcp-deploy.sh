#!/usr/bin/env bash
# Provision JobPilot on GCP: Artifact Registry, images, Terraform, secrets.
# Prerequisites: gcloud + terraform, billing-enabled project, Owner or equivalent.
#
#   export GCP_PROJECT=your-project-id
#   export GCP_REGION=europe-north1
#   ./scripts/gcp-deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:?Set GCP_PROJECT to your GCP project id}"
REGION="${GCP_REGION:-europe-north1}"
TAG="${IMAGE_TAG:-latest}"
TF_DIR="$ROOT/infra/gcp/terraform"
REPO="${REGION}-docker.pkg.dev/${PROJECT}/jobpilot"

command -v gcloud >/dev/null
command -v terraform >/dev/null

gcloud config set project "$PROJECT"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com

if ! gcloud artifacts repositories describe jobpilot --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create jobpilot \
    --repository-format=docker \
    --location="$REGION" \
    --description="JobPilot images"
fi

gcloud builds submit "$ROOT" \
  --config "$ROOT/infra/gcp/cloudbuild.yaml" \
  --substitutions="_REGION=${REGION},_TAG=${TAG}"

cat > "$TF_DIR/terraform.tfvars" <<EOF
project_id = "${PROJECT}"
region     = "${REGION}"
api_image  = "${REPO}/api:${TAG}"
web_image  = "${REPO}/web:${TAG}"
db_tier    = "${DB_TIER:-db-f1-micro}"
EOF

terraform -chdir="$TF_DIR" init
terraform -chdir="$TF_DIR" apply ${TF_AUTO_APPROVE:-}

if [[ -f "$ROOT/.env" ]]; then
  GCP_PROJECT="$PROJECT" "$ROOT/scripts/gcp-secrets.sh"
fi

echo
echo "API: $(terraform -chdir="$TF_DIR" output -raw api_url)"
echo "Web: $(terraform -chdir="$TF_DIR" output -raw web_url)"
echo "Ops token secret: $(terraform -chdir="$TF_DIR" output -raw ops_token_secret)"
echo
echo "Read the ops token with:"
echo "  gcloud secrets versions access latest --secret=jobpilot-ops-token"
echo "Manually run a cycle:"
echo "  gcloud run jobs execute jobpilot-cycle --region=${REGION}"
