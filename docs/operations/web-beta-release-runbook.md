# Web beta release runbook

> Hosting note: the active beta target is now Hetzner + Supabase. Follow
> `docs/operations/hetzner-supabase-release-runbook.md`. The Google Cloud sections below are retained
> as the prior deployment design and are not the current execution path.

This runbook gates a Lá Lành web beta that processes birth data, inferred astrology profiles,
relationship inputs, mood and private share capabilities. A reachable URL is not a completed
release.

## Before deployment

- Use a dedicated staging Google Cloud project with billing alerts and named owners.
- Confirm every committed or uncommitted product change intended for the beta is included in the
  build context; do not deploy an older clean commit by accident.
- Run the full repository check. Known failures must be fixed or the affected feature must be
  explicitly disabled and retested before external invitation.
- Confirm the Swiss Ephemeris library and pinned ephemeris-file checksums build successfully.
- Review the privacy notice against the actual fields and vendors in
  `docs/legal/store-privacy-data-map.md`.
- Record the Swiss Ephemeris release posture: compliant AGPL distribution/source offer for the
  complete networked work, or an applicable professional license with retained proof. Staging
  startup rejects an unresolved development posture.
- `asia-southeast1` stores and processes the beta in Singapore. Before inviting Vietnamese testers,
  complete the applicable personal-data processing and cross-border transfer review under Law
  91/2025/QH15 and Decree 356/2025/NĐ-CP, and make the privacy notice name the cloud processor,
  destination, purpose and retention accurately.
- Keep AI generation disabled unless the provider governance gate in the chart synthesis runbook is
  separately approved.

## Security and privacy gates

- Cloud Run, Cloud SQL and scheduled jobs use dedicated service accounts.
- Secret values exist only in Secret Manager; the deployed revision pins concrete versions.
- The Cloud SQL instance has deletion protection, automated backups and point-in-time recovery.
- The database has no `0.0.0.0/0` authorized network. Cloud Run connects through the Cloud SQL
  integration.
- Cookies are `Secure`, host-only and same-origin. Mutation requests still require the CSRF header
  and a trusted exact HTTPS origin.
- API, HTML and capability responses use `Cache-Control: no-store`; share and Radar pages use
  `Referrer-Policy: no-referrer` and cannot be framed.
- Access logs are disabled at the application server. Cloud Run creates request logs automatically,
  so the named `_Default`-sink exclusion for this service must be present and enabled before inviting
  testers. Google documents that Log Router can temporarily buffer entries before routing; URL-borne
  capability tokens therefore remain a closed-beta residual and must move out of paths before an
  open launch. Application logs must not contain request bodies, birth data, coordinates,
  relationship content, cookies, receipt tokens or share tokens.
- Guest and bounded-feedback cleanup jobs both execute successfully and run at least every six
  hours. Alert if no successful execution is recorded within the promised window.
- The user can delete their guest data, and deletion is retested against the deployed database.
- The privacy notice explains active-data retention and the separate Cloud SQL backup retention
  window. Restores must re-apply deletions made after the restored point before serving traffic.
- The consent, purpose, withdrawal and deletion flow is reviewed against Vietnam's Personal Data
  Protection Law 91/2025/QH15, in force from 2026-01-01. This engineering gate is not a substitute
  for legal review before an open public launch.

## Deployment verification

1. Migration job exits successfully before the new service revision receives traffic.
2. `/v1/health` returns 200 and `/v1/ready` confirms database plus chart-engine readiness.
3. `/radar`, `/tarot` and direct SPA deep links load over HTTPS.
4. Complete onboarding, birth input, reveal, Daily Note, private Radar, and one-/three-card Tarot in
   a fresh browser. Confirm the Daily/Radar prompt link opens the intended question without private
   prose or names in the URL.
5. Refresh every important deep link; no route may turn blank or return the SPA for an unknown API.
6. Verify guest resume after refresh, CSRF rejection without the token, and deletion with the token.
7. Verify Radar owner isolation, receipt scoping, share revocation, `no-store`, `noindex` and
   referrer policy using the deployed origin.
8. Verify the request-log exclusion is enabled and that the scheduler identity can invoke only the
   two retention jobs.
9. Run cleanup once and verify aggregate experiment, resonance, and Tarot counts without printing
   payloads.
10. Test rollback to the previous Cloud Run revision without rolling back the database schema.

## Closed-beta operating limits

- Invite a small named cohort first; do not index or advertise the URL publicly.
- Keep Cloud Run at zero minimum and three maximum instances until load evidence justifies a change.
- Monitor 5xx rate, p95 latency, Cloud SQL connections/storage, scheduler failures and billing.
- The in-process admission limiter is a backstop, not a distributed edge limit. Before an open beta,
  add a distributed abuse-control layer and retest proxy/client address handling.

## Current release blockers

- The Google Cloud project, billing account and operator authentication are external state and must
  be verified during the first deployment.
- Swiss Ephemeris AGPL/professional-license posture and evidence have not been supplied by the
  product owner.
- Singapore cross-border processing review and the matching privacy-notice update have not been
  confirmed by the product owner.
- A custom domain is optional for review; DNS ownership and mapping are not complete until observed.
- Any known repository test failure remains a blocker for inviting external testers even if the
  Cloud Run smoke checks pass.

## Official references checked

- Cloud Run deployment: https://docs.cloud.google.com/run/docs/deploying
- Cloud Run automatically generated request logs: https://docs.cloud.google.com/run/docs/logging
- Cloud Logging exclusion routing: https://docs.cloud.google.com/logging/docs/routing/overview
- Cloud Run secrets: https://docs.cloud.google.com/run/docs/configuring/services/secrets
- Cloud SQL backups: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups
- Cloud SQL point-in-time recovery: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/pitr
- Firebase Hosting cookie behavior considered and rejected for this contract:
  https://firebase.google.com/docs/hosting/manage-cache
- Vietnam Personal Data Protection Law 91/2025/QH15 (official government record):
  https://vanban.chinhphu.vn/?docid=214590&pageid=27160&typegroupid=3
