# US07–US09 implementation evidence

## Implemented vertical slice

- US07: Western Tropical/Jyotish Sidereal engine, Lahiri/Raman/Krishnamurti, True/Mean Node, Placidus/Whole Sign/Equal, nakshatra/pada, classical graha drishti, provenance, overview/detail/settings/current-sky screens.
- US08: delayed local ownership checkpoint, intro/context/preview/create/share/copy/history/resend/replacement/revoke screens and server lifecycle. Replacement invalidates the old capability rather than pretending resend creates a new link.
- US09: public no-account landing, 3–5 moderated statements, anonymous/alias review, idempotent submit, persisted privacy-safe report, receipt withdrawal, private owner result, hide and hard delete.
- App: Capacitor iOS/Android source targets consume the same production React bundle; public link remains web-first.
- New chart snapshots use authenticated AES-256-GCM envelopes instead of readable JSON; Lá Chứng owner mutations are Origin/CSRF/session bound.

## Automated evidence

| Contract | Evidence |
|---|---|
| US07 engine families and no cross-contamination | `tests/astro/test_engine_traditions.py` |
| US07 synthesis and provenance | `tests/readings/test_service.py`, `tests/readings/test_api.py` |
| Delayed owner checkpoint | `tests/identity/test_identity_api.py` |
| US08/09 replacement, anonymous submit, replay, safe projection, report, hide/delete, withdraw | `tests/la_chung/test_flow.py` |
| Existing US01–06 regression | Full API/web checks in repository |
| Encrypted persisted chart snapshot | `tests/birth/test_postgres_encryption.py` |

## Explicit release blockers

- Local owner identity has no account recovery and must be replaced/configured before external launch.
- Edge-level capability-path redaction, verified HTML security headers, production KMS, PostgreSQL race evidence, lifecycle retention worker and independent penetration test remain mandatory.
- Native Keychain/Keystore session adapter, associated domains, signing, simulator accessibility and App Store/Play declarations remain mandatory.
- Swiss Ephemeris licensing decision remains mandatory.

This artifact is evidence for a development vertical slice, not permission to release to real users.
