# PR #280 reclassified S → M (fix-forward #286)

PR #280 (`9aa05533`) declared **S**. It changes derived astrology output (a derived profile under
`AGENTS.md` §3) in `apps/api/app/domains/astro/sky_events.py`: station contacts (~782), lunation
contacts (~788) and solar-return attribution (~802). §4 then requires **M**.

Behavior: a contact is now returned only when it holds across the whole natal domain (unknown birth
time). Synthetic example: a Venus domain [160.0°, 162.5°] no longer returns a station contact that
held at one end only. Solar return is attributed at day start.

## M gates

- G1: matches the "no certain claim when the time is unknown" rule; fewer, not new, statements.
- G4: pure computation; no storage, schema or API change.
- G6: `apps/api/tests/astro/test_sky_events.py` (domain-edge and day-start cases, synthetic data).
- G7: no session, permission or log change.
- G8: no new field collected, stored, sent or logged; the existing derived output is narrowed.
  Data map unchanged.
