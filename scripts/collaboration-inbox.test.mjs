import assert from 'node:assert/strict';
import test from 'node:test';
import { readInbox, renderInbox } from './collaboration-inbox.mjs';

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
