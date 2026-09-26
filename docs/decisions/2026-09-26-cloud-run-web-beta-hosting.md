# Decision: one-origin Cloud Run hosting for the web beta

## Status

Accepted for the closed web beta on 2026-09-26.

## Decision

Build the Vite client and FastAPI service into one container and serve both from one Cloud Run
origin. Use Cloud SQL, Secret Manager, Artifact Registry, Cloud Run Jobs and Cloud Scheduler in the
same Google Cloud project. The first review URL uses Cloud Run's managed `run.app` HTTPS domain.

## Why Firebase Hosting rewrite is not used

Lá Lành currently uses separate host-only cookies for the guest session, CSRF token, owner session,
Radar invite and Radar receipt. Firebase Hosting strips incoming cookies before a Cloud Run rewrite
and permits only a cookie named `__session`. Renaming one cookie would not preserve this contract.
Serving web and API directly from one Cloud Run origin retains the existing same-origin and CSRF
behavior without weakening browser security or expanding the beta scope into an auth migration.

## Consequences

- Static files are served by Cloud Run rather than a global static CDN during the small beta.
- Hashed assets receive immutable cache headers; HTML and API responses do not.
- The beta sends `noindex` headers globally and excludes this service's automatically generated
  request logs from the `_Default` bucket. Cloud Router's temporary buffering means capability
  tokens must move out of URL paths before an open launch.
- A later CDN or external load balancer must preserve all cookies and `Set-Cookie` headers.
- Firebase Hosting can be reconsidered only after a deliberate session architecture change and full
  guest, owner, CSRF, Radar and capability-link regression testing.

## Sources checked

- Firebase Hosting cache and cookie behavior: https://firebase.google.com/docs/hosting/manage-cache
- Cloud Run container deployment: https://docs.cloud.google.com/run/docs/deploying
- Cloud Run Secret Manager integration: https://docs.cloud.google.com/run/docs/configuring/services/secrets
- Cloud SQL backup/PITR guidance: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups
