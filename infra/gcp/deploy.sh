#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID to the Google Cloud project id.}"
REGION="${GCP_REGION:-asia-southeast1}"
SERVICE="${GCP_RUN_SERVICE:-la-lanh-beta}"
SQL_INSTANCE="${GCP_SQL_INSTANCE:-la-lanh-beta-db}"
RUN_SERVICE_ACCOUNT="la-lanh-run@${PROJECT_ID}.iam.gserviceaccount.com"
SCHEDULER_SERVICE_ACCOUNT="la-lanh-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"
DATABASE_SECRET="${GCP_DATABASE_SECRET:-la-lanh-database-url}"
HASH_SECRET="${GCP_HASH_SECRET:-la-lanh-guest-hash-key}"
ENCRYPTION_SECRET="${GCP_ENCRYPTION_SECRET:-la-lanh-guest-encryption-key}"
MIGRATION_JOB="${SERVICE}-migrate"
GUEST_CLEANUP_JOB="${SERVICE}-cleanup-guests"
FEEDBACK_CLEANUP_JOB="${SERVICE}-cleanup-feedback"
IMAGE_TAG="$(date -u +%Y%m%d-%H%M%S)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/la-lanh/web-beta:${IMAGE_TAG}"
SWISSEPH_LICENSE_MODE="${LA_LANH_SWISSEPH_LICENSE_MODE:-}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

secret_version() {
  local name="$1"
  local version
  version="$(gcloud secrets versions list "$name" \
    --project "$PROJECT_ID" \
    --filter='state=ENABLED' \
    --sort-by='~createTime' \
    --limit=1 \
    --format='value(name)')"
  [[ -n "$version" ]] || {
    echo "No enabled version found for secret: $name" >&2
    exit 1
  }
  basename "$version"
}

deploy_job() {
  local job="$1"
  shift
  gcloud run jobs deploy "$job" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --image "$IMAGE" \
    --service-account "$RUN_SERVICE_ACCOUNT" \
    --set-cloudsql-instances "$CONNECTION_NAME" \
    --set-secrets "$SECRET_BINDINGS" \
    --set-env-vars "$BASE_ENV" \
    --max-retries=0 \
    --task-timeout=10m \
    "$@"
}

grant_scheduler_job_access() {
  local job="$1"
  gcloud run jobs add-iam-policy-binding "$job" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --member="serviceAccount:${SCHEDULER_SERVICE_ACCOUNT}" \
    --role=roles/run.invoker \
    --condition=None >/dev/null
}

upsert_schedule() {
  local scheduler_name="$1"
  local run_job="$2"
  local schedule="$3"
  local uri="https://run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${run_job}:run"
  local common=(
    --location "$REGION"
    --schedule "$schedule"
    --time-zone "Etc/UTC"
    --uri "$uri"
    --http-method POST
    --message-body '{}'
    --headers 'Content-Type=application/json'
    --oauth-service-account-email "$SCHEDULER_SERVICE_ACCOUNT"
    --oauth-token-scope 'https://www.googleapis.com/auth/cloud-platform'
    --project "$PROJECT_ID"
  )
  if gcloud scheduler jobs describe "$scheduler_name" \
    --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
    gcloud scheduler jobs update http "$scheduler_name" "${common[@]}"
  else
    gcloud scheduler jobs create http "$scheduler_name" "${common[@]}"
  fi
}

require_command gcloud
require_command curl

case "$SWISSEPH_LICENSE_MODE" in
  agpl)
    if [[ "${CONFIRM_AGPL_COMPLIANCE:-}" != "YES" ]]; then
      echo "Set CONFIRM_AGPL_COMPLIANCE=YES only after the complete networked work meets AGPL obligations." >&2
      exit 2
    fi
    ;;
  professional)
    if [[ -z "${SWISSEPH_PRO_LICENSE_REFERENCE:-}" ]]; then
      echo "Set SWISSEPH_PRO_LICENSE_REFERENCE to the retained professional-license evidence reference." >&2
      exit 2
    fi
    ;;
  *)
    echo "Set LA_LANH_SWISSEPH_LICENSE_MODE to agpl or professional before deployment." >&2
    exit 2
    ;;
esac

if [[ "${CONFIRM_VN_DATA_TRANSFER_REVIEW:-}" != "YES" ]]; then
  echo "Set CONFIRM_VN_DATA_TRANSFER_REVIEW=YES after reviewing the Singapore cross-border data flow." >&2
  exit 2
fi

gcloud config set project "$PROJECT_ID" >/dev/null

for secret in "$DATABASE_SECRET" "$HASH_SECRET" "$ENCRYPTION_SECRET"; do
  gcloud secrets describe "$secret" --project "$PROJECT_ID" >/dev/null
done

CONNECTION_NAME="$(gcloud sql instances describe "$SQL_INSTANCE" \
  --project "$PROJECT_ID" --format='value(connectionName)')"
DATABASE_VERSION="$(secret_version "$DATABASE_SECRET")"
HASH_VERSION="$(secret_version "$HASH_SECRET")"
ENCRYPTION_VERSION="$(secret_version "$ENCRYPTION_SECRET")"
SECRET_BINDINGS="LA_LANH_DATABASE_URL=${DATABASE_SECRET}:${DATABASE_VERSION},LA_LANH_GUEST_HASH_KEY=${HASH_SECRET}:${HASH_VERSION},LA_LANH_GUEST_ENCRYPTION_KEY=${ENCRYPTION_SECRET}:${ENCRYPTION_VERSION}"
BASE_ENV="^@^LA_LANH_ENVIRONMENT=staging@LA_LANH_CORS_ORIGINS=[\"https://placeholder.invalid\"]@LA_LANH_GUEST_COOKIE_SECURE=true@LA_LANH_NATIVE_APP_ENABLED=false@LA_LANH_GENERATION_ENABLED=false@LA_LANH_GENERATION_PROVIDER=disabled@LA_LANH_LOG_LEVEL=INFO@LA_LANH_REQUIRE_WEB_DIST=true@LA_LANH_SWISSEPH_LICENSE_MODE=${SWISSEPH_LICENSE_MODE}"

gcloud builds submit . --project "$PROJECT_ID" --tag "$IMAGE"

deploy_job "$MIGRATION_JOB" --command=alembic --args=upgrade,head
gcloud run jobs execute "$MIGRATION_JOB" \
  --project "$PROJECT_ID" --region "$REGION" --wait

gcloud run deploy "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --image "$IMAGE" \
  --service-account "$RUN_SERVICE_ACCOUNT" \
  --set-cloudsql-instances "$CONNECTION_NAME" \
  --set-secrets "$SECRET_BINDINGS" \
  --set-env-vars "$BASE_ENV" \
  --allow-unauthenticated \
  --ingress=all \
  --execution-environment=gen2 \
  --cpu=1 \
  --memory=1Gi \
  --concurrency=20 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=60 \
  --port=8080

SERVICE_URL="$(gcloud run services describe "$SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
ORIGINS="[\"${SERVICE_URL}\"]"
if [[ -n "${GCP_APP_ORIGIN:-}" ]]; then
  [[ "$GCP_APP_ORIGIN" == https://* ]] || {
    echo "GCP_APP_ORIGIN must use https://" >&2
    exit 1
  }
  ORIGINS="[\"${SERVICE_URL}\",\"${GCP_APP_ORIGIN%/}\"]"
fi
gcloud run services update "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --update-env-vars="^@^LA_LANH_CORS_ORIGINS=${ORIGINS}"

deploy_job "$GUEST_CLEANUP_JOB" \
  --command=python --args=-m,scripts.cleanup_guests,--batch-size,500
deploy_job "$FEEDBACK_CLEANUP_JOB" \
  --command=python --args=-m,scripts.cleanup_expired,--batch-size,500
grant_scheduler_job_access "$GUEST_CLEANUP_JOB"
grant_scheduler_job_access "$FEEDBACK_CLEANUP_JOB"

upsert_schedule "${SERVICE}-guest-retention" "$GUEST_CLEANUP_JOB" "25 */6 * * *"
upsert_schedule "${SERVICE}-feedback-retention" "$FEEDBACK_CLEANUP_JOB" "40 */6 * * *"

gcloud run jobs execute "$GUEST_CLEANUP_JOB" \
  --project "$PROJECT_ID" --region "$REGION" --wait
gcloud run jobs execute "$FEEDBACK_CLEANUP_JOB" \
  --project "$PROJECT_ID" --region "$REGION" --wait

curl --fail --silent --show-error --retry 8 --retry-all-errors \
  --retry-delay 3 "${SERVICE_URL}/v1/health" >/dev/null
curl --fail --silent --show-error --retry 8 --retry-all-errors \
  --retry-delay 3 "${SERVICE_URL}/v1/ready" >/dev/null
curl --fail --silent --show-error --retry 8 --retry-all-errors \
  --retry-delay 3 -H 'Accept: text/html' "${SERVICE_URL}/radar" >/dev/null

echo
echo "Lá Lành beta is live: ${SERVICE_URL}"
echo "Image: ${IMAGE}"
echo "Secret versions are pinned in this Cloud Run revision."
