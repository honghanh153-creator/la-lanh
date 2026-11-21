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

// 18.11 (Codex on #723): a PR held behind another PR shows "chờ PR khác", never "chờ owner".
test('a hold behind another PR is labelled as waiting on that PR, not on the owner', () => {
  assert.deepEqual(labelChange({ labels: ['st: chờ owner'] }, { turn: 'hold', reason: 'chờ PR #722 cùng file' }), { add: 'st: chờ PR khác', remove: ['st: chờ owner'] });
  assert.deepEqual(labelChange({ labels: [] }, { turn: 'hold', reason: 'xếp chồng trên agent/claude/x' }), { add: 'st: chờ PR khác', remove: [] });
  for (const reason of ['needs-owner', 'base là main: chỉ owner', 'owner bỏ khỏi plan hôm nay'])
    assert.deepEqual(labelChange({ labels: [] }, { turn: 'hold', reason }), { add: 'st: chờ owner', remove: [] }, reason);
  // The PR leaves the wait label once its turn moves on.
  assert.deepEqual(labelChange({ labels: ['st: chờ PR khác'] }, { turn: 'claude-check' }), { add: 'st: đang kiểm tra', remove: ['st: chờ PR khác'] });
});

// 18.11 (hourly check 16:45): a draft is paused by its agent, not held for the owner (#726).
test('a draft is labelled paused by its agent, never "chờ owner"', () => {
  assert.deepEqual(labelChange({ labels: ['st: chờ owner'] }, { turn: 'hold', reason: 'draft' }), { add: 'st: tạm dừng', remove: ['st: chờ owner'] });
  assert.deepEqual(labelChange({ labels: ['st: tạm dừng'] }, { turn: 'claude-check' }), { add: 'st: đang kiểm tra', remove: ['st: tạm dừng'] });
  assert.deepEqual(labelChange({ labels: [] }, { turn: 'hold', reason: 'needs-owner' }), { add: 'st: chờ owner', remove: [] });
});

