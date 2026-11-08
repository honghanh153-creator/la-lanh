# PR #323 reclassified S → M (fix-forward #324)

PR #323 (`b9397447`, merged as `bb8aa59b`) declared **S**. It makes dancing (`nhay`) at a table keep
you seated in the Hẹn ở Lá prototype: `prototype/hen-o-la/game.js:177` and
`prototype/hen-o-la/quan.js:121` now use the shared `H.keepsSeat(act)` rule from `event.js`.
Before, Nhảy stood you up, and at a locked rotation table you could not sit back down until the
next round. That is a visible behaviour change in an existing feature, so under
`docs/operations/product-development-process.md` §0 it is **M**. Being a standalone prototype gives
no risk-level exemption.

## M gates

- G1: the new behaviour matches the prototype README ("Nhảy, mặt hề, vẫy tay, chắp tay và ngủ gật
  không làm bạn đứng dậy"). The prototype has no US/AC yet; that gap is recorded in the #319 decision.
- G2: no layout or control change; the character stays in the chair while dancing instead of standing.
- G3: no new or changed copy.
- G4: not applicable; the rule is a pure function in `event.js`, no API, schema or migration.
- G5: classic scripts, no new dependency.
- G6: `prototype/hen-o-la/event.test.cjs`, test "dancing and other gestures at a locked table keep
  the seat in both real controllers (fix-forward #324)", runs the real `startAct` from `game.js`
  and `quan.js` in a `node:vm` context and checks that every free gesture keeps `sit`, `seatKind`,
  `task` and `locked`, while watering a plant still stands you up. Mutation check: adding an
  unconditional stand-up after the `keepsSeat` line in either controller makes the test fail.
- G7: no session, permission, token, network or log change.
- G8: no personal data collected or stored; all guests are fictional.
- G9: prototype only; nothing shipped, no merge to main or deploy.
- G10: no cost or licence change.
