import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readdirSync, readFileSync, utimesSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { acquireLock, readOwner, withFileLock } from './collab-lock.mjs';

const dir = () => mkdtempSync(join(tmpdir(), 'collab-lock-'));
const DEAD = 999999;
const alive = pid => pid !== DEAD;
const age = (path, ms) => { const t = (Date.now() - ms) / 1000; utimesSync(path, t, t); };
const opts = { staleMs: 3600000, alive };

test('interleave (Codex #258): A pauses after reading a dead owner, B reclaims; A must not delete B\'s lock', () => {
  const lock = join(dir(), 'check.lock');
  writeFileSync(lock, `${DEAD} old`);
  let releaseB;
  const a = acquireLock(lock, { ...opts, pause: step => { if (step === 'read' && !releaseB) releaseB = acquireLock(lock, opts); } });
  assert.ok(releaseB, 'B reclaims the dead lock first');
  assert.equal(a, null, 'A finds a live owner and stays out');
  assert.equal(readOwner(lock).pid, process.pid);
  releaseB();
  assert.equal(existsSync(lock), false);
});

test('interleave (Codex #279 P1): while A holds the reclaim guard, B can neither reclaim nor delete', () => {
  const lock = join(dir(), 'review.lock');
  writeFileSync(lock, `${DEAD} old`);
  let b = 'not run';
  const releaseA = acquireLock(lock, { ...opts, pause: step => { if (step === 'guarded' && b === 'not run') b = acquireLock(lock, opts); } });
  assert.ok(releaseA);
  assert.equal(b, null, 'the guard of that incarnation is held by a live run');
  assert.equal(acquireLock(lock, opts), null, 'one holder');
  releaseA();
});

test('interleave (Codex #279 P1): a stale guard read by A and recovered by B is not deleted again by A', () => {
  const lock = join(dir(), 'tick.lock');
  writeFileSync(lock, `${DEAD} old`);
  const guard = `${lock}.old.gone`;
  writeFileSync(guard, `${DEAD} crashed`);
  age(guard, 61000);
  let releaseB;
  const a = acquireLock(lock, { ...opts, pause: step => { if (step === 'guard-read' && !releaseB) releaseB = acquireLock(lock, opts); } });
  assert.ok(releaseB, 'B recovers the crashed guard and takes the lock');
  assert.equal(a, null, 'A does not take a second copy');
  assert.equal(readOwner(lock).pid, process.pid);
  releaseB();
});

test('a release that cannot take the guard deletes nothing; a late stale holder keeps its hands off the new lock', () => {
  const lock = join(dir(), 'tick.lock');
  const releaseOld = acquireLock(lock, { staleMs: 1000, alive });
  age(lock, 5000);
  const releaseNew = acquireLock(lock, { staleMs: 1000, alive });
  assert.ok(releaseNew, 'past staleMs the old lock is reclaimed');
  const now = readFileSync(lock, 'utf8');
  releaseOld();
  assert.equal(readFileSync(lock, 'utf8'), now);
  const token = now.trim().split(' ')[1];
  writeFileSync(`${lock}.${token}.gone`, `${process.pid} other`);
  releaseNew();
  assert.equal(readFileSync(lock, 'utf8'), now, 'guard held by a live run: release skips the delete');
});

test('crash safety (Codex #279 P1): an empty guard or a leftover temp file never blocks forever', () => {
  const d = dir();
  const lock = join(d, 'check.lock');
  writeFileSync(lock, `${DEAD} old`);
  writeFileSync(`${lock}.old.gone`, '');
  assert.equal(acquireLock(lock, opts), null, 'a fresh empty guard may still be mid-write');
  age(`${lock}.old.gone`, 61000);
  writeFileSync(`${lock}.tmp-${DEAD}-dead`, '');
  const release = acquireLock(lock, opts);
  assert.ok(release, 'an empty guard older than 60 s is recovered');
  assert.match(readFileSync(lock, 'utf8'), new RegExp(`^${process.pid} [0-9a-f]{16}$`), 'the lock is published with its full owner');
  release();
  assert.deepEqual(readdirSync(d).filter(n => !n.includes('.tmp-')), []);
});

test('withFileLock returns busy without calling fn; a lock without a PID is reclaimed only by age', () => {
  const lock = join(dir(), 'review.lock');
  writeFileSync(lock, '{}');
  let ran = 0;
  const o = { staleMs: 45 * 60000, alive, busy: { status: 'busy' } };
  assert.deepEqual(withFileLock(lock, o, () => ran++), { status: 'busy' });
  age(lock, 46 * 60000);
  assert.equal(withFileLock(lock, o, () => { ran++; return 'ok'; }), 'ok');
  assert.equal(ran, 1);
  assert.equal(existsSync(lock), false);
});
