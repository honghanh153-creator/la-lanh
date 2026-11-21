import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { readReceipts, receiptSummary, renderReceipts, writeRunReceipt } from './collab-run-receipt.mjs';
import { runTick } from './collab-tick.mjs';

const fresh = () => join(mkdtempSync(join(tmpdir(), 'receipts-')), 'run-receipts.jsonl');
const sha = 'a'.repeat(40);

test('research item 3: a receipt keeps only fixed words, a commit and numbers', () => {
  const path = fresh();
  const r = writeRunReceipt({ kind: 'tick', result: 'ok', sha, counts: { done: 3, note: 'chuỗi tự do', 'bad key': 1, big: Infinity }, at: new Date('2026-11-21T12:00:00Z'), path });
  assert.deepEqual(r, { at: '2026-11-21T12:00:00.000Z', kind: 'tick', result: 'ok', sha, counts: { done: 3 } }, 'text and odd keys are dropped');
  assert.equal(writeRunReceipt({ kind: 'tick', result: 'ok', sha: 'not-a-sha', path }).sha, null);
  assert.throws(() => writeRunReceipt({ kind: 'deploy', result: 'ok', path }), /unknown receipt kind/);
  assert.throws(() => writeRunReceipt({ kind: 'tick', result: 'fine', path }), /unknown receipt result/);
  assert.equal(readReceipts(path).length, 2);
});

test('research item 3: the board line says what really ran in 24 hours, and "chưa chạy" for a job with none', () => {
  const path = fresh();
  const at = iso => new Date(iso);
  writeRunReceipt({ kind: 'tick', result: 'ok', sha, at: at('2026-11-21T01:00:00Z'), path });
  writeRunReceipt({ kind: 'tick', result: 'error', sha: 'b'.repeat(40), at: at('2026-11-21T02:00:00Z'), path });
  writeRunReceipt({ kind: 'tick', result: 'skipped', sha, at: at('2026-11-21T02:10:00Z'), path });
  writeRunReceipt({ kind: 'night-audit', result: 'ok', sha, at: at('2026-11-19T17:00:00Z'), path });
  const s = receiptSummary(readReceipts(path), { nowMs: Date.parse('2026-11-21T12:00:00Z') });
  assert.deepEqual(s.tick, { runs: 2, errors: 1, last: { at: '2026-11-21T02:00:00.000Z', sha: 'b'.repeat(40) } }, 'a skipped tick is not a run');
  assert.equal(s['night-audit'].runs, 0, 'older than 24 hours');
  assert.equal(renderReceipts(s), 'Đã chạy thật 24 giờ qua: vòng tự động 2 lượt (lỗi 1), lần cuối 09:00, code bbbbbbb; soát đêm: chưa chạy; người giả hằng đêm: chưa chạy.');
});

test('research item 3: the tick, the night audit and the nightly personas each leave a receipt', () => {
  const written = [];
  const given = runTick({ raw: () => '', json: () => [] }, () => [], { run: g => ({ ...g, status: 'ran', done: [{ pr: 1 }, { pr: 2 }] }), gapNote: () => null, areaNote: () => null, probe: () => [], receipt: r => written.push(r), receipts: () => 'Đã chạy thật 24 giờ qua: x.' });
  assert.deepEqual(written, [{ kind: 'tick', result: 'ok', counts: { done: 2 } }]);
  assert.ok(given.health().includes('Đã chạy thật 24 giờ qua: x.'), 'the board shows the receipts line');
  const busy = [];
  runTick({ raw: () => '', json: () => [] }, () => [], { run: () => ({ status: 'busy' }), gapNote: () => null, areaNote: () => null, probe: () => [], receipt: r => busy.push(r) });
  assert.equal(busy[0].result, 'skipped');
  const failing = runTick({ raw: () => '', json: () => [] }, () => [], { run: () => ({ status: 'ran' }), gapNote: () => null, areaNote: () => null, probe: () => [], receipt: () => { throw new Error('disk full'); } });
  assert.equal(failing.status, 'ran', 'a failed receipt never fails the tick');
  const source = readFileSync(join(import.meta.dirname, 'personas-nightly.mjs'), 'utf8');
  assert.match(source, /receipt\(\{ kind: 'personas', result: 'ok', sha: state\.end,/, 'the persona run names the commit it measured');
  const tick = readFileSync(join(import.meta.dirname, 'collab-tick.mjs'), 'utf8');
  assert.match(tick, /receipt\(\{ kind: 'night-audit',/);
});
