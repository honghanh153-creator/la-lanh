import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-status-'));
const trust = await import('./collab-trust.mjs');
const { boardMarker, renderBoard, upsertBoard } = await import('./collab-status.mjs');
const { tick } = await import('./collab-turn.mjs');

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
  assert.match(body, /Codex hôm nay: 3\/12/);
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

test('#145 r2: a review waiting at the daily Codex cap shows a budget stop, not "no work"', () => {
  const date = '2026-11-13';
  trust.writeJson(trust.dayStatePath(date), { codexRuns: 12 });
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
