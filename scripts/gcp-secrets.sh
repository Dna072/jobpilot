#!/usr/bin/env bash
# Push SMTP / GitHub secrets from a local .env into Secret Manager.
# Usage: GCP_PROJECT=my-project ./scripts/gcp-secrets.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT:?Set GCP_PROJECT}"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
# read KEY=VALUE lines, ignore comments
while IFS= read -r line; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ -z "${line// }" ]] && continue
  export "$line"
done < "$ENV_FILE"
set +a

gcloud config set project "$PROJECT"

put() {
  local secret="$1"
  local value="${2:-}"
  if [[ -z "$value" || "$value" == "unset" ]]; then
    echo "skip $secret (empty)"
    return
  fi
  printf '%s' "$value" | gcloud secrets versions add "$secret" --data-file=-
  echo "updated $secret"
}

put jobpilot-smtp-host "${SMTP_HOST:-}"
put jobpilot-smtp-username "${SMTP_USERNAME:-}"
put jobpilot-smtp-password "${SMTP_PASSWORD:-}"
put jobpilot-email-from "${EMAIL_FROM:-}"
put jobpilot-email-to "${EMAIL_TO:-}"
put jobpilot-github-token "${GITHUB_TOKEN:-}"
