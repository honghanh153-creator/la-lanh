---
name: verify-la-lanh
description: Run the Lá Lành web app like a user on fake data and collect evidence (full-page screenshots at phone widths, console errors, failed requests, axe-core a11y scan, overlapping/clipped text). Use before opening any PR that touches apps/web UI, and to reproduce a reported UI bug. Also covers keeping docs/operations/feature-map.json current when a route or screen changes.
---

# Verify Lá Lành like a user

Fixed steps live in the CLI (`scripts/verify/verify.mjs` + `apps/web/tests/verify/`). Your job is
the judgment: pick the features, read the report, look at the screenshots, decide what is a real
problem and put the evidence in the PR.

## When to use

- Before opening any PR that changes `apps/web/src/**` (screens, styles, copy, shared UI, router).
- To reproduce a UI bug someone reported: run the feature it names, at the width they used.
- Not needed for docs-only, API-only or script-only PRs (`--changed` prints "nothing to run").

## Before you run

It builds the app and drives Chromium, so it is a heavy check. Only one heavy check may run on
the machine at a time. The CLI refuses to start (exit 3) if `pgrep -f "playwright|vitest|pnpm check"`
finds another job; wait for it to finish instead of passing `--allow-concurrent`.

Node and pnpm are not on PATH on the owner's Mac:

```sh
export PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
```

## Pick the features

The map is `docs/operations/feature-map.json`. Each feature lists its routes, the `source_files`
that draw it, the user path from Welcome, role selectors, states and the fake-data fixture.

```sh
node scripts/verify/verify.mjs --list                         # ids, routes, titles
node scripts/verify/verify.mjs --changed                      # features touched vs origin/collab/integration
node scripts/verify/verify.mjs --features home,mood,card      # explicit
node scripts/verify/verify.mjs --features all                 # everything (~2-4 min)
```

`--changed` maps changed files to features through `source_files`. A changed web file that no
feature lists (shared UI, global CSS, router, API client, the verify harness itself) can affect any
screen, so it runs all features. Defaults: widths `360,390` (height 844), output under
`apps/web/test-results/verify/<timestamp>/` (git-ignored). `--reuse-build` skips the build when
you already built this commit. `pnpm verify:ui` is the same CLI.

Exit codes: `0` pass, `1` findings, `2` usage or build/server problem, `3` another heavy check running.

## Read the report

The output folder has `summary.md` (read this first), `report.json`, `screens/*.png` and `raw/*.json`.
`verify-ac.json` lists each acceptance criterion of the features run, with the commit:
- `chưa đạt` means a configured `ac_checks` entry did not find its content on screen (the run fails);
- `đạt phần tự động` means only the named parts were seen; the `manual` notes say what still needs API or hand checks;
- `không tự động` means nothing is checked on screen yet.

Never report an AC as met from this file alone (L04).

Per feature, each automated state is walked at each width. Findings that FAIL:

| Finding | What it means | What to do |
| --- | --- | --- |
| `did not reach <selector>` | The user path broke or the screen changed text/role | Real bug, or the map is stale (fix the map in the same PR) |
| `overlap: <control> covers text` | A visible button/link/icon is drawn on top of text that is not its label | Open the PNG and confirm; this is the Home close-X class of bug |
| `clipped text` / `offscreen text` | Text cut by an overflow box or running off the screen | Open the PNG; check long Vietnamese words at 360px |
| `page scrolls sideways` | Horizontal overflow | Find the wide element |
| `console error` / `page error` | Runtime error on the screen | Real bug unless caused by a missing fake answer |
| `failed request` / `http error` | A non-API asset failed or 4xx/5xx | Real bug (missing asset, bad path) |
| `a11y serious/critical` | axe-core WCAG 2.x A/AA violation | Real; contrast and names are the usual ones |

Warnings do not fail the run: `a11y moderate/minor`, `request to another host` (check it is not
sending personal data to a third party), and `no fake answer for <call>`. A missing fake answer
means the screen calls an endpoint the fixture does not know; add it to
`apps/web/tests/verify/fixtures.ts` with synthetic data if the screen looks half-rendered.

Always open the screenshots of the features you changed, at both widths, and look for what the
checks cannot judge: wrong hierarchy, cramped spacing, copy that reads badly, a state that looks
broken. Use the 8 questions in `docs/operations/user-experience-release-gate.md` as the yardstick.
`summary.md` also lists the states that are not automated (loading/offline/empty and so on);
check by hand the ones your diff touches.

## Put the evidence in the PR

In the PR body, under `## Kiểm thử`, add:

```md
Verify (`node scripts/verify/verify.mjs --changed`), commit <sha>, widths 360/390:
- PASS 5/5 features (home, mood, note-detail, card, saved), or FAIL with the list below
- Findings fixed in this PR: …
- Findings left (pre-existing, not in this PR's scope): … (issue #…)
- Screens checked by eye: home @360/390, card @390 …
```

Under G2 (UI/UX) cite the run and what you checked by eye. Under G6 cite the command and exit code.
Paste the summary table from `summary.md` and the FAIL lines that matter; do not paste
`raw/*.json` wholesale. Screenshots use fake data only, so a person may attach them to the PR;
the `ui-screens` workflow also uploads key screens as a build artifact for UI PRs. Never attach screenshots taken
against a real account or real birth data.

## Maintain the map

When a PR adds, renames or removes a route, or changes the text/role of a selector the map uses,
update `docs/operations/feature-map.json` in the same PR:

1. New route in `apps/web/src/app/router.tsx` → add it to an existing feature's `routes`, or add a
   feature with `id`, `title`, `us`/`ac` (or `gap` when there is no user story), `routes`,
   `source_files`, `user_path`, `owner_only`, `key_selectors` and at least one automated state
   (`fixture`, `walk` starting with `goto`, `ready`).
2. Selectors are ARIA role + accessible name copied from source (the app has no `data-testid`).
   Text that comes from fake data gets `"source": "fixture"`.
3. Set `owner_only: true` for screens with privacy, consent, withdrawal, deletion or crisis copy;
   agents never write new copy there.
4. Run `pnpm verify:map` (coverage check + tests). It fails when a router route has no entry, a
   mapped route no longer exists, or a selector name is not in the source.
5. Run the verify CLI on the new feature once.
