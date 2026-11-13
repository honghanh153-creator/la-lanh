import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-status-'));
const trust = await import('./collab-trust.mjs');
const { boardMarker, ownerNotes, plainTitle, postOwnerNotes, renderBoard, sentNoteKeys, upsertBoard } = await import('./collab-status.mjs');
const { openOpsAlert, opsAlert, resolveOpsAlert, tick } = await import('./collab-turn.mjs');
const { renderCheck } = await import('./collab-check.mjs');

const A = 'a'.repeat(40);
// The live tip of collab/integration in every fixture (P1-A).
const BASE = 'e'.repeat(40);
const now = { date: '2026-11-01', hour: 14, minute: 5 };
const own = { author: { login: 'honghanh153-creator' }, isCrossRepository: false };
const pr = extra => ({ number: 7, title: 'feat(tarot): x', state: 'OPEN', isDraft: false, baseRefName: 'collab/integration', headRefName: 'b', headRefOid: A, baseTipOid: BASE, labels: [], createdAt: '2026-10-30T00:00:00Z', comments: [], ...own, ...extra });

test('the board says the state, when it was updated and what waits on the owner', () => {
  const body = renderBoard({ now, status: 'running', doing: 'author check #7', expectMinutes: 90, area: 'content', codexRuns: 3,
    turns: [{ number: 7, area: 'content', turn: 'claude-check', reason: 'chưa có Author check @ head' },
      { number: 139, area: 'content', turn: 'hold', reason: 'needs-owner' }] });
  assert.match(body, /ĐANG CHẠY\*\* — author check #7/);
  assert.match(body, /Cập nhật lúc \*\*14:05 2026-11-01\*\*/);
  assert.doesNotMatch(body, /cũ hơn 20 phút/, 'running work names its own deadline instead');
  const long = renderBoard({ now, status: 'running', doing: 'Codex review #7', expectMinutes: 30 });
  assert.match(long, /chạy tới khoảng \*\*14:35\*\*[\s\S]*Qua 14:45/);
  assert.match(renderBoard({ now, status: 'ran' }), /cũ hơn 20 phút/);
  assert.match(body, /\| #7 \| content \| claude-check \|/);
  assert.match(body, /Chờ owner: #139\./);
  assert.match(body, /Codex hôm nay: 3\/32/);
  assert.doesNotThrow(() => trust.assertAgentBody(body));
  assert.match(renderBoard({ now, status: 'closed' }), /NGOÀI GIỜ/);
  assert.match(renderBoard({ now, status: 'error', error: 'thiếu công cụ trên PATH: pnpm' }), /LỖI[\s\S]*thiếu công cụ/);
});

test('the board is one comment edited in place', () => {
  const calls = [];
  let comments = [];
  const gh = {
    // gh api --paginate --slurp: an array of pages.
    json: args => { assert.ok(args.includes('--slurp')); return [comments.slice(0, 1), comments.slice(1)]; },
    raw: (args, input) => {
      calls.push([args[2], args[3]]);
      if (args[2] === 'POST') { comments = [{ id: 55, author_association: 'OWNER', body: JSON.parse(input).body }]; return JSON.stringify({ id: 55 }); }
      return '{}';
    },
  };
  const body = renderBoard({ now, status: 'idle' });
  assert.equal(upsertBoard(gh, 133, body), 55);
  assert.equal(upsertBoard(gh, 133, body), 55);
  assert.deepEqual(calls.map(c => c[0]), ['POST', 'PATCH']);
  assert.match(calls[1][1], /issues\/comments\/55$/);
  assert.throws(() => upsertBoard(gh, 133, 'no marker'), /marker/);
  assert.ok(body.includes(boardMarker));
});

test('every tick updates the board, before heavy work too, and a board failure never breaks a tick', () => {
  const date = '2026-11-02';
  const comments = [{ authorAssociation: 'OWNER', createdAt: `${date}T01:50:00Z`, body: `${trust.agentMarker} daily-plan date=${date} -->` }];
  const open = [pr({ number: 1 })];
  const gh = {
    pr: () => open[0], openPrs: () => open, raw: () => '', comment: () => {},
    json: args => (args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments }),
  };
  const shown = [];
  const board = info => shown.push([info.status, info.doing ?? '']);
  tick({ gh, now: { date, hour: 11, minute: 5 }, board, merge: () => ({}), check: () => ({ status: 'PASS' }), review: () => ({ status: 'posted', verdict: 'APPROVE' }) });
  assert.deepEqual(shown.map(s => s[0]), ['running', 'running', 'ran']);
  assert.match(shown[0][1], /author check #1/);
  assert.match(shown[1][1], /Codex review #1/);
  shown.length = 0;
  tick({ gh, now: { date, hour: 23, minute: 40 }, board, merge: () => ({}), review: () => ({}) });
  assert.deepEqual(shown.map(s => s[0]), ['closed']);
  const result = tick({ gh, now: { date, hour: 12, minute: 5 }, board: () => { throw new Error('GitHub down'); }, merge: () => ({}), check: () => ({ status: 'FAIL' }), review: () => ({}) });
  assert.notEqual(result.status, 'error', 'a failing board does not fail the tick');
});

test('S8: a repeat ops-alert comments on the open issue of its subject instead of opening a new one', () => {
  const at = { date: '2026-11-09', hour: 17, minute: 8 };
  const calls = [];
  let open = [];
  const gh = {
    json: args => { calls.push(['list', args.join(' ')]); return open; },
    raw: (args, input) => { calls.push([args.slice(0, 3).join(' '), input ?? '']); if (args[1] === 'create') open = [{ number: 370, title: args[5] }]; return ''; },
  };
  assert.deepEqual(opsAlert(gh, 'tick lỗi 2 lần', 'collab loop', at), { number: null, created: true });
  const created = calls.find(c => c[0].startsWith('issue create'));
  assert.ok(created, 'the first alert opens an issue');
  assert.equal(open[0].title, '[ops-alert] collab loop', 'the title carries no date, so one thread spans days');
  calls.length = 0;
  assert.deepEqual(opsAlert(gh, 'tick lỗi lần nữa', 'collab loop', at), { number: 370, created: false });
  assert.equal(calls.filter(c => c[0].startsWith('issue create')).length, 0, 'no second issue');
  const comment = calls.find(c => c[0] === 'issue comment 370');
  assert.match(comment[1], /^Lặp lại lúc 2026-11-09 17:08: tick lỗi lần nữa/);
  assert.match(comment[1], /<!-- la-lanh-agent ops-alert -->$/);
  // Older dated titles of the same subject are reused (newest first); other subjects are not.
  assert.equal(openOpsAlert([{ number: 368, title: '[ops-alert] collab loop 2026-11-09' }, { number: 322, title: '[ops-alert] collab loop 2026-11-08' },
    { number: 350, title: '[ops-alert] tác vụ hẹn giờ bị treo 2026-11-08' }, { number: 352, title: '[ops-alert] collab loop failed 2026-11-08' }], 'collab loop'), 368);
  assert.equal(openOpsAlert([{ number: 350, title: '[ops-alert] tác vụ hẹn giờ bị treo 2026-11-08' }], 'collab loop'), null);
  // A failing lookup still raises the alert as a new issue.
  calls.length = 0;
  const down = { json: () => { throw new Error('gh down'); }, raw: (args, input) => { calls.push([args.slice(0, 2).join(' '), input ?? '']); return ''; } };
  assert.deepEqual(opsAlert(down, 'x', 'tác vụ hẹn giờ bị treo', at), { number: null, created: true });
  assert.ok(calls.some(c => c[0] === 'issue create'));
});

test('S8 part 2: resolving closes the open issue of that subject only, and a failed lookup throws for a retry', () => {
  const calls = [];
  const gh = {
    json: () => [{ number: 350, title: '[ops-alert] tác vụ hẹn giờ bị treo 2026-11-08' }, { number: 370, title: '[ops-alert] collab loop' }],
    raw: args => { calls.push(args); return ''; },
  };
  assert.deepEqual(resolveOpsAlert(gh, 'Autopilot (mỗi giờ): đã chạy xong lại', 'tác vụ hẹn giờ bị treo'), { number: 350, closed: true });
  assert.deepEqual(calls[0].slice(0, 3), ['issue', 'close', '350']);
  assert.match(calls[0][calls[0].indexOf('--comment') + 1], /^Tự đóng: Autopilot[\s\S]*<!-- la-lanh-agent ops-alert -->$/);
  calls.length = 0;
  assert.deepEqual(resolveOpsAlert({ json: () => [], raw: args => { calls.push(args); } }, 'x', 'tác vụ hẹn giờ bị treo'), { number: null, closed: false });
  assert.equal(calls.length, 0, 'nothing open, nothing closed');
  assert.throws(() => resolveOpsAlert({ json: () => { throw new Error('gh down'); }, raw: () => '' }, 'x', 'tác vụ hẹn giờ bị treo'), /gh down/);
});

test('#145 r2: a review waiting at the daily Codex cap shows a budget stop, not "no work"', () => {
  const date = '2026-11-13';
  trust.writeJson(trust.dayStatePath(date), { codexRuns: trust.codexDailyCap });
  const comments = [{ authorAssociation: 'OWNER', createdAt: `${date}T01:50:00Z`, body: `${trust.agentMarker} daily-plan date=${date} -->` }];
  // A signed PASS on the live base (P1-A/P1-B), so the PR waits for review.
  const base = 'e'.repeat(40);
  const seal = trust.checkSeal({ head: A, base, receipt: trust.signReceipt({ kind: 'check', pr: 9, head: A, base, result: 'PASS' }) });
  const checked = pr({ number: 9, baseTipOid: base, comments: [{ authorAssociation: 'OWNER', createdAt: `${date}T02:00:00Z`, body: `Author check: PASS @ ${A}\n${seal}` }] });
  const gh = {
    pr: () => checked, openPrs: () => [checked], raw: () => '', comment: () => {},
    json: args => (args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments }),
  };
  const shown = [];
  tick({ gh, now: { date, hour: 15, minute: 5 }, board: info => shown.push(info.status), merge: () => ({}), review: () => ({ status: 'posted' }) });
  assert.deepEqual(shown, ['cap']);
  assert.match(renderBoard({ now, status: 'cap' }), /HẾT LƯỢT CODEX HÔM NAY/);
});

// ---- owner 12.11: notify the owner with new comments, not silent edits ----
const planComment = date => ({ authorAssociation: 'OWNER', createdAt: `${date}T01:50:00Z`, body: `${trust.agentMarker} daily-plan date=${date} -->` });
const noteGh = (date, open, comments = [planComment(date)]) => {
  const posted = [];
  return {
    posted, comments,
    pr: () => open[0], openPrs: () => open, raw: () => '',
    comment: (kind, number, body) => { trust.assertAgentBody(body); posted.push(body); comments.push({ authorAssociation: 'OWNER', createdAt: `${date}T09:00:00Z`, body }); },
    json: args => (args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments }),
  };
};
let cacheN = 0;
const notifier = gh => { const cachePath = join(trust.stateDir, `notes-${cacheN++}.json`); return (notes, comments) => postOwnerNotes(gh, 50, notes, comments, { cachePath }); };
// Merge evidence needs a local receipt for this PR, head and base (P1-B), as the real check and review paths write it.
const approved = (sha, n) => {
  const receipt = (kind, result) => trust.signReceipt({ kind, pr: n, head: sha, base: BASE, result, p2: 0 });
  return [{ authorAssociation: 'OWNER', createdAt: '2026-11-01T00:00:00Z', body: renderCheck({ head: sha, status: 'PASS', base: BASE, receipt: receipt('check', 'PASS'), exitCode: 0, seconds: 1, date: 'x' }) },
    { authorAssociation: 'OWNER', createdAt: '2026-11-01T00:01:00Z', body: [`Review verdict: APPROVE @ ${sha}`, 'Reviewer: Codex (auto, scripts/codex-review.mjs)', '', trust.verdictSeal({ head: sha, p2: 0, base: BASE, receipt: receipt('verdict', 'APPROVE') })].join('\n') }];
};

test('merges post one new comment per tick, one plain line each, and a re-run never posts twice', () => {
  const date = '2026-12-01';
  const open = [pr({ number: 11, title: 'feat(daily): clearer mood note', comments: approved(A, 11) }), pr({ number: 12, title: 'fix(radar): shorter hint', comments: approved(A, 12) })];
  const gh = noteGh(date, open);
  const notify = notifier(gh);
  const run = minute => tick({ gh, now: { date, hour: 15, minute }, merge: () => ({ status: 'merged' }), review: () => ({}), notify });
  run(5);
  assert.equal(gh.posted.length, 1, 'both merges in one comment');
  assert.match(gh.posted[0], /^Đã gộp vào integration: clearer mood note \(#11\)\.\nĐã gộp vào integration: shorter hint \(#12\)\.\n/);
  assert.match(gh.posted[0], /<!-- la-lanh-agent owner-note keys=merged-11,merged-12 -->$/);
  run(15);
  assert.equal(gh.posted.length, 1, 'the same merges are never announced again');
  // A lost local cache still dedupes on the marker in the posted comment.
  assert.equal(postOwnerNotes(gh, 50, [{ key: 'merged-11', lines: ['x'] }], gh.comments, { cachePath: join(trust.stateDir, 'fresh-cache.json') }), null);
  assert.deepEqual([...sentNoteKeys([{ authorAssociation: 'NONE', body: `${trust.agentMarker} owner-note keys=merged-99 -->` }])], [], 'an outsider cannot suppress a note');
});

test('two failing ticks in a row post one note; the streak ending and starting again posts again', () => {
  const date = '2026-12-02';
  const gh = noteGh(date, []);
  const notify = notifier(gh);
  const run = (minute, preflight) => tick({ gh, now: { date, hour: 16, minute }, preflight, merge: () => ({}), review: () => ({}), notify });
  run(5, () => ['uv']);
  assert.equal(gh.posted.length, 0, 'one failure is not a streak');
  run(15, () => ['uv']);
  run(25, () => ['uv']);
  assert.equal(gh.posted.length, 1);
  assert.match(gh.posted[0], /^Vòng tự động bị lỗi 2 lượt liền từ 16:05\. Chi tiết ở bảng trạng thái\./);
  run(35, () => []);
  run(45, () => ['uv']);
  run(55, () => ['uv']);
  assert.equal(gh.posted.length, 2, 'a new streak is a new event');
  assert.match(gh.posted[1], /từ 16:45/);
});

test('a PR newly labelled needs-owner posts once; a new head that needs the owner again posts again', () => {
  const date = '2026-12-03';
  const open = [pr({ number: 21, title: 'content(daily): new bundle', labels: [{ name: 'needs-owner' }] })];
  const gh = noteGh(date, open);
  const notify = notifier(gh);
  const run = minute => tick({ gh, now: { date, hour: 14, minute }, merge: () => ({}), review: () => ({}), notify });
  run(5); run(15);
  assert.deepEqual(gh.posted.map(b => b.split('\n')[0]), ['Cần bạn xem: new bundle (#21).']);
  open[0] = { ...open[0], headRefOid: 'c'.repeat(40) };
  run(25);
  assert.equal(gh.posted.length, 2);
});

test('the digest posts once near 12:00 and 22:00 with done, doing, waiting, next and the metrics', () => {
  const date = '2026-12-04';
  const open = [pr({ number: 31, title: 'content(daily): calmer start', comments: approved(A, 31) }), pr({ number: 32, title: 'content(tarot): plain card', headRefName: 'agent/claude/x' }),
    pr({ number: 33, title: 'feat(radar): fewer words', labels: [{ name: 'needs-owner' }] })];
  const gh = noteGh(date, open);
  const notify = notifier(gh);
  const metrics = () => ['Bộ Daily phục vụ được: 1/3 bộ.'];
  const merge = n => { open.splice(open.findIndex(p => p.number === n), 1); return { status: 'merged' }; };
  trust.writeJson(trust.dayStatePath(date), { codexRuns: 0, failures: 0, planned: [31, 32] });
  const run = (hour, minute) => tick({ gh, now: { date, hour, minute }, merge, check: () => ({ status: 'FAIL' }), review: () => ({}), notify, metrics });
  run(11, 50);
  const beforeNoon = gh.posted.length;
  assert.ok(!gh.posted.some(b => /Tóm tắt/.test(b)), 'no digest before 12:00');
  run(12, 5);
  run(12, 15);
  const digests = gh.posted.filter(b => /Tóm tắt 12:00/.test(b));
  assert.equal(digests.length, 1, 'one digest per slot');
  assert.ok(gh.posted.length - beforeNoon === 1);
  const lines = digests[0].split('\n');
  assert.deepEqual(lines.slice(0, 6), [
    '**Tóm tắt 12:00**',
    '- Xong: 1/2 việc đã chọn hôm nay; đã gộp 1 PR.',
    '- Đang làm: plain card (#32).',
    '- Chờ bạn: fewer words (#33).',
    '- Tiếp theo: Claude chọn việc kế tiếp từ backlog khi có chỗ.',
    '- Bộ Daily phục vụ được: 1/3 bộ.',
  ]);
  assert.ok(lines.length <= 12, 'short');
  run(13, 30);
  run(22, 10);
  assert.equal(gh.posted.filter(b => /Tóm tắt 22:00/.test(b)).length, 1);
  assert.ok(gh.posted.every(b => !/REQUEST_CHANGES|APPROVE|claude-fix|codex-review|[0-9a-f]{40}/.test(b)), 'no codes');
});

test('notes are plain, carry the agent marker and never use the owner reply words', () => {
  const now = { date: '2026-12-05', hour: 12, minute: 1 };
  const notes = ownerNotes({ now, merged: [{ number: 1, title: 'Duyệt: tricky title' }], failures: 2, streakAt: '11:40', turns: [{ number: 2, turn: 'hold', reason: 'needs-owner', title: 'Giữ đúng', head: A }] });
  assert.deepEqual(notes.map(n => n.key), ['merged-1', 'stuck-2026-12-05-1140', `owner-2-${A.slice(0, 7)}`, 'digest-2026-12-05-12']);
  const gh = { comment: (kind, n, body) => trust.assertAgentBody(body) };
  assert.doesNotThrow(() => postOwnerNotes(gh, 50, notes, [], { cachePath: join(trust.stateDir, 'plain.json') }));
  assert.equal(plainTitle('feat(home)!: calmer start'), 'calmer start');
  assert.deepEqual(ownerNotes({ now: { ...now, hour: 13, minute: 5 } }), [], 'nothing happened: nothing posted');
});

test('the board shows the metric lines', () => {
  const body = renderBoard({ now, status: 'ran', metrics: ['Việc đang làm: 1/1, đang chờ review: 0/1.'] });
  assert.match(body, /\*\*Số đo\*\*\n- Việc đang làm: 1\/1, đang chờ review: 0\/1\./);
  const date = '2026-12-06';
  const shown = [];
  tick({ gh: noteGh(date, []), now: { date, hour: 15, minute: 5 }, board: info => shown.push(info.metrics), merge: () => ({}), review: () => ({}), metrics: () => ['m1'] });
  assert.deepEqual(shown.at(-1), ['m1']);
  shown.length = 0;
  tick({ gh: noteGh(date, []), now: { date, hour: 23, minute: 45 }, board: info => shown.push(info.metrics), merge: () => ({}), review: () => ({}), metrics: () => { throw new Error('should not run at night'); } });
  assert.deepEqual(shown, [null], 'metrics are not read at night');
});
