import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, utimesSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { acquireLock, withFileLock } from './collab-lock.mjs';

const dir = () => mkdtempSync(join(tmpdir(), 'collab-lock-'));
const DEAD = 999999;
const alive = pid => pid !== DEAD;
const age = (path, ms) => { const t = (Date.now() - ms) / 1000; utimesSync(path, t, t); };

test('interleave (Codex #258): B tries to replace the lock while A reclaims it, and only one holds it', () => {
  const lock = join(dir(), 'check.lock');
  writeFileSync(lock, String(DEAD));
  let b = 'not run';
  // A pauses after verifying the dead PID; B runs then (the old race window) and must be refused.
  const releaseA = acquireLock(lock, { staleMs: 3600000, alive, waitMs: 0, pause: step => {
    if (step === 'verified') b = acquireLock(lock, { staleMs: 3600000, alive, waitMs: 0 });
  } });
  assert.ok(releaseA, 'A reclaims the dead lock');
  assert.equal(b, null, 'B cannot create or reclaim while A holds the reclaim mutex');
  assert.equal(readFileSync(lock, 'utf8'), String(process.pid));
  assert.equal(existsSync(`${lock}.reclaim`), false, 'the mutex is released after the reclaim');
  assert.equal(acquireLock(lock, { staleMs: 3600000, alive, waitMs: 0 }), null, 'a live holder is not reclaimed');
  releaseA();
  assert.equal(existsSync(lock), false);
});

test('interleave: a stale holder releasing late does not delete the new holder\'s lock', () => {
  const lock = join(dir(), 'tick.lock');
  const releaseOld = acquireLock(lock, { staleMs: 1000, alive, waitMs: 0 });
  age(lock, 5000);
  const releaseNew = acquireLock(lock, { staleMs: 1000, alive, waitMs: 0 });
  assert.ok(releaseNew, 'the old lock is past staleMs and is reclaimed');
  writeFileSync(lock, '424242');
  releaseOld();
  assert.equal(readFileSync(lock, 'utf8'), '424242', 'release removes only a lock that still holds its own PID');
});

test('the mutex of a crashed reclaimer older than 60 s with a dead owner is removed once', () => {
  const lock = join(dir(), 'review.lock');
  writeFileSync(`${lock}.reclaim`, `${DEAD} x`);
  assert.equal(acquireLock(lock, { staleMs: 1000, alive, waitMs: 0 }), null, 'a fresh mutex is respected');
  age(`${lock}.reclaim`, 61000);
  const release = acquireLock(lock, { staleMs: 1000, alive, waitMs: 0 });
  assert.ok(release, 'the crashed mutex is removed and the lock taken');
  release();
  writeFileSync(`${lock}.reclaim`, `${process.pid} x`);
  age(`${lock}.reclaim`, 61000);
  assert.equal(acquireLock(lock, { staleMs: 1000, alive, waitMs: 0 }), null, 'a mutex whose owner lives is kept');
});

test('withFileLock returns busy without calling fn, and a lock without a PID is reclaimed only by age', () => {
  const lock = join(dir(), 'review.lock');
  writeFileSync(lock, '{}');
  let ran = 0;
  assert.deepEqual(withFileLock(lock, { staleMs: 45 * 60000, alive, waitMs: 0, busy: { status: 'busy' } }, () => ran++), { status: 'busy' });
  age(lock, 46 * 60000);
  assert.equal(withFileLock(lock, { staleMs: 45 * 60000, alive, waitMs: 0, busy: { status: 'busy' } }, () => { ran++; return 'ok'; }), 'ok');
  assert.equal(ran, 1);
  assert.equal(existsSync(lock), false);
});
