#!/usr/bin/env bash
# Pause JobPilot on GCP without deleting data.
# Stops the 15-minute scout/watch, the weekly email, the public API/dashboard,
# and (by default) Cloud SQL so you are not billed for a running database.
#
#   export GCP_PROJECT=skandix-app
#   ./scripts/gcp-stop.sh
#
# Resume later with ./scripts/gcp-resume.sh
# Use --keep-sql if you only want to pause jobs and leave Cloud SQL running.
set -euo pipefail

PROJECT="${GCP_PROJECT:?Set GCP_PROJECT}"
REGION="${GCP_REGION:-europe-north1}"
SCHEDULER_REGION="${SCHEDULER_REGION:-europe-west1}"
KEEP_SQL=false

for arg in "$@"; do
  case "$arg" in
    --keep-sql) KEEP_SQL=true ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

command -v gcloud >/dev/null

gcloud config set project "$PROJECT"

echo "Pausing Cloud Scheduler jobs in ${SCHEDULER_REGION}..."
for job in jobpilot-cycle jobpilot-watch jobpilot-weekly-report; do
  if gcloud scheduler jobs describe "$job" --location="$SCHEDULER_REGION" --project="$PROJECT" >/dev/null 2>&1; then
    gcloud scheduler jobs pause "$job" --location="$SCHEDULER_REGION" --project="$PROJECT"
    echo "  paused $job"
  else
    echo "  skip $job (not found)"
  fi
done

echo "Scaling Cloud Run services to zero in ${REGION}..."
for svc in jobpilot-api jobpilot-web; do
  if gcloud run services describe "$svc" --region="$REGION" --project="$PROJECT" >/dev/null 2>&1; then
    gcloud run services update "$svc" \
      --region="$REGION" \
      --project="$PROJECT" \
      --max-instances=0 \
      --quiet
    echo "  $svc max-instances=0"
  else
    echo "  skip $svc (not found)"
  fi
done

if [[ "$KEEP_SQL" == "true" ]]; then
  echo "Leaving Cloud SQL running (--keep-sql)."
else
  echo "Stopping Cloud SQL instance jobpilot (data is kept)..."
  if gcloud sql instances describe jobpilot --project="$PROJECT" >/dev/null 2>&1; then
    gcloud sql instances patch jobpilot \
      --project="$PROJECT" \
      --activation-policy=NEVER \
      --quiet
    echo "  Cloud SQL is stopped"
  else
    echo "  skip jobpilot SQL (not found)"
  fi
fi

TFVARS="$(cd "$(dirname "$0")/.." && pwd)/infra/gcp/terraform/terraform.tfvars"
if [[ -f "$TFVARS" ]]; then
  if grep -q '^paused' "$TFVARS"; then
    sed -i 's/^paused.*/paused = true/' "$TFVARS"
  else
    printf '\npaused = true\n' >> "$TFVARS"
  fi
  echo "Set paused = true in infra/gcp/terraform/terraform.tfvars so the next apply does not start jobs again."
fi

echo
echo "JobPilot is paused. Nothing will scout, watch GitHub, or send application emails."
echo "To start it again:"
echo "  export GCP_PROJECT=${PROJECT}"
echo "  ./scripts/gcp-resume.sh"
