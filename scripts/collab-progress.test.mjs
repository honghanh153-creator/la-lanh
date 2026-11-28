import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'progress-'));
const { needsMessage, progressDir, progressLines, readProgress, setProgress } = await import('./collab-progress.mjs');

test('L75: sessions write progress to one shared board; the report reads it; only blocked or decision asks for a message', () => {
  const home = mkdtempSync(join(tmpdir(), 'progress-home-'));
  const t0 = new Date('2026-11-22T10:00:00Z');
  assert.equal(setProgress({ key: 'conflict-heal', status: 'working', note: 'viết test\nđỏ/xanh', pr: 902, session: 'claude-a', now: t0, home }).message, false);
  assert.equal(setProgress({ key: 'go-vuong.lo-3', status: 'blocked', note: 'thiếu file trạng thái', next: 'chờ điều phối', now: t0, home }).message, true);
  setProgress({ key: 'spend-split', status: 'done', pr: 901, now: t0, home });
  setProgress({ key: 'old-done', status: 'done', now: new Date('2026-11-20T10:00:00Z'), home });
  writeFileSync(join(progressDir(home), 'broken.json'), '{nope');
  const later = new Date('2026-11-22T13:30:00Z');
  const entries = readProgress({ home, now: later });
  assert.deepEqual(entries.map(e => e.key), ['go-vuong.lo-3', 'conflict-heal', 'spend-split'], 'blocked first; done older than a day and broken files left out');
  assert.equal(entries[1].note, 'viết test đỏ/xanh', 'one line');
  assert.equal(entries[1].old, true, 'not updated for 3 hours');
  const lines = progressLines(entries);
  assert.equal(lines[0], 'Tiến độ các phiên (bảng chung):');
  assert.equal(lines[1], '- go-vuong.lo-3: bị kẹt ⚠️ — thiếu file trạng thái; tiếp: chờ điều phối (cập nhật 17:00, cũ hơn 3 giờ)');
  assert.equal(lines[2], '- conflict-heal (#902): đang làm — viết test đỏ/xanh (cập nhật 17:00, cũ hơn 3 giờ)');
  assert.equal(lines[3], '- spend-split (#901): xong (cập nhật 17:00)');
  assert.deepEqual(progressLines([]), ['Tiến độ các phiên: chưa phiên nào ghi']);
  assert.deepEqual(['working', 'waiting', 'done', 'blocked', 'decision'].map(needsMessage), [false, false, false, true, true]);
  assert.equal(readdirSync(progressDir(home)).some(f => f.endsWith('.tmp')), false, 'written atomically');
  assert.throws(() => setProgress({ key: '../x', status: 'working', home }), /key/);
  assert.throws(() => setProgress({ key: 'x', status: 'maybe', home }), /status/);
  assert.throws(() => setProgress({ key: 'x', status: 'working', pr: 'abc', home }), /pr/);
  assert.match(readFileSync(new URL('./collab-turn.mjs', import.meta.url), 'utf8'), /progressLines\(readProgress\(\)\)/, 'the report (ops-run.sh report) reads the board');
});

test('L75: the command line writes and shows the board', () => {
  const home = mkdtempSync(join(tmpdir(), 'progress-cli-'));
  const env = { ...process.env, LA_LANH_COLLAB_HOME: home, LA_LANH_SESSION: 'claude-test' };
  const script = fileURLToPath(new URL('./collab-progress.mjs', import.meta.url));
  assert.match(execFileSync(process.execPath, [script, '--set', 'item-1', '--status', 'decision', '--note', 'chọn A hay B'], { env, encoding: 'utf8' }), /nhắn phiên điều phối ngay/);
  assert.match(execFileSync(process.execPath, [script, '--set', 'item-2', '--status', 'working'], { env, encoding: 'utf8' }), /không cần nhắn ai/);
  const shown = execFileSync(process.execPath, [script], { env, encoding: 'utf8' });
  assert.match(shown, /- item-1: cần quyết định ⚠️ — chọn A hay B/);
  assert.match(shown, /- item-2: đang làm/);
  assert.equal(JSON.parse(execFileSync(process.execPath, [script, '--json'], { env, encoding: 'utf8' }))[0].session, 'claude-test');
});
