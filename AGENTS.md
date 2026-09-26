# Lá Lành — project quality gates

These rules apply to every product, design, documentation, backend, web, and app change in this repository.

Before calling work complete, review all three gates below. Do not treat passing tests as a substitute for them.

## 1. Documentation and product contract

- Read the relevant PRD, SRS, product plan, user story, AC, validation rules, edge cases, and DoD.
- Map changed behavior back to the applicable requirement or explicitly record the gap.
- Keep API contracts, migrations, user-facing copy, privacy copy, and operational documentation aligned with runtime behavior.
- When a referenced standard, platform rule, library contract, or policy may have changed, verify it using current primary/official sources on the web.

## 2. Security

- Review authentication/session ownership, authorization, CSRF, input validation, abuse/rate limits, cryptography/key handling, logs, public endpoints, share links, dependencies, storage, network transport, error disclosure, and deletion paths.
- For the mobile app, use OWASP MASVS/MASTG as the baseline and examine platform permissions and native storage separately from the web/PWA surface.
- Threat-model new data flows and failure/rollback paths. Do not ship known P0/P1 security findings.

## 3. Data privacy

- Inventory every personal-data field collected, inferred, transmitted, stored, cached, logged, shared, exported, or sent to a third party/SDK.
- Verify purpose limitation, data minimization, explicit and timely consent, retention, encryption, access control, withdrawal/deletion, data-subject rights, and safe defaults.
- Birth date, birth time, birthplace, coordinates, relationship/matching data, mood, identifiers, tokens, and derived astrology profiles require explicit review.
- Ensure runtime behavior, in-app privacy copy, Apple App Privacy details, Google Play Data Safety declarations, and the privacy policy remain consistent.
- Re-check current Vietnamese privacy law and applicable platform policies from official sources when the change affects personal data.

Every handoff must report: sources checked, findings fixed, unresolved risks, and which AC/DoD remain incomplete.

For chart synthesis or native release work, also follow `docs/operations/chart-synthesis-release-runbook.md`. Treat every public share/invite as sensitive-by-capability: prevent caching/indexing, keep tokens out of logs/referrers, and preserve revocation behavior.
