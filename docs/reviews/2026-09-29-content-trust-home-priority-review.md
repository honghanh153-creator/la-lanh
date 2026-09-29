# Content trust and Home priority review

Date: 2026-09-29

Status: implementation and local QA passed; moderated beta validation remains pending.

## Outcome

- Home DOM and visual order is now question heading → Daily Note → discovery/Tarot.
- The reported Pisces paragraph was replaced by an observable event, an explicit inference gap and
  a testable action.
- Disclaimers now use a labelled `role="note"` treatment with icon, border and background on Daily,
  deep-reading, Reveal, Aura preview, Radar and Tarot result surfaces.
- Western methodology increased from five to eight bounded concept sources; Tarot increased from
  five to eight. No book text, examples, spreads, exercises or card entries were imported.
- `ContentReviewAgent` is offline and deterministic. It receives rendered strings, never production
  records, and reports only persona ID, surface, section and rule ID.

## Ten-persona matrix

The automated run used ten synthetic personas, one for each of ten distinct zodiac signs. Each
persona received one Daily reading and one Tarot reading across relationship, work, energy,
self-care, communication and general contexts: 20 generated readings total. Daily alternated
between date-only and full-chart inputs; Tarot rotated one-, three- and five-card spreads.

Blocking checks covered:

- retired or abstract filler;
- disclaimer language inside core content;
- scenes without observable context;
- actions without a concrete verb;
- missing or unvalidated evidence and unregistered provenance;
- duplicate core readings on the same surface.

Result: 10/10 synthetic personas passed; 20/20 readings had no critical/high finding.

This is not a claim that ten real people completed moderated research. A real beta cohort is still
needed to measure whether users find the language useful, personal and natural rather than merely
passing deterministic rules.

## Verification evidence

- `pnpm check`: passed.
- Web: 135 tests passed.
- API: 368 tests passed.
- Content matrix, Tarot knowledge, Radar experience, privacy/runtime/mobile guards: passed.
- QA CLI: guest → birth → Daily Note flow passed.
- Browser QA: mobile 390×844, end-to-end Welcome → birth → Reveal → Home passed.
- Visual check confirmed the Daily card precedes discovery and the disclaimer is visibly distinct.

Known non-blocking issue: the production build still reports the existing JavaScript chunk-size
warning (`~717 kB` minified). No new remote SDK, telemetry, model provider or personal-data flow was
introduced by this change.

The repository-wide gate passed through API tests and failed only when the sandbox refused the QA
server's temporary localhost bind. The same `pnpm qa:test` command then passed outside that sandbox:
three server tests, production build and the real guest → birth → Daily Note smoke flow all passed.
