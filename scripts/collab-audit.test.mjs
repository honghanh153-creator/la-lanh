import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { collectFacts, readOutputs, receipt, saveFacts } from './collab-audit.mjs';

const head = 'e'.repeat(40);
const output = JSON.stringify({ verdict: 'APPROVE', sha: head, complete: true, summary: 'ok', findings: [] });
const digest = createHash('sha256').update(output).digest('hex');
const verdict = (body, at = '2026-11-14T03:00:00Z') => ({ authorAssociation: 'OWNER', createdAt: at, body });
const real = verdict(`Review verdict: APPROVE @ ${head}\nReviewer: Codex (auto, scripts/codex-review.mjs)\n\nok\n\nOutput SHA-256: \`${digest}\`\n<!-- la-lanh-agent codex-auto-review sha=${head} p2=0 -->`);
const pr = (n, comments, extra = {}) => ({ number: n, title: `fix: ${n}`, headRefOid: head, createdAt: '2026-11-14T01:00:00Z', mergedAt: '2026-11-14T04:00:00Z', comments, ...extra });
const outputs = [{ pr: 7, head12: head.slice(0, 12), digest }];

test('forged marker is not a real receipt', () => {
  assert.deepEqual(receipt(pr(7, [real]), outputs), { ok: true });
  const forged = verdict(`Review verdict: APPROVE @ ${head}\nReviewer: Codex\n\nOutput SHA-256: \`${'0'.repeat(64)}\`\n<!-- la-lanh-agent codex-auto-review sha=${head} -->`);
  assert.match(receipt(pr(7, [forged]), outputs).why, /không có file output Codex khớp/);
  assert.match(receipt(pr(7, [verdict(`Review verdict: APPROVE @ ${head}`)]), outputs).why, /không phải review tự động/);
  assert.match(receipt(pr(8, [real]), outputs).why, /không có file output Codex khớp/, 'a real output of another PR does not count');
  const late = { ...real, createdAt: '2026-11-14T05:00:00Z' };
  assert.match(receipt(pr(7, [late]), outputs).why, /không có verdict/, 'a verdict posted after the merge does not count');
  const then = verdict(`Review verdict: REQUEST_CHANGES @ ${head}\nReviewer: Codex\n<!-- la-lanh-agent codex-auto-review sha=${head} -->`, '2026-11-14T03:30:00Z');
  assert.match(receipt(pr(7, [real, then]), outputs).why, /REQUEST_CHANGES/);
});

test('local Codex outputs are read by PR, head and digest', () => {
  const dir = mkdtempSync(join(tmpdir(), 'audit-logs-'));
  writeFileSync(join(dir, `codex-2026-11-14-pr7-${head.slice(0, 12)}-1.json`), output);
  writeFileSync(join(dir, 'review-2026-11-14-pr7.json'), '{}');
  assert.deepEqual(readOutputs(dir), outputs);
});

const fakeGh = ({ merged, alerts = [] }) => ({ json: args => {
  if (args[0] === 'pr') { if (merged instanceof Error) throw merged; return merged; }
  if (args[0] === 'issue') return alerts;
  throw new Error(`unexpected ${args.join(' ')}`);
} });

test('missing source stays unmeasured, never zero', () => {
  const f = collectFacts({ date: '2026-11-14', now: new Date('2026-11-14T16:00:00Z'), gh: fakeGh({ merged: new Error('gh: HTTP 502') }), outputs: () => outputs, day: () => null });
  for (const m of ['M2', 'M6', 'M7', 'M9', 'M1', 'M5', 'M10']) {
    assert.equal(f.metrics[m].value, null, `${m} has no value`);
    assert.ok(f.metrics[m].missing, `${m} says why`);
  }
  assert.match(f.metrics.M2.missing, /HTTP 502/);
});

test('two PRs completing one AC count once: work items are not counted from PRs', () => {
  const f = collectFacts({ date: '2026-11-14', now: new Date('2026-11-14T16:00:00Z'), gh: fakeGh({ merged: [pr(7, [real]), pr(9, [real])] }), outputs: () => outputs, day: () => ({ codexRuns: 12 }) });
  assert.equal(f.metrics.M5.value, null, 'M5 stays unmeasured until the plan has task ids and criteria');
  assert.deepEqual({ v: f.metrics.M2.value, of: f.metrics.M2.of, items: f.metrics.M2.items }, { v: 1, of: 2, items: [{ pr: 9, why: 'không có file output Codex khớp mã băm' }] });
  assert.equal(f.metrics.M6.value, 3);
  assert.equal(f.metrics.M7.value, 1);
  assert.equal(f.metrics.M9.value, 12);
});

test('late events enter the finalized day; a retry after a failure does not duplicate', () => {
  const dir = mkdtempSync(join(tmpdir(), 'audit-exp-'));
  const gh = fakeGh({ merged: [pr(7, [real])] });
  const provisional = collectFacts({ date: '2026-11-14', now: new Date('2026-11-14T16:00:00Z'), gh, outputs: () => outputs, day: () => null });
  assert.equal(provisional.final, false, '23:00 VN is provisional');
  saveFacts(provisional, dir);
  saveFacts(provisional, dir);
  assert.deepEqual(readdirSync(dir), ['2026-11-14.json'], 'one file per day');
  const lateGh = fakeGh({ merged: [pr(7, [real]), pr(11, [real], { mergedAt: '2026-11-14T16:40:00Z' })] });
  const final = collectFacts({ date: '2026-11-14', now: new Date('2026-11-14T17:30:00Z'), gh: lateGh, outputs: () => outputs, day: () => null });
  assert.equal(final.final, true, 'after midnight VN the day is final');
  saveFacts(final, dir);
  assert.equal(JSON.parse(readFileSync(join(dir, '2026-11-14.json'), 'utf8')).metrics.M2.of, 2, 'the 23:40 merge is in the final record');
  assert.equal(saveFacts(provisional, dir).kept, true, 'a provisional re-run never replaces the final record');
});

test('disagreements and owner overrides are counted for the day', () => {
  const log = [
    { date: '2026-11-14', pr: 7, winner: 'codex' }, { date: '2026-11-14', task: 'L21', winner: 'claude' },
    { date: '2026-11-14', type: 'override', of: 'x', winner: 'claude' }, { date: '2026-11-13', pr: 1, winner: 'codex' },
  ];
  const f = collectFacts({ date: '2026-11-14', now: new Date('2026-11-14T16:00:00Z'), gh: fakeGh({ merged: [] }), outputs: () => [], day: () => null, disagreements: () => log });
  assert.deepEqual(f.metrics.M8, { value: 2, codex: 1, claude: 1, owner: 0, overrides: 1 });
});
