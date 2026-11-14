import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-snapshot-'));
const assert = (await import('node:assert/strict')).default;
const test = (await import('node:test')).default;
const trust = await import('./collab-trust.mjs');
const { collect, renderSnapshot, saveOnce, snapshotPath, takeSnapshot } = await import('./collab-snapshot.mjs');
const { ownerNotes, renderBoard } = await import('./collab-status.mjs');
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
  assert.equal(lines[0], '- Đã gộp vào integration hôm nay: 1 PR.');
  assert.match(lines.at(-1), new RegExp(`· snapshot ${first.digest}$`));
  // The tick digest of the same slot prints the same block.
  const notes = ownerNotes({ now: { date, hour: 14, minute: 5 }, merged: [{ number: 1, title: 'a' }, { number: 2, title: 'b' }, { number: 3, title: 'c' }], snapshot: slot => takeSnapshot({ slot, date, dir, sources: sources([]) }) });
  const digest = notes.find(n => n.key.startsWith('digest-')).lines;
  for (const line of lines) assert.ok(digest.includes(line), `digest repeats: ${line}`);
  assert.ok(!digest.some(l => /Đã gộp 3 PR/.test(l)), 'the tick does not count again');
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
