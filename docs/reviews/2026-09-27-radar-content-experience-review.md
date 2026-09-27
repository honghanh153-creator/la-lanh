# Radar content and experience review — 2026-09-27

## Outcome

Radar now turns the relationship knowledge corpus into evidence-bound, ordinary-life actions.
The user explicitly chooses one of four reading voices; the choice is stored with the Radar request
and disclosed to both participants before a consented report is generated.

## Experience review

The first browser pass found a release-blocking content defect: technically traceable prompts still
exposed internal editorial terms such as `Composite`, `mutual` and method-oriented wording. The
implementation now separates astrology method concepts from publishable action concepts. Internal
concepts remain available to the explanation layer; only concrete, reversible relationship prompts
can appear under **Đem ra đời thật**.

At 390 px the Radar form and result had no horizontal overflow. The 43.2 px circular back target was
raised to 44 px. The report keeps its summary, three independent indicators and collapsed chapter
index visible before detailed evidence. Technical evidence remains progressive disclosure.

## Security and privacy review

- The new `voice` value is a fixed four-value preference, not free text and not inferred from chart or
  behaviour.
- Raw birth date, time, place and coordinates remain absent from the stored/public reading projection.
- Invite recipients see the selected voice before consenting.
- Action cards are published only when their evidence IDs resolve to Radar receipts.
- No score is presented as a probability, verdict or automated matching decision.
- No reading text or birth input was added to analytics or logs.

The design follows data-minimisation and user-control principles from OWASP MASVS privacy guidance,
and the mobile review checks contrast, reflow, focus, headings and target size against WCAG 2.2.

## Verification evidence

- Content matrix: 630 daily variants, 23 relationship concepts, 8 Radar themes.
- Experience audit: 4 contexts x 4 voices; distinct, evidence-bound, privacy-minimised actions.
- API tests: full suite passed; Radar and relationship targeted suites passed after final content fixes.
- Web: 33 files / 107 tests passed; TypeScript and lint passed.
- Contracts: OpenAPI and generated TypeScript contract current.
- Production QA: native ephemeris assets, web build, fresh schema, API proxy and SPA deep links passed.
- Browser: onboarding through full-chart activation and private Radar result completed at 390 x 844.

## Remaining non-blocking item

The web bundle is about 716 kB before gzip and still emits the existing Vite chunk-size warning.
This affects performance work, not correctness of the content/UX gate, and should be handled as a
separate code-splitting change.
