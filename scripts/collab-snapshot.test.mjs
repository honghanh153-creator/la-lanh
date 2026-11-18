import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-snapshot-'));
const assert = (await import('node:assert/strict')).default;
const test = (await import('node:test')).default;
// Incident 18.11.2026: a merge reservation written by one tick test must not steer the next.
test.beforeEach(async () => (await import('./collab-reservation.mjs'))._resetReservation());
const trust = await import('./collab-trust.mjs');
const { collect, renderSnapshot, saveOnce, snapshotPath, takeSnapshot } = await import('./collab-snapshot.mjs');
const { renderBoard } = await import('./collab-status.mjs');
const { tick } = await import('./collab-turn.mjs');

// Synthetic sources only.
const date = '2026-11-20';
const sources = (merged, extra = {}) => ({
  base: () => 'c'.repeat(40),
  merged: () => merged,
  openPrs: () => [{ number: 9, labels: [{ name: 'needs-owner' }] }, { number: 10, labels: [] }],
  alerts: () => [{ number: 300, title: '[ops-alert] collab loop', createdAt: '2026-11-20T02:00:00Z' }],
  day: () => ({ codexRuns: 7, failures: 0, plannedItems: [{ item: 12 }, { pr: 40 }] }),
  lessons: () => 'Lời hứa sửa quy trình: 3/26 đã chạy thật.',
  work: planned => ({ picked: planned.filter(p => p.item).length, finished: [], open: [], unlinked: [40] }),
  ...extra,
});
const at = iso => () => new Date(iso);

test('two reports in one slot read one snapshot and print the same numbers', () => {
  const dir = mkdtempSync(join(tmpdir(), 'snap-'));
  const first = takeSnapshot({ slot: '14', date, dir, sources: sources([{ number: 1, title: 'a', mergedAt: '2026-11-20T03:00:00Z' }]), clock: at('2026-11-20T07:00:00Z') });
  // A second report a minute later sees more merges on GitHub, but reads the slot's snapshot.
  const second = takeSnapshot({ slot: '14', date, dir, sources: sources([{ number: 1, title: 'a', mergedAt: '2026-11-20T03:00:00Z' }, { number: 2, title: 'b', mergedAt: '2026-11-20T07:00:30Z' }]), clock: at('2026-11-20T07:01:00Z') });
  assert.deepEqual(second, first);
  assert.deepEqual(renderSnapshot(second), renderSnapshot(first));
  const lines = renderSnapshot(first);
  assert.equal(lines[0], '- Đã gộp vào integration hôm nay: 1 PR (số PR, không phải số việc).');
  assert.match(lines.at(-1), new RegExp(`· snapshot ${first.digest}$`));
  const other = takeSnapshot({ slot: '22', date, dir, sources: sources([]), clock: at('2026-11-20T15:00:00Z') });
  assert.notEqual(other.digest, first.digest, 'another slot is another snapshot');
});

test('the day is the Vietnam day up to the cut-off, and a failed source is unmeasured, never zero', () => {
  const merged = [
    { number: 1, title: 'a', mergedAt: '2026-11-19T17:30:00Z' }, // 00:30 on the 20th in Vietnam
    { number: 2, title: 'b', mergedAt: '2026-11-19T16:30:00Z' }, // 23:30 on the 19th
    { number: 3, title: 'c', mergedAt: '2026-11-20T08:00:00Z' }, // after the cut-off
  ];
  const s = collect({ date, slot: '14', clock: at('2026-11-20T07:00:00Z'), ...sources(merged) });
  assert.deepEqual(s.merged.map(m => m.number), [1]);
  const broken = collect({ date, slot: '14', clock: at('2026-11-20T07:00:00Z'), ...sources([], { merged: () => { throw new Error('gh: timeout'); }, alerts: () => { throw new Error('rate limit'); } }) });
  assert.equal(broken.merged, null);
  assert.equal(broken.sources.merged, 'chưa đo được: gh: timeout');
  const text = renderSnapshot(broken).join('\n');
  assert.match(text, /Đã gộp vào integration hôm nay: chưa đo được \(gh: timeout\)\./);
  assert.match(text, /Sự cố đang mở: chưa đo được \(rate limit\)\./);
  assert.doesNotMatch(text, /: 0 PR/);
});

test('a slot is written once, atomically', () => {
  const dir = mkdtempSync(join(tmpdir(), 'snap-once-'));
  const path = snapshotPath(date, '08', dir);
  const a = collect({ date, slot: '08', clock: at('2026-11-20T01:00:00Z'), ...sources([]) });
  const b = collect({ date, slot: '08', clock: at('2026-11-20T01:00:05Z'), ...sources([{ number: 5, title: 'x', mergedAt: '2026-11-20T00:30:00Z' }]) });
  assert.deepEqual(saveOnce(a, path), a);
  assert.deepEqual(saveOnce(b, path), a, 'the second writer reads the first');
  assert.deepEqual(JSON.parse(readFileSync(path, 'utf8')), a);
  assert.throws(() => takeSnapshot({ slot: '12', date, dir, sources: sources([]) }), /slot phải là/);
});

test('a clean tick does not clear an open incident without recovery evidence', () => {
  const day = '2026-11-21';
  trust.writeJson(trust.dayStatePath(day), { codexRuns: 0, failures: 0 });
  const boards = [];
  const gh = { openPrs: () => [], json: args => (args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }] : { comments: [] }), comment: () => {}, raw: () => '' };
  const open = [{ number: 300, title: '[ops-alert] collab loop', createdAt: '2026-11-21T02:00:00Z' }];
  tick({ gh, now: { date: day, hour: 23, minute: 45 }, board: info => boards.push(renderBoard(info)), incidents: () => open, merge: () => ({}), review: () => ({}) });
  assert.equal(trust.readJson(trust.dayStatePath(day), {}).failures ?? 0, 0, 'the tick itself was clean');
  assert.match(boards.at(-1), /Sự cố đang mở\*\* \(chỉ đóng khi có bằng chứng phục hồi\)\n- #300 \[ops-alert\] collab loop \(từ 21\/11 09:00\)/);
  tick({ gh, now: { date: day, hour: 23, minute: 55 }, board: info => boards.push(renderBoard(info)), incidents: () => { throw new Error('gh down'); }, merge: () => ({}), review: () => ({}) });
  assert.match(boards.at(-1), /Sự cố đang mở:\*\* chưa đọc được từ GitHub/, 'an unreadable list is not "no incident"');
  tick({ gh, now: { date: day, hour: 23, minute: 58 }, board: info => boards.push(renderBoard(info)), incidents: () => [], merge: () => ({}), review: () => ({}) });
  assert.doesNotMatch(boards.at(-1), /Sự cố đang mở/, 'only a closed issue ends it');
});

// Codex r1 on #497 (P2): readJson turned a missing or broken day state into {}, which printed
// zero Codex runs and "no work picked". A source that cannot be read is unmeasured.
test('an unavailable day state is unmeasured, never zero runs or no picked work', async () => {
  const { realSources } = await import('./collab-snapshot.mjs');
  const { writeFileSync, mkdirSync } = await import('node:fs');
  const take = day => collect({ date: day, slot: '14', clock: at(`${day}T07:00:00Z`), ...sources([], { day: realSources(null, day).day }) });
  const missing = renderSnapshot(take('2026-11-22')).join('\n');
  assert.match(missing, /Lượt Codex hôm nay: chưa đo được \(chưa có trạng thái ngày\)\./);
  assert.match(missing, /Việc đạt tiêu chí: chưa đo được \(chưa đọc được trạng thái ngày\)\./);
  assert.doesNotMatch(missing, /0\/\d+; lỗi liên tiếp: 0|chưa chọn việc/);
  mkdirSync(join(trust.dayStatePath('2026-11-23'), '..'), { recursive: true });
  writeFileSync(trust.dayStatePath('2026-11-23'), '{"codexRuns": 3,');
  const broken = take('2026-11-23');
  assert.equal(broken.day, null);
  assert.equal(broken.sources.day, 'chưa đo được: trạng thái ngày hỏng');
  assert.equal(broken.work, null);
  // A day state without the picked list (the plan is not made yet) counts runs but not work.
  trust.writeJson(trust.dayStatePath('2026-11-24'), { codexRuns: 2, failures: 0 });
  const early = renderSnapshot(take('2026-11-24')).join('\n');
  assert.match(early, /Lượt Codex hôm nay: 2\/\d+; lỗi liên tiếp: 0\./);
  assert.match(early, /Việc đạt tiêu chí: chưa đo được \(chưa có danh sách việc đã chọn\)\./);
});

// Codex r1 on #497 (P2): merged PRs were cut at takenAt, finished work was not, so one snapshot
// could read "0 PR" next to "1/1 việc".
test('a PR merged after the cut-off finishes no item in the snapshot', async () => {
  const { realSources } = await import('./collab-snapshot.mjs');
  const sha = 'd'.repeat(40);
  // #456 P1-B: the APPROVE is signed for PR 5 and bound to its comment URL, as codex-review.mjs posts it.
  const { asPosted } = await import('./collab-test-post.mjs');
  const reviewed = [{ authorAssociation: 'OWNER', createdAt: '2026-11-20T06:00:00Z', body: `Author check: PASS @ ${sha}\n${trust.agentMarker} x -->` },
    asPosted(trust, { authorAssociation: 'OWNER', createdAt: '2026-11-20T06:30:00Z', body: `Review verdict: APPROVE @ ${sha}\nReviewer: Codex\n${trust.verdictSeal({ head: sha, p2: 0, base: null, receipt: trust.signReceipt({ kind: 'verdict', pr: 5, head: sha, base: null, result: 'APPROVE', p2: 0 }) })}` })];
  const late = { number: 5, title: 'x', body: 'Việc: #12\nTiêu chí đạt: TC1', state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha, comments: reviewed, mergedAt: '2026-11-20T07:00:30Z' };
  const fetch = () => ({ body: '## Tiêu chí đạt\n\n- [ ] Thẻ ngắn hơn\n', prs: [late] });
  const take = iso => collect({ date, slot: '14', clock: at(iso), ...sources([late], { work: realSources(null, date, { fetch }).work }) });
  const before = renderSnapshot(take('2026-11-20T07:00:00Z'));
  assert.equal(before[0], '- Đã gộp vào integration hôm nay: 0 PR (số PR, không phải số việc).');
  assert.equal(before[1], '- Việc đạt tiêu chí: 0/1 việc đã chọn đạt đủ tiêu chí; 1 PR chưa gắn việc (#40), không tính.');
  const after = renderSnapshot(take('2026-11-20T07:01:00Z'));
  assert.equal(after[0], '- Đã gộp vào integration hôm nay: 1 PR (số PR, không phải số việc).');
  assert.match(after[1], /^- Việc đạt tiêu chí: 1\/1 việc đã chọn/);
});

// Codex r1 on #497 (P2): the snapshot block replaced the outcome metrics of §2.11 in the digest.
