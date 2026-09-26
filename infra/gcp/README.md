# Lá Lành web beta on Google Cloud

The beta uses one Cloud Run origin for both the Vite web build and FastAPI. This preserves the
existing guest, CSRF, owner and capability cookies. Do not replace it with a Firebase Hosting
rewrite without redesigning the session contract: Firebase Hosting strips every incoming cookie
except the specially named `__session` cookie.

## What the scripts create

- Artifact Registry repository for immutable container images.
- Cloud SQL for PostgreSQL in the same region as Cloud Run.
- Secret Manager entries for the database URL, hash key and encryption key.
- A least-privilege Cloud Run service account.
- A migration job that must pass before the service is updated.
- Two retention jobs, scheduled every six hours, for expired guests and bounded feedback.
- One public Cloud Run service with a maximum of three instances for the closed beta.
- A named `_Default`-sink exclusion so Cloud Run request URLs for this service are not retained;
  application and job logs remain available without request bodies or personal data.

The default region is `asia-southeast1` (Singapore). The initial review URL is the generated
`run.app` HTTPS URL; a custom domain is optional and can be added later.

## First deployment

Use Google Cloud Shell, or a local terminal with the Google Cloud CLI installed and authenticated.
Run from the repository root:

```bash
export GCP_PROJECT_ID="your-staging-project-id"
export GCP_REGION="asia-southeast1"
export CONFIRM_CREATE_BILLABLE_RESOURCES="YES"
export CONFIRM_VN_DATA_TRANSFER_REVIEW="YES"

# Choose exactly one Swiss Ephemeris release posture after legal/license review:
export LA_LANH_SWISSEPH_LICENSE_MODE="professional"
export SWISSEPH_PRO_LICENSE_REFERENCE="internal-proof-reference"
# Or use AGPL with LA_LANH_SWISSEPH_LICENSE_MODE=agpl and
# CONFIRM_AGPL_COMPLIANCE=YES after the complete networked work complies.

./infra/gcp/bootstrap.sh
./infra/gcp/deploy.sh
```

`bootstrap.sh` refuses to create Cloud SQL until the explicit billing confirmation is present. It
does not print generated credentials. The scheduler identity can invoke only the two retention jobs,
not every Cloud Run workload in the project. `deploy.sh` resolves and pins concrete Secret Manager
versions, migrates the database, deploys the service, verifies retention jobs, and smoke-tests the
result before printing the review URL. The deploy command also refuses to run until the operator
records a Swiss Ephemeris release posture and confirms that the Singapore cross-border data flow has
been reviewed. These confirmations are evidence gates, not substitutes for qualified legal advice.

To add an existing HTTPS custom domain to the trusted-origin list during a later deploy:

```bash
export GCP_APP_ORIGIN="https://beta.example.com"
./infra/gcp/deploy.sh
```

Map the domain to Cloud Run only after DNS ownership is verified. Keep the generated `run.app`
origin trusted until the custom-domain flow has been tested end to end.

## Release and rollback

Every deploy creates a timestamped image and an immutable Cloud Run revision. If smoke testing
fails, do not invite testers. Route traffic back to the last known-good revision in Cloud Run, then
investigate without changing or deleting the database.

Before inviting external testers, follow
[`docs/operations/web-beta-release-runbook.md`](../../docs/operations/web-beta-release-runbook.md).
