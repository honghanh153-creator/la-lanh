# PR #323 reclassified S → M (fix-forward #324, item 1)

PR #323 (`b9397447`, merged as `bb8aa59b`) declared **S**. It changes what a player sees in the
existing Hẹn ở Lá prototype: at a locked rotation table, Nhảy no longer stands the player up
(`prototype/hen-o-la/game.js:177`), and in the café controller both Nhảy and Mặt hề now keep the
player seated (`prototype/hen-o-la/quan.js:121`; the old list there held only `ngugat`, `chaptay`,
`vaytay`). Under `product-development-process.md` §0 a visible behavior change in an existing feature
is **M**. Being a standalone, unshipped prototype does not lower the level.

## Scope of `b9397447`

1. `prototype/hen-o-la/event.js`: shared `SEATED_GESTURES` (the five `FREE_ACTS`) and `keepsSeat(act)`.
2. `prototype/hen-o-la/game.js`, `prototype/hen-o-la/quan.js`: each controller calls `H.keepsSeat(act)`
   instead of its own list.
3. `prototype/hen-o-la/event.test.cjs:169`: new regression test.

## M gates

- G1: behavior now matches the prototype README line that the five small gestures do not make you
  stand up. The prototype has no US/AC (gap already recorded in the #319 decision).
- G2: no new element, state or style; the character stays in the seated pose it already had. Not
  re-checked in a browser.
- G3: no new copy.
- G4: no backend. G5: classic scripts, no new dependency.
- G6, what is actually covered:
  - `event.test.cjs:169` checks that `SEATED_GESTURES` equals `FREE_ACTS`, that place actions
    (`docsach`, `tuoicay`, `goido`, `vuotcho`, `nam`) are not seat-keeping, and that both controllers
    contain the `if (!H.keepsSeat(act))` call (source regex, `:183`).
  - **Not covered:** the loop at `:174` changes a synthetic body itself and calls neither controller.
    An unconditional stand-up added after the `keepsSeat` check in `game.js` or `quan.js` would keep
    the test green.
  - Gap (open, #324 item 2): drive both controllers through their real action path and assert that
    dancing keeps `sit`, `seatKind`, `task` and `locked`. Recorded here; not fixed by this receipt.
- G7: no session, permission, token, network or log change.
- G8: no personal data collected or stored; all characters are fictional.
- G9: no release; integration branch only. G10: no cost or third party.
