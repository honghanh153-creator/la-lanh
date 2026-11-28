// Three-agent dispatch 28.11.2026, part C: one host writer, idempotent steps, backpressure.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { admit, applyOnce, hostLimits } from './collab-writer.mjs';
import { admittedView, bufferStatus } from './collab-buffer.mjs';
import { readJson, writeJson } from './collab-trust.mjs';

const dir = () => mkdtempSync(join(tmpdir(), 'writer-'));
const bump = d => ({ ...d, codexRuns: (d.codexRuns ?? 0) + 1 });

test('writer: the same step applied twice (retry, restart) counts once; a new step counts', () => {
  const d = dir();
  const path = join(d, 'day.json');
  const opts = { lock: join(d, 'writer.lock'), lease: join(d, 'lease.json') };
  assert.equal(applyOnce(path, 'codex-run:a', bump, opts).status, 'applied');
  assert.equal(applyOnce(path, 'codex-run:a', bump, opts).status, 'duplicate');
  // A restart: a new process reads the same file and retries the same step.
  assert.equal(applyOnce(path, 'codex-run:a', bump, { ...opts }).status, 'duplicate');
  assert.equal(applyOnce(path, 'codex-run:b', bump, opts).status, 'applied');
  assert.equal(readJson(path).codexRuns, 2);
  assert.throws(() => applyOnce(path, '', bump, opts), /idempotency key/);
});

test('writer: a writer that lost the coordinator lease cannot write (fencing epoch)', () => {
  const d = dir();
  const path = join(d, 'queue.json');
  const lease = join(d, 'lease.json');
  writeJson(lease, { holder: 'claude', epoch: 3, released: false });
  const opts = { lock: join(d, 'writer.lock'), lease };
  assert.equal(applyOnce(path, 'q1', s => ({ ...s, items: [1] }), { ...opts, epoch: 3 }).status, 'applied');
  writeJson(lease, { holder: 'codex', epoch: 4, released: false });
  assert.equal(applyOnce(path, 'q2', s => ({ ...s, items: [1, 2] }), { ...opts, epoch: 3 }).status, 'fenced');
  assert.deepEqual(readJson(path).items, [1]);
});

test('writer: the host lock held by a live run makes the step busy, not lost or doubled', () => {
  const d = dir();
  const lock = join(d, 'writer.lock');
  writeFileSync(lock, `${process.pid} live-holder`);
  const path = join(d, 'x.json');
  assert.equal(applyOnce(path, 'k', bump, { lock, lease: join(d, 'l.json'), waitMs: 50 }).status, 'busy');
  assert.equal(readJson(path, null), null, 'nothing written');
});

test('writer: backpressure 3 in progress, 2 waiting for review, 2 heavy jobs', () => {
  assert.deepEqual(hostLimits, { inProgress: 3, inReview: 2, heavy: 2 });
  assert.equal(admit({ inProgress: 0, inReview: 0 }).room, 3);
  assert.equal(admit({ inProgress: 2, inReview: 1 }).room, 1);
  assert.equal(admit({ inProgress: 3, inReview: 0 }).room, 0, 'full: nothing new opens');
  assert.equal(admit({ inProgress: 0, inReview: 2 }).room, 0, 'two waiting for review: nothing new opens');
  assert.match(admit({ inProgress: 0, inReview: 2 }).reasons[0], /chờ review 2\/2/);
  assert.equal(admit({ heavy: 2 }).heavyRoom, 0);
  assert.equal(admit({ heavy: 1 }).heavyRoom, 1);
  // #949 r1 (C5): one admitted view; the lanes never open more than the host admits.
  const lanes = { plan7w: { inProgress: 0, inReview: 0, topUp: true }, daily: { inProgress: 0, inReview: 0, topUp: true }, process: { inProgress: 0, inReview: 0, topUp: true } };
  const open = admittedView({ topUp: true, topUpCount: 3, topUpLanes: ['plan7w', 'daily', 'process'], inProgress: 2, inReview: 0, lanes });
  assert.deepEqual([open.topUp, open.topUpCount, open.topUpLanes, open.lanes.daily.topUp], [true, 1, ['plan7w'], false], 'room 1: only the first lane opens');
  const full = admittedView({ topUp: true, topUpCount: 3, topUpLanes: ['plan7w', 'daily', 'process'], inProgress: 0, inReview: 2, lanes });
  assert.deepEqual([full.topUp, full.topUpCount, full.topUpLanes, full.lanes.plan7w.topUp], [false, 0, [], false]);
  assert.match(full.backpressure[0], /chờ review 2\/2/);
  const late = admittedView({ topUp: true, topUpCount: 3, topUpLanes: ['plan7w'], inProgress: 0, inReview: 0, lanes }, { late: true });
  assert.deepEqual([late.topUp, late.topUpCount, late.topUpLanes], [false, 0, []], 'nothing opens from lastStartAt on');
});
