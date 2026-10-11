# Content + Google login — consolidated release preparation

## Contract

Owner request (10 October 2026): finish Astro/Tarot content, review **all** pending changes for one production release, and reduce welcome to two entry actions. Implementation and local verification are authorized; this request prepares a release for the owner, not an automatic production deploy, paid generation or billing change.

- Welcome: **Đồng ý & bắt đầu** resumes the valid profile on this browser; creates a guest only when none is valid. The old `restart=1` URL must not replace an active profile. Second entry action: **Đăng nhập** with Google. Remove demo/profile-switch links. Animation pause and privacy are utility controls, not alternate entry paths.
- Google via Supabase Auth, server-side PKCE. No browser Supabase token/localStorage identity, no Google secrets in this repository. Fixed callback, random state, encrypted verifier, short TTL, one exchange, initiating credential binding and explicit account-retention consent. Existing-account restore still requires confirmation and never merges two users' data.
- Direct, ordinary Vietnamese for Astro and Tarot. Correct meaning before rewriting; summary before chapters; interpretation is not a claim to know private events, another person's feelings, or a certain future. CMS remains independent and optional.
- Review every tracked **and untracked** implementation change, migrations, contracts, costs, owner isolation, privacy and user comprehension. Test fixtures are not real-user comprehension evidence.

## Units and acceptance

1. **Entry/Google IAM**: offline tests first, fixed-origin callback and PKCE transport, existing owner retention, restore/replay/cancel/expiry/foreign-cookie regressions. Google delivery has a separate activation gate from email SMTP. No new-profile switch affordance. New-account login can start the already-consented guest onboarding. Live Google configuration and two-account/device acceptance must be observed before enabling the flag.
2. **Content completion**: enumerate current review findings; fix the rendering/meaning contract rather than weakening the reviewer. Review active daily/natal/planet/house/aspect/transit/Jyotish/Tarot outputs. Extend concrete semantic goldens and rewrite evidence/negation/clarity gates. Unsupported traditions must explain the available data in plain language, not invent reviewed coverage. Run the synthetic corpus, preserve provenance and uncertainty separately from core prose.
3. **Release review**: full backend/frontend, generated contract, content/knowledge/runtime guards and real local browser at mobile/desktop widths. Read-only independent reviews of content, IAM/security/privacy, persistence/cost and UX. Fix actionable findings and rerun impacted/full checks. Record an honest Go/No-Go with live-provider, migration/role/backup and paid-output gates, plus one consolidated deploy/rollback checklist.

## References and boundaries

- `AGENTS.md`; `docs/architecture/account-iam-and-retention.md`; `docs/reviews/2026-10-10-optional-account-iam-verification.md`; `docs/operations/hetzner-supabase-release-runbook.md`.
- [Supabase Google Auth](https://supabase.com/docs/guides/auth/social-login/auth-google), [PKCE](https://supabase.com/docs/guides/auth/sessions/pkce-flow), [Auth advanced guide](https://supabase.com/docs/guides/auth/server-side/advanced-guide); changelog checked before implementation.
- Preserve existing dirty WIP. Native implementation inline because it depends on uncommitted shared types/config/contracts; read-only sidecar reviews can run independently. No new paid reviewer/provider calls, no live credentials printed, no automatic deploy/commit/push.
- Existing application generation ceiling remains USD 1/month. Do not represent the application ceiling as protection against a stolen provider key used elsewhere.

Execution evidence and remaining gates belong in a separate review receipt, not unchecked assumptions in this plan.

## Deployment extension authorized by owner

The follow-up explicitly authorizes completion and production deployment of the entire offered
bundle. Commit/push corresponding AGPL source and deploy only after current-tree review and release
gates. This supersedes the original no-deploy boundary, not the cost/secret constraints.

Before activation: durable admission/drain must keep foreground sessions responsive, preserve
source/consent/erasure fences and nonrefundable budgets; linked identity must be hard-deleted through
Supabase with retryable DELETING state on failure. Confirm Google provider credentials/allowlist and
real two-account acceptance, existing OpenAI key installation, production-role migrations, backups
and exact-image/public smoke. Missing credentials are blockers, never permission to mock or
silently enable a broken provider. Final deployment evidence goes in a dated follow-up receipt.

## Execution status

- Entry and Google server-PKCE/UI implementation: locally implemented with offline regressions; public configuration, identity-erasure and real-provider/device acceptance remain gated.
- Content renderer, meaning/context brief and rewrite validation: locally implemented; final consolidated checks and browser review are recorded in the [release receipt](../reviews/2026-10-10-content-google-consolidated-release-review.md). No paid rewrite or real-user comprehension certification.
- Consolidated review covers the complete WIP inventory. The completed full review receipt is
  `docs/reviews/2026-10-10-production-bundle-code-review.json`. Its original Not ready verdict is
  preserved; follow-up fixes are recorded separately. Provider I/O now runs outside owner locks,
  using durable disclosure fences and nonrefundable budgets. Late-cookie, history crash recovery,
  per-result Tarot drain, account error contracts and Auth cleanup/worker configuration have fixes
  under final verification. Do not mark their tests or production activation complete from this plan.
- No production deploy, commit/push, billing change or key rotation performed in this request.
