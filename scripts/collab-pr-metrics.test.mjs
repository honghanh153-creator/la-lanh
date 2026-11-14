import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { prMetrics, reworkRefs, summary } from './collab-pr-metrics.mjs';

test('per-PR numbers and summary', () => {
  const pr = { number: 7, title: 't', createdAt: '2026-11-01T00:00:00Z', mergedAt: '2026-11-01T03:00:00Z',
    comments: [{ body: 'Review verdict: REQUEST_CHANGES @ a' }, { body: 'Review verdict: APPROVE @ b' }] };
  const runs = [{ pr: 7, ms: 600000 }, { pr: 7, ms: 300000 }, { pr: 8, ms: 1 }];
  const rework = reworkRefs([{ title: 'fix-forward: copy from #7', labels: [{ name: 'fix-forward' }] }, { title: 'unrelated #9' }]);
  const row = prMetrics(pr, runs, rework);
  assert.deepEqual(row, { pr: 7, title: 't', hours: 3, codexRuns: 2, codexMinutes: 15, changeRequests: 1, rework: true });
  const clean = prMetrics({ ...pr, number: 8, comments: [] }, runs, rework);
  assert.deepEqual(summary([row, clean]), { prs: 2, avgHours: 3, avgCodexRuns: 1.5, avgChangeRequests: 0.5, firstPassRate: 50, reworkRate: 50 });
});

test('a revert title counts as rework on its own, without labels (Codex #354 P2)', () => {
  assert.deepEqual([...reworkRefs([{ title: 'Revert "synthetic change (#7)"' }])], [7]);
  assert.deepEqual([...reworkRefs([{ title: 'revert: drop x', body: 'undoes #12', labels: [] }])], [12]);
  assert.deepEqual([...reworkRefs([{ title: 'docs: how to revert #5' }, { title: 'feat: x #6', labels: [{ name: 'enhancement' }] }])], []);
  assert.deepEqual([...reworkRefs([{ title: 'x #8', labels: ['fix-forward'] }])], [8]);
});
