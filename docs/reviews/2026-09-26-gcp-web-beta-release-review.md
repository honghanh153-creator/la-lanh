# Google Cloud web beta release review

Date: 2026-09-26

Status: complete

Code review: targeted manual due to unrelated branch work. The working tree already contains a
large amount of product work, so widening review to the branch would mix this release slice with
unrelated user changes.

## Verdict

The deployment slice is ready for Google Cloud foundation setup and a first authenticated staging
deployment. It is **not yet approved for inviting external testers** because the product owner has
not supplied the Google Cloud project/billing context, a Swiss Ephemeris release posture, or evidence
that the Singapore cross-border data flow and matching privacy notice were reviewed.

## Actionable findings

| Priority | Finding | Resolution |
|---|---|---|
| Blocker | Swiss Ephemeris network use requires an explicit AGPL-compliant or professional-license posture. | Staging/production configuration and the deploy script now fail closed until the posture and its corresponding operational evidence are supplied. |
| Blocker | `asia-southeast1` stores/processes Vietnamese-user data in Singapore. | Deploy now requires an explicit cross-border review confirmation; the release runbook and privacy inventory name the processor route and legal review gate. |
| High | Cloud Run creates request logs automatically, while existing capability links contain tokens in URL paths. | A named `_Default` sink exclusion prevents this service's request URLs from being retained; global `noindex`/`no-referrer` remain enabled. URL-path capability migration remains required before an open launch because Log Router can buffer entries temporarily and platform traces need separate evidence. |
| Medium | The scheduler identity originally had project-wide Cloud Run invocation authority. | Permission is now granted only on the two retention jobs after they are deployed. |
| Medium | A closed beta could accidentally be indexed. | The Cloud Run adapter now emits `X-Robots-Tag: noindex, nofollow, noarchive` on every response. |
| External | The image has not been built by Cloud Build and the service has not been exercised against Cloud SQL. | Run bootstrap/deploy only after the product owner supplies the project and release confirmations; the scripts stop on migration, cleanup, readiness or smoke-test failure. |

## Security and privacy coverage

- Reviewed secret creation, version pinning and per-secret access grants.
- Reviewed Cloud SQL connector use, absence of authorized public networks, backups, PITR and deletion
  protection.
- Reviewed public service IAM, dedicated runtime/scheduler identities, job-scoped scheduler access
  and billable-resource confirmation.
- Reviewed same-origin cookies/CSRF compatibility, HTML/API cache behavior, CSP, HSTS, frame denial,
  referrer policy and indexing controls.
- Reviewed retention job creation and first-run verification.
- Reviewed current Radar, Lá Chứng and safe-share capability URL behavior against Cloud Run's
  automatically generated request logging.
- Reviewed the current Vietnam Personal Data Protection Law/Decree gate and Swiss Ephemeris dual
  license release gate. This is engineering evidence, not legal advice.

## Validation evidence

- API: 325 tests passed.
- Web: 105 tests passed earlier in this release pass; lint, typecheck and production build passed.
- Cloud adapter: SPA deep-link, asset cache, API 404/no-store, noindex and unresolved-license tests
  passed.
- Static checks: Ruff and MyPy passed; shell syntax and whitespace checks passed.
- Local unified-origin smoke: health, readiness, Radar SPA route and unknown-API 404 passed.
- Actual Google Cloud build/deploy: pending external project/authentication and release confirmations.

## Residuals before open launch

- Move share/capability tokens out of URL paths (for example into a fragment-to-cookie exchange),
  then verify Cloud Logging and Cloud Trace never retain them.
- Add a distributed abuse-control layer; the in-process limiter is only a closed-beta backstop.
- Obtain qualified privacy/legal sign-off and record the required processing/cross-border assessment
  evidence.
- Record Swiss Ephemeris license proof with the released image digest and ephemeris checksum.
- Pin container base images by digest after the first verified Cloud Build, then establish automated
  dependency and image vulnerability scanning.
