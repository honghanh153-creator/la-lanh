import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { append, entry, override, read } from './collab-disagree.mjs';

test('experiment arm 1: a disagreement needs both positions, a PR and a known winner, and is kept in order', () => {
  const path = join(mkdtempSync(join(tmpdir(), 'disagree-')), 'd.jsonl');
  assert.deepEqual(read(path), []);
  const at = new Date('2026-11-14T03:00:00Z');
  append(entry({ pr: 480, claude: 'giữ 3 lần thử', codex: 'giữ lỗi tới khi phục hồi', winner: 'codex', at }), path);
  append(entry({ pr: 481, claude: 'a', codex: 'b', winner: 'owner', note: 'owner lật lại', at }), path);
  assert.deepEqual(read(path).map(e => [e.pr, e.winner, e.date]), [[480, 'codex', '2026-11-14'], [481, 'owner', '2026-11-14']]);
  assert.throws(() => entry({ pr: 'x', claude: 'a', codex: 'b', winner: 'codex' }), /PR number/);
  assert.deepEqual(entry({ task: 'L21', claude: 'a', codex: 'b', winner: 'codex', at }).task, 'L21', 'a plan disagreement before any PR');
  const first = read(path)[0];
  append(override({ of: first.at, winner: 'claude', note: 'owner chọn ý Claude', at }), path);
  assert.deepEqual(read(path).at(-1), { at: at.toISOString(), date: '2026-11-14', type: 'override', of: first.at, winner: 'claude', note: 'owner chọn ý Claude' });
  assert.deepEqual(read(path)[0], first, 'the original line is never edited');
  assert.throws(() => override({ of: first.at, winner: 'claude', note: '' }), /note/);
  assert.throws(() => entry({ pr: 1, claude: '', codex: 'b', winner: 'codex' }), /both positions/);
  assert.throws(() => entry({ pr: 1, claude: 'a', codex: 'b', winner: 'nobody' }), /winner/);
  writeFileSync(path, `${JSON.stringify({ pr: 1 })}\nnot json\n`, { flag: 'a' });
  assert.equal(read(path).length, 4, 'a broken line is skipped, the rest is kept');
});

// ---- L25: disputes that reach the owner ----
const { agentMarker, assertAgentBody } = await import('./collab-trust.mjs');
const L25 = await import('./collab-disagree.mjs');
const A = 'a'.repeat(40);
const B = 'b'.repeat(40);
// Vietnam wall clock (UTC+7) on a November 2026 day, as epoch milliseconds.
const vn = (day, hour, minute = 0) => Date.UTC(2026, 10, day, hour - 7, minute);
const isoAt = ms => new Date(ms).toISOString();

// One PR (or issue) on a fake GitHub; comments get the time of the shared test clock.
function world({ head = A, labels = [], number = 515 } = {}) {
  const w = { now: vn(14, 10), head, labels: [...labels], labelEvents: [], comments: [], posts: [], notes: [], failComment: false, failNotify: false, failEvents: false, state: 'OPEN' };
  const view = () => ({ number, state: w.state, headRefOid: w.head, labels: w.labels.map(name => ({ name })), comments: structuredClone(w.comments) });
  w.gh = {
    pr: () => view(),
    json: () => { const v = view(); delete v.headRefOid; return v; },
    raw: args => {
      // GitHub's issue events for needs-owner, one JSON object per line as the --jq filter prints them.
      if (args[0] === 'api') {
        if (w.failEvents) throw new Error('api down');
        return w.labelEvents.map(e => `${JSON.stringify(e)}\n`).join('');
      }
      const i = args.indexOf('--add-label');
      if (i >= 0 && !w.labels.includes(args[i + 1])) { w.labels.push(args[i + 1]); w.labelEvents.push({ event: 'labeled', at: isoAt(w.now) }); }
      const j = args.indexOf('--remove-label');
      if (j >= 0 && w.labels.includes(args[j + 1])) { w.labels = w.labels.filter(l => l !== args[j + 1]); w.labelEvents.push({ event: 'unlabeled', at: isoAt(w.now) }); }
      return '';
    },
    comment: (kind, n, body) => {
      if (w.failComment) throw new Error('network down');
      assertAgentBody(body);
      w.posts.push({ kind, n, body });
      w.comments.push({ authorAssociation: 'OWNER', createdAt: isoAt(w.now), body });
    },
  };
  w.notify = text => { if (w.failNotify) throw new Error('osascript failed'); w.notes.push(text); };
  w.ownerSays = (body, at = w.now) => w.comments.push({ authorAssociation: 'OWNER', createdAt: isoAt(at), body });
  const dir = mkdtempSync(join(tmpdir(), 'dispute-'));
  w.path = join(dir, 'disputes.jsonl');
  w.logFile = join(dir, 'disagreements.jsonl');
  w.open = (extra = {}) => {
    const first = L25.openRound({ pr: number, round: 1, claude: 'Claude vòng 1', codex: 'Codex vòng 1', head: w.head, nowMs: w.now, path: w.path, ...extra });
    L25.openRound({ id: first.id, round: 2, claude: 'Claude vòng 2', codex: 'Codex vòng 2', codexConclusion: 'Giữ ba lần thử rồi báo lỗi', head: w.head, nowMs: w.now, path: w.path });
    return first.id;
  };
  w.escalate = id => L25.escalate({ id, gh: w.gh, notify: w.notify, nowMs: w.now, path: w.path });
  w.settle = () => L25.settleDisputes({ gh: w.gh, notify: w.notify, nowMs: w.now, path: w.path, logFile: w.logFile }).done;
  w.state_ = id => L25.disputes(read(w.path)).get(id);
  w.questions = () => w.posts.filter(p => p.body.includes(`${agentMarker} disagree id=`));
  return w;
}

test('a dispute after two rounds asks the owner once; 30 daytime minutes without a reply follow Codex and log "chốt do hết giờ"', () => {
  const w = world();
  const id = w.open();
  assert.throws(() => L25.openRound({ id, round: 3, claude: 'a', codex: 'b', head: A, path: w.path }), /at most two rounds/);
  assert.equal(L25.disputeView(read(w.path))[515].hold, `bất đồng ${id}: chưa hỏi owner`, 'held as soon as round 2 still disagrees');
  assert.equal(w.escalate(id).clock, 'started');
  assert.deepEqual(w.labels, ['needs-owner']);
  assert.equal(w.questions().length, 1);
  assert.match(w.questions()[0].body, /`Theo Claude` hoặc `Theo Codex`/);
  assert.equal(w.notes.length, 1, 'one desktop notification');
  assert.equal(w.escalate(id).status, 'already-asked', 'the same question is not asked twice');
  w.now = vn(14, 10, 29);
  assert.equal(w.settle()[0].status, 'waiting');
  w.now = vn(14, 10, 30);
  assert.deepEqual(w.settle()[0], { id, status: 'decided', decidedBy: 'timeout', chosen: 'codex' });
  const decided = w.state_(id).decided;
  assert.equal(decided.note, 'chốt do hết giờ');
  assert.equal(decided.conclusion, 'Giữ ba lần thử rồi báo lỗi', "Codex's specific conclusion");
  const line = read(w.logFile);
  assert.equal(line.length, 1, 'one M8 entry');
  assert.deepEqual([line[0].pr, line[0].winner, line[0].decidedBy, line[0].chosen, line[0].note, line[0].dispute], [515, 'codex', 'timeout', 'codex', 'chốt do hết giờ', id]);
  assert.match(w.posts.at(-1).body, /chốt do hết giờ[\s\S]*Author check và review mới/);
  assert.deepEqual(w.labels, [], 'the label the escalation added is removed');
  assert.equal(w.questions().length, 1, 'asked once');
  assert.deepEqual(w.settle(), [], 'a closed dispute costs nothing');
});

test('L25: the owner replies before 30 minutes; the reply decides, not the clock', () => {
  const w = world();
  const id = w.open();
  w.escalate(id);
  w.now = vn(14, 10, 12);
  w.ownerSays('theo claude nhé');
  assert.deepEqual(w.settle()[0], { id, status: 'decided', decidedBy: 'owner', chosen: 'claude' });
  assert.equal(w.state_(id).decided.conclusion, 'Claude vòng 2');
  assert.equal(read(w.logFile)[0].winner, 'claude');
  assert.match(w.posts.at(-1).body, /owner chọn theo Claude/);
});

test('L25: sent at 23:00 → held → resent at 08:00 → timeout at 08:30', () => {
  const w = world();
  w.now = vn(14, 23);
  const id = w.open();
  assert.equal(w.escalate(id).clock, 'held-until-morning');
  w.now = vn(15, 7, 50);
  assert.equal(w.settle()[0].status, 'held-until-morning');
  w.now = vn(15, 8, 0);
  assert.equal(w.settle()[0].clock, 'started');
  assert.equal(w.questions().length, 2, 'asked again in the morning');
  assert.match(w.questions()[1].body, /hỏi lần 2/);
  assert.equal(w.notes.length, 2);
  w.now = vn(15, 8, 29);
  assert.equal(w.settle()[0].status, 'waiting');
  w.now = vn(15, 8, 30);
  assert.equal(w.settle()[0].decidedBy, 'timeout');
  // 21:45 + 30 minutes does not fit before 22:00 either.
  assert.equal(L25.clockFits(vn(14, 21, 30)), true);
  assert.equal(L25.clockFits(vn(14, 21, 31)), false);
  assert.equal(L25.nextMorning(vn(14, 21, 45)), vn(15, 8));
  assert.equal(L25.nextMorning(vn(15, 7, 59)), vn(15, 8));
});

test('L25: a reply arriving overnight is read in the morning before any resend', () => {
  const w = world();
  w.now = vn(14, 23);
  const id = w.open();
  w.escalate(id);
  w.ownerSays('Theo Codex', vn(15, 6));
  w.now = vn(15, 8, 3);
  assert.deepEqual(w.settle()[0], { id, status: 'decided', decidedBy: 'owner', chosen: 'codex' });
  assert.equal(w.questions().length, 1, 'no second question');
});

test('L25: a crash after sending does not send a second question', () => {
  const w = world();
  const id = w.open();
  // The first run posted the comment and died before writing "sent".
  append({ at: isoAt(w.now), type: 'escalate', id }, w.path);
  w.comments.push({ authorAssociation: 'OWNER', createdAt: isoAt(w.now), body: `câu hỏi\n${L25.questionMarker(id, 1, true, undefined, A)}` });
  w.labels.push('needs-owner');
  w.labelEvents.push({ event: 'labeled', at: isoAt(w.now) });
  append({ at: isoAt(w.now), type: 'label-added', id, target: 'pr:515' }, w.path);
  w.now = vn(14, 10, 10);
  assert.equal(w.settle()[0].status, 'sent');
  assert.equal(w.questions().length, 0, 'nothing new was posted');
  const q = w.state_(id).questions;
  assert.equal(q.length, 1);
  assert.equal(q[0].recovered, true);
  assert.equal(w.escalate(id).status, 'already-asked');
  w.now = vn(14, 10, 40);
  assert.equal(w.settle()[0].decidedBy, 'timeout');
  assert.deepEqual(w.labels, []);
});

test('L25: a failed send does not start the clock', () => {
  const w = world();
  const id = w.open();
  w.failComment = true;
  assert.throws(() => w.escalate(id), /network down/);
  assert.equal(w.state_(id).questions.length, 0);
  w.now = vn(14, 11);
  assert.equal(w.settle()[0].status, 'error', 'the retry fails too');
  w.failComment = false;
  w.now = vn(14, 12);
  assert.equal(w.settle()[0].clock, 'started', 'the retry sends');
  assert.equal(w.state_(id).questions[0].clockFrom, isoAt(vn(14, 12)));
  w.now = vn(14, 12, 20);
  assert.equal(w.settle()[0].status, 'waiting', 'counted from the successful send, not from the first try');
  // A failed notification after the comment: the comment is not repeated, the clock waits for it.
  const w2 = world();
  const id2 = w2.open();
  w2.failNotify = true;
  assert.equal(w2.escalate(id2).status, 'sent-unnotified');
  w2.failNotify = false;
  w2.now = vn(14, 11);
  assert.equal(w2.settle()[0].clock, 'started');
  assert.equal(w2.questions().length, 1);
  w2.now = vn(14, 11, 29);
  assert.equal(w2.settle()[0].status, 'waiting');
});

test('L25: an owner-only dispute never times out and is not asked again', () => {
  const w = world();
  const id = w.open({ group: 'privacy' });
  assert.equal(w.state_(id).ownerOnly, true);
  assert.equal(w.escalate(id).clock, 'owner-only');
  assert.match(w.questions()[0].body, /chỉ owner quyết/);
  for (const at of [vn(14, 11), vn(14, 23), vn(15, 8), vn(15, 9)]) { w.now = at; assert.equal(w.settle()[0].status, 'waiting-owner'); }
  assert.equal(w.questions().length, 1);
  w.ownerSays('Theo Claude');
  assert.equal(w.settle()[0].decidedBy, 'owner');
  const task = L25.openRound({ task: 'L05', round: 1, claude: 'a', codex: 'b', path: w.path });
  assert.equal(task.ownerOnly, true, 'L05 is owner-only');
});

test('L25: an agent comment saying "Theo Codex" is not the owner', () => {
  const w = world();
  const id = w.open();
  w.escalate(id);
  w.now = vn(14, 10, 5);
  w.ownerSays(`Theo Codex\n${agentMarker} handoff -->`);
  w.comments.push({ authorAssociation: 'NONE', createdAt: isoAt(w.now), body: 'Theo Codex' });
  assert.equal(w.settle()[0].status, 'waiting');
  assert.equal(L25.parseDisputeReply('Theo Codex nhé').chosen, 'codex');
  assert.equal(L25.parseDisputeReply('Tôi nghĩ theo Codex'), null);
});

test('L25: a reply to an older question does not count', () => {
  const w = world();
  const id = w.open();
  w.escalate(id);
  w.now = vn(14, 10, 5);
  w.ownerSays('Theo Claude');
  // Before any tick reads it, a new argument is recorded and the owner is asked again.
  w.now = vn(14, 10, 6);
  L25.openRound({ id, round: 2, claude: 'Claude bằng chứng mới', codex: 'Codex giữ ý', head: A, nowMs: w.now, path: w.path });
  assert.equal(w.escalate(id).clock, 'started');
  w.now = vn(14, 10, 20);
  assert.equal(w.settle()[0].status, 'waiting', 'the reply came before the current question');
  w.now = vn(14, 10, 36);
  assert.equal(w.settle()[0].decidedBy, 'timeout');
});

test('L25: the head changed → no auto decision; a new head may be asked again', () => {
  const w = world();
  const id = w.open();
  w.escalate(id);
  w.head = B;
  w.now = vn(14, 11);
  assert.equal(w.settle()[0].status, 'stale');
  w.now = vn(14, 12);
  assert.equal(w.settle()[0].status, 'stale', 'no timeout on a stale question');
  assert.match(L25.disputeView(read(w.path))[515].hold, /head đổi/);
  assert.equal(w.escalate(id).clock, 'started', 'a new head is a substantive change');
  assert.equal(w.state_(id).questions[1].head, B);
  L25.withdraw({ id, note: 'Claude sửa theo Codex trên head mới', nowMs: w.now, path: w.path });
  assert.equal(w.settle()[0].status, 'withdrawn');
  assert.equal(L25.disputeView(read(w.path))[515].hold, null);
  assert.deepEqual(read(w.logFile), [], 'a withdrawn dispute is not a decision');
});

test('L25: two disputes on one PR are tracked independently; needs-owner stays while another owner reason waits', () => {
  const w = world();
  const one = w.open();
  const two = w.open();
  assert.deepEqual([one, two], ['pr515-1', 'pr515-2']);
  w.escalate(one);
  w.now = vn(14, 10, 10);
  w.escalate(two);
  w.now = vn(14, 10, 15);
  w.ownerSays('Theo Claude');
  assert.deepEqual(w.settle().map(r => r.status), ['waiting', 'waiting'], 'a reply without a code is ambiguous with two questions open');
  w.ownerSays(`Theo Claude ${two}`);
  assert.deepEqual(w.settle().map(r => [r.id, r.status, r.chosen]), [[one, 'waiting', undefined], [two, 'decided', 'claude']]);
  assert.deepEqual(w.labels, ['needs-owner'], 'the other dispute still waits on the owner');
  w.now = vn(14, 10, 31);
  assert.deepEqual(w.settle().map(r => [r.id, r.decidedBy]), [[one, 'timeout']]);
  assert.deepEqual(w.labels, [], 'removed once no owner question is left');
  // A label that was already there belongs to another reason and is never removed.
  const w2 = world({ labels: ['needs-owner'] });
  const id = w2.open();
  w2.escalate(id);
  assert.doesNotMatch(w2.questions()[0].body, /label=added/);
  w2.now = vn(14, 10, 30);
  w2.settle();
  assert.deepEqual(w2.labels, ['needs-owner']);
  // An automatic REQUEST_CHANGES after our label also keeps it (codex-review stops for the owner).
  const w3 = world();
  const id3 = w3.open();
  w3.escalate(id3);
  assert.match(w3.questions()[0].body, /label=added/);
  w3.now = vn(14, 10, 5);
  w3.ownerSays(`Review verdict: REQUEST_CHANGES @ ${A}\n${agentMarker} codex-auto-review sha=${A} p2=0 -->`);
  w3.now = vn(14, 10, 30);
  w3.settle();
  assert.deepEqual(w3.labels, ['needs-owner']);
});

test('L25: full argument text is kept beyond 600 characters; the comment shows a short version', () => {
  const w = world();
  const long = `${'lý lẽ dài '.repeat(120)}\nhết.`;
  assert.ok(long.length > 600);
  const first = L25.openRound({ pr: 515, round: 1, claude: long, codex: long, head: A, nowMs: w.now, path: w.path });
  L25.openRound({ id: first.id, round: 2, claude: long, codex: long, head: A, nowMs: w.now, path: w.path });
  assert.equal(read(w.path)[1].claude, long);
  w.escalate(first.id);
  assert.match(w.questions()[0].body, /\[\.\.\.truncated\][\s\S]*disputes\.jsonl, mã pr515-1/);
  w.now = vn(14, 10, 30);
  w.settle();
  assert.equal(read(w.logFile)[0].claude, long, 'the M8 entry keeps it too');
  assert.equal(entry({ pr: 1, claude: long, codex: 'b', winner: 'codex' }).claude, long);
  assert.throws(() => entry({ pr: 1, claude: 'x'.repeat(L25.maxText + 1), codex: 'b', winner: 'codex' }), /nothing is cut/);
});

test('L25: a task dispute asks on its issue and escalation needs round 2', () => {
  const w = world({ number: 600, head: null });
  const r1 = L25.openRound({ task: 'L21', round: 1, claude: 'a', codex: 'b', path: w.path, nowMs: w.now });
  assert.throws(() => w.escalate(r1.id), /after round 2/);
  L25.openRound({ id: r1.id, round: 2, claude: 'a2', codex: 'b2', path: w.path, nowMs: w.now });
  assert.throws(() => w.escalate(r1.id), /--issue/);
  L25.openRound({ id: r1.id, round: 2, issue: 600, claude: 'a2', codex: 'b3', path: w.path, nowMs: w.now });
  assert.equal(w.escalate(r1.id).clock, 'started');
  assert.equal(w.questions()[0].kind, 'issue');
  w.now = vn(14, 10, 30);
  assert.equal(w.settle()[0].decidedBy, 'timeout');
  assert.equal(read(w.logFile)[0].task, 'L21');
});

test('L25: a round recorded after the question supersedes it: no timeout on the old clock, no reply to it decides, a fresh ask works', () => {
  // Without any reply: the old question's 30 minutes pass after the change and decide nothing.
  const w0 = world();
  const id0 = w0.open();
  w0.escalate(id0);
  w0.now = vn(14, 10, 29);
  L25.openRound({ id: id0, round: 2, claude: 'Claude B', codex: 'Codex B', head: A, nowMs: w0.now, path: w0.path });
  w0.now = vn(14, 10, 30);
  assert.deepEqual(w0.settle()[0], { id: id0, status: 'superseded' });
  assert.equal(w0.state_(id0).decided, null);
  const w = world();
  const id = w.open();
  assert.equal(w.escalate(id).clock, 'started');
  w.now = vn(14, 10, 20);
  w.ownerSays('Theo Claude');
  // Before any tick reads the reply, a changed round 2 is recorded, then the 30 minutes pass.
  w.now = vn(14, 10, 29);
  L25.openRound({ id, round: 2, claude: 'Claude đề xuất B', codex: 'Codex đề xuất B', codexConclusion: 'Làm theo B', head: A, nowMs: w.now, path: w.path });
  w.now = vn(14, 10, 30);
  assert.deepEqual(w.settle()[0], { id, status: 'superseded' }, 'no timeout on the old question');
  w.now = vn(14, 11, 30);
  assert.equal(w.settle()[0].status, 'superseded', 'the old clock never decides the new proposal');
  assert.equal(w.state_(id).decided, null, 'the reply to the old question decides nothing');
  assert.match(L25.disputeView(read(w.path))[515].hold, /lý lẽ đổi/);
  assert.deepEqual(w.labels, ['needs-owner'], 'still waiting on the owner');
  // A fresh question shows the new round and starts its own clock.
  assert.equal(w.escalate(id).clock, 'started');
  assert.equal(w.questions().length, 2);
  assert.match(w.questions()[1].body, /Làm theo B[\s\S]*q=2 r=3/);
  w.now = vn(14, 11, 59);
  assert.equal(w.settle()[0].status, 'waiting', 'the reply before the fresh question does not count');
  w.now = vn(14, 12, 0);
  assert.equal(w.settle()[0].decidedBy, 'timeout');
  assert.equal(w.state_(id).decided.conclusion, 'Làm theo B');
  assert.equal(read(w.logFile)[0].claude, 'Claude đề xuất B');
});

test('L25: a decision uses the round that was sent, also after a crash between the post and the record', () => {
  const w = world();
  const id = w.open();
  // The first run posted question 1 showing round 2 (r=2) and died before writing "sent".
  append({ at: isoAt(w.now), type: 'escalate', id }, w.path);
  w.comments.push({ authorAssociation: 'OWNER', createdAt: isoAt(w.now), body: `câu hỏi\n${L25.questionMarker(id, 1, false, 2, A)}` });
  // A changed round is recorded before the recovery.
  L25.openRound({ id, round: 2, claude: 'Claude đề xuất B', codex: 'Codex đề xuất B', head: A, nowMs: w.now, path: w.path });
  w.now = vn(14, 10, 5);
  assert.equal(w.settle()[0].status, 'sent');
  assert.equal(w.state_(id).questions[0].rounds, 2, 'the recovered question is about the round it showed');
  w.now = vn(14, 10, 10);
  w.ownerSays('Theo Codex');
  assert.equal(w.settle()[0].status, 'superseded', 'a reply to proposal A does not pick proposal B');
  assert.equal(w.state_(id).decided, null);
  // Without a newer round, an owner reply decides with exactly the sent snapshot.
  const w2 = world();
  const id2 = w2.open();
  w2.escalate(id2);
  w2.now = vn(14, 10, 3);
  w2.ownerSays('Theo Codex');
  assert.equal(w2.settle()[0].chosen, 'codex');
  assert.equal(w2.state_(id2).decided.rounds, 2);
  assert.equal(w2.state_(id2).decided.conclusion, 'Giữ ba lần thử rồi báo lỗi');
});

test('L25: a timeout removes needs-owner only when the dispute added it and nothing touched the hold since', () => {
  // Clean case: only the dispute's own comments and a bare owner reply to another question.
  const clean = world();
  const id = clean.open();
  clean.escalate(id);
  clean.now = vn(14, 10, 30);
  clean.settle();
  assert.deepEqual(clean.labels, [], 'the label the escalation added is removed');
  const keeps = (touch, why) => {
    const w = world();
    const d = w.open();
    w.escalate(d);
    w.now = vn(14, 10, 10);
    touch(w);
    w.now = vn(14, 10, 30);
    const posts = w.posts.length;
    assert.equal(w.settle()[0].status, 'decided', why);
    assert.deepEqual(w.labels, ['needs-owner'], why);
    assert.equal(w.posts.length, posts + 1, `${why}: only the decision is posted, nothing about the label`);
    assert.ok(!read(w.path).some(e => e.type === 'label-removed'), why);
  };
  keeps(w => w.ownerSays('Giữ needs-owner: lời UI ở màn Hợp gu chưa được duyệt.'), 'an owner comment after the escalation');
  keeps(w => w.ownerSays('Theo Codex\nNhưng lời UI chưa duyệt, đừng merge.'), 'a reply that says more than the choice');
  keeps(w => w.ownerSays(`Review verdict: REQUEST_CHANGES @ ${A}\n${agentMarker} codex-auto-review sha=${A} p2=0 -->`), 'codex-review stopped for the owner');
  keeps(w => w.ownerSays(`Bàn giao: chờ owner duyệt copy, giữ needs-owner.\n${agentMarker} handoff -->`), 'an agent comment about needs-owner');
  keeps(w => { w.labels = []; w.labelEvents.push({ event: 'unlabeled', at: isoAt(w.now) }); w.labels.push('needs-owner'); w.labelEvents.push({ event: 'labeled', at: isoAt(w.now) }); }, 'the owner removed and re-added the label');
  keeps(w => { w.failEvents = true; }, 'the label history cannot be read');
});

test('L25: a reply names any id that --open accepts, and a malformed id never counts', () => {
  assert.deepEqual(L25.parseDisputeReply('Theo Claude privacy-review-1'), { chosen: 'claude', id: 'privacy-review-1' });
  assert.deepEqual(L25.parseDisputeReply('`Theo Codex L21.a-12`.'), { chosen: 'codex', id: 'l21.a-12' });
  assert.deepEqual(L25.parseDisputeReply('Theo Codex, pr515-2 nhé'), { chosen: 'codex', id: 'pr515-2' });
  assert.deepEqual(L25.parseDisputeReply('Theo Codex nhé'), { chosen: 'codex', id: null });
  assert.equal(L25.parseDisputeReply('Theo Codex pr515').invalid, 'pr515');
  assert.throws(() => L25.openRound({ id: 'privacy', pr: 515, round: 1, claude: 'a', codex: 'b', head: A, path: join(mkdtempSync(join(tmpdir(), 'id-')), 'd.jsonl') }), /--id must/);
  // Two questions on one issue, both with hyphenated generated ids.
  const w = world({ number: 600, head: null });
  const ids = [1, 2].map(() => {
    const r1 = L25.openRound({ task: 'privacy-review', issue: 600, round: 1, claude: 'a', codex: 'b', path: w.path, nowMs: w.now });
    L25.openRound({ id: r1.id, round: 2, claude: 'a2', codex: 'b2', path: w.path, nowMs: w.now });
    w.escalate(r1.id);
    return r1.id;
  });
  assert.deepEqual(ids, ['privacy-review-1', 'privacy-review-2']);
  w.now = vn(14, 10, 5);
  w.ownerSays('Theo Claude privacy-review-2');
  assert.deepEqual(w.settle().map(r => [r.id, r.status, r.chosen]), [[ids[0], 'waiting', undefined], [ids[1], 'decided', 'claude']]);
  // A malformed id is refused, not read as a reply to the one question left.
  w.now = vn(14, 10, 10);
  w.ownerSays('Theo Codex privacy-review');
  assert.equal(w.settle()[0].status, 'waiting');
  assert.equal(w.state_(ids[0]).decided, null);
});

test('L25: a one-line reply that also holds the PR decides but keeps needs-owner; only an exact bare reply frees it', () => {
  const run = (body, number = 515) => {
    const w = world({ number });
    const id = w.open();
    w.escalate(id);
    assert.deepEqual(w.labels, ['needs-owner']);
    w.now = vn(14, 10, 10);
    w.ownerSays(body);
    const r = w.settle()[0];
    return { w, r, removed: read(w.path).some(e => e.type === 'label-removed') };
  };
  // Codex 15.11, verbatim: picks Codex and asks for an independent hold on the same line.
  const held = run('Theo Codex, nhưng đừng merge vì chưa duyệt lời UI.');
  assert.deepEqual([held.r.status, held.r.decidedBy, held.r.chosen], ['decided', 'owner', 'codex']);
  assert.deepEqual(held.w.labels, ['needs-owner'], 'the independent hold keeps the label');
  assert.equal(held.removed, false, 'nothing removes the label');
  // Extra words fail closed: the choice counts, the label stays.
  const nhe = run('Theo Codex nhé');
  assert.deepEqual([nhe.r.status, nhe.r.chosen], ['decided', 'codex']);
  assert.deepEqual(nhe.w.labels, ['needs-owner']);
  assert.equal(nhe.removed, false);
  // An exact bare reply, with or without its id and a final '.', still frees the label it added.
  for (const [body, number] of [['Theo Codex', 515], ['  theo   codex  ', 515], ['Theo Codex pr520-1.', 520], ['Theo Claude!', 515]]) {
    const bare = run(body, number);
    assert.equal(bare.r.status, 'decided', body);
    assert.deepEqual(bare.w.labels, [], `${body}: the label the escalation added is removed`);
    assert.equal(bare.removed, true, body);
  }
});

test('L25: a crash recovery keeps the head the question was asked at; a moved or unknown head is stale, never timed out', () => {
  const crash = marker => {
    const w = world();
    const id = w.open();
    // The first run posted question 1 at head A and died before writing "sent"; then B was pushed.
    append({ at: isoAt(w.now), type: 'escalate', id }, w.path);
    w.comments.push({ authorAssociation: 'OWNER', createdAt: isoAt(w.now), body: `câu hỏi\n${marker(id)}` });
    w.labels.push('needs-owner');
    w.labelEvents.push({ event: 'labeled', at: isoAt(w.now) });
    append({ at: isoAt(w.now), type: 'label-added', id, target: 'pr:515' }, w.path);
    return { w, id };
  };
  const { w, id } = crash(d => L25.questionMarker(d, 1, true, 2, A));
  w.head = B;
  w.now = vn(14, 10, 5);
  assert.equal(w.settle()[0].status, 'stale');
  assert.equal(w.questions().length, 0, 'nothing new was posted');
  assert.equal(w.notes.length, 0, 'the owner is not told about a stale question');
  const q = w.state_(id).questions;
  assert.deepEqual([q.length, q[0].head, q[0].recovered], [1, A, true], 'the question head is A, not B');
  w.now = vn(14, 11);
  assert.equal(w.settle()[0].status, 'stale', 'no timeout decision');
  assert.equal(w.state_(id).decided, null);
  assert.deepEqual(read(w.logFile), []);
  assert.match(L25.disputeView(read(w.path))[515].hold, /head đổi/);
  assert.equal(w.escalate(id).clock, 'started', 'the new head may be asked');
  assert.equal(w.state_(id).questions[1].head, B);
  // The marker a question carries names its head.
  assert.match(w.questions()[0].body, new RegExp(`q=2 r=2 h=${B}`));
  // A marker without h= (or a malformed one) recovers as stale even when the head did not move.
  for (const marker of [d => L25.questionMarker(d, 1, true, 2), d => L25.questionMarker(d, 1, true, 2, 'not-a-sha')]) {
    const old = crash(marker);
    old.w.now = vn(14, 10, 5);
    assert.equal(old.w.settle()[0].status, 'stale');
    assert.equal(old.w.state_(old.id).questions[0].head, null);
    old.w.now = vn(14, 11);
    assert.equal(old.w.settle()[0].status, 'stale', 'fail closed: no timeout');
    assert.equal(old.w.state_(old.id).decided, null);
  }
});
