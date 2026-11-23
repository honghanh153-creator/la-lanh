import test from 'node:test';
import assert from 'node:assert/strict';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'antigravity-'));
const { agentMarker, cutoffMs, ownerLogin, vnNow } = await import('./collab-trust.mjs');
const { briefLimit, postSecond, secondBrief } = await import('./collab-second-review.mjs');
const { secondReviewProblem } = await import('./codex-fallback.mjs');
const { mergeGate } = await import('./collab-merge.mjs');
const { antigravityStep, appEnv, parseCritic, readAnswer, secondTargets, startConversation, statePath } = await import('./collab-antigravity.mjs');

const SHA = 'a'.repeat(40);
let id = 300;
const comment = (body, at) => ({ authorAssociation: 'OWNER', body, createdAt: at, url: `https://github.com/o/r/pull/901#issuecomment-${id++}` });
const fixedNote = comment(`Codex sửa thay Claude …\n\n${agentMarker} fallback pr=901 head=${SHA} -->`, '2026-11-22T08:00:00Z');
const pr = (state, head = SHA) => ({ number: 901, title: 'ops(loop): x', headRefOid: head, comments: state.comments, labels: [{ name: 'area:ops' }] });
const user = { type: 'CORTEX_STEP_TYPE_USER_INPUT', status: 'CORTEX_STEP_STATUS_DONE' };
const reply = (text, status = 'CORTEX_STEP_STATUS_DONE') => ({ type: 'CORTEX_STEP_TYPE_PLANNER_RESPONSE', status, plannerResponse: { response: text, modifiedResponse: text } });
function setup() {
  const home = mkdtempSync(join(tmpdir(), 'ag-home-'));
  const state = { comments: [fixedNote], started: [], answers: [] };
  const gh = {
    pr: () => pr(state),
    raw: () => 'diff --git a/scripts/a.mjs b/scripts/a.mjs\n+x',
    comment: (kind, n, body) => { const c = comment(body, `2026-11-22T09:0${state.comments.length}:00Z`); state.comments.push(c); return `${c.url}\n`; },
  };
  const run = (nowMs = 1000) => antigravityStep({ gh, prs: [pr(state)], home, nowMs, start: (brief, title) => { state.started.push({ brief, title }); return `conv-${state.started.length}`; }, steps: () => state.answers });
  return { home, state, gh, run };
}

test('L70: Antigravity reads the first "Kết luận" line only, and an answer that used a tool is not one', () => {
  assert.equal(parseCritic('Kết luận: APPROVE\nKhông có phát hiện'), 'APPROVE');
  assert.equal(parseCritic('\n**Kết luận: REQUEST_CHANGES**\nP1 a.mjs:3 sai'), 'REQUEST_CHANGES');
  assert.equal(parseCritic('Mình nghĩ là ổn.\nKết luận: APPROVE'), null, 'the verdict must be the first line');
  assert.equal(parseCritic('Kết luận: APPROVE hoặc REQUEST_CHANGES'), null);
  assert.deepEqual(readAnswer([user, reply('Kết luận: APPROVE')]), { done: true, text: 'Kết luận: APPROVE', tools: [] });
  assert.equal(readAnswer([user, reply('Kết', 'CORTEX_STEP_STATUS_GENERATING')]).done, false);
  assert.deepEqual(readAnswer([user, { type: 'CORTEX_STEP_TYPE_RUN_COMMAND', status: 'CORTEX_STEP_STATUS_DONE' }, reply('Kết luận: APPROVE')]).tools, ['CORTEX_STEP_TYPE_RUN_COMMAND']);
});

test('L70: one step per tick: start, wait, then post a signed second review that the gate counts', () => {
  const { home, state, run } = setup();
  assert.deepEqual(run(), { status: 'started', pr: 901 });
  assert.match(state.started[0].brief, /không dùng trình duyệt hay công cụ nào/);
  assert.match(state.started[0].brief, /```diff\ndiff --git a\/scripts\/a\.mjs/);
  assert.equal(state.started[0].title, 'Phản biện PR #901');
  state.answers = [user, reply('Kết', 'CORTEX_STEP_STATUS_GENERATING')];
  assert.deepEqual(run(2000), { status: 'waiting', pr: 901 });
  assert.equal(state.started.length, 1, 'no second conversation while one is open');
  state.answers = [user, reply('Kết luận: APPROVE\nKhông có phát hiện')];
  const posted = run(3000);
  assert.equal(posted.status, 'posted');
  assert.equal(posted.verdict, 'APPROVE');
  assert.match(state.comments.at(-1).body, /^Phản biện: APPROVE @ a{40}\nReviewer: Antigravity\nSecond-receipt: [0-9a-f]{32}\n/);
  assert.equal(secondReviewProblem(pr(state)), null, 'the signed Antigravity APPROVE lets the gate through');
  assert.deepEqual(JSON.parse(readFileSync(statePath(home), 'utf8')), {});
  assert.equal(run(4000), null, 'nothing waits any more');
});

test('L70: a REQUEST_CHANGES goes back to a fix; tool use, a bad format, a slow answer or a new head drop the job', () => {
  const asks = setup();
  asks.run();
  asks.state.answers = [user, reply('Kết luận: REQUEST_CHANGES\nP1 scripts/a.mjs:1 sai')];
  assert.equal(asks.run().verdict, 'REQUEST_CHANGES');
  assert.equal(secondReviewProblem(pr(asks.state)).turn, 'claude-fix');

  const tool = setup();
  tool.run();
  tool.state.answers = [user, { type: 'CORTEX_STEP_TYPE_RUN_COMMAND', status: 'CORTEX_STEP_STATUS_DONE' }, reply('Kết luận: APPROVE')];
  assert.match(tool.run().reason, /dùng công cụ \(CORTEX_STEP_TYPE_RUN_COMMAND\): không tính/);
  assert.equal(tool.state.comments.length, 1, 'nothing posted');
  assert.equal(secondReviewProblem(pr(tool.state)).turn, 'hold');

  const format = setup();
  format.run();
  format.state.answers = [user, reply('Ổn cả.')];
  assert.match(format.run().reason, /không theo mẫu/);

  const slow = setup();
  slow.run(0);
  slow.state.answers = [user];
  assert.equal(slow.run(19 * 60000).status, 'waiting');
  assert.match(slow.run(21 * 60000).reason, /quá 20 phút/);

  const moved = setup();
  moved.run();
  const out = antigravityStep({ gh: moved.gh, prs: [pr(moved.state, 'd'.repeat(40))], home: moved.home, start: () => 'conv-new', steps: () => assert.fail('the old conversation is not read') });
  assert.equal(out.status, 'started', 'the old head is dropped and the new head gets a new critic');
});

test('L71: Antigravity critiques every ready PR; Codex-fixed first; its REQUEST_CHANGES blocks any PR, its APPROVE is needed only after Codex', () => {
  const claudePr = (n, comments = []) => ({ number: n, title: 'ops: y', headRefOid: 'b'.repeat(40), comments, labels: [], author: { login: ownerLogin }, isCrossRepository: false, files: [{ path: 'scripts/b.mjs', additions: 2 }] });
  const fixed = { number: 901, title: 'ops(loop): x', headRefOid: SHA, comments: [fixedNote], labels: [] };
  const turns = [{ number: 902, turn: 'merge' }, { number: 903, turn: 'claude-fix' }, { number: 904, turn: 'codex-review' }, { number: 901, turn: 'hold' }];
  const prs = [claudePr(902), claudePr(903), claudePr(904), fixed];
  assert.deepEqual(secondTargets(prs, turns).map(p => p.number), [901, 902, 904], 'Codex-fixed first, then PRs at review or merge');
  assert.deepEqual(secondTargets(prs, []).map(p => p.number), [901], 'without turns only the held PR');
  assert.deepEqual(secondTargets([{ ...claudePr(902), isCrossRepository: true }, { ...claudePr(904), author: { login: 'someone' } }], turns), [], 'never a fork or a stranger');
  const home = mkdtempSync(join(tmpdir(), 'ag-every-'));
  const started = [];
  const out = antigravityStep({ gh: { raw: () => 'diff --git a/x b/x\n+y' }, prs: [claudePr(902)], turns, home, start: (b, t) => { started.push(t); return 'conv-1'; }, steps: () => [] });
  assert.deepEqual(out, { status: 'started', pr: 902 }, 'a PR Claude wrote gets a critic too');
  assert.equal(secondReviewProblem(claudePr(902)), null, 'its APPROVE is not required');
  const state = { comments: [] };
  const gh = { pr: () => claudePr(902, state.comments), comment: (k, n, body) => { const c = comment(body, '2026-11-22T10:00:00Z'); state.comments.push(c); return `${c.url}\n`; } };
  postSecond({ gh, number: 902, reviewer: 'Antigravity', verdict: 'REQUEST_CHANGES', head: 'b'.repeat(40), notes: 'Kết luận: REQUEST_CHANGES\nP1 scripts/b.mjs:1 sai' });
  assert.equal(secondReviewProblem(claudePr(902, state.comments)).turn, 'claude-fix');
  assert.ok(mergeGate(claudePr(902, state.comments), { disputes: {} }).reasons.some(r => /Antigravity\) REQUEST_CHANGES/.test(r)));
  assert.throws(() => postSecond({ gh, number: 902, reviewer: 'Claude', verdict: 'APPROVE', head: 'b'.repeat(40), notes: 'ok' }), /không chờ phản biện thứ hai/);
  assert.deepEqual(secondTargets([claudePr(902, state.comments)], turns), [], 'one critic per head');
});

test('the app token goes to the child env only, never into the command line', () => {
  const user = mkdtempSync(join(tmpdir(), 'ag-user-'));
  mkdirSync(join(user, '.gemini', 'antigravity', 'daemon'), { recursive: true });
  writeFileSync(join(user, '.gemini', 'antigravity', 'daemon', 'hub_1.json'), JSON.stringify({ httpPort: 4321, csrfToken: 'tok-secret-123' }));
  const env = appEnv(user);
  assert.deepEqual(env, { ANTIGRAVITY_LS_ADDRESS: '127.0.0.1:4321', ANTIGRAVITY_CSRF_TOKEN: 'tok-secret-123' });
  const bin = join(user, 'agentapi');
  const argsFile = join(user, 'args.txt');
  writeFileSync(bin, `#!/bin/sh\nprintf '%s\\n' "$@" > '${argsFile}'\n[ "$ANTIGRAVITY_CSRF_TOKEN" = tok-secret-123 ] || exit 3\necho '{"response":{"newConversation":{"conversationId":"0123abcd-0000-4000-8000-00000000abcd"}}}'\n`);
  chmodSync(bin, 0o755);
  assert.equal(startConversation('brief', 'Phản biện PR #901', { env, bin }), '0123abcd-0000-4000-8000-00000000abcd');
  const args = readFileSync(argsFile, 'utf8');
  assert.match(args, /^new-conversation\n--model=pro\n--title=Phản biện PR #901\nbrief\n$/);
  assert.doesNotMatch(args, /tok-secret/);
});

test('L70 (Codex r1 on #894): the production tick runs Antigravity, then the Codex fix, both bounded by one deadline; from 23:35 no fix starts', async () => {
  const { runTick } = await import('./collab-tick.mjs');
  const seen = [];
  const clockMs = () => cutoffMs(vnNow().date) - 60 * 60000;
  const opts = runTick({ raw: () => '', json: () => [] }, () => [], { run: given => given, gapNote: () => null, areaNote: () => null, clockMs,
    antigravity: a => { seen.push(['second', a.left(), a.turns]); return { status: 'started', pr: 901 }; },
    fallbackFix: a => { seen.push(['fix', a.left()]); return null; } });
  // Codex r1 on #899 (P1): Antigravity is the tick's `critic` hook (run before merges), the fix its `fallback` hook.
  assert.deepEqual(opts.critic({ turns: ['t'], prs: [{ number: 901 }] }), { status: 'started', pr: 901 });
  assert.equal(opts.fallback({ turns: [], prs: [{ number: 901 }] }), null);
  assert.deepEqual(seen.map(s => s[0]), ['second', 'fix'], 'the tick wires the Antigravity hook and the fix');
  assert.deepEqual(seen[0][2], ['t'], 'Antigravity gets the turns');
  assert.ok(seen.every(([, left]) => left === 60 * 60000 - 15000), 'one deadline: 23:59 minus 15 s');
  seen.length = 0;
  opts.fallback({ turns: [], prs: [], late: () => true });
  assert.deepEqual(seen, [], 'past 23:35: no Codex fix');
});

test('Codex r1 on #899 (P1): the merge gate holds a PR while Antigravity critiques its head, for at most 20 minutes', async () => {
  const { criticPending, statePath, answerLimitMs } = await import('./collab-antigravity.mjs');
  const home = mkdtempSync(join(tmpdir(), 'critic-'));
  const at = 1_000_000;
  const write = v => { mkdirSync(join(home, 'state'), { recursive: true }); writeFileSync(statePath(home), JSON.stringify(v)); };
  const p = { number: 901, headRefOid: SHA };
  write({ 901: { head: SHA, id: 'c1', at } });
  assert.match(criticPending(p, { home, nowMs: at + 60000 }), /Antigravity đang phản biện/);
  assert.equal(criticPending(p, { home, nowMs: at + answerLimitMs + 1 }), null, 'a stopped app holds nothing after 20 minutes');
  assert.equal(criticPending({ ...p, headRefOid: 'b'.repeat(40) }, { home, nowMs: at }), null, 'another head is not held');
  write({ 901: { head: SHA, tooLong: true, at } });
  assert.equal(criticPending(p, { home, nowMs: at }), null, 'a diff too long to send holds nothing');
  const held = mergeGate({ number: 901, headRefOid: SHA, labels: [], comments: [] }, { disputes: {}, critic: () => 'Antigravity đang phản biện head này' });
  assert.ok(held.reasons.includes('Antigravity đang phản biện head này'));
});

test('Codex r1 on #894 (P1): a diff longer than the brief is not sent to Antigravity, and no brief-only critic may APPROVE it', () => {
  const s = setup();
  s.gh.raw = () => `diff --git a/x b/x\n+${'y'.repeat(briefLimit)}`;
  const out = s.run();
  assert.equal(out.status, 'skipped');
  assert.match(out.reason, /chờ Claude/);
  assert.equal(s.state.started.length, 0);
  assert.equal(s.run(), null, 'remembered for this head');
  for (const reviewer of ['Antigravity', 'Gemini']) {
    assert.throws(() => postSecond({ gh: s.gh, number: 901, reviewer, verdict: 'APPROVE', head: SHA, notes: 'Kết luận: APPROVE' }), /không được APPROVE/);
  }
  assert.match(secondBrief(pr(s.state), 'x'.repeat(briefLimit + 1)), /bạn chưa đọc đủ, không được APPROVE/);
  assert.doesNotMatch(secondBrief(pr(s.state), 'x'.repeat(briefLimit + 1), { full: true }), /bị cắt/);
  postSecond({ gh: s.gh, number: 901, reviewer: 'Claude', verdict: 'APPROVE', head: SHA, notes: 'Kết luận: APPROVE\nĐã đọc đủ diff' });
  assert.equal(secondReviewProblem(pr(s.state)), null, 'Claude reads the full diff and may approve');
});
