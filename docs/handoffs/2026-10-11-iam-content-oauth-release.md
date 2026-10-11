---
artifact_contract: "ce-handoff/v1"
created_at: "2026-10-11"
title: "IAM, content and Google OAuth release continuation"
summary: "Consolidated local candidate and verified provider setup; production, native login and paid activation still have open gates."
keywords: ["iam", "session-isolation", "content", "tarot", "google-oauth", "deployment"]
repository: "honghanh153-creator/la-lanh"
branch: "feat/luna-content-rewrite-runtime"
capture_base: "99a3079a383a4cb529c1331a596bc47f75b5f07f"
resume_focus: "Finish release gates from the draft PR without losing the current source, privacy boundaries or provider setup."
---

# Start here

The owner requested a PR and a durable handoff so a new session can continue without this chat. This document accompanies the consolidated candidate, not a production release. The PR head is the source snapshot to use; checkout its exact head before comparing test evidence. Production remains older.

The latest user request authorizes committing/pushing this work and opening a PR. It does not authorize merging, new charges, changing Google audience, accepting additional terms, deleting real user data, or bypassing the release gates. Prior production-deployment intent is recorded in the plan below, but its unmet conditions still apply. A receiving session should verify current state and confirm its next action with the owner.

Read these in order:

1. `AGENTS.md`: documentation/product, security and data-privacy gates apply to every change. Passing tests is not a release certificate.
2. `docs/operations/google-oauth-platform-setup.md`: current verified Google/Supabase receipts, exact client IDs, callback targets, secret-handling incident and native/tooling gaps. This supersedes earlier OAuth setup status in the dated reviews.
3. `docs/reviews/2026-10-10-production-followup-fixes.md`: corrections after the full review, historical local and isolated PostgreSQL evidence, plus remaining operational blockers. Earlier review verdicts remain immutable.
4. `docs/plans/2026-10-11-radar-privacy-remediation.md`: transactional capacity/idempotency/pagination remediation and the narrow live Supabase function repair. Local 0036 is not deployed.
5. `docs/operations/hetzner-supabase-release-runbook.md`: exact-image, backup/restore, migration, role, deployment, smoke and rollback sequence. Do not start `deploy.sh` as a substitute for a backup rehearsal.
6. `docs/plans/2026-10-10-content-google-release-completion.md`: approved product contract and later deployment extension. `docs/reviews/2026-10-10-content-google-consolidated-release-review.md` is an earlier checkpoint; use the follow-up and OAuth receipt for current status.

## Repository and runtime snapshot

| Item | Verified state at capture |
| --- | --- |
| GitHub | Public AGPL source: `https://github.com/honghanh153-creator/la-lanh`; remote `origin`; base `main` |
| PR branch | `feat/luna-content-rewrite-runtime`; no open PR before this publishing run |
| Starting HEAD | `99a3079a383a4cb529c1331a596bc47f75b5f07f`, same source as fetched `origin/main` before this bundle |
| Public app | `https://la-lanh.2-28-136-44.sslip.io/welcome` |
| VPS | `2.28.136.44`; `/opt/la-lanh/current` resolves to `/opt/la-lanh/releases/a7fadf7e4511/source` |
| Containers | `la-lanh-app-1`, image `la-lanh:a7fadf7e4511`, healthy; Caddy `2.10.2-alpine` |
| Public health | `GET /v1/ready` returns `{"status":"ready"}` |
| Public account API | `GET /v1/account` returns HTTP 404; old deployed release does not supply the candidate account route |
| Database | Supabase `rlowapjpwsamjftpggen`, Frankfurt; last inspected application Alembic head `20261008_0028` |
| Cleanup | `la-lanh-guest-cleanup.timer` and `la-lanh-expired-cleanup.timer` active in the latest read-only SSH check |
| Candidate schema | Ordered migrations 0029 through `20261011_0036`; must run before the candidate API |
| Mobile | Capacitor 8 shell, not React Native/Expo; bundle/application ID `vn.lalanh.app` |

These network and SSH checks were read-only. The schema head and secret inventory above include earlier inspection evidence, not a new database query in this publishing run. Recheck them before deployment without printing secret contents. Supabase provider enablement does not deploy code to the VPS.

## Product decisions that must survive

These decisions came from the owner, not from a new feature proposal:

- Core note/chart/Tarot use stays guest-first. Google login is optional and preserves data across devices.
- Welcome has two entry actions: **Đồng ý & bắt đầu** resumes the valid profile on this browser, and **Đăng nhập**. No demo CTA and no another-profile creation CTA. The legacy `/demo` route remains; removing the CTA did not remove every route.
- Guest lifetime is 30 days of inactivity. Account lifetime is 365 days of inactivity with its own disclosure/consent. Device credentials have their own 30-day inactivity clock. Automatic history has a separate creation-based maximum of 30 days; saved notes/current chart sources follow profile lifetime.
- Do not wipe a valid browser profile merely because a user returns, retries, is offline or opens `restart=1`.
- Direct, ordinary Vietnamese is the approved default. Meaning and concrete context must improve before the Luna wording layer. Do not turn examples into certain predictions or claims about another person's private thoughts.
- The affectionate-sharp voice samples are proposals. A final A/B/C voice/prompt has not been selected; do not assume the owner chose one.
- Daily note stays near the top of Home; feedback/share are compact. Tarot result summary precedes expandable card chapters. Onboarding and Tarot reveal have motion plus pause/reduced-motion handling.
- Radar focuses on checking a known person privately. Vòng Lá discovery, five-stranger matching/chat, reader marketplace and social games are deferred. Old plans or mounted legacy routes do not authorize reopening them.
- CMS/Studio is optional and independent: approved content works without it. Normal user accounts must not gain operator access.
- The product remains app-first, with web beta for testing. A working web callback is not iOS/Android acceptance.
- Latest pilot ceiling is USD 1/month, not the historical USD 1/day. Reuse the existing key; no new key, recharge, budget increase or paid call is authorized by this PR request.

## What the candidate contains

### Account and session continuity

Read `docs/architecture/account-iam-and-retention.md` and `apps/api/app/domains/accounts/README.md` for the API/security contract.

- Server-side Supabase Google PKCE, short-lived encrypted verifier, random state, fixed callback, one-use exchange and initiating-credential binding. Provider bearers are discarded rather than stored in frontend/localStorage.
- First link keeps the guest data owner. Existing-account restore is explicit; it does not merge another guest's chart/history/AI consent. Logout/revoke affects the intended device; deletion is terminal locally, with retryable provider erasure.
- Backend owns credential/device/account authorization. Client IDs, browser emails and `user_metadata` cannot grant access.
- Browser cross-tab coordination, stale-response/adoption fences, background/BFCache verification and explicit cookie renewal prevent old responses from replacing the current owner. Cookie-writing transports drain under the fence even after cancellation; do not release the fence on a timeout to hide a late-cookie race.
- Web Locks unavailable fails cookie issuance closed. Physical native support/behavior remains unverified.
- Source identity and plan revision distinguish changed dates/chart precision; current Aura/Daily projections update coherently. Frozen saved/share revisions must stay frozen. Similar prose is not proof of leakage, and different prose is not proof of isolation.

Start source review in `apps/web/src/shared/api/client.ts`, `shared/session/sessionCoordinator.ts`, `app/SessionBoundary.tsx`, and the backend `domains/guest`, `domains/birth`, `domains/accounts` and `domains/history` boundaries. Relevant tests are grouped under those domains and `sessionIsolation.test.ts` / `sessionCoordinator.test.ts`.

### Content and experience

- Daily semantic eligibility/personalization is a layer below rewrite; direct scene/action context comes from authored meaning, not just random paraphrases.
- Tarot has card meaning → question/context → spread role → summary/chapter rendering → gate → optional rewrite. Current source versions include `tarot-renderer-v6`, `tarot-meaning-brief-v2`, `tarot-gates-v4` and `gpt-6-luna-tarot-v4`.
- Five-card summaries preserve all drawn meanings within a bounded length. Negation/intent and every-card evidence are checked before generated wording can replace the baseline. Raw free-text question and exact birth inputs are excluded from the provider envelope.
- Unsupported Jyotish interpretation uses structural calculated data rather than invented Western personality copy.
- Knowledge examples are authored with cited references, not a claim that complete commercial books were ingested. Synthetic content audits do not establish real-user comprehension.

Read `domains/tarot/meaning_brief.py`, `context_readings.py`, `engine.py`, `quality.py`, `rewrite.py`; `domains/readings/daily_personalization.py`, `daily_psychology.py`, `knowledge.py`, `review_agent.py`; and `infrastructure/generation/privacy.py`. The content release contract is in `docs/operations/content-matrix-release-gate.md`.

### Security, privacy and spend controls

- Durable send/disclosure fences replace holding owner locks during provider I/O. Withdrawal, owner change, deletion and publication recheck authority; uncertain sends retain conservative budget debit.
- Daily/monthly spend ledgers survive owner erasure and application rollback. Never downgrade/delete ledgers to refill budget. The app cap does not protect a stolen key used outside the app.
- Linked identity erasure needs a protected Supabase server secret. `compose.auth.yaml` mounts it only for app/cleanup, never rewrite worker. Worker Auth flags explicitly remain false. `compose-files.sh` keeps erasure available even after new login is disabled.
- Body/admission/metrics bounds and private `no-store` errors are part of this bundle.
- Radar has a transactional owner cap of 100 retained rows, default 20/max 50 summary pagination, direct owner/ID share lookup, keyed retry conflict detection and matching frontend retry/history behavior. Revocation does not free retained capacity; actual deletion does. Many new guest identities can still abuse process-local admission limits, so ingress/global protections remain operational work.
- Private Radar input is denied external rewrite. Invited-pair rewrite needs both subjects' distinct consent; general owner consent is not consent from the other person.
- Only the two content-guard function search paths were repaired live, with Advisor WARN cleared. That repair did not advance Alembic or deploy candidate privacy/UI code.

The completed privacy-focused Security Scan was partial, not an exhaustive clean bill. Read the scope/limits in the follow-up review. `docs/legal/store-privacy-data-map.md` describes retained and transmitted fields, plaintext coarse Radar context, account/history consent and backup limitations. Backup/provider physical deletion remains unverified.

## OAuth: exact continuation point

Google project: `la-lanh-beta`. iOS, Android and Web clients were created in that order with user approval. Exact IDs and Android fingerprints are in `docs/operations/google-oauth-platform-setup.md`; do not create duplicates.

- Google scopes saved: `openid`, `userinfo.email`, `userinfo.profile`. No Gmail, Contacts, Calendar or birthday scope.
- Audience is External / Testing with one approved test user. Public audience is not enabled.
- Web Google origin is `https://la-lanh.2-28-136-44.sslip.io`; its Google redirect is `https://rlowapjpwsamjftpggen.supabase.co/auth/v1/callback`.
- User directly entered the additional Web secret into Supabase and saved. Google Enabled and Web-first/iOS/Android Client IDs were verified. Skip nonce checks and Allow users without email remain off. This is saved config, not a successful token exchange.
- Supabase Site URL still reads `http://localhost:3000`, with **no redirect URLs**. Approval was requested to set Site URL to the public app origin and allow exactly `/auth/callback`; it has not been received. Do not interpret DONE on secret entry as approval to widen redirects.
- Backend appends a login-specific state query to the fixed callback. Real allowlist matching/state preservation must be tested; do not add broad wildcards or remove state/PKCE/nonce checks to make it work.
- Google's generated secret copy button includes plaintext in its accessible label. A prior label inspection exposed the added test secret in tool output. The owner was informed; no secret was stored in Git. Replace it before production activation, with approval and direct user credential entry. Never dump full DOM/AX, enumerate secret-page button names, or screenshot value columns. Do not repeat the secret in an incident report.
- User requested built-in browser only and closed external Chrome task tabs. Do not reopen external Chrome. Existing signed-in Google/Supabase tabs may survive, but reacquire/verify them in the next session; browser state is not durable PR evidence.

### Native gaps and machine-local tooling

The current native shell has no Google SDK/ID-token bridge, iOS OAuth URL types, Android OAuth intent filter or reviewed device-bound system-browser handoff. `window.location.assign` is a web flow; system browser and Capacitor WebView do not share guest cookies automatically. Do not use Google consent inside an embedded WebView or transfer bearer tokens via an unprotected deep link.

Machine-local, not included in Git:

- JDK: `~/Library/Java/JavaVirtualMachines/la-lanh-temurin21.jdk/Contents/Home`, verified Temurin 21.0.12.1.
- Android command-line tools: `~/Library/Android/sdk/cmdline-tools/latest`, verified official archive checksums.
- Beta-only key: `~/.android/debug.keystore`, mode 0600; its public certificate, not a placeholder, was registered with Google. Never use this key as production/Play signing identity.
- Source `infra/mobile/android-beta-env.sh` before local builds. No home shell profile was edited.
- Required packages: platform-tools, platforms;android-36, build-tools;36.0.0. Installer's January 16, 2019 package license awaits acceptance; the owner previously accepted the differently dated download-page agreement only. A process from this session may no longer exist. Reinspect the prompt, do not pipe yes into all licenses.
- No signed APK, Gradle signing report, native sign-in/device acceptance or iOS Team ID proof exists yet.

## Verification for this PR snapshot

Fresh publish-time results are recorded in `docs/reviews/2026-10-11-pr-handoff-verification.md`. Earlier numerical receipts are dated checkpoints, not evidence for every later patch. The first checks in this session failed on sandbox access to the uv cache and missing Node on PATH; those failures are not passes. The rerun uses the app's bundled Node runtime and permission for local cache/loopback QA only.

Known limits that remain even when local checks pass:

- Environment-gated PostgreSQL tests need an exact-image, least-privileged-role rehearsal; historical isolated PG results do not establish current production readiness.
- No paid model output or real 10–20-user comprehension study was run for this PR.
- No two real Google accounts/devices, provider erase, physical native storage/callback or live BFCache acceptance is certified.
- Vite chunk size and mixed import warnings are unresolved build advisories, not a measured performance fix.
- The textual credential scan is a bounded pattern check, not proof that every binary asset or remote log is free of secrets.

## Suggested next sequence and blockers

This is orientation, not authorization to perform every action without the current owner:

1. Checkout the PR head; read the latest handoff/receipts rather than treating historical unchecked plans as current truth. Recheck flags/live image/schema without reading user rows or secrets.
2. Obtain exact Supabase redirect approval and save/verify only the approved origin/callback. Replace the exposed test Web secret through a protected user handoff; verify exchange before retiring any prior secret. Do not publish Google audience yet.
3. Install the required existing credentials via protected input: VPS identity-erasure credential and, only for an approved paid rollout, the owner's existing OpenAI key. Earlier inventory found neither on the VPS. Never put them in chat, shell arguments, app.env, screenshots, frontend or Git.
4. Prepare protected backup and isolated restore, documented backup retention/deletion replay, then rehearse populated 0028 → 0036 in the exact candidate image and actual least-privileged runtime role. Check RLS/browser grants, spend preservation, legacy writer compatibility and deletion/revocation continuity. No production database downgrade.
5. Privately smoke the exact built image with generation disabled; run guest/returning-session, changed date/time/place/aura, daily detail/share/revoke, Tarot 1/3/5, Radar exact/unknown/retry/history/capacity, profile/history/delete flows. Do not inspect actual users' profiles for QA.
6. With a safe test deployment/configuration and user sign-in, verify two real Google accounts in isolated contexts: cancel/replay/expiry/wrong-cookie, explicit restore without merge, logout/relogin, independent devices, guest continuity and provider hard erasure. Do not turn mocks into a live-login claim.
7. Complete reviewed native identity integration and separate builds/devices if the release includes iOS/Android. Web beta and native release may have different acceptance scope, but client registration alone satisfies neither.
8. Only after applicable gates, deploy matching published AGPL source; record image digest/schema/source, public deep links and real smoke. Keep cleanup operational and log no personal payloads/capability paths.
9. Paid rewrite remains a separate decision and rollout. Preserve USD 1/month, approved surface/subject consent, minimal provider envelope, deterministic fallback and stop switch. No paid test merely to demonstrate PR completeness.
10. Rollback first disables admissions/exposure/workers and selects a verified compatible old image. Retain additive schema, spend/deletion/revocation records; do not restore erased data or revive old credentials.

No merge, deployment, new billing, paid generation, credential rotation or additional OAuth permission change is part of creating this PR.

## How to review without rereading every dated artifact

- IAM/source-of-authority: accounts service/repository/provider → owner/session boundaries → client coordinator → account/session regressions.
- Send/erase/cost atomicity: rewrite authorization/repository/send_fence/worker → history and account erasure → PostgreSQL concurrency tests → migrations 0029–0034.
- Radar abuse: `domains/radar/service.py` → routes → migration 0036 → `tests/radar/test_limits.py` → `useRadarHistory` and retry UI tests.
- Content correctness: meaning brief/knowledge → authored context → renderer → quality/rewrite gates → corpus/review receipts. Do not judge only the rewrite prompt.
- Operations: compose selector/Auth overlay/entrypoint/retention runner → release playbook → exact-image backup/restore evidence. `deploy.sh` currently does not prove that evidence itself.

When continuing, report what is actually fixed/tested/deployed, what is only saved provider configuration, and what remains blocked. Do not promise zero vulnerabilities, permanent deletion of every backup/provider copy, unique prose for every person, or scientific prediction from chart/card content.
