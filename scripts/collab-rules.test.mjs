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

// Fix-forward #643: each case below passed the mention-only check of #614 and must now be red.
test('#643: a value the rule text states must equal the facts, not merely sit beside them', () => {
  const r8 = real.replace(/^(\| R8 \|[^|]*\|[^|]*)Trần 80 lượt/m, '$1Trần 60 lượt');
  assert.notEqual(r8, real);
  assert.match(problems(r8).join('\n'), /R8: bảng ghi 60 lượt, khối rules-facts là 80/);
  const base = real.replace(/^(\| R8 \|.*)base: 80/m, '$1base: 60');
  assert.match(problems(base).join('\n'), /R8: bảng ghi base: 60/);
  const r9 = real.replace(/^(\| R9 \|[^|]*\|[^|]*)23:35/m, '$123:35, có khi 23:00');
  assert.match(problems(r9).join('\n'), /R9: bảng ghi giờ 23:00/);
  // A dropped owner kind: the count, the list and the kind itself.
  const r2 = real.replace(/^(\| R2 \|[^|]*\|[^|]*)Chỉ 4 loại[^;]*; /m, '$1Chỉ 3 loại việc chờ owner: ');
  assert.notEqual(r2, real);
  assert.match(problems(r2).join('\n'), /R2: bảng phải ghi "Chỉ 4 loại"|R2: bảng không nêu loại cost_access/);
  // Empty slots, and a retired slot that is the active 07:00 report.
  assert.match(problems(setFact(real, 'reportSlots', [])).join('\n'), /reportSlots không được rỗng/);
  const retired07 = problems(setFact(real, 'retiredReportSlots', ['07:00'])).join('\n');
  assert.match(retired07, /07:00 vừa là giờ báo cáo vừa là giờ đã bỏ/);
  assert.match(retired07, /R5: bảng ghi đã bỏ bản 08:00, khối rules-facts không có trong retiredReportSlots/);
  // A slot scheduled in the table but missing from the facts.
  const r5 = real.replace(/^(\| R5 \|[^|]*\| )07:00 bản chính/m, '$107:00 và 08:00 bản chính');
  assert.match(problems(r5).join('\n'), /R5: bảng ghi báo cáo 08:00, khối rules-facts không có trong reportSlots/);
});

// Fix-forward #654: removing item (2) left "phát hành" in item (3) and the highest number at 4.
test('#654: every owner kind is checked inside its own numbered item', () => {
  const no2 = real.replace(/\(2\) phát hành cho người dùng thật \(`main`, deploy\); /, '');
  assert.notEqual(no2, real);
  const bad = problems(no2).join('\n');
  assert.match(bad, /R2: bảng liệt kê các mục \(1, 3, 4\), ownerKinds cần \(1, 2, 3, 4\)/);
  assert.match(bad, /R2: mục \(2\) không nêu loại release/);
  // Swapping two items puts each kind under the wrong number.
  const swapped = real.replace('(1) chi phí', '(9) chi phí').replace('(2) phát hành', '(1) phát hành').replace('(9) chi phí', '(2) chi phí');
  assert.match(problems(swapped).join('\n'), /R2: mục \(1\) không nêu loại cost_access/);
});

test('rules sheet: the version changes with any edit and only then', () => {
  assert.equal(rulesVersion(real), rulesVersion(String(real)));
  assert.notEqual(rulesVersion(real), rulesVersion(real.replace('R9', 'R9 ')));
  assert.equal(parseRules(real).rows[0].id, 'R1');
});
