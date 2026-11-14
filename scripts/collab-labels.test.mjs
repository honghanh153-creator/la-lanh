import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { labelChange, syncStatusLabels } from './collab-labels.mjs';

test('label follows the turn and only changes when needed', () => {
  assert.deepEqual(labelChange({ labels: [] }, { turn: 'codex-review' }), { add: 'st: chờ review', remove: [] });
  assert.deepEqual(labelChange({ labels: [{ name: 'st: chờ review' }, { name: 'area:content' }] }, { turn: 'claude-fix' }), { add: 'st: cần sửa', remove: ['st: chờ review'] });
  assert.deepEqual(labelChange({ labels: ['st: đã duyệt'] }, { turn: 'merge' }), { add: null, remove: [] });
  const calls = [];
  syncStatusLabels({ raw: a => calls.push(a.slice(0, 3).join(' ')) }, [{ number: 5, labels: [] }, { number: 6, labels: ['st: đã duyệt'] }], [{ number: 5, turn: 'hold' }, { number: 6, turn: 'merge' }]);
  assert.deepEqual(calls, ['label create st: chờ owner', 'pr edit 5']);
});
