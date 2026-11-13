import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { append, entry, read } from './collab-disagree.mjs';

test('experiment arm 1: a disagreement needs both positions, a PR and a known winner, and is kept in order', () => {
  const path = join(mkdtempSync(join(tmpdir(), 'disagree-')), 'd.jsonl');
  assert.deepEqual(read(path), []);
  const at = new Date('2026-11-14T03:00:00Z');
  append(entry({ pr: 480, claude: 'giữ 3 lần thử', codex: 'giữ lỗi tới khi phục hồi', winner: 'codex', at }), path);
  append(entry({ pr: 481, claude: 'a', codex: 'b', winner: 'owner', note: 'owner lật lại', at }), path);
  assert.deepEqual(read(path).map(e => [e.pr, e.winner, e.date]), [[480, 'codex', '2026-11-14'], [481, 'owner', '2026-11-14']]);
  assert.throws(() => entry({ pr: 'x', claude: 'a', codex: 'b', winner: 'codex' }), /PR number/);
  assert.throws(() => entry({ pr: 1, claude: '', codex: 'b', winner: 'codex' }), /both positions/);
  assert.throws(() => entry({ pr: 1, claude: 'a', codex: 'b', winner: 'nobody' }), /winner/);
  writeFileSync(path, `${JSON.stringify({ pr: 1 })}\nnot json\n`, { flag: 'a' });
  assert.equal(read(path).length, 3, 'a broken line is skipped, the rest is kept');
});
