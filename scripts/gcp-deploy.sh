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
if ! command -v terraform >/dev/null || ! terraform version 2>/dev/null | grep -q '^Terraform v'; then
  cat >&2 <<'EOF'
Terraform is not installed (Cloud Shell ships a stub that only prints install help).
Install the real binary, then re-run this script:

  mkdir -p "$HOME/bin"
  wget -O /tmp/terraform.zip https://releases.hashicorp.com/terraform/1.15.9/terraform_1.15.9_linux_amd64.zip
  unzip -o /tmp/terraform.zip -d /tmp
  mv -f /tmp/terraform "$HOME/bin/terraform"
  export PATH="$HOME/bin:$PATH"
  terraform version

Put this in $HOME/.customize_environment so Cloud Shell keeps it:

  mkdir -p "$HOME/bin"
  export PATH="$HOME/bin:$PATH"
EOF
  exit 1
fi

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

ACCOUNT="$(gcloud config get-value account)"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Cloud Build's service account must be able to push images (this runs before Terraform).
gcloud artifacts repositories add-iam-policy-binding jobpilot \
  --location="$REGION" \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/artifactregistry.writer" \
  --quiet >/dev/null || true

if ! gcloud artifacts repositories describe jobpilot --location="$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create jobpilot \
    --repository-format=docker \
    --location="$REGION" \
    --description="JobPilot images"
fi

if ! gcloud builds submit "$ROOT" \
  --config "$ROOT/infra/gcp/cloudbuild.yaml" \
  --substitutions="_REGION=${REGION},_TAG=${TAG}"; then
  cat >&2 <<EOF

Cloud Build failed. The logged-in account (${ACCOUNT}) needs permission to create builds
in project ${PROJECT}. If you are Owner/Editor of the project, run:

  gcloud services enable cloudbuild.googleapis.com --project=${PROJECT}
  gcloud projects add-iam-policy-binding ${PROJECT} \\
    --member="user:${ACCOUNT}" \\
    --role="roles/cloudbuild.builds.editor"

Also confirm billing is enabled for ${PROJECT}. Then re-run ./scripts/gcp-deploy.sh
EOF
  exit 1
fi

cat > "$TF_DIR/terraform.tfvars" <<EOF
project_id = "${PROJECT}"
region     = "${REGION}"
api_image  = "${REPO}/api:${TAG}"
web_image  = "${REPO}/web:${TAG}"
db_tier    = "${DB_TIER:-db-f1-micro}"
paused     = false
EOF

terraform -chdir="$TF_DIR" init

# If SMTP secrets were created by gcp-secrets.sh first, adopt them so apply does not fail.
import_secret() {
  local addr="$1"
  local secret_id="$2"
  if gcloud secrets describe "$secret_id" --project="$PROJECT" >/dev/null 2>&1; then
    terraform -chdir="$TF_DIR" import -input=false "$addr" \
      "projects/${PROJECT}/secrets/${secret_id}" >/dev/null 2>&1 || true
  fi
}
import_secret google_secret_manager_secret.smtp_host jobpilot-smtp-host
import_secret google_secret_manager_secret.smtp_username jobpilot-smtp-username
import_secret google_secret_manager_secret.smtp_password jobpilot-smtp-password
import_secret google_secret_manager_secret.email_from jobpilot-email-from
import_secret google_secret_manager_secret.email_to jobpilot-email-to
import_secret google_secret_manager_secret.github_token jobpilot-github-token

# Deploy creates the Artifact Registry repo before Cloud Build; adopt it if Terraform
# does not already manage it (otherwise apply fails with HTTP 409).
if gcloud artifacts repositories describe jobpilot --location="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
  terraform -chdir="$TF_DIR" import -input=false \
    google_artifact_registry_repository.jobpilot \
    "projects/${PROJECT}/locations/${REGION}/repositories/jobpilot" >/dev/null 2>&1 || true
fi

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
