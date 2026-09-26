# Plan — Private Radar hợp gu vertical slice

> **2026-09-21 product correction:** the active primary path is now direct `private_check`: A enters birth information that B has allowed A to use, Radar computes transiently and sends no link/notification. The existing consented invitation remains only the fallback when A does not have that permission. See `docs/foundation/la-lanh-radar-hop-gu-spec.md` and US-12/13 for the authoritative flow.

## Goal

Replace the misleading pool-matching CTA with a complete private 1:1 Radar flow, repair birthplace selection and produce security/privacy evidence.

## Completed work

1. Reframed active product from pool discovery to known-person pair reading.
2. Expanded local birthplace search to all 34 current province-level units; made Vietnamese `đ/d` and accents searchable.
3. Added encrypted Radar request/result persistence and migration `20260920_0020`.
4. Added owner create/list/share/revoke/result APIs and public preview/current/accept/withdraw APIs.
5. Reused real `RelationshipBundle` engine; prohibited scalar score display.
6. Added Radar landing, creator, public disclosure, continuation/consent and result screens.
7. Redirected legacy `/vong-la` routes to Radar; removed pool flow from active navigation.
8. Added guest onboarding handoff so an invite recipient returns to Radar after exact birth data.
9. Added backend E2E with two independent sessions, privacy headers, encryption and withdrawal.
10. Updated US-12/13 and marked US-14–18 deferred.

## Remaining release work

- Add abuse report/block operations and operational moderation dashboard.
- Add distributed idempotency key to Radar create/accept.
- Add automated expiry purge and encryption-key rotation evidence.
- Add exact city/town-level offline gazetteer; 34 province centers are a safe MVP fallback, not precision parity with a full geocoder.
- Add native Universal/App Links, Keychain/Keystore continuation storage and native share sheet.
- Run iOS/Android simulator/device QA, accessibility, deep-link and app-resume tests.
