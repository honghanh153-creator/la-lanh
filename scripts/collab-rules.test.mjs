import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { codeFacts, parseRules, problems, readSheet, rulesVersion, sheetPath } from './collab-rules.mjs';

const real = readFileSync(sheetPath(), 'utf8');
const setFact = (text, key, value) => text.replace(/```json rules-facts\n([\s\S]*?)\n```/, (all, body) => {
  const facts = JSON.parse(body);
  facts[key] = value;
  return `\`\`\`json rules-facts\n${JSON.stringify(facts, null, 2)}\n\`\`\``;
});

test('rules sheet: the committed sheet is complete and its facts equal the code', () => {
  const sheet = readSheet();
  assert.ok(sheet.rows.length >= 17, 'R1–R17 at least');
  assert.deepEqual(problems(real), []);
});

test('rules sheet: a fact changed on one side only goes red (cap, hours, owner kinds)', () => {
  // The sheet says 60 while the code says 80: the stale cap of 15.11 must not come back silently.
  assert.match(problems(setFact(real, 'codexDailyCap', 60)).join('\n'), /codexDailyCap = 60 nhưng code = 80/);
  assert.match(problems(setFact(real, 'lastStartAt', '23:00')).join('\n'), /lastStartAt/);
  assert.match(problems(setFact(real, 'cutoffAt', '23:30')).join('\n'), /cutoffAt/);
  assert.match(problems(setFact(real, 'ownerKinds', ['cost_access', 'release', 'sensitive_copy'])).join('\n'), /ownerKinds/);
  // And the other side: the code moves, the sheet does not.
  assert.match(problems(real, { ...codeFacts(), codexDailyCap: 100 }).join('\n'), /codexDailyCap = 80 nhưng code = 100/);
});

test('rules sheet: rows keep their ids and every column, the facts block must parse', () => {
  const dropped = real.replace(/^\| R3 \|.*\n/m, '');
  assert.match(problems(dropped).join('\n'), /R4: Id phải theo thứ tự/);
  const noSource = real.replace(/^(\| R5 \|[^|]*\|[^|]*\|)[^|]*\|/m, '$1  |');
  assert.match(problems(noSource).join('\n'), /R5: thiếu cột source/);
  const badState = real.replace(/^(\| R6 \|.*\|)\s*chạy\s*\|$/m, '$1 xong |');
  assert.match(problems(badState).join('\n'), /R6: trạng thái/);
  assert.match(problems(real.replace('```json rules-facts', '```json')).join('\n'), /thiếu hoặc hỏng khối/);
});

test('rules sheet: the table and the facts block cannot disagree', () => {
  // Facts and code move together to 90, the R8 row still says 80: red.
  const moved = setFact(real, 'codexDailyCap', 90);
  assert.match(problems(moved, { ...codeFacts(), codexDailyCap: 90 }).join('\n'), /R8: bảng không nhắc 90/);
  assert.match(problems(setFact(real, 'reportSlots', ['07:00', '14:00', '21:00'])).join('\n'), /R5: bảng không nhắc 21:00/);
});

test('rules sheet: the version changes with any edit and only then', () => {
  assert.equal(rulesVersion(real), rulesVersion(String(real)));
  assert.notEqual(rulesVersion(real), rulesVersion(real.replace('R9', 'R9 ')));
  assert.equal(parseRules(real).rows[0].id, 'R1');
});
