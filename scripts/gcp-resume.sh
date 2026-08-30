#!/usr/bin/env bash
# Resume a JobPilot GCP deployment that was paused with ./scripts/gcp-stop.sh
#
#   export GCP_PROJECT=skandix-app
#   ./scripts/gcp-resume.sh
set -euo pipefail

PROJECT="${GCP_PROJECT:?Set GCP_PROJECT}"
REGION="${GCP_REGION:-europe-north1}"
SCHEDULER_REGION="${SCHEDULER_REGION:-europe-west1}"

command -v gcloud >/dev/null

gcloud config set project "$PROJECT"

echo "Starting Cloud SQL instance jobpilot..."
if gcloud sql instances describe jobpilot --project="$PROJECT" >/dev/null 2>&1; then
  gcloud sql instances patch jobpilot \
    --project="$PROJECT" \
    --activation-policy=ALWAYS \
    --quiet
  echo "  Cloud SQL is starting (wait a minute before hitting the API)"
else
  echo "  skip jobpilot SQL (not found)"
fi

echo "Restoring Cloud Run services in ${REGION}..."
for svc in jobpilot-api jobpilot-web; do
  if gcloud run services describe "$svc" --region="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
    gcloud run services update "$svc" \
      --region="$REGION" \
      --project="$PROJECT" \
      --max-instances=2 \
      --quiet
    echo "  $svc max-instances=2"
  else
    echo "  skip $svc (not found)"
  fi
done

echo "Resuming Cloud Scheduler jobs in ${SCHEDULER_REGION}..."
for job in jobpilot-cycle jobpilot-watch jobpilot-weekly-report; do
  if gcloud scheduler jobs describe "$job" --location="$SCHEDULER_REGION" --project="$PROJECT" >/dev/null 2>&1; then
    gcloud scheduler jobs resume "$job" --location="$SCHEDULER_REGION" --project="$PROJECT"
    echo "  resumed $job"
  else
    echo "  skip $job (not found)"
  fi
done

TFVARS="$(cd "$(dirname "$0")/.." && pwd)/infra/gcp/terraform/terraform.tfvars"
if [[ -f "$TFVARS" ]]; then
  if grep -q '^paused' "$TFVARS"; then
    sed -i 's/^paused.*/paused = false/' "$TFVARS"
  else
    printf '\npaused = false\n' >> "$TFVARS"
  fi
fi

echo
echo "JobPilot is running again. Cycle and repo-watch will fire on their 15-minute schedule."
