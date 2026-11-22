import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { areaWatch, unlabelled, workflowPath } from './collab-area-label.mjs';
import { runTick } from './collab-tick.mjs';

// Synthetic PRs only.
const owner = { login: 'honghanh153-creator' };
const pr = (number, files, extra = {}) => ({ number, title: `x ${number}`, labels: [], files: files.map(path => ({ path })), isDraft: false, baseRefName: 'collab/integration', author: owner, isCrossRepository: false, ...extra });
const fakeGh = () => { const edits = []; return { edits, raw: args => { edits.push(args.join(' ')); return ''; } }; };
const statePath = () => join(mkdtempSync(join(tmpdir(), 'area-watch-')), 'area-watch.json');

test('workflow files are told apart from product files', () => {
  assert.ok(['scripts/collab-turn.mjs', 'scripts/codex-review.mjs', 'docs/operations/luat-dang-hieu-luc.md', 'docs/reviews/2026-11-20-collab-loop-retro.md', '.github/workflows/pr-check.yml', 'AGENTS.md'].every(workflowPath));
  assert.ok(!['apps/web/tests/e2e/keep-action-profiles.spec.ts', 'scripts/qa-product-journey.mjs', 'package.json', 'apps/api/app/main.py'].some(workflowPath));
  assert.deepEqual(unlabelled([pr(1, ['AGENTS.md']), pr(2, ['AGENTS.md'], { labels: [{ name: 'area:content' }] }), pr(3, ['AGENTS.md'], { isDraft: true }),
    pr(4, ['AGENTS.md'], { baseRefName: 'main' }), pr(5, ['AGENTS.md'], { isCrossRepository: true })]).map(p => p.number), [1], 'own, ready, into integration, without an area label');
});

// L58 (21.11.2026): #743, #747, #748, #761, #764, #810, #818 and #820 had no area label, fell to the
// last group and never got a check or a review for up to three days.
test('L58: an unlabelled workflow PR is labelled area:ops; any other unlabelled PR alerts after two ticks, once per set', () => {
  const path = statePath();
  const gh = fakeGh();
  const logs = [];
  const alerts = [];
  const resolved = [];
  let open = [pr(747, ['docs/operations/luat-dang-hieu-luc.md']), pr(820, ['apps/web/tests/e2e/keep-action-profiles.spec.ts']), pr(9, ['apps/api/app/main.py'], { labels: [{ name: 'area:feature' }] }),
    pr(802, ['apps/api/app/content/radar.json'], { title: 'content(radar): Đồng nghiệp and Gia đình lines' })];
  const run = at => areaWatch({ gh, list: () => open, statePath: path, nowIso: at, log: t => logs.push(t), alert: t => alerts.push(t), resolve: t => resolved.push(t) });
  const first = run('2026-11-21T10:00:00Z');
  assert.deepEqual(first.labelled, [747]);
  assert.deepEqual(gh.edits, ['pr edit 747 --repo honghanh153-creator/la-lanh --add-label area:ops']);
  assert.match(logs[0], /#747 .*area:ops/);
  assert.equal(alerts.length, 0, 'a PR just opened gets one tick to be labelled');
  open = open.filter(p => p.number !== 747);
  run('2026-11-21T10:10:00Z');
  assert.equal(alerts.length, 1);
  assert.match(alerts[0], /#820\./);
  assert.doesNotMatch(alerts[0], /#802/, 'a title that names its group places the PR without a label');
  run('2026-11-21T10:20:00Z');
  assert.equal(alerts.length, 1, 'the same set does not alert every ten minutes');
  open = [...open, pr(830, ['apps/web/src/x.tsx'])];
  run('2026-11-21T10:30:00Z');
  run('2026-11-21T10:40:00Z');
  assert.equal(alerts.length, 2, 'a new unlabelled PR raises it again');
  assert.match(alerts[1], /#820, #830/);
  open = open.filter(p => p.number === 802);
  run('2026-11-21T10:50:00Z');
  assert.equal(resolved.length, 1, 'closed once nothing is left');
  run('2026-11-21T11:00:00Z');
  assert.equal(resolved.length, 1);
});

test('L58: the tick entry runs the area watch, and a failing watch never stops the tick', () => {
  const seen = [];
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gapNote: () => null, areaNote: o => { seen.push(o); return null; } });
  assert.equal(seen.length, 1);
  assert.deepEqual(['gh', 'log', 'alert', 'resolve'].map(k => k in seen[0]), [true, true, true, true]);
  assert.equal(typeof given.review, 'function');
  const after = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gapNote: () => null, areaNote: () => { throw new Error('gh: HTTP 502'); } });
  assert.equal(typeof after.review, 'function');
});
