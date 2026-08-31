# Privacy and security flow notes

Sources checked on 2026-08-31:

- Vietnam Decree 13/2023/ND-CP on personal data protection: date of birth is basic personal data; consent must be voluntary, specific, informed, affirmative, and demonstrable; deletion requests are handled within 72 hours unless an exception applies; children's personal data requires child and parent/guardian consent where applicable.
- EDPB GDPR SME guidance: consent should be freely given, specific, informed, unambiguous, and easy to withdraw.
- FTC COPPA guidance: apps with actual knowledge they collect personal information from children under 13 need verifiable parental consent before collection unless a narrow exception applies.
- Apple App Store privacy details and Google Play Data safety guidance: collected app data, purposes, linkage, tracking, retention, and security practices must be declared for store submission.

Product decisions for the MVP:

- The app does not require login before the birth reveal. Account creation remains deferred until matching/social actions.
- Consent is collected at the moment the birth date is submitted, not as a separate pre-app wall.
- The app clearly states data category, purpose, storage, protection, retention, and deletion path before submission.
- The client blocks birth dates indicating a user under 16 before sending the date to the API. A parent/guardian flow must be designed before processing children's data.
- Birth date must not appear in URL, cookie, local storage, analytics payloads, or logs.
- Guest token remains HttpOnly; CSRF token is separate and checked with trusted origin on mutations.
- Raw birth date is encrypted at rest and snapshots retain only the minimum reveal data needed for app continuity.
- App store submission needs privacy labels/data safety answers for birth date, guest identifier, app interactions, diagnostics, and any future analytics/SDKs.

Open gates before public release:

- Legal review for Vietnam personal data impact assessment and any cross-border data transfer filing.
- Verifiable parent/guardian consent design if the product supports users under 16.
- Apple Privacy Nutrition Label and Google Play Data Safety form based on the final SDK inventory.
- Swiss Ephemeris licensing decision remains blocked by `docs/legal/swiss-ephemeris-release-gate.md`.
