---
title: Radar capacity and Google privacy remediation
date: 2026-10-11
status: candidate-verified-release-gates-open
---

# Radar and privacy remediation

Scope is the reported Radar resource-exhaustion finding and the privacy/configuration gaps from the completed partial Security Scan. Preserve the existing IAM/content release changes. This document is not a production release receipt or a legal compliance certification.

## Acceptance criteria

- [x] Both Radar creation modes share an owner-level limit of 100 retained rows, including expired, withdrawn and revoked rows. Enforcement is in the database transaction, not just the UI or one server process.
- [x] List responses default to 20 summaries, never exceed 50, and support owner-bound keyset pagination and mode filtering. Result ciphertext is not loaded for summary lists.
- [x] Sharing an older invite reads only the authorized target row, not the whole history.
- [x] An unchanged in-memory retry key replays one active request, even at capacity. Changed input conflicts; revoked or completed invite links do not resurrect. Legacy callers without a key remain capacity-bounded.
- [x] Frontend preserves the key after a failed request/session renewal, changes it for a different draft/owner and clears it after success. It does not persist the other person's birth input.
- [x] Capacity and retry-conflict errors have distinct codes, no-store delivery and understandable UI. Revocation alone does not free retained storage. Actual deletion does.
- [x] Narrow live Supabase configuration repair pins both content guard functions to pg_catalog. Advisor rerun has no WARN findings. Backend-only RLS-without-policy INFO notices remain intentionally denied to browser roles.
- [x] Policy source describes Google/Supabase basic identity processing, optional AI consent, encrypted Radar nickname/result, plaintext coarse context/voice, keyed retry metadata and backup limitations.
- [x] Complete one independent patch review and PostgreSQL concurrency/migration proof. Disposable verified-TLS PostgreSQL migrated through 0036; four behavior tests passed initially and the cross-owner test passed after correcting a multi-event-loop test fixture (one targeted rerun). No real user rows or production migrations were involved.
- [ ] Protected backup/restore rehearsal, backup expiry and deletion replay after restore. Never equate an access expiry or timer installation with verified deletion of every copy.
- [ ] Verify provider identity erasure, actual Google scopes and redirect allowlists using two real accounts/devices. Keep public Google off until these pass.
- [ ] Deploy the consolidated candidate and verify the new /privacy content on HTTPS before referencing it in Google branding.

## Verification receipt

The working-tree candidate passed 1,235 API tests (56 environment-gated integration tests skipped), 308 web tests, the 23-test focused Radar/middleware suite, syntax/type/contracts/privacy/runtime guards and web production build. These are synthetic/source checks, not two real Google accounts or a production release. The skipped IAM/rewrite PostgreSQL integration suites still need the exact-image release rehearsal.

The initial isolated PostgreSQL run had four passes and one fixture failure: a second TestClient used a different event loop with the same asyncpg pool. The regression now clears the first actor's cookies and runs the second actor on the same active ASGI loop. Its PostgreSQL rerun passed (194.24s). The quota race, parallel retry, history pagination and private-check tests passed on PostgreSQL without production-source changes for the fixture error. Live Supabase Advisor has no WARN/ERROR; its INFO notice covers 30 default-deny backend tables and is not silenced by opening browser policies.

Only the two function search paths were repaired live. Application source, policy and migration 0036 remain undeployed. No commit, push, paid AI request or public Google activation was performed.

The complete ordered fix report is retained separately from the sealed scan: [Radar fix report](/Users/phamhanh/.codex/state/plugins/codex-security/scans/la-lanh/artifacts-8836d0314576827f604e23b6bcd52970a43d4739d0ad0172c278079edc4218d7/findings/radar-bounded-creation/fix.md). The disposable PostgreSQL container, remote generated TLS files, SSH test tunnel and local preview were cleaned up. Production app `la-lanh:a7fadf7e4511` and Caddy remained running, app healthy, after cleanup.

## Google setup handoff

Create URL: https://console.cloud.google.com/auth/clients/create?project=la-lanh-beta

The existing prepared form is Web application, name La Lanh Beta Web, origin https://la-lanh.2-28-136-44.sslip.io and redirect https://rlowapjpwsamjftpggen.supabase.co/auth/v1/callback. The user performs Create and secret entry. Do not put the secret in chat, screenshots, source or documentation. Do not enable the AI-agent-client option.

Google Data Access needs only openid, userinfo.email and userinfo.profile. No Gmail, calendar, contacts or birthday scopes. Name/photo may be processed by the identity providers under profile; do not promise that providers receive only the app's retained masked email. The app callback is a different URL, https://la-lanh.2-28-136-44.sslip.io/auth/callback, configured in Supabase's redirect allowlist. A shared sslip.io domain is not evidence of verified domain ownership.

After deployment, Google branding home URL is https://la-lanh.2-28-136-44.sslip.io and privacy URL is https://la-lanh.2-28-136-44.sslip.io/privacy. Check the actual public response before saving. Do not invent a terms page.

## Release order and blockers

1. Finish syntax/type, attack-regression, legitimate-flow and independent review checks. Use only synthetic databases for destructive tests.
2. Record live image, schema head and flags without reading secret values. Live schema is 0028; manually repairing two function configurations did not advance Alembic.
3. Verify a protected backup, an isolated restore, migration 0028 through 0036 in the exact image, least-privileged runtime grants, cleanup and erasure handling. Migration 0035 is idempotent with the narrow live function repair; do not stamp it manually.
4. Publish matching AGPL source and deploy the complete bundle, not just the UI or CMS. Do not enable paid rewrite or billing as a side effect.
5. Verify HTTPS privacy and guest flows, then configure provider credentials through protected user entry. Verify real account isolation, logout, retention, cancellation and deletion before public Google activation.

The 100-row cap does not eliminate abuse by an unlimited number of fresh guest identities. Admission limits are process-local backstops. Production ingress/global abuse controls remain operational checks, not a claim of immunity to denial of service.

The independent review found that a successful mutation could be reported as failed by a later session renewal, or remain pending during that renewal. Individual private requests now return their own acknowledged outcomes. Browser cookie expiry renews on the explicit session checks performed by SessionBoundary and feature entry, while retaining the cross-tab cookie fence. Existing cookie-writing login/logout transports still drain before releasing that fence; do not abort them to hide a timeout and risk late cross-account cookies.

## References

- [Supabase Google setup and scopes](https://supabase.com/docs/guides/auth/social-login/auth-google)
- [Google user data policy](https://developers.google.com/terms/api-services-user-data-policy)
- [Vietnam Law 91/2025/QH15](https://vanban.chinhphu.vn/?docid=214590&pageid=27160) and [Decree 356/2025/NĐ-CP](https://vanban.chinhphu.vn/?docid=216387&pageid=27160), official metadata confirms effect from 2026-01-01. This pass did not certify all statutory/controller/cross-border obligations from a full legal review.
- [PostgreSQL function configuration](https://www.postgresql.org/docs/current/sql-alterfunction.html)
- [Operational playbook](../operations/hetzner-supabase-release-runbook.md)
- [Data map](../legal/store-privacy-data-map.md)
