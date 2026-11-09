import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-status-'));
const trust = await import('./collab-trust.mjs');
const { boardMarker, renderBoard, upsertBoard } = await import('./collab-status.mjs');
const { openOpsAlert, opsAlert, resolveOpsAlert, tick } = await import('./collab-turn.mjs');

const A = 'a'.repeat(40);
const now = { date: '2026-11-01', hour: 14, minute: 5 };
const own = { author: { login: 'honghanh153-creator' }, isCrossRepository: false };
const pr = extra => ({ number: 7, title: 'feat(tarot): x', state: 'OPEN', isDraft: false, baseRefName: 'collab/integration', headRefName: 'b', headRefOid: A, labels: [], createdAt: '2026-10-30T00:00:00Z', comments: [], ...own, ...extra });

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
  const checked = pr({ number: 9, comments: [{ authorAssociation: 'OWNER', createdAt: `${date}T02:00:00Z`, body: `Author check: PASS @ ${A}\n${trust.agentMarker} x -->` }] });
  const gh = {
    pr: () => checked, openPrs: () => [checked], raw: () => '', comment: () => {},
    json: args => (args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments }),
  };
  const shown = [];
  tick({ gh, now: { date, hour: 15, minute: 5 }, board: info => shown.push(info.status), merge: () => ({}), review: () => ({ status: 'posted' }) });
  assert.deepEqual(shown, ['cap']);
  assert.match(renderBoard({ now, status: 'cap' }), /HẾT LƯỢT CODEX HÔM NAY/);
});
