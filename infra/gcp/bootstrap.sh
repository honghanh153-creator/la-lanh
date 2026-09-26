#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID to the Google Cloud project id.}"
REGION="${GCP_REGION:-asia-southeast1}"
SERVICE="${GCP_RUN_SERVICE:-la-lanh-beta}"
SQL_INSTANCE="${GCP_SQL_INSTANCE:-la-lanh-beta-db}"
DB_NAME="${GCP_DB_NAME:-la_lanh}"
DB_USER="${GCP_DB_USER:-la_lanh_app}"
RUN_SERVICE_ACCOUNT="la-lanh-run@${PROJECT_ID}.iam.gserviceaccount.com"
SCHEDULER_SERVICE_ACCOUNT="la-lanh-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"

DATABASE_SECRET="${GCP_DATABASE_SECRET:-la-lanh-database-url}"
HASH_SECRET="${GCP_HASH_SECRET:-la-lanh-guest-hash-key}"
ENCRYPTION_SECRET="${GCP_ENCRYPTION_SECRET:-la-lanh-guest-encryption-key}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

ensure_secret() {
  local name="$1"
  local value="$2"
  if gcloud secrets describe "$name" --project "$PROJECT_ID" >/dev/null 2>&1; then
    echo "Secret already exists: $name"
    return
  fi
  printf '%s' "$value" | gcloud secrets create "$name" \
    --project "$PROJECT_ID" \
    --replication-policy=automatic \
    --data-file=- >/dev/null
  echo "Created secret: $name"
}

require_command gcloud
require_command openssl

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1)"
if [[ -z "$ACTIVE_ACCOUNT" ]]; then
  echo "No active Google Cloud account. Run: gcloud auth login" >&2
  exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null
gcloud projects describe "$PROJECT_ID" >/dev/null
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  logging.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  --project "$PROJECT_ID"

if ! gcloud artifacts repositories describe la-lanh \
  --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud artifacts repositories create la-lanh \
    --repository-format=docker \
    --location "$REGION" \
    --description="Lá Lành beta container images" \
    --project "$PROJECT_ID"
fi

if ! gcloud iam service-accounts describe "$RUN_SERVICE_ACCOUNT" \
  --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create la-lanh-run \
    --display-name="Lá Lành Cloud Run" \
    --project "$PROJECT_ID"
fi

if ! gcloud iam service-accounts describe "$SCHEDULER_SERVICE_ACCOUNT" \
  --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create la-lanh-scheduler \
    --display-name="Lá Lành retention scheduler" \
    --project "$PROJECT_ID"
fi

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${RUN_SERVICE_ACCOUNT}" \
  --role=roles/cloudsql.client \
  --condition=None >/dev/null
if ! gcloud sql instances describe "$SQL_INSTANCE" \
  --project "$PROJECT_ID" >/dev/null 2>&1; then
  if [[ "${CONFIRM_CREATE_BILLABLE_RESOURCES:-}" != "YES" ]]; then
    echo "Cloud SQL is not present. Re-run with CONFIRM_CREATE_BILLABLE_RESOURCES=YES." >&2
    echo "This creates a billable PostgreSQL instance with backups and deletion protection." >&2
    exit 2
  fi
  gcloud sql instances create "$SQL_INSTANCE" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --database-version=POSTGRES_17 \
    --edition=ENTERPRISE \
    --tier=db-g1-small \
    --storage-size=10 \
    --storage-type=SSD \
    --storage-auto-increase \
    --availability-type=zonal \
    --backup-start-time=18:00 \
    --enable-point-in-time-recovery \
    --retained-backups-count=7 \
    --deletion-protection
fi

if ! gcloud sql databases describe "$DB_NAME" --instance "$SQL_INSTANCE" \
  --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud sql databases create "$DB_NAME" \
    --instance "$SQL_INSTANCE" --project "$PROJECT_ID"
fi

if ! gcloud secrets describe "$DATABASE_SECRET" --project "$PROJECT_ID" >/dev/null 2>&1; then
  DB_PASSWORD="${GCP_DB_PASSWORD:-$(openssl rand -hex 24)}"
  if gcloud sql users list --instance "$SQL_INSTANCE" --project "$PROJECT_ID" \
    --filter="name=${DB_USER}" --format='value(name)' | grep -qx "$DB_USER"; then
    gcloud sql users set-password "$DB_USER" \
      --instance "$SQL_INSTANCE" --password "$DB_PASSWORD" --project "$PROJECT_ID"
  else
    gcloud sql users create "$DB_USER" \
      --instance "$SQL_INSTANCE" --password "$DB_PASSWORD" --project "$PROJECT_ID"
  fi
  CONNECTION_NAME="$(gcloud sql instances describe "$SQL_INSTANCE" \
    --project "$PROJECT_ID" --format='value(connectionName)')"
  DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"
  ensure_secret "$DATABASE_SECRET" "$DATABASE_URL"
fi

ensure_secret "$HASH_SECRET" "$(openssl rand -base64 32)"
ensure_secret "$ENCRYPTION_SECRET" "$(openssl rand -base64 32)"

for secret in "$DATABASE_SECRET" "$HASH_SECRET" "$ENCRYPTION_SECRET"; do
  gcloud secrets add-iam-policy-binding "$secret" \
    --project "$PROJECT_ID" \
    --member="serviceAccount:${RUN_SERVICE_ACCOUNT}" \
    --role=roles/secretmanager.secretAccessor \
    --condition=None >/dev/null
done

LOG_EXCLUSION="la-lanh-beta-request-logs"
REQUEST_LOG_FILTER="resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE}\" AND log_id(\"run.googleapis.com/requests\")"
if gcloud logging sinks describe _Default --project "$PROJECT_ID" \
  --format='value(exclusions.name)' | tr ';' '\n' | grep -qx "$LOG_EXCLUSION"; then
  gcloud logging sinks update _Default \
    --project "$PROJECT_ID" \
    --update-exclusion="name=${LOG_EXCLUSION},filter=${REQUEST_LOG_FILTER},description=Do not retain Lá Lành request URLs in the default log bucket" \
    >/dev/null
else
  gcloud logging sinks update _Default \
    --project "$PROJECT_ID" \
    --add-exclusion="name=${LOG_EXCLUSION},filter=${REQUEST_LOG_FILTER},description=Do not retain Lá Lành request URLs in the default log bucket" \
    >/dev/null
fi

echo
echo "Google Cloud foundation is ready."
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Next:    GCP_PROJECT_ID=$PROJECT_ID GCP_REGION=$REGION ./infra/gcp/deploy.sh"
