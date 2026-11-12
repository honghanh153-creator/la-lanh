import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { execFileSync, spawnSync } from 'node:child_process';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-loop-'));
const trust = await import('./collab-trust.mjs');
const { checksPerTick, fileBlocker, planTurns, prTurn, tickGap, turnsFor, tick } = await import('./collab-turn.mjs');
const preflightMod = await import('./collab-preflight.mjs');
const { committedTurns, copyReview, planMax, planMin, planState, renderPlan } = await import('./collab-plan.mjs');
const review = await import('./codex-review.mjs');
const { mergeGate, runMerge } = await import('./collab-merge.mjs');
const { ciCheck, clonePreflight, checkSource, heavyJobFree, checkBudgetMs, guardHits, guardTerms, prePushRanges, privateHits, readGuardTerms, isHeavy, machineBusy, withSystemPath, prepareAuthorClone, renderCheck, runCheck, runCheckInClone, runGroup, withCheckLock } = await import('./collab-check.mjs');

const A = 'a'.repeat(40);
const B = 'b'.repeat(40);
const C = 'c'.repeat(40);
let clock = 0;
const owner = body => ({ authorAssociation: 'OWNER', createdAt: `2026-10-30T0${Math.floor(clock / 60)}:${String(clock++ % 60).padStart(2, '0')}:00Z`, body });
const outsider = body => ({ ...owner(body), authorAssociation: 'NONE' });
const check = (sha, status = 'PASS') => owner(renderCheck({ head: sha, status, exitCode: status === 'PASS' ? 0 : 1, seconds: 1, date: 'x' }));
const pr = (extra = {}) => ({ number: 7, title: 'feat(tarot): plain summary', author: { login: 'honghanh153-creator' }, isCrossRepository: false, state: 'OPEN', isDraft: false, baseRefName: 'collab/integration', headRefName: 'feat/x', headRefOid: A, mergeable: 'MERGEABLE', labels: [], createdAt: '2026-10-29T00:00:00Z', comments: [], body: goodBody, ...extra });

function fakeGh(state) {
  const calls = [];
  return {
    calls,
    pr: () => structuredClone(state.pr),
    openPrs: () => structuredClone(state.open ?? [state.pr]),
    json: args => { calls.push(['json', args]); return state.json?.(args) ?? []; },
    raw: (args, input) => {
      calls.push(['raw', args, input]);
      if (args[0] === 'issue' && args[1] === 'create') return 'https://github.com/x/y/issues/901\n';
      return '';
    },
    comment: (kind, number, body) => { trust.assertAgentBody(body); calls.push(['comment', kind, number, body]); state.pr.comments.push(owner(body)); },
  };
}

test('verdict lines count only at the top of a trusted comment', () => {
  assert.deepEqual(trust.parseVerdict(`Review verdict: APPROVE @ ${A}\nok`), { verdict: 'APPROVE', sha: A });
  assert.deepEqual(trust.parseVerdict(`Reviewer: Codex\nReview verdict: REQUEST_CHANGES @ ${A}`), { verdict: 'REQUEST_CHANGES', sha: A });
  assert.equal(trust.parseVerdict(`Handoff\nReview verdict: APPROVE @ ${A}`), null);
  assert.equal(trust.parseVerdict(`Review verdict: APPROVE @ ${A.slice(0, 7)}`), null);
  assert.equal(trust.trustedComments([outsider(`Review verdict: APPROVE @ ${A}`)]).length, 0);
});

test('owner replies parse with or without diacritics; agents cannot post them', () => {
  assert.equal(trust.parseOwnerReply('Duyệt').action, 'approve');
  assert.equal(trust.parseOwnerReply('duyet nhé').action, 'approve');
  assert.equal(trust.parseOwnerReply('Giữ').action, 'hold');
  assert.deepEqual(trust.parseOwnerReply('Bỏ #12\nbo #3'), { action: 'drop', dropped: [12, 3] });
  assert.equal(trust.parseOwnerReply('Hôm nay ổn'), null);
  assert.throws(() => trust.assertAgentBody(`Duyệt\n${trust.agentMarker} x -->`), /owner reply grammar/);
  assert.throws(() => trust.assertAgentBody('no marker'), /marker/);
});

test('turns follow check → review → fix/merge on the exact head', () => {
  const p = pr();
  assert.equal(prTurn(p).turn, 'claude-check');
  p.comments.push(check(A));
  assert.equal(prTurn(p).turn, 'codex-review');
  p.comments.push(outsider(`Review verdict: APPROVE @ ${A}`));
  assert.equal(prTurn(p).turn, 'codex-review', 'an outsider cannot approve');
  p.comments.push(owner(`Review verdict: REQUEST_CHANGES @ ${A}`));
  assert.equal(prTurn(p).turn, 'claude-fix');
  p.headRefOid = B;
  assert.equal(prTurn(p).turn, 'claude-check', 'a new head needs a new author check');
  p.comments.push(check(B, 'FAIL'));
  assert.equal(prTurn(p).turn, 'claude-fix');
  p.comments.push(check(B));
  assert.equal(prTurn(p).turn, 'codex-review');
  p.comments.push(owner(`Review verdict: APPROVE @ ${B}`));
  assert.equal(prTurn(p).turn, 'merge');
  assert.equal(prTurn({ ...p, baseRefName: 'feat/parent' }).turn, 'hold');
  assert.equal(prTurn({ ...p, baseRefName: 'main' }).turn, 'hold');
  assert.equal(prTurn({ ...p, labels: [{ name: 'needs-owner' }] }).turn, 'hold');
  assert.equal(prTurn(p, { dropped: [7] }).turn, 'hold');
  assert.equal(prTurn({ ...p, mergeable: 'CONFLICTING' }).turn, 'claude-fix', 'an approved PR in conflict goes to Claude, not to merge');
  assert.equal(prTurn({ ...p, comments: [], mergeable: 'CONFLICTING' }).turn, 'claude-fix', 'no check on a head that cannot merge');
  assert.equal(prTurn({ ...p, mergeable: 'UNKNOWN' }).turn, 'merge', 'GitHub still computing: collab-merge decides');
});

test('queue order is ops → content → privacy → feature, oldest first', () => {
  const order = turnsFor([
    pr({ number: 1, title: 'docs(registry): r33' }),
    pr({ number: 2, title: 'feat(prototype): game lab 14' }),
    pr({ number: 3, title: 'feat(privacy): data export' }),
    pr({ number: 4, title: 'feat(tarot): pass 2', createdAt: '2026-10-29T02:00:00Z' }),
    pr({ number: 5, title: 'feat(radar): readable Hợp gu', createdAt: '2026-10-29T01:00:00Z' }),
    pr({ number: 6, title: 'anything', labels: [{ name: 'area:content' }], createdAt: '2026-10-30T00:00:00Z' }),
  ]).map(t => t.number);
  assert.deepEqual(order, [1, 5, 4, 6, 3, 2]);
});

test('daily gate: 08:50 plan, owner window, 10:00 auto start, 23:30 stop', () => {
  const date = '2026-10-30';
  const at = (hour, minute) => ({ date, hour, minute });
  const plan = { authorAssociation: 'OWNER', createdAt: '2026-10-30T01:50:00Z', body: `${trust.agentMarker} daily-plan date=${date} -->` };
  const reply = (body, createdAt = '2026-10-30T02:05:00Z', extra = {}) => ({ authorAssociation: 'OWNER', createdAt, body, ...extra });
  assert.equal(planState(at(8, 40), []).state, 'closed');
  assert.equal(planState(at(8, 55), []).state, 'not-made');
  assert.equal(planState(at(9, 10), [plan]).state, 'waiting');
  assert.equal(planState(at(9, 10), [plan, reply('Duyệt')]).state, 'open');
  assert.equal(planState(at(10, 30), [plan, reply('Giữ')]).state, 'held');
  assert.equal(planState(at(10, 5), [plan]).state, 'open');
  assert.equal(planState(at(9, 10), [plan, reply(`Duyệt\n${trust.agentMarker} x -->`)]).state, 'waiting', 'agent-marked text is not the owner');
  assert.equal(planState(at(9, 10), [reply('Duyệt', '2026-10-30T01:00:00Z'), plan]).state, 'waiting', 'replies before the plan do not count');
  assert.equal(planState(at(9, 10), [plan, reply('Duyệt', undefined, { authorAssociation: 'NONE' })]).state, 'waiting');
  assert.deepEqual(planState(at(10, 5), [plan, reply('Bỏ #5')]).dropped, [5]);
  assert.equal(planState(at(23, 35), [plan, reply('Duyệt')]).state, 'closed');
  assert.doesNotThrow(() => trust.assertAgentBody(renderPlan(at(8, 50), turnsFor([pr()]), { codexLeft: 12 })));
});

const finding = (severity, category) => ({ severity, category, file: 'apps/web/x.ts', line: 3, title: 't', detail: 'd' });
const output = (extra = {}) => ({ verdict: 'APPROVE', sha: A, reviewed_range: 'x..y', complete: true, summary: 'ok', findings: [], ...extra });

test('P2 policy blocks privacy/security/copy only, and the script never lowers a verdict', () => {
  assert.deepEqual(review.applyPolicy(output({ findings: [finding('P2', 'docs')] })).verdict, 'APPROVE');
  assert.equal(review.applyPolicy(output({ findings: [finding('P2', 'docs')] })).fixForward.length, 1);
  for (const category of ['privacy', 'security', 'user_copy']) assert.equal(review.applyPolicy(output({ findings: [finding('P2', category)] })).verdict, 'REQUEST_CHANGES');
  assert.equal(review.applyPolicy(output({ findings: [finding('P1', 'test')] })).verdict, 'REQUEST_CHANGES');
  assert.equal(review.applyPolicy(output({ verdict: 'REQUEST_CHANGES', findings: [finding('P3', 'other')] })).verdict, 'REQUEST_CHANGES');
  assert.equal(review.applyPolicy(output({ complete: false })).verdict, 'REQUEST_CHANGES');
  assert.throws(() => review.validateOutput(output({ sha: B }), A), /not head/);
  assert.throws(() => review.validateOutput(output({ findings: [{ severity: 'P9' }] }), A), /finding/);
  assert.equal(review.fillPrompt('{{HEAD}} {{BODY}}', { HEAD: A, BODY: '{{HEAD}}' }), `${A} {{HEAD}}`);
});

function fakeRun({ head = A, codex = () => '' } = {}) {
  const calls = [];
  return {
    calls,
    run: (cmd, args, opts) => {
      calls.push([cmd, args, opts]);
      if (cmd === '/usr/bin/git' && args[0] === 'rev-parse') return `${head}\n`;
      if (cmd === '/usr/bin/git' && args[0] === 'merge-base' && args[1] !== '--is-ancestor') return `${C}\n`;
      if (cmd === review.codexBin) return codex(args, opts);
      return '';
    },
  };
}

test('review posts verdict, files fix-forward first, and records the output hash', () => {
  const state = { pr: pr({ comments: [check(A)] }) };
  const gh = fakeGh(state);
  const runner = fakeRun();
  const raw = JSON.stringify(output({ findings: [finding('P2', 'docs'), finding('P3', 'other')] }));
  const result = review.runReview(7, { gh, run: runner.run, readOut: () => raw, now: { date: '2026-10-30', hour: 11, minute: 0 } });
  assert.equal(result.status, 'posted');
  assert.equal(result.verdict, 'APPROVE');
  const codexCall = runner.calls.find(c => c[0] === review.codexBin);
  assert.ok(codexCall[1].includes('read-only') && codexCall[1].includes('gpt-6.1-sol') && codexCall[1].includes('model_reasoning_effort="high"'));
  assert.match(codexCall[2].input, new RegExp(`git diff ${C}\\.\\.${A}`));
  const order = gh.calls.filter(c => c[0] === 'comment' || (c[0] === 'raw' && c[1][1] === 'create' && c[1][0] === 'issue')).map(c => c[0]);
  assert.deepEqual(order, ['raw', 'comment']);
  const body = gh.calls.find(c => c[0] === 'comment')[3];
  assert.equal(trust.parseVerdict(body).sha, A);
  assert.match(body, /Fix-forward: #901/);
  assert.match(body, /p2=1 -->/);
  assert.match(body, /Output SHA-256: `[0-9a-f]{64}`/);
  assert.equal(prTurn(state.pr).turn, 'merge');
  assert.equal(review.runReview(7, { gh, run: runner.run, readOut: () => raw }).status, 'refused', 'no second verdict for the same head');
});

test('fix-forward #238: a finding that lists 30 places keeps all of them in the verdict and the issue', () => {
  const places = Array.from({ length: 30 }, (_, i) => `apps/web/src/features/synthetic/place${String(i).padStart(2, '0')}.tsx:${100 + i}`);
  const detail = `Same pattern at: ${places.join(', ')}.`;
  assert.ok(detail.length > 1200);
  const state = { pr: pr({ comments: [check(A)] }) };
  const gh = fakeGh(state);
  const raw = JSON.stringify(output({ findings: [{ ...finding('P2', 'docs'), detail }] }));
  assert.equal(review.runReview(7, { gh, run: fakeRun().run, readOut: () => raw, now: { date: '2026-11-05', hour: 11, minute: 0 } }).status, 'posted');
  const body = gh.calls.find(c => c[0] === 'comment')[3];
  const issue = gh.calls.find(c => c[0] === 'raw' && c[1][0] === 'issue' && c[1][1] === 'create')[2];
  for (const text of [body, issue]) {
    for (const place of places) assert.ok(text.includes(place), `${place} kept`);
    assert.ok(!text.includes('[...truncated]'));
  }
});

test('the scheduled PR list asks GitHub for mergeability (K24 needs it)', () => {
  let asked;
  trust.makeGh((cmd, args) => { asked = args; return '[]'; }).openPrs();
  assert.ok(asked.at(-1).split(',').includes('mergeable'));
});

test('a re-review across an integration merge reads only the PR files (K25)', () => {
  const prior = owner(`Review verdict: REQUEST_CHANGES @ ${B}\n${trust.agentMarker} codex-auto-review sha=${B} p2=0 -->`);
  const raw = JSON.stringify(output());
  for (const [merges, scoped] of [['d'.repeat(40), true], ['', false]]) {
    const runner = fakeRun();
    const base = runner.run;
    const run = (cmd, args, opts) => {
      if (cmd === '/usr/bin/git' && args[0] === 'rev-list' && args[1] === '--merges') return merges;
      if (cmd === '/usr/bin/git' && args[0] === 'diff' && args[1] === '-z') return 'Open QA.command\0a"b.txt\0';
      return base(cmd, args, opts);
    };
    review.runReview(7, { gh: fakeGh({ pr: pr({ comments: [prior, check(A)] }) }), run, readOut: () => raw, now: { date: '2026-11-02', hour: 11, minute: 0 } });
    const input = runner.calls.find(c => c[0] === review.codexBin)[2].input;
    assert.match(input, new RegExp(`git diff ${B}\\.\\.${A}`));
    assert.equal(input.includes('la-lanh-review-delta.patch'), scoped);
    const scopedDiff = runner.calls.find(c => c[0] === '/usr/bin/git' && c[1][0] === 'diff' && c[1].includes('--'));
    assert.deepEqual(scopedDiff?.[1].slice(-2), scoped ? [':(literal)Open QA.command', ':(literal)a"b.txt'] : undefined, 'names reach git as literal paths');
  }
});

test('review refuses without an author check, stops on limits, and escalates to the owner', () => {
  const now = { date: '2026-10-31', hour: 11, minute: 0 };
  assert.equal(review.runReview(7, { gh: fakeGh({ pr: pr() }), run: fakeRun().run, now }).status, 'refused');

  const limited = fakeRun({ codex: () => { const e = new Error('fail'); e.stderr = 'You have hit your usage limit'; throw e; } });
  const limitedGh = fakeGh({ pr: pr({ comments: [check(A)] }) });
  assert.equal(review.runReview(7, { gh: limitedGh, run: limited.run, now }).status, 'limit');
  assert.equal(limitedGh.calls.filter(c => c[0] === 'comment').length, 0);
  assert.equal(trust.readJson(trust.dayStatePath(now.date), {}).codexRuns ?? 0, 0, 'limits do not use a daily run');

  const blocking = JSON.stringify(output({ verdict: 'REQUEST_CHANGES', findings: [finding('P1', 'correctness')] }));
  const state = { pr: pr({ headRefOid: B, comments: [check(A), owner(`Review verdict: REQUEST_CHANGES @ ${A}\n${trust.agentMarker} codex-auto-review sha=${A} p2=0 -->`), check(B)] }) };
  const gh = fakeGh(state);
  const runner = fakeRun({ head: B });
  const result = review.runReview(7, { gh, run: runner.run, readOut: () => blocking.replace(A, B), now });
  assert.equal(result.verdict, 'REQUEST_CHANGES');
  assert.equal(result.needsOwner, true);
  assert.ok(gh.calls.some(c => c[0] === 'raw' && c[1].includes('--add-label') && c[1].includes('needs-owner')));
  assert.match(runner.calls.find(c => c[0] === review.codexBin)[2].input, new RegExp(`git diff ${A}\\.\\.${B}`), 're-review reads the delta');
});

test('daily cap refuses automatic reviews', () => {
  const now = { date: '2026-11-01', hour: 12, minute: 0 };
  trust.writeJson(trust.dayStatePath(now.date), { codexRuns: trust.codexDailyCap });
  const result = review.runReview(7, { auto: true, gh: fakeGh({ pr: pr({ comments: [check(A)] }) }), run: fakeRun().run, now });
  assert.equal(result.status, 'refused');
});

test('merge gate needs APPROVE and PASS on head, integration base and a fix-forward link', () => {
  const ok = pr({ comments: [check(A), owner(`Review verdict: APPROVE @ ${A}`)] });
  assert.deepEqual(mergeGate(ok).reasons, []);
  assert.ok(!mergeGate({ ...ok, baseRefName: 'main' }).ok);
  assert.ok(!mergeGate({ ...ok, mergeable: 'CONFLICTING' }).ok);
  assert.ok(!mergeGate({ ...ok, labels: ['needs-owner'] }).ok);
  assert.ok(!mergeGate(pr({ comments: [owner(`Review verdict: APPROVE @ ${A}`)] })).ok, 'needs author check');
  assert.ok(!mergeGate(pr({ comments: [check(A), owner(`Review verdict: APPROVE @ ${A}`), owner(`Review verdict: REQUEST_CHANGES @ ${A}`)] })).ok);
  assert.ok(!mergeGate(pr({ comments: [check(A), outsider(`Review verdict: APPROVE @ ${A}`)] })).ok);
  assert.ok(!mergeGate(pr({ comments: [check(A), owner(`Review verdict: APPROVE @ ${A}\n${trust.agentMarker} codex-auto-review sha=${A} p2=2 -->`)] })).ok);

  const state = { pr: ok, open: [ok, pr({ number: 8, baseRefName: 'feat/x' })] };
  const gh = fakeGh(state);
  assert.equal(runMerge(7, { gh }).status, 'merged');
  const merge = gh.calls.find(c => c[0] === 'raw' && c[1][1] === 'merge')[1];
  assert.deepEqual(merge.slice(-3), ['--merge', '--match-head-commit', A]);
  assert.ok(!merge.includes('--admin') && !merge.includes('--auto') && !merge.includes('--squash'));
  assert.ok(gh.calls.some(c => c[0] === 'raw' && c[1][1] === 'edit' && c[1][2] === '8' && c[1].includes('collab/integration')));
});

test('tick makes the plan once, waits for the owner, then runs merges and capped reviews', () => {
  const comments = [];
  const ghFor = open => ({
    ...fakeGh({ pr: open[0], open }),
    json: args => args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments },
    comment: (kind, number, body) => { trust.assertAgentBody(body); comments.push({ authorAssociation: 'OWNER', createdAt: '2026-11-02T01:50:00Z', body }); },
  });
  const open = [pr({ number: 1, comments: [check(A), owner(`Review verdict: APPROVE @ ${A}`)] }), pr({ number: 2, comments: [check(A)] }), pr({ number: 3, comments: [check(A)] }), pr({ number: 4, comments: [check(A)] }), pr({ number: 5 })];
  const date = '2026-11-02';
  const done = { merge: [], review: [] };
  const deps = now => ({ gh: ghFor(open), now: { date, ...now }, merge: n => { done.merge.push(n); return { status: 'merged' }; }, review: n => { done.review.push(n); return { status: 'posted' }; } });
  assert.equal(tick(deps({ hour: 8, minute: 52 })).status, 'plan-made');
  assert.match(comments[0].body, /## Plan 2026-11-02/);
  assert.equal(tick(deps({ hour: 9, minute: 20 })).status, 'waiting');
  assert.equal(tick(deps({ hour: 10, minute: 1 })).status, 'ran');
  assert.deepEqual(done, { merge: [1], review: [2, 3] });
  assert.equal(tick(deps({ hour: 10, minute: 11 })).status, 'ran', 'the next tick keeps working (retro D1)');
  const queue = JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  assert.deepEqual(queue.items, [], 'author checks are the tick\'s job, not Claude\'s queue');
});

test('r1: a newer FAIL outvotes an older PASS, and a retarget voids earlier verdicts', () => {
  const failedLater = pr({ comments: [check(A), owner(`Review verdict: APPROVE @ ${A}`), check(A, 'FAIL')] });
  assert.ok(!mergeGate(failedLater).ok);
  assert.equal(prTurn(failedLater).turn, 'claude-fix');
  const retargeted = pr({ comments: [check(A), owner(`Review verdict: APPROVE @ ${A}`), owner(`Base changed.\n\n${trust.agentMarker} retarget parent=6 -->`)] });
  assert.ok(!mergeGate(retargeted).ok);
  assert.equal(prTurn(retargeted).turn, 'codex-review');
  retargeted.comments.push(owner(`Review verdict: APPROVE @ ${A}`));
  assert.ok(mergeGate(retargeted).ok);
});

test('r1: only one review uses the shared clone at a time', () => {
  const lock = join(trust.stateDir, 'review.lock');
  trust.writeJson(lock, {});
  try {
    const result = review.runReview(7, { gh: fakeGh({ pr: pr({ comments: [check(A)] }) }), run: fakeRun().run });
    assert.equal(result.status, 'busy');
  } finally { rmSync(lock, { force: true }); }
});

const plannedGh = (open, date) => {
  const comments = [{ authorAssociation: 'OWNER', createdAt: `${date}T01:50:00Z`, body: `${trust.agentMarker} daily-plan date=${date} -->` }];
  return { ...fakeGh({ pr: open[0], open }), json: args => args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments } };
};

test('r1: the clock is re-read before each review, so nothing new starts after 23:30', () => {
  const date = '2026-11-03';
  const open = [pr({ number: 1, comments: [check(A)] }), pr({ number: 2, comments: [check(A)] })];
  const times = [{ hour: 23, minute: 20 }, { hour: 23, minute: 20 }, { hour: 23, minute: 41 }];
  const started = [];
  const result = tick({ gh: plannedGh(open, date), clock: () => ({ date, ...(times.shift() ?? { hour: 23, minute: 45 }) }), merge: () => ({}), review: n => { started.push(n); return { status: 'posted' }; } });
  assert.equal(result.status, 'ran');
  assert.deepEqual(started, [1]);
});

test('r1: review errors count as tick failures and alert on the second', () => {
  const date = '2026-11-04';
  const open = [pr({ number: 1, comments: [check(A)] })];
  const alerts = [];
  const run = hour => tick({ gh: plannedGh(open, date), now: { date, hour, minute: 5 }, merge: () => ({}), review: () => ({ status: 'error', reason: 'codex missing' }), alert: text => alerts.push(text) });
  assert.equal(run(11).status, 'ran-with-errors');
  assert.equal(alerts.length, 0);
  run(12);
  assert.equal(alerts.length, 1);
});

test('r1: privacy and features wait while content has machine work; a content PR waiting for Claude does not block', () => {
  const date = '2026-11-05';
  const open = [
    pr({ number: 1, title: 'feat(tarot): copy', comments: [check(A), owner(`Review verdict: REQUEST_CHANGES @ ${A}`)] }),
    pr({ number: 2, title: 'feat(privacy): export', comments: [check(A), owner(`Review verdict: APPROVE @ ${A}`)] }),
    pr({ number: 3, title: 'feat(tarot): held', isDraft: true }),
  ];
  const merged = [];
  const content = pr({ number: 4, title: 'feat(tarot): needs a check' });
  open.push(content);
  const result = tick({ gh: plannedGh(open, date), now: { date, hour: 11, minute: 5 }, merge: n => { merged.push(n); return { status: 'merged' }; }, check: () => ({ status: 'FAIL' }), review: () => ({ status: 'posted' }) });
  assert.equal(result.area, 'content', 'content machine work (#4 check) goes first');
  assert.deepEqual(merged, []);
  const queue = JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  assert.deepEqual(queue.items.map(i => i.number), [1], 'Claude still fixes content first');
  open.pop();
  const next = tick({ gh: plannedGh(open, date), now: { date, hour: 12, minute: 5 }, merge: n => { merged.push(n); return { status: 'merged' }; }, review: () => ({ status: 'posted' }) });
  assert.equal(next.area, 'privacy', 'a content PR waiting for Claude does not stall the machine');
  assert.deepEqual(merged, [2]);
});

test('r2: every CLI entry loads and exits without hanging on an import cycle', () => {
  for (const [file, args, expect] of [['collab-tick.mjs', ['--self-test'], /collab-tick ok/], ['codex-review.mjs', [], /Usage/], ['collab-merge.mjs', [], /Usage/], ['collab-check.mjs', [], /Usage/]]) {
    const result = spawnSync(process.execPath, [join(import.meta.dirname, file), ...args], { encoding: 'utf8', timeout: 10000, env: { ...process.env, LA_LANH_COLLAB_HOME: trust.stateDir } });
    assert.equal(result.error, undefined, `${file} must not time out`);
    assert.match(`${result.stdout}${result.stderr}`, expect, file);
    assert.doesNotMatch(result.stderr, /unsettled top-level await/, file);
  }
});

test('r2 (#131): scheduled reviews read the clock after preparing the clone', () => {
  const late = review.runReview(7, { auto: true, gh: fakeGh({ pr: pr({ comments: [check(A)] }) }), run: fakeRun().run, now: { date: '2026-11-06', hour: 23, minute: 29 }, nowMs: () => Date.parse('2026-11-06T12:00:00+07:00'), clock: () => ({ date: '2026-11-06', hour: 23, minute: 33 }) });
  assert.equal(late.status, 'refused');
  const runner = fakeRun();
  review.runReview(7, { auto: true, gh: fakeGh({ pr: pr({ comments: [check(A)] }) }), run: runner.run, readOut: () => JSON.stringify(output()), now: { date: '2026-11-06', hour: 23, minute: 0 }, nowMs: () => Date.parse('2026-11-06T12:00:00+07:00'), clock: () => ({ date: '2026-11-06', hour: 23, minute: 25 }) });
  // #243: Codex ends early enough to publish the verdict before 23:55.
  assert.equal(runner.calls.find(c => c[0] === review.codexBin)[2].timeout, 30 * 60000 - review.reviewFinalizeReserveMs);
  const tight = fakeRun();
  review.runReview(8, { auto: true, gh: fakeGh({ pr: pr({ number: 8, comments: [check(A)] }) }), run: tight.run, readOut: () => JSON.stringify(output()), now: { date: '2026-11-07', hour: 23, minute: 0 }, nowMs: () => Date.parse('2026-11-07T12:00:00+07:00'), clock: () => ({ date: '2026-11-07', hour: 23, minute: 29 }) });
  assert.equal(tight.calls.find(c => c[0] === review.codexBin)[2].timeout, 26 * 60000 - review.reviewFinalizeReserveMs);
  const none = fakeRun();
  assert.equal(review.runReview(9, { auto: true, gh: fakeGh({ pr: pr({ number: 9, comments: [check(A)] }) }), run: none.run, now: { date: '2026-11-07', hour: 23, minute: 0 }, nowMs: () => Date.parse('2026-11-07T12:00:00+07:00'), clock: () => ({ date: '2026-11-07', hour: 23, minute: 50 }) }).status, 'refused');
  assert.ok(!none.calls.some(c => c[0] === review.codexBin), 'no Codex run without room to publish');
});

test('r3: the tick runs one author check itself, then reviews that PR', () => {
  const date = '2026-11-08';
  const open = [pr({ number: 1 }), pr({ number: 2 })];
  const calls = [];
  const result = tick({ gh: plannedGh(open, date), now: { date, hour: 11, minute: 5 }, merge: () => ({}),
    check: n => { calls.push(['check', n]); return { status: 'PASS' }; }, review: n => { calls.push(['review', n]); return { status: 'posted' }; } });
  assert.equal(result.status, 'ran');
  assert.deepEqual(calls, [['check', 1], ['check', 2], ['review', 1], ['review', 2]], 'fix E: ready PRs are checked back to back, then reviewed in the same tick');
  const failed = [];
  tick({ gh: plannedGh(open, date), now: { date, hour: 12, minute: 5 }, merge: () => ({}), check: () => ({ status: 'FAIL' }), review: n => { failed.push(n); return {}; } });
  assert.deepEqual(failed, [], 'a FAIL is not reviewed');
});

test('owner data 03.11: the private guard expands dates and finds added lines, never removed ones', () => {
  const terms = guardTerms('# synthetic only\ndate:2001-02-03\nZz Secret\n\n');
  for (const spelling of ['2001-02-03', '03/02/2001', '3/2/2001', '03.02.2001', '20010203', 'zz secret']) assert.ok(terms.includes(spelling), spelling);
  const diff = ['+++ b/apps/x.py', '@@ -1,0 +5,2 @@', '+ok line', '+born 03.02.2001', '+++ b/docs/y.md', '@@ -7 +7 @@', '-old ZZ SECRET', '+clean'].join('\n');
  assert.deepEqual(guardHits(terms, { diff }), ['apps/x.py:6']);
  assert.deepEqual(guardHits(terms, { diff: '', texts: { 'commit message': 'fix\nZZ secret here' } }), ['commit message']);
  assert.deepEqual(guardHits([], { diff }), [], 'no list, nothing to block');
});

test('owner data 03.11: a guarded term fails the author check before pnpm runs and is never echoed', () => {
  const never = () => { throw new Error('must not run pnpm'); };
  const terms = () => guardTerms('zz-secret-term');
  const gh = fakeGh({ pr: pr() });
  const git = args => (args[0] === 'rev-parse' ? A : args.includes('-p') ? '+++ b/apps/fixture.ts\n@@ -0,0 +12 @@\n+const x = "zz-secret-term";' : '');
  const result = runCheck(7, { gh, git, busy: () => null, spawn: never, terms });
  assert.equal(result.status, 'FAIL');
  const receipt = gh.calls.find(c => c[0] === 'comment')[3];
  assert.equal(trust.parseAuthorCheck(receipt).status, 'FAIL');
  assert.match(receipt, /dữ liệu riêng tư[\s\S]*apps\/fixture\.ts:12/);
  assert.doesNotMatch(receipt, /zz-secret-term/);
  assert.equal(runCheck(7, { gh: fakeGh({ pr: pr({ body: 'see ZZ-SECRET-TERM' }) }), git: args => (args[0] === 'rev-parse' ? A : ''), busy: () => null, spawn: never, terms }).status, 'FAIL', 'PR body is scanned');
  const broken = args => { if (args.includes('-p')) throw new Error('no base'); return args[0] === 'rev-parse' ? A : ''; };
  assert.equal(runCheck(7, { gh: fakeGh({ pr: pr() }), git: broken, busy: () => null, spawn: never, terms }).status, 'FAIL', 'fails closed without a diff');
});

test('#198 r1: every outgoing commit is scanned, the pushed refs are scanned, paths are masked', () => {
  const terms = guardTerms('date:2001-02-03');
  // Commit A adds the value, commit B removes it: the net diff is clean, the log patch is not.
  const seen = [];
  const git = args => { seen.push(args); return args.includes('-p') ? '+++ b/apps/a.ts\n@@ -0,0 +3 @@\n+x = "2001-02-03"\n+++ b/apps/a.ts\n@@ -3 +2,0 @@\n-x = "2001-02-03"' : ''; };
  assert.deepEqual(privateHits({}, git, () => terms), ['apps/a.ts:3']);
  assert.ok(seen.every(a => a.includes('log') && a.includes('-m') && a.includes('origin/collab/integration..HEAD')), 'author check scans the PR commits, merges included');
  // Pre-push: each pushed ref, every commit the remote lacks; a deleted ref sends nothing.
  const Z = '0'.repeat(40);
  assert.deepEqual(prePushRanges(`refs/heads/a ${A} refs/heads/a ${Z}\nrefs/heads/b ${B} refs/heads/b ${A}\n(delete) ${Z} refs/heads/c ${A}\n`), [[A, '--not', '--remotes=origin'], [B, '--not', '--remotes=origin']]);
  const ranges = [];
  privateHits({}, args => { if (args.includes('-p')) ranges.push(args.slice(-3)); return ''; }, () => terms, prePushRanges(`refs/heads/b ${B} refs/heads/b ${A}`));
  assert.deepEqual(ranges, [[B, '--not', '--remotes=origin']]);
  // A path holding the value is a hit, and the receipt masks it.
  const hits = guardHits(terms, { diff: '+++ b/fixtures/2001-02-03.txt\n@@ -0,0 +1 @@\n+fine' });
  assert.deepEqual(hits, ['fixtures/[ẩn].txt']);
  assert.doesNotMatch(renderCheck({ head: A, status: 'FAIL', exitCode: 'guard', seconds: 0, date: 'd', guard: hits }), /2001-02-03/);
});

test('#198 r2: real git history — a merge resolution and a rename-only change are caught', () => {
  const dir = mkdtempSync(join(tmpdir(), 'guard-repo-'));
  const run = args => String(execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', '-c', 'commit.gpgsign=false', ...args], { cwd: dir, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })).trim();
  const write = (name, text) => writeFileSync(join(dir, name), text);
  const terms = () => guardTerms('date:2001-02-03');
  run(['init', '-q', '-b', 'main']);
  write('a.txt', 'base\n'); write('sample.txt', 'same\n');
  run(['add', '.']); run(['commit', '-qm', 'base']);
  run(['update-ref', 'refs/remotes/origin/collab/integration', 'HEAD']);
  run(['checkout', '-qb', 'side']); write('b.txt', 'side\n'); run(['add', '.']); run(['commit', '-qm', 'side']);
  run(['checkout', '-q', 'main']); write('c.txt', 'main\n'); run(['add', '.']); run(['commit', '-qm', 'main']);
  assert.deepEqual(privateHits({}, run, terms), [], 'clean history passes');
  // The merge resolution alone adds the value: neither parent nor any message has it.
  run(['merge', '-q', '--no-ff', '--no-commit', 'side']); write('a.txt', 'base\nresolved 2001-02-03\n'); run(['add', '.']); run(['commit', '-qm', 'merge side']);
  assert.deepEqual(privateHits({}, run, terms), ['a.txt:2']);
  run(['reset', '-q', '--hard', 'HEAD~1']);
  // A rename with no content change: no +++ header with the new name, still a hit, shown masked.
  run(['mv', 'sample.txt', '2001-02-03.txt']); run(['commit', '-qm', 'rename']);
  assert.deepEqual(privateHits({}, run, terms), ['[ẩn].txt']);
  // An empty new file has no hunk at all.
  run(['reset', '-q', '--hard', 'HEAD~1']); write('03.02.2001', ''); run(['add', '.']); run(['commit', '-qm', 'empty']);
  assert.deepEqual(privateHits({}, run, terms), ['[ẩn]']);
  rmSync(dir, { recursive: true, force: true });
});

test('#198 r1: an unreadable guard list blocks instead of switching the guard off', () => {
  const dir = mkdtempSync(join(tmpdir(), 'guard-'));
  assert.deepEqual(readGuardTerms(join(dir, 'absent.txt')), [], 'no file: no guard');
  assert.throws(() => readGuardTerms(dir), /unreadable/, 'a directory at the path is an error');
  assert.deepEqual(privateHits({}, () => '', () => readGuardTerms(dir)), ['danh sách chặn không đọc được']);
  const never = () => { throw new Error('must not run pnpm'); };
  assert.equal(runCheck(7, { gh: fakeGh({ pr: pr() }), git: args => (args[0] === 'rev-parse' ? A : ''), busy: () => null, spawn: never, terms: () => readGuardTerms(dir) }).status, 'FAIL');
  rmSync(dir, { recursive: true, force: true });
});

test('r3: author check runs alone, with CI=1, in the given checkout', () => {
  const gh = fakeGh({ pr: pr() });
  const git = args => (args[0] === 'rev-parse' ? A : '');
  assert.equal(runCheck(7, { gh, git, busy: () => '123 sh -c pnpm contracts:check', spawn: () => { throw new Error('must not run'); } }).status, 'busy');
  const spawned = [];
  const result = runCheck(7, { gh, git, cwd: '/tmp/author', busy: () => null, spawn: (cmd, args, opts) => { spawned.push({ cmd, args, opts }); return { status: 0 }; } });
  assert.equal(result.status, 'PASS');
  assert.equal(spawned[0].opts.env.CI, '1');
  assert.ok(spawned[0].opts.env.PATH.split(':').includes('/sbin'), 'system tools (sha256sum) are reachable');
  assert.equal(spawned[0].opts.cwd, '/tmp/author');
  assert.equal(trust.parseAuthorCheck(gh.calls.find(c => c[0] === 'comment')[3]).status, 'PASS');
  const nested = withCheckLock(() => runCheck(7, { gh, git, busy: () => null, spawn: () => ({ status: 0 }) }));
  assert.equal(nested.status, 'busy', 'a second check waits for the lock');
});

test('r4 (P0): fork or outside PRs are never checked, reviewed or merged', () => {
  const approved = [check(A), owner(`Review verdict: APPROVE @ ${A}`)];
  for (const hostile of [pr({ isCrossRepository: true, comments: approved }), pr({ author: { login: 'someone-else' }, comments: approved }), pr({ author: undefined, comments: approved })]) {
    assert.equal(prTurn(hostile).turn, 'hold');
    assert.ok(!mergeGate(hostile).ok);
    const never = () => { throw new Error('must not run anything for an untrusted PR'); };
    assert.equal(runCheckInClone(7, { gh: fakeGh({ pr: hostile }), run: never, busy: () => null }).status, 'refused');
    assert.equal(runCheck(7, { gh: fakeGh({ pr: hostile }), git: args => (args[0] === 'rev-parse' ? A : ''), busy: () => null, spawn: never }).status, 'refused');
    assert.equal(review.runReview(7, { gh: fakeGh({ pr: { ...hostile, comments: [check(A)] } }), run: never }).status, 'refused');
  }
  assert.deepEqual(turnsFor([pr({ number: 9, title: 'ops(collab): x', isCrossRepository: true })]).map(t => t.turn), ['hold'], 'an ops title from a fork gets no priority');
});

test('r4 (P1): automatic checks start nothing after 23:30 and end by 23:55', () => {
  const at = (hour, minute) => () => ({ date: 'd', hour, minute });
  assert.equal(checkBudgetMs({ auto: true, clock: at(11, 0) }), 90 * 60000 - 15000);
  assert.equal(checkBudgetMs({ auto: true, clock: at(23, 20) }), 35 * 60000 - 15000);
  assert.equal(checkBudgetMs({ auto: true, clock: at(23, 30) }), 0);
  assert.equal(checkBudgetMs({ auto: true, clock: at(8, 0) }), 0);
  assert.equal(checkBudgetMs({ auto: false, clock: at(23, 50) }), 90 * 60000);
  // Selected at 23:20, ready after a slow clone/install at 23:33: refused before pnpm check starts.
  const times = [at(23, 20)(), at(23, 33)()];
  const spawned = [];
  const run = (cmd, args) => (cmd === '/usr/bin/git' && args[0] === 'rev-parse' ? `${A}\n` : '');
  const result = runCheckInClone(7, { gh: fakeGh({ pr: pr() }), run, group: () => ({ status: 0 }), auto: true, clock: () => times.shift() ?? at(23, 40)(), busy: () => null, spawn: (...a) => { spawned.push(a); return { status: 0 }; } });
  assert.equal(result.status, 'refused');
  assert.deepEqual(spawned, []);
});

test('r4 (P1): the deadline kills the whole process group', () => {
  // A marker built at run time, so pgrep cannot match the shell that launched the tests.
  const marker = `${30 + (process.pid % 7)}.${Date.now() % 100000}`;
  const started = Date.now();
  runGroup('/bin/sh', ['-c', `sleep ${marker} & sleep ${marker}`], { timeoutMs: 1000 });
  assert.ok(Date.now() - started < 15000, 'returns at the deadline');
  const left = spawnSync('pgrep', ['-f', `^sleep ${marker}`], { encoding: 'utf8' }).stdout.trim();
  assert.equal(left, '', 'no child outlives the check');
});

test('r5 (#137 r2 P1): clone preparation is bounded by the nightly deadline', () => {
  const minute = 60000;
  let fake = 0;
  const calls = [];
  // Worst case: every build step uses its whole budget and times out.
  const group = (cmd, args, opts) => { calls.push({ cmd, ms: opts.timeoutMs, left: 26 * minute - fake }); fake += opts.timeoutMs; return { status: 124 }; };
  const run = (cmd, args) => (args[0] === 'rev-parse' ? A : '');
  // Selected at 23:29: 26 minutes to 23:55.
  assert.throws(() => prepareAuthorClone(7, A, run, { deadlineMs: 26 * minute, nowMs: () => fake, group }), /hết giờ/);
  assert.ok(calls.length >= 1);
  assert.ok(calls.every(c => c.ms <= c.left), 'no step may run past the deadline');
  assert.ok(!calls.some(c => c.cmd === 'make'), 'make never starts after the deadline');
  assert.ok(fake <= 26 * minute);
  const result = runCheckInClone(7, { gh: fakeGh({ pr: pr() }), run, auto: true, clock: () => ({ date: 'd', hour: 23, minute: 29 }), nowMs: () => fake, group, busy: () => null, spawn: () => { throw new Error('pnpm check must not start'); } });
  assert.equal(result.status, 'refused');
});

test('r5 (#137 r2 P1): members that ignore SIGTERM are force-killed before the supervisor returns', () => {
  const marker = `${40 + (process.pid % 7)}.${Date.now() % 100000}`;
  const started = Date.now();
  const result = runGroup('/bin/sh', ['-c', `trap '' TERM; sleep ${marker} & sleep ${marker}`], { timeoutMs: 500, graceMs: 1000, stdio: 'ignore' });
  assert.equal(result.status, 124);
  assert.ok(Date.now() - started < 10000);
  assert.equal(spawnSync('pgrep', ['-f', `^sleep ${marker}`], { encoding: 'utf8' }).stdout.trim(), '', 'nothing survives');
});

test('#140: the budget ends at the exact 23:55:00 instant, with room for cleanup', () => {
  const nowMs = () => Date.parse('2026-11-09T23:29:59+07:00');
  const budget = checkBudgetMs({ auto: true, clock: () => ({ date: '2026-11-09', hour: 23, minute: 29 }), nowMs });
  const cutoff = Date.parse('2026-11-09T23:55:00+07:00');
  // Deadline plus the 5 s grace and the kill poll stay before the cutoff.
  assert.ok(nowMs() + budget + 5000 + 1000 <= cutoff, `budget ${budget} runs past 23:55`);
  assert.ok(budget > 24 * 60000);
});

test('retro D3: the plan says when the Mac stopped ticking', () => {
  const now = Date.parse('2026-10-31T09:41:00+07:00');
  assert.equal(tickGap({ at: new Date(now - 10 * 60000).toISOString() }, now), null);
  assert.deepEqual(tickGap({ at: '2026-10-30T21:25:43Z' }, now), { from: '04:25', to: '09:41' });
  const body = renderPlan({ date: '2026-10-31', hour: 9, minute: 41 }, [], { codexLeft: 12, gap: { from: '04:25', to: '09:41' } });
  assert.match(body, /Máy không chạy tick từ 04:25 tới 09:41/);
  assert.doesNotThrow(() => trust.assertAgentBody(body));
});

test('owner 12.11: the plan picks 3–5 work items with a source and what the user sees, no PR quota', () => {
  const body5 = n => goodBody.replace('G1 Tài liệu: plan §3', `G1 Tài liệu: US-${n} AC2`).replace(/Người dùng thấy gì:[^\n]*/, `Người dùng thấy gì: câu số ${n} dễ đọc hơn`);
  const many = turnsFor(Array.from({ length: 8 }, (_, i) => pr({ number: 20 + i, body: body5(20 + i), createdAt: `2026-10-${10 + i}T00:00:00Z` })).concat(pr({ number: 99, isDraft: true })));
  const committed = committedTurns(many);
  assert.equal(committed.length, planMax, 'never more than 5 work items');
  assert.equal(planMin, 3);
  assert.ok(!committed.some(t => t.number === 99), 'a held PR is not picked');
  const body = renderPlan({ date: '2026-11-03', hour: 8, minute: 50 }, many, { codexLeft: 12 });
  assert.match(body, /\*\*Việc chọn hôm nay \(3–5 việc\):\*\*/);
  assert.match(body, /1\. #20 feat\(tarot\): plain summary\n {3}- Nguồn \/ AC: US-20 AC2\n {3}- Người dùng thấy gì: câu số 20 dễ đọc hơn/);
  assert.match(body, /Tiến độ hôm nay = việc xong \/ việc đã chọn/);
  assert.match(body, /Lượt Codex tự động còn hôm nay: 12\/32\./);
  assert.doesNotMatch(body, /16|20 PR|% hôm nay|Cam kết/, 'no PR quota and no % of committed PRs');
  const few = renderPlan({ date: '2026-11-03', hour: 8, minute: 50 }, turnsFor([pr()]), { codexLeft: 12 });
  assert.match(few, /1\. #7 [^\n]*\n {3}- Nguồn \/ AC: plan §3\n {3}- Người dùng thấy gì: không trực tiếp \(vận hành\)/);
  const bare = renderPlan({ date: '2026-11-03', hour: 8, minute: 50 }, turnsFor([pr({ body: '' })]), { codexLeft: 12 });
  assert.match(bare, /- Nguồn \/ AC: chưa ghi\n {3}- Người dùng thấy gì: chưa ghi/);
  assert.match(few, /Còn thiếu 2 việc so với mức 3/);
  assert.match(few, /1 việc đang làm \+ 1 việc đang review/);
  assert.doesNotThrow(() => trust.assertAgentBody(body));
  assert.doesNotThrow(() => trust.assertAgentBody(few));
});

test('owner 12.11: the preflight asks for a "Người dùng thấy gì:" line; ops PRs may say not directly', () => {
  assert.deepEqual(preflightMod.bodyProblems(goodBody), []);
  const without = goodBody.replace(/\nNgười dùng thấy gì:[^\n]*/, '');
  assert.deepEqual(preflightMod.bodyProblems(without), ['PR body thiếu dòng "Người dùng thấy gì:"']);
  assert.deepEqual(preflightMod.bodyProblems(`${without}\nNgười dùng thấy gì:   `), ['PR body thiếu dòng "Người dùng thấy gì:"'], 'a blank answer is not an answer');
  assert.deepEqual(preflightMod.bodyProblems(`${without}\nNgười dùng thấy gì: không trực tiếp (vận hành)`), []);
  assert.deepEqual(preflightMod.bodyProblems(`${without}\n- **Người dùng thấy gì:** nút lưu rõ hơn`), []);
  assert.deepEqual(preflightMod.bodyProblems(`${without}\nGhi chú: Người dùng thấy gì: x`), ['PR body thiếu dòng "Người dùng thấy gì:"'], 'the line must start with it');
});

test('false FAIL 31.10: pnpm check always sees the system tool directories', () => {
  assert.equal(withSystemPath('/a:/usr/bin'), '/a:/usr/bin:/bin:/usr/sbin:/sbin');
  assert.equal(withSystemPath(''), '/usr/bin:/bin:/usr/sbin:/sbin');
});

test('false FAIL 31.10: the tick names missing tools instead of running checks', async () => {
  const { missingTools, requiredTools } = await import('./collab-tick.mjs');
  assert.ok(requiredTools.includes('pnpm') && requiredTools.includes('sha256sum'));
  assert.deepEqual(missingTools('/nonexistent'), requiredTools);
  assert.deepEqual(missingTools('/x', () => ''), []);
});

test('#141 r1 P1: missing tools go through the tick failure path and alert on the second', () => {
  const date = '2026-11-10';
  const alerts = [];
  const gh = { ...fakeGh({ pr: pr(), open: [] }), json: () => { throw new Error('no GitHub call before the preflight'); } };
  const run = hour => tick({ gh, now: { date, hour, minute: 5 }, preflight: () => ['uv'], merge: () => ({}), review: () => ({}), alert: text => alerts.push(text) });
  const first = run(11);
  assert.equal(first.status, 'error');
  assert.match(first.error, /thiếu công cụ trên PATH: uv/);
  assert.match(trust.readJson(join(trust.stateDir, 'heartbeat.json'), {}).status, /thiếu công cụ/);
  assert.equal(alerts.length, 0);
  run(12);
  assert.equal(alerts.length, 1, 'the second consecutive failure alerts');
});

test('busy check matches the running program, not a command line that mentions it (31.10)', () => {
  for (const heavy of [
    'sh -c pnpm contracts:check && pnpm verify:runtime && pnpm grammar:check',
    '/Users/x/apps/api/.venv/bin/python /Users/x/apps/api/.venv/bin/pytest -q',
    'uv run --directory apps/api pytest',
    '/x/node/bin/node /x/node_modules/.bin/../vitest/vitest.mjs run',
    '/x/node/bin/node /x/node_modules/@playwright/test/cli.js test',
    // #142 r1: the current check wrapper and bare interpreters.
    'sh -c pnpm collab:test && pnpm contracts:check && pnpm verify:runtime',
    'node /x/node_modules/@playwright/test/cli.js test',
    'node /x/node_modules/vitest/vitest.mjs run',
    'uv run pytest',
    'pnpm check',
    '/x/node /x/pnpm.cjs check',
    'pytest -q',
  ]) assert.ok(isHeavy(heavy), heavy);
  for (const light of [
    '/bin/zsh -c source snap.sh && eval \'pgrep -f "contracts:check|vitest|pytest|playwright"\'',
    'node /x/scripts/collab-check.mjs --pr 1 --clone',
    'grep -E vitest|pytest',
    'tail -f /x/check-139.log',
    '/bin/zsh -c sh -c pnpm collab:test',
    'node /x/scripts/codex-review.mjs --pr 3',
  ]) assert.ok(!isHeavy(light), light);
  const ps = () => `  ${process.pid} sh -c pnpm contracts:check\n  41405 /bin/zsh -c pgrep -f contracts:check\n  9 /bin/zsh\n`;
  assert.equal(machineBusy(ps), null, 'its own process and agent shells are ignored');
  assert.match(machineBusy(() => '  77 sh -c pnpm contracts:check && x\n'), /^77 sh -c pnpm contracts:check/);
});

test('WIP 1 + 1 (owner 12.11): the tick asks for a new task only when nothing is in progress and review has room', () => {
  const date = '2026-11-12';
  const queue = () => JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  const agent = (number, extra = {}) => pr({ number, headRefName: `agent/claude/t${number}`, ...extra });
  const inFix = [check(A), owner(`Review verdict: REQUEST_CHANGES @ ${A}`)];
  const run = (open, minute) => tick({ gh: plannedGh(open, date), now: { date, hour: 15, minute }, merge: () => ({}), check: () => ({ status: 'FAIL' }), review: () => ({ status: 'posted' }) });
  run([agent(1, { comments: inFix }), agent(2, { comments: [check(A)] })], 5);
  assert.equal(queue().topUp, false, '1 in progress + 1 in review: no new task');
  assert.deepEqual([queue().inProgress, queue().inReview], [1, 1]);
  run([agent(3, { comments: [check(A)] })], 15);
  assert.equal(queue().topUp, true, 'one in review and nothing in progress: Claude starts one task');
  assert.equal(queue().topUpCount, 1);
  run([agent(4, { comments: [check(A)] }), agent(5, { comments: [check(A)] })], 25);
  assert.equal(queue().topUp, false, 'two in review: finish before starting');
  run([agent(6, { comments: inFix })], 35);
  assert.equal(queue().topUp, false, 'a task in progress fills the slot even with review empty');
  run([pr({ number: 7, comments: inFix })], 45);
  assert.equal(queue().topUp, true, 'an owner branch is not agent work in progress');
});

test('retro S1: runs in a row with no area ask for a top-up from the third and alert on the sixth', () => {
  const date = '2026-11-13';
  const alerts = [];
  const queue = () => JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  const run = (open, minute) => tick({ gh: plannedGh(open, date), now: { date, hour: 18, minute }, merge: () => ({}), check: () => ({ status: 'FAIL' }), review: () => ({}), alert: text => alerts.push(text) });
  for (let i = 1; i <= 7; i += 1) {
    run([], i);
    assert.equal(queue().idleRuns, i);
    assert.equal(queue().topUp, true);
  }
  assert.equal(alerts.length, 1, 'one alert at the sixth idle run, not on every run after it');
  assert.match(alerts[0], /chạy không 6 lượt liền/);
  run([7, 8, 9, 10, 11].map(number => pr({ number, headRefName: `agent/claude/t${number}` })), 30);
  assert.equal(queue().idleRuns, 0, 'a run with an area resets the count');
  assert.equal(queue().topUp, false);
});

test('#237: a failed idle alert is retried on the next idle run until it is delivered', () => {
  const date = '2026-11-14';
  const alerts = [];
  let fail = true;
  const logs = [];
  const alert = text => { if (fail) { fail = false; throw new Error('gh down'); } alerts.push(text); };
  const run = minute => tick({ gh: plannedGh([], date), now: { date, hour: 18, minute }, merge: () => ({}), check: () => ({ status: 'FAIL' }), review: () => ({}), alert, log: line => logs.push(line) });
  for (let i = 1; i <= 6; i += 1) run(i);
  assert.equal(alerts.length, 0, 'the sixth run tried and failed');
  assert.equal(logs.filter(line => /idle alert failed, retry next run: gh down/.test(line)).length, 1, '#292: the failed delivery is logged with its error');
  run(7);
  assert.equal(alerts.length, 1, 'the seventh run retries the failed alert');
  run(8); run(9);
  assert.equal(alerts.length, 1, 'no repeat once delivered');
});

test('#292: the launchd tick hands tick() a stderr logger, so a failed delivery is not silent', async () => {
  const { runTick, tickLog } = await import('./collab-tick.mjs');
  const opts = runTick(fakeGh({ pr: pr(), open: [] }), () => [], { run: given => given });
  assert.equal(opts.log, tickLog, 'the production caller supplies the logger');
  const written = [];
  tickLog('idle alert failed, retry next run: gh down', text => written.push(text));
  assert.equal(written.length, 1);
  assert.match(written[0], /^\d{4}-\d{2}-\d{2}T\S+ collab-tick: idle alert failed, retry next run: gh down\n$/);
});

// ---- Loop fixes A–E (owner 04.11.2026) ----
const goodBody = [
  '- Mức: M — script vòng tự động',
  ...['G1 Tài liệu: plan §3', 'G2 UI/UX: không áp dụng, không đụng giao diện', 'G3 Câu chữ: không có câu mới', 'G4 BE: không áp dụng', 'G5 FE: không áp dụng',
    'G6 QC: node --test', 'G7 Bảo mật: không đụng phiên, quyền, dữ liệu cá nhân hay log', 'G8 Data privacy: không thu dữ liệu', 'G9 Release: không áp dụng cho PR vào integration', 'G10 Chi phí / license: không'].map(l => `- ${l}`),
  'Người dùng thấy gì: không trực tiếp (vận hành)',
].join('\n');

test('fix A: the preflight names a blank gate, a missing level and an unanswered G7', () => {
  assert.deepEqual(preflightMod.bodyProblems(goodBody), []);
  const template = readFileSync(new URL('../.github/pull_request_template.md', import.meta.url), 'utf8');
  const blank = preflightMod.bodyProblems(template);
  assert.match(blank[0], /thiếu cổng G1, G2, G3, G4, G5, G6, G7, G8, G10$/, 'G9 is pre-filled by the template');
  assert.ok(blank.includes('PR body thiếu mức rủi ro S/M/L'), 'the template "S | M | L" is not a choice');
  assert.deepEqual(preflightMod.bodyProblems(goodBody.replace(/- G7 [^\n]*/, '- G7 Bảo mật: ok')), ['G7 chưa trả lời checklist (phiên, quyền, dữ liệu cá nhân, log)']);
  assert.deepEqual(preflightMod.bodyProblems(goodBody.replace('- G10 Chi phí / license: không', '')), ['PR body thiếu cổng G10'], 'G1 never stands in for G10');
});

test('fix A: ruff and mypy run only on the changed Python files of apps/api', () => {
  assert.deepEqual(preflightMod.changedPython([{ path: 'apps/api/app/x.py' }, { path: 'apps/web/a.ts' }, { path: 'scripts/y.py' }, 'apps/api/tests/t.py']), ['app/x.py', 'tests/t.py']);
  const runs = [];
  const spawn = (cmd, args) => { runs.push([cmd, ...args].join(' ')); return { status: args.includes('mypy') ? 1 : 0, stdout: 'app/x.py:3: error: bad' }; };
  const result = preflightMod.runPreflight({ body: goodBody, files: [{ path: 'apps/api/app/x.py' }, { path: 'README.md' }] }, { cwd: '/repo', spawn, exists: () => true });
  assert.deepEqual(runs, ['uv run --directory apps/api ruff check app/x.py', 'uv run --directory apps/api ruff format --check app/x.py', 'uv run --directory apps/api mypy app/x.py']);
  assert.equal(result.status, 'FAIL');
  assert.match(result.reasons[0], /^mypy lỗi: app\/x\.py:3/);
  const none = [];
  assert.equal(preflightMod.runPreflight({ body: goodBody, files: [{ path: 'docs/a.md' }] }, { cwd: '/repo', spawn: () => { none.push(1); return { status: 1 }; } }).status, 'PASS');
  assert.deepEqual(none, [], 'no Python changed: uv never starts');
  assert.equal(preflightMod.runPreflight({ body: '', files: [{ path: 'apps/api/app/x.py' }] }, { cwd: '/repo', spawn: () => { throw new Error('no lint when the body fails'); } }).status, 'FAIL');
});

test('fix A: a preflight failure posts nothing, skips the check and sends the PR to claude-fix', () => {
  const date = '2026-11-12';
  const open = [pr({ number: 1, headRefOid: A }), pr({ number: 2, headRefOid: B })];
  const gh = plannedGh(open, date);
  const checked = [];
  const result = tick({ gh, now: { date, hour: 11, minute: 5 }, merge: () => ({}), review: () => ({ status: 'posted' }),
    prPreflight: n => n === 1 ? { status: 'FAIL', reasons: ['PR body thiếu mức rủi ro S/M/L'] } : { status: 'PASS' },
    check: n => { checked.push(n); return { status: 'PASS' }; } });
  assert.equal(result.status, 'ran');
  assert.deepEqual(checked, [2], 'the failing PR spends no check; the next ready PR runs');
  assert.ok(!gh.calls.some(c => c[0] === 'comment' && c[2] === 1), 'preflight posts nothing on the PR');
  const turn = turnsFor(open).find(t => t.number === 1);
  assert.equal(turn.turn, 'claude-fix');
  assert.equal(turn.reason, 'preflight: PR body thiếu mức rủi ro S/M/L');
  assert.equal(turnsFor([{ ...open[0], headRefOid: C }])[0].turn, 'claude-check', 'a new head clears the record');
  preflightMod.recordPreflight(1, A, { status: 'PASS' });
});

test('fix A: the clone check stops on a lint failure before pnpm and posts nothing', () => {
  const posted = [];
  const gh = { ...fakeGh({ pr: pr() }), comment: (...a) => posted.push(a) };
  const run = (cmd, args) => args[0] === 'rev-parse' ? A : '';
  const result = runCheckInClone(7, { gh, run, group: () => ({ status: 0 }), busy: () => null, terms: () => [],
    preflight: () => ({ status: 'FAIL', reasons: ['ruff lỗi: x'] }), spawn: () => { throw new Error('pnpm check must not start'); } });
  assert.deepEqual(result, { status: 'preflight', reasons: ['ruff lỗi: x'] });
  assert.deepEqual(posted, []);
  assert.equal(turnsFor([pr()])[0].turn, 'claude-fix', 'a lint failure is recorded for this head');
  preflightMod.recordPreflight(7, A, { status: 'PASS' });
});

test('12.11 trial: CI source reads pr-check at the head and never installs, builds or runs the PR', () => {
  const posted = [];
  const gh = { ...fakeGh({ pr: pr() }), comment: (...a) => posted.push(a) };
  const run = (cmd, args) => args[0] === 'rev-parse' ? A : '';
  const never = () => { throw new Error('nothing of the PR may run on the Mac in CI mode'); };
  const ci = (_, head) => { assert.equal(head, A); return { state: 'PASS', conclusion: 'success', url: 'https://github.com/x/actions/runs/1' }; };
  const result = runCheckInClone(7, { gh, run, group: never, spawn: never, busy: never, terms: () => [], preflight: () => null, source: 'ci', ci });
  assert.equal(result.status, 'PASS');
  assert.equal(posted.length, 1);
  assert.match(posted[0][2], new RegExp(`^Author check: PASS @ ${A}`));
  assert.match(posted[0][2], /Nguồn: CI `pr-check \/ check` · success/);
  assert.match(posted[0][2], new RegExp(`author-check sha=${A}`));
  const fail = runCheckInClone(7, { gh, run, group: never, spawn: never, busy: never, terms: () => [], preflight: () => null, source: 'ci', ci: () => ({ state: 'FAIL', conclusion: 'cancelled', url: '' }) });
  assert.equal(fail.status, 'FAIL');
  assert.match(posted[1][2], /^Author check: FAIL @/);
  assert.match(posted[1][2], /CI bị huỷ/);
  const wait = runCheckInClone(7, { gh, run, group: never, spawn: never, busy: never, terms: () => [], preflight: () => null, source: 'ci', ci: () => ({ state: 'pending' }) });
  assert.equal(wait.status, 'ci-pending');
  assert.equal(posted.length, 2, 'a pending CI posts nothing');
});

test('12.11 trial: ciCheck passes only a completed success of the pr-check check job at the exact head', () => {
  // Synthetic GitHub API: workflow runs of pr-check.yml by head, then the jobs of one run.
  const at = (runs, jobsByRun = {}) => ({ json: args => {
    const path = args[1];
    if (/\/actions\/workflows\/pr-check\.yml\/runs\?head_sha=/.test(path)) return { workflow_runs: runs };
    const id = /\/actions\/runs\/(\d+)\/jobs/.exec(path)?.[1];
    if (id) return { jobs: jobsByRun[id] ?? [] };
    throw new Error(`unexpected api ${path}`);
  } });
  const w = o => ({ id: 1, path: '.github/workflows/pr-check.yml', head_sha: A, status: 'completed', created_at: '2026-11-12T01:00:00Z', html_url: 'r', ...o });
  const j = o => ({ name: 'check', run_id: 1, head_sha: A, status: 'completed', conclusion: 'success', html_url: 'u', ...o });
  assert.equal(ciCheck(at([]), A).state, 'pending');
  assert.equal(ciCheck(at([w({ status: 'in_progress' })], { 1: [j({ status: 'in_progress', conclusion: null })] }), A).state, 'pending');
  assert.equal(ciCheck(at([w()], { 1: [j()] }), A).state, 'PASS');
  for (const conclusion of ['failure', 'cancelled', 'skipped', 'timed_out', 'neutral', 'action_required']) assert.equal(ciCheck(at([w()], { 1: [j({ conclusion })] }), A).state, 'FAIL', conclusion);
  assert.equal(ciCheck(at([w()], { 1: [j({ name: 'scope' })] }), A).conclusion, 'missing', 'a finished run without a check job fails');
  assert.equal(ciCheck(at([w({ head_sha: C })], { 1: [j()] }), A).state, 'pending', 'another head does not count');
  assert.equal(ciCheck(at([w()], { 1: [j({ head_sha: C })] }), A).state, 'FAIL', 'a job at another head does not count');
  assert.equal(ciCheck(at([w({ id: 1, conclusion: 'failure' }), w({ id: 2, created_at: '2026-11-12T02:00:00Z' })], { 1: [j({ conclusion: 'failure' })], 2: [j({ run_id: 2 })] }), A).state, 'PASS', 'the newest run decides');
  assert.equal(ciCheck(at([w({ id: 2, created_at: '2026-11-12T02:00:00Z' }), w()], { 1: [j()], 2: [j({ run_id: 2, conclusion: 'failure' })] }), A).state, 'FAIL');
  assert.throws(() => ciCheck(at([]), 'nope'));
  assert.equal(checkSource({ LA_LANH_CHECK_SOURCE: 'ci' }), 'ci');
  assert.equal(checkSource({}), 'local');
});

test('Codex #443 r1: a check job of another workflow never passes a head whose pr-check failed', () => {
  const calls = [];
  const gh = { json: args => {
    calls.push(args[1]);
    if (args[1].includes('/actions/workflows/')) return { workflow_runs: [
      { id: 9, path: '.github/workflows/other.yml', head_sha: A, status: 'completed', created_at: '2026-11-12T03:00:00Z' },
      { id: 1, path: '.github/workflows/pr-check.yml', head_sha: A, status: 'completed', created_at: '2026-11-12T01:00:00Z' },
    ] };
    if (args[1].includes('/actions/runs/1/')) return { jobs: [
      { name: 'check', run_id: 1, head_sha: A, status: 'completed', conclusion: 'failure' },
      { name: 'check', run_id: 9, head_sha: A, status: 'completed', conclusion: 'success' },
    ] };
    return { jobs: [{ name: 'check', run_id: 9, head_sha: A, status: 'completed', conclusion: 'success' }] };
  } };
  const result = ciCheck(gh, A);
  assert.equal(result.state, 'FAIL');
  assert.equal(result.conclusion, 'failure');
  assert.match(calls[0], /\/actions\/workflows\/pr-check\.yml\/runs\?head_sha=a{40}/, 'runs are looked up through the pr-check workflow file');
  assert.ok(!calls.some(c => c.includes('check-runs')), 'check names are never trusted on their own');
  assert.ok(!calls.some(c => c.includes('/runs/9/')), 'the other workflow is never read');
});

test('Codex #443 r1: CI mode keeps only the metadata preflight and never starts uv on PR files', () => {
  const never = () => { throw new Error('ruff/mypy must not run on the Mac in CI mode'); };
  const py = pr({ files: [{ path: 'apps/api/app/x.py', additions: 1, deletions: 0 }] });
  assert.equal(clonePreflight('ci', { spawn: never, exists: () => true })(py, '/clone', () => 60000).status, 'PASS');
  const bad = clonePreflight('ci', { spawn: never, exists: () => true })(pr({ body: 'no gates' }), '/clone', () => 60000);
  assert.equal(bad.status, 'FAIL', 'the body template is still checked locally');
  const ran = [];
  const local = clonePreflight('local', { spawn: (cmd, args) => { ran.push([cmd, ...args].join(' ')); return { status: 0 }; }, exists: () => true })(py, '/clone', () => 60000);
  assert.equal(local.status, 'PASS');
  assert.ok(ran.some(c => c.startsWith('uv run')), 'local mode still lints the changed Python files');
});

test('#306: a direct clone check with a failing body records it, routes to claude-fix and stops retrying', () => {
  const bad = pr({ number: 306, body: 'no gates here' });
  let fetched = 0;
  const gh = { ...fakeGh({ pr: bad }), pr: () => { fetched += 1; return bad; } };
  const never = () => { throw new Error('no clone, lock or pnpm before a body fix'); };
  const first = runCheckInClone(306, { gh, run: never, group: never, busy: () => null, spawn: never });
  assert.equal(first.status, 'preflight');
  assert.ok(first.reasons.includes('PR body thiếu mức rủi ro S/M/L'));
  const turn = turnsFor([bad]).find(t => t.number === 306);
  assert.equal(turn.turn, 'claude-fix', 'held until the body changes, not claude-check');
  assert.match(turn.reason, /^preflight: /);
  const again = runCheckInClone(306, { gh, run: never, group: never, busy: () => null, spawn: never, held: { quick: never } });
  assert.equal(again.held, true, 'the recorded failure answers the second call');
  const fixed = { ...bad, body: goodBody };
  assert.equal(turnsFor([fixed])[0].turn, 'claude-check', 'an edited body clears the hold');
  preflightMod.recordPreflight(306, A, { status: 'PASS' });
});

test('fix B: a later PR on the same file waits for the earlier one', () => {
  const f = (...paths) => paths.map(path => ({ path }));
  const first = pr({ number: 10, createdAt: '2026-11-01T00:00:00Z', files: f('scripts/a.mjs', 'docs/x.md') });
  const second = pr({ number: 11, createdAt: '2026-11-02T00:00:00Z', files: f('scripts/a.mjs') });
  const other = pr({ number: 12, createdAt: '2026-11-03T00:00:00Z', files: f('scripts/b.mjs') });
  const draft = pr({ number: 9, createdAt: '2026-10-01T00:00:00Z', isDraft: true, files: f('scripts/b.mjs') });
  const stacked = pr({ number: 8, createdAt: '2026-10-01T00:00:00Z', baseRefName: 'feat/base', files: f('docs/x.md') });
  const turns = Object.fromEntries(turnsFor([first, second, other, draft, stacked]).map(t => [t.number, t]));
  assert.equal(turns[10].turn, 'claude-check', 'the earliest PR goes first');
  assert.equal(turns[11].turn, 'hold');
  assert.equal(turns[11].reason, 'chờ PR #10 cùng file');
  assert.equal(turns[12].turn, 'claude-check', 'a draft or a PR stacked off integration holds nothing');
  assert.equal(fileBlocker(second, [second]), null);
});

test('fix C: the plan lists committed PRs with new copy or a clarity-ratchet change as "cần duyệt câu"', () => {
  assert.deepEqual(copyReview(['apps/api/app/domains/content/daily.py', 'apps/api/tests/content/test_daily.py', 'scripts/x.mjs']), { copy: ['apps/api/app/domains/content/daily.py'], ratchet: [] });
  assert.deepEqual(copyReview(['apps/api/scripts/content_clarity_exceptions.json']), { copy: [], ratchet: ['apps/api/scripts/content_clarity_exceptions.json'] });
  assert.equal(copyReview(['scripts/collab-plan.mjs']), null);
  // #229: reading content outside content/ also needs owner review.
  for (const f of ['apps/api/app/domains/tarot/action_copy.py', 'apps/api/app/domains/relationships/knowledge.py', 'apps/api/app/domains/readings/voice.py']) {
    assert.deepEqual(copyReview([f]), { copy: [f], ratchet: [] }, f);
  }
  assert.equal(copyReview(['apps/api/app/domains/relationships/service.py']), null);
  const turns = turnsFor([
    pr({ number: 31, createdAt: '2026-11-01T00:00:00Z', files: [{ path: 'apps/api/app/domains/content/daily.py' }] }),
    pr({ number: 32, createdAt: '2026-11-02T00:00:00Z', files: [{ path: 'apps/api/scripts/content_clarity_baseline.json' }] }),
    pr({ number: 33, createdAt: '2026-11-03T00:00:00Z', files: [{ path: 'scripts/x.mjs' }] }),
  ]);
  const body = renderPlan({ date: '2026-11-04', hour: 8, minute: 50 }, turns, { codexLeft: 10 });
  assert.match(body, /#31 \*\*cần duyệt câu\*\*: câu mới ở `apps\/api\/app\/domains\/content\/daily\.py`\./);
  assert.match(body, /#32 \*\*cần duyệt câu\*\*: clarity ratchet có thể tăng \(`content_clarity_baseline\.json`\)\./);
  assert.doesNotMatch(body, /#33 \*\*cần duyệt câu/);
  assert.doesNotThrow(() => trust.assertAgentBody(body));
  assert.doesNotMatch(renderPlan({ date: '2026-11-04', hour: 8, minute: 50 }, turnsFor([pr()]), { codexLeft: 10 }), /cần duyệt câu/);
});

test('fix E: one heavy job at a time — no new check while the lock is busy, at most checksPerTick', () => {
  const date = '2026-11-13';
  const open = Array.from({ length: 5 }, (_, i) => pr({ number: 40 + i, createdAt: `2026-11-0${i + 1}T00:00:00Z` }));
  let running = 0; let peak = 0;
  const checked = [];
  const check = n => { running++; peak = Math.max(peak, running); checked.push(n); running--; return { status: 'PASS' }; };
  tick({ gh: plannedGh(open, date), now: { date, hour: 11, minute: 5 }, merge: () => ({}), review: () => ({ status: 'posted' }), check });
  assert.equal(checked.length, checksPerTick);
  assert.equal(peak, 1, 'strictly serial');
  const busy = [];
  tick({ gh: plannedGh(open, date), now: { date, hour: 11, minute: 15 }, merge: () => ({}), review: () => ({ status: 'posted' }), heavyFree: () => false, check: n => { busy.push(n); return { status: 'PASS' }; } });
  assert.equal(busy.length, 1, 'a busy lock stops the drain after the scheduled check');
  const stopped = [];
  tick({ gh: plannedGh(open, date), now: { date, hour: 11, minute: 25 }, merge: () => ({}), review: () => ({ status: 'posted' }), check: n => { stopped.push(n); return { status: 'busy' }; } });
  assert.equal(stopped.length, 1, 'a refused or busy check ends the drain');
  let t = 0;
  const slow = [];
  tick({ gh: plannedGh(open, date), now: { date, hour: 11, minute: 35 }, nowMs: () => t, merge: () => ({}), review: () => ({ status: 'posted' }), check: n => { slow.push(n); t += 61 * 60000; return { status: 'PASS' }; } });
  assert.equal(slow.length, 1, 'no new check after 60 minutes, before the 90-minute tick lock expires');
  assert.equal(heavyJobFree(() => '1 pnpm check'), false);
  assert.equal(heavyJobFree(() => null), true);
});

test('review 228 P1: the budget is read again after the preflight, and lint is bounded by it', () => {
  let t = 0;
  const gh = { ...fakeGh({ pr: pr() }), comment: () => { throw new Error('nothing posted'); } };
  const run = (cmd, args) => args[0] === 'rev-parse' ? A : '';
  const seen = [];
  const result = runCheckInClone(7, { gh, run, nowMs: () => t, group: () => ({ status: 0 }), busy: () => null, terms: () => [],
    preflight: (p, dir, left) => { seen.push(left()); t += 200 * 60000; return { status: 'PASS', reasons: [] }; },
    spawn: () => { throw new Error('pnpm check must not start past the deadline'); } });
  assert.equal(result.status, 'refused');
  assert.ok(seen[0] > 0, 'the preflight gets the remaining budget');
  const timeouts = [];
  let left = 1000;
  preflightMod.lintProblems(['app/x.py'], { cwd: '/repo', exists: () => true, left: () => left, spawn: (c, a, o) => { timeouts.push(o.timeout); left = 0; return { status: 0 }; } });
  assert.deepEqual(timeouts, [1000], 'no lint step starts after the deadline');
});

test('review 228 P2: a fork or outside PR never holds an owner PR on a shared file', () => {
  const f = (...paths) => paths.map(path => ({ path }));
  const outside = pr({ number: 20, createdAt: '2026-11-01T00:00:00Z', author: { login: 'someone-else' }, files: f('scripts/a.mjs') });
  const fork = pr({ number: 21, createdAt: '2026-11-01T00:00:01Z', isCrossRepository: true, files: f('scripts/a.mjs') });
  const mine = pr({ number: 22, createdAt: '2026-11-02T00:00:00Z', files: f('scripts/a.mjs') });
  assert.equal(fileBlocker(mine, [outside, fork, mine]), null);
  assert.equal(turnsFor([outside, fork, mine]).find(t => t.number === 22).turn, 'claude-check');
});

test('fix B fix-forward: a PR that is itself on hold never holds another PR on a shared file', () => {
  const f = (...paths) => paths.map(path => ({ path }));
  const parked = pr({ number: 127, createdAt: '2026-10-20T00:00:00Z', labels: [{ name: 'needs-owner' }], files: f('app/privacy.py') });
  const dropped = pr({ number: 130, createdAt: '2026-10-21T00:00:00Z', files: f('app/privacy.py') });
  const privacy = pr({ number: 199, createdAt: '2026-11-03T00:00:00Z', files: f('app/privacy.py') });
  const all = [parked, dropped, privacy];
  assert.equal(fileBlocker(privacy, all, { dropped: [130] }), null);
  const turns = Object.fromEntries(turnsFor(all, { dropped: [130] }).map(t => [t.number, t]));
  assert.equal(turns[199].turn, 'claude-check', 'a needs-owner or dropped PR does not hold #199');
  assert.equal(fileBlocker(privacy, all), 130, 'a blocker that can move still holds');
  const feature = pr({ number: 120, title: 'feat: noi binh yen prototype', labels: [{ name: 'area:feature' }], createdAt: '2026-10-01T00:00:00Z', files: f('app/privacy.py') });
  const priv = pr({ number: 199, title: 'fix(privacy): erasure', labels: [{ name: 'area:privacy' }], createdAt: '2026-11-03T00:00:00Z', files: f('app/privacy.py') });
  assert.equal(fileBlocker(priv, [feature, priv]), null, 'a later group never holds an earlier group');
  assert.equal(fileBlocker(feature, [feature, priv]), 199, 'the earlier group goes first on a shared file');
});

test('review 228: a deleted Python file is not linted by default', () => {
  const calls = [];
  assert.deepEqual(preflightMod.lintProblems(['app/deleted_for_test_only.py'], { cwd: '/nonexistent-la-lanh', spawn: () => { calls.push(1); return { status: 1 }; } }), []);
  assert.equal(calls.length, 0);
});

test('#158/#159: top-up is computed from the queue left after this tick merges', () => {
  const date = '2026-11-15';
  const approved = [check(A), owner(`Review verdict: APPROVE @ ${A}`)];
  // Two agent PRs are merge-ready when the tick starts, so WIP is full before the merges.
  const open = [1, 2].map(number => pr({ number, headRefName: `agent/claude/q${number}`, comments: approved }));
  const merged = [];
  const merge = n => { merged.push(n); open.splice(open.findIndex(p => p.number === n), 1); return { status: 'merged' }; };
  tick({ gh: plannedGh(open, date), now: { date, hour: 15, minute: 5 }, merge, check: () => ({ status: 'FAIL' }), review: () => ({}) });
  assert.deepEqual(merged, [1, 2], 'both merge-ready PRs merged in this tick');
  const queue = JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  assert.equal(queue.buffer, 0, 'WIP counts the PRs still open after the merges');
  assert.equal(queue.topUp, true, 'the emptied WIP asks Claude for the next task in the same tick');
  assert.equal(queue.topUpCount, 1);
});

// ---- #253: buffer rule and flow samples on the scheduled path ----
test('#253: the persisted queue uses the WIP rule and the tick samples the flow metric', () => {
  const date = '2026-11-14';
  const one = [pr({ number: 1, headRefName: 'agent/claude/b1' })];
  tick({ gh: plannedGh(one, date), now: { date, hour: 15, minute: 5 }, merge: () => ({}), check: () => ({ status: 'FAIL' }), review: () => ({}) });
  const queue = JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  assert.equal(queue.topUp, true, 'one PR in review and nothing in progress');
  assert.equal(queue.topUpCount, 1);
  assert.equal(queue.buffer, 1);
  const flow = trust.readJson(join(trust.stateDir, 'beats', `flow-${trust.vnNow().date}.json`), null);
  assert.ok(flow?.samples >= 1, 'the scheduled tick records a flow sample without any CLI read');
});

test('#253: report turns leave out PRs dropped from today\'s plan', () => {
  const date = '2026-11-14';
  const now = { date, hour: 15, minute: 5 };
  const gh = plannedGh([pr({ number: 999 })], date);
  const base = gh.json;
  gh.json = args => { const out = base(args); return Array.isArray(out) ? out : { comments: [...out.comments, { authorAssociation: 'OWNER', createdAt: `${date}T02:00:00Z`, body: 'Bỏ #999' }] }; };
  const { turns } = planTurns(gh, now);
  assert.ok(!turns.some(t => t.number === 999 && ['claude-check', 'codex-review', 'merge'].includes(t.turn)), 'a dropped PR is not actionable');
});
