import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-loop-'));
const trust = await import('./collab-trust.mjs');
const { prTurn, turnsFor, tick } = await import('./collab-turn.mjs');
const { planState, renderPlan } = await import('./collab-plan.mjs');
const review = await import('./codex-review.mjs');
const { mergeGate, runMerge } = await import('./collab-merge.mjs');
const { renderCheck } = await import('./collab-check.mjs');

const A = 'a'.repeat(40);
const B = 'b'.repeat(40);
const C = 'c'.repeat(40);
let clock = 0;
const owner = body => ({ authorAssociation: 'OWNER', createdAt: `2026-10-30T0${Math.floor(clock / 60)}:${String(clock++ % 60).padStart(2, '0')}:00Z`, body });
const outsider = body => ({ ...owner(body), authorAssociation: 'NONE' });
const check = (sha, status = 'PASS') => owner(renderCheck({ head: sha, status, exitCode: status === 'PASS' ? 0 : 1, seconds: 1, date: 'x' }));
const pr = (extra = {}) => ({ number: 7, title: 'feat(tarot): plain summary', state: 'OPEN', isDraft: false, baseRefName: 'collab/integration', headRefName: 'feat/x', headRefOid: A, mergeable: 'MERGEABLE', labels: [], createdAt: '2026-10-29T00:00:00Z', comments: [], body: 'PR body', ...extra });

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
});

test('queue order is content → privacy → feature → ops, oldest first', () => {
  const order = turnsFor([
    pr({ number: 1, title: 'docs(registry): r33' }),
    pr({ number: 2, title: 'feat(prototype): game lab 14' }),
    pr({ number: 3, title: 'feat(privacy): data export' }),
    pr({ number: 4, title: 'feat(tarot): pass 2', createdAt: '2026-10-29T02:00:00Z' }),
    pr({ number: 5, title: 'feat(radar): readable Hợp gu', createdAt: '2026-10-29T01:00:00Z' }),
    pr({ number: 6, title: 'anything', labels: [{ name: 'area:content' }], createdAt: '2026-10-30T00:00:00Z' }),
  ]).map(t => t.number);
  assert.deepEqual(order, [5, 4, 6, 3, 2, 1]);
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
  trust.writeJson(trust.dayStatePath(now.date), { codexRuns: 12 });
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
  assert.equal(tick(deps({ hour: 10, minute: 11 })).status, 'already-ran-this-hour');
  const queue = JSON.parse(readFileSync(join(trust.stateDir, 'claude-queue.json'), 'utf8'));
  assert.deepEqual(queue.items.map(i => [i.number, i.turn]), [[5, 'claude-check']]);
});
