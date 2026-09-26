# Quality gates: documentation, security, and data privacy

Last verified: 2026-09-02 against the current official platform guidance and Vietnam's Personal Data Protection Law in force from 2026-01-01.

This checklist is required for every Lá Lành change.

## Completion checklist

### Documentation

- Relevant PRD/SRS/user story/AC/DoD identified.
- UI states, field validation, edge cases, API contract, migration, and tests agree.
- Product behavior is not claimed complete when only a mock, fallback, PWA, or partial provider exists.
- Time-sensitive technical and platform requirements were checked against official documentation.

### Security

- Trust boundaries and abuse cases documented.
- Session ownership and authorization enforced server-side.
- State-changing web requests have origin/CSRF protection where applicable.
- Input length/type/range validation exists client-side and server-side.
- Sensitive data is encrypted at rest and protected in transit; keys and tokens are not logged or exported.
- Public/share endpoints expose only privacy-safe projections.
- Mobile storage, permissions, deep links, backups, screenshots, clipboard, and app lifecycle reviewed against OWASP MASVS/MASTG.
- Failure, retry, replay, concurrency, rollback, and deletion behavior tested.

### Data privacy

- Data inventory and purpose recorded for each new or changed field.
- Collection occurs only when necessary and after an understandable just-in-time disclosure/consent.
- Retention, deletion, consent withdrawal, and guest-session expiry are implemented and testable.
- URLs, analytics, logs, crash reports, localStorage, notifications, share cards, and third-party SDKs contain no unapproved personal data.
- Apple App Privacy and Google Play Data Safety declarations match the actual app and all integrated SDKs.
- Vietnamese legal requirements are re-verified when processing behavior changes.

## Primary reference set

- Vietnam: [Decree 13/2023/ND-CP](https://vanban.chinhphu.vn/?classid=1&docid=207759&orggroupid=2&pageid=27160) and [Personal Data Protection Law 91/2025/QH15 on the official legal database](https://vbpl.moj.gov.vn/bocongan/Pages/vbpq-thuoctinh.aspx?ItemID=179252&Keyword=), effective 2026-01-01.
- Mobile security: [OWASP MASVS](https://mas.owasp.org/MASVS/) and [OWASP Mobile Application Security](https://owasp.org/www-project-mobile-app-security/).
- iOS distribution/privacy: [Apple App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/), privacy manifests, and App Review Guidelines.
- Android distribution/privacy: [Google Play User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311), [prominent disclosure and consent](https://support.google.com/googleplay/android-developer/answer/11150561), and [Data Safety guidance](https://support.google.com/googleplay/android-developer/answer/10787469).
- Web/API security: OWASP ASVS, API Security Top 10, and framework/library official documentation.

Search results, blog posts, vendor summaries, and legal commentary can help discovery but do not replace primary sources. For legal conclusions or public release, obtain qualified Vietnamese legal review.

## Required handoff format

Every implementation handoff must state:

1. Documents and official sources checked.
2. Security findings fixed and tests run.
3. Personal data touched, storage/transmission locations, retention, and deletion behavior.
4. Residual risks and release blockers.
5. AC/DoD status: complete, partial, or not implemented.
