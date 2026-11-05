import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { promptPath } from './codex-review.mjs';

test('retro S2: the review prompt asks for every place of the same class in one round', () => {
  const fixed = readFileSync(promptPath, 'utf8');
  assert.match(fixed, /search the whole repository for every other place with the same pattern/);
  assert.match(fixed, /`file:line` entries/);
  assert.match(fixed, /same class again in a place an earlier round could have named is itself a P2 `docs` finding/);
});
