import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { cleanRelease, probeHolds, probeReport, probeView, renderReport, sameFileHolds, trialMerge } from './collab-merge-probe.mjs';
import { runTick } from './collab-tick.mjs';

// A throwaway repository with one base and three branches; synthetic content only.
function repoWithBranches() {
  const dir = mkdtempSync(join(tmpdir(), 'probe-repo-'));
  const git = (...args) => execFileSync('/usr/bin/git', ['-C', dir, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { encoding: 'utf8' }).trim();
  git('init', '-q', '-b', 'main');
  writeFileSync(join(dir, 'a.txt'), 'one\ntwo\nthree\nfour\nfive\n');
  git('add', '.'); git('commit', '-q', '-m', 'base');
  const branch = (name, text) => { git('checkout', '-q', '-b', name, 'main'); writeFileSync(join(dir, 'a.txt'), text); git('commit', '-q', '-am', name); return git('rev-parse', 'HEAD'); };
  const top = branch('top', 'ONE\ntwo\nthree\nfour\nfive\n');
  const bottom = branch('bottom', 'one\ntwo\nthree\nfour\nFIVE\n');
  const clash = branch('clash', 'uno\ntwo\nthree\nfour\nfive\n');
  return { dir, top, bottom, clash };
}
// The fetch from GitHub is skipped; every other git call runs for real.
const noFetch = (cmd, args, opts) => (args.includes('fetch') ? '' : execFileSync(cmd, args, opts));

test('research item 2: a trial merge of two heads says clean, conflict or unknown, never guesses clean', () => {
  const { dir, top, bottom, clash } = repoWithBranches();
  const pr = (number, headRefOid) => ({ number, headRefOid });
  assert.deepEqual(trialMerge(pr(1, top), pr(2, bottom), { dir, run: noFetch }), { result: 'clean' }, 'same file, different lines');
  assert.deepEqual(trialMerge(pr(1, top), pr(3, clash), { dir, run: noFetch }), { result: 'conflict' }, 'same line changed twice');
  assert.equal(trialMerge(pr(1, top), pr(4, 'f'.repeat(40)), { dir, run: noFetch }).result, 'unknown', 'a head that is not in the clone');
  assert.equal(trialMerge(pr(1, top), pr(2, bottom), { dir, run: () => { throw Object.assign(new Error('x'), { stderr: 'fatal: could not read' }); } }).result, 'unknown', 'a failed fetch');
});

test('research item 2: holds are probed once an hour and once per pair of heads; the report counts what could be checked', () => {
  const owner = { login: 'honghanh153-creator' };
  const prs = [
    { number: 10, headRefOid: 'a'.repeat(40), baseTipOid: 'b'.repeat(40), files: [{ path: 'x.json' }, { path: 'y.mjs' }], author: owner },
    { number: 11, headRefOid: 'c'.repeat(40), files: [{ path: 'x.json' }], author: owner },
    { number: 12, headRefOid: 'd'.repeat(40), files: [{ path: 'x.json' }], author: owner },
  ];
  const turns = [{ number: 10, turn: 'claude-check' }, { number: 11, turn: 'hold', reason: 'chờ PR #10 cùng file' }, { number: 12, turn: 'hold', reason: 'draft' }];
  assert.deepEqual(sameFileHolds(prs, turns).map(x => [x.pr.number, x.blocker.number]), [[11, 10]], 'only same-file holds');
  const path = join(mkdtempSync(join(tmpdir(), 'probe-log-')), 'merge-probe.jsonl');
  const statePath = join(mkdtempSync(join(tmpdir(), 'probe-state-')), 'merge-probe.json');
  const tried = [];
  const trial = (a, b) => { tried.push([a.number, b.number]); return { result: 'clean' }; };
  const t0 = Date.parse('2026-11-21T12:00:00Z');
  const first = probeHolds({ list: () => ({ prs, turns }), trial, nowMs: t0, path, statePath });
  assert.deepEqual(first.map(e => [e.pr, e.blocker, e.result, e.shared.join()]), [[11, 10, 'clean', 'x.json']]);
  assert.deepEqual(probeHolds({ list: () => { throw new Error('not within the hour'); }, trial, nowMs: t0 + 30 * 60000, path, statePath }), [], 'at most once an hour');
  assert.deepEqual(probeHolds({ list: () => ({ prs, turns }), trial, nowMs: t0 + 61 * 60000, path, statePath }), [], 'the same heads are not probed again');
  prs[1].headRefOid = 'e'.repeat(40);
  probeHolds({ list: () => ({ prs, turns }), trial: () => ({ result: 'unknown', why: 'x' }), nowMs: t0 + 122 * 60000, path, statePath });
  assert.equal(tried.length, 1);
  const entries = readFileSync(path, 'utf8').trim().split('\n').map(l => JSON.parse(l));
  const report = probeReport(entries, { nowMs: t0 + 3 * 3600000 });
  assert.deepEqual([report.observed, report.pairs, report.clean, report.unknown, report.cleanShare], [2, 1, 1, 1, 100], 'unknown is never counted as clean');
  assert.match(renderReport(report), /Tỉ lệ sạch trong các lần kiểm được: 100%/);
  assert.equal(probeReport([], {}).cleanShare, null);
});

test('research item 2: the tick entry runs the probe after the tick, and a failing probe never fails the tick', () => {
  const seen = [];
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gapNote: () => null, areaNote: () => null, probe: o => { seen.push(o); return []; } });
  assert.equal(seen.length, 1);
  assert.equal(typeof seen[0].list, 'function');
  assert.equal(typeof given.review, 'function');
  const after = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => g, gapNote: () => null, areaNote: () => null, probe: () => { throw new Error('git missing'); } });
  assert.equal(typeof after.review, 'function');
});

test('L63: the hold release reads the last trial result for the exact pair of heads; a missing log releases nothing', () => {
  const path = join(mkdtempSync(join(tmpdir(), 'probe-view-')), 'merge-probe.jsonl');
  const a = 'a'.repeat(40);
  const b = 'b'.repeat(40);
  writeFileSync(path, [
    JSON.stringify({ pr: 2, head: a, blocker: 1, blockerHead: b, result: 'conflict' }),
    'not json',
    JSON.stringify({ pr: 2, head: a, blocker: 1, blockerHead: b, result: 'clean' }),
  ].join('\n'));
  const view = probeView(path);
  const reg = [{ path: 'apps/api/app/domains/content/copy_registry.json' }];
  assert.equal(cleanRelease({ number: 2, headRefOid: a, files: reg }, { number: 1, headRefOid: b, files: reg }, view), true, 'the newest result for the pair wins');
  assert.equal(probeView(join(tmpdir(), 'no-such-dir', 'x.jsonl')).size, 0);
  assert.equal(cleanRelease({ number: 2, headRefOid: a, files: reg }, { number: 1, headRefOid: b, files: reg }), false, 'no results: the hold stays');
});
