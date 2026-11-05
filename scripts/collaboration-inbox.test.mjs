import assert from 'node:assert/strict';
import test from 'node:test';
import { readInbox, renderInbox } from './collaboration-inbox.mjs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { agentsMaxBytes, docSizeProblems, repoDocs } from './agent-doc-size.mjs';

test('inbox shows task decisions and PR handoffs', () => {
  const output = renderInbox([{ number: 2, title: 'Task', url: 'https://github.com/example/2', body: 'Worker: Claude. Files: Tarot. Handoff: abc.', comments: [{ body: 'Latest commit: def' }] }],
    [{ number: 3, title: 'Change', headRefName: 'agent/claude', baseRefName: 'collab/integration', body: 'Tests pass',
      reviews: [{ state: 'COMMENTED', commit: { oid: 'abc123' }, body: 'Review verdict: REQUEST_CHANGES @ abc123' }] }]);
  assert.match(output, /READ-ONLY/);
  assert.match(output, /Worker: Claude/);
  assert.match(output, /agent\/claude -> collab\/integration/);
  assert.match(output, /Tests pass/);
  assert.match(output, /Latest commit: def/);
  assert.match(output, /Latest review \(COMMENTED @ abc123\): Review verdict: REQUEST_CHANGES @ abc123/);
});
test('only fixed read-only gh argv are executed', () => {
  const calls = [];
  const output = readInbox((command, args, options) => {
    calls.push({ command, args, options });
    return JSON.stringify([{ number: 7, title: '$(do-not-run)', body: '`do-not-run`', headRefName: 'x', baseRefName: 'y' }]);
  });
  assert.equal(calls.length, 2);
  assert.ok(calls.every(c => c.command === 'gh' && c.args[1] === 'list' && !c.options.shell));
  assert.ok(calls[1].args.at(-1).split(',').includes('reviews'));
  assert.match(output, /\$\(do-not-run\)/);
});
test('API failures and invalid JSON are not mistaken for an empty task board', () => {
  assert.throws(() => readInbox(() => { throw new Error('Offline'); }));
  assert.throws(() => readInbox(() => 'invalid JSON'));
});
test('remote text is bounded and terminal control characters are stripped', () => {
  const output = renderInbox([{ number: 1, title: '\u001b[2J', body: 'x'.repeat(10000) }], []);
  assert.ok(!output.includes('\u001b'));
  assert.ok(output.length < 5000);
  assert.match(output, /\[\.\.\.truncated: read the full Issue\/PR\]/);
});

// Retro S5: the instruction files every agent reads at start must fit what each tool loads.
const root = join(dirname(fileURLToPath(import.meta.url)), '..');

test('the repository instruction files fit what Claude Code and Codex actually load', () => {
  assert.deepEqual(docSizeProblems(repoDocs(root)), []);
});

test('a CLAUDE.md over 200 lines is reported', () => {
  assert.deepEqual(docSizeProblems({ 'CLAUDE.md': 'x\n'.repeat(200) }), []);
  assert.match(docSizeProblems({ 'CLAUDE.md': 'x\n'.repeat(201) })[0], /CLAUDE\.md: 201 dòng/);
});

test('AGENTS.md is measured along the root-to-folder chain Codex joins', () => {
  const half = 'a'.repeat(agentsMaxBytes / 2);
  const files = { 'AGENTS.md': half, 'web/AGENTS.md': half, 'web/app/AGENTS.md': 'b', 'api/AGENTS.md': half };
  assert.deepEqual(docSizeProblems(files), ['web/app/AGENTS.md: chuỗi AGENTS.md 32769 byte (tối đa 32768)']);
  assert.match(docSizeProblems({ 'AGENTS.md': 'é'.repeat(agentsMaxBytes / 2 + 1) })[0], /32770 byte/);
});
