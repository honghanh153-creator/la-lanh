// One source of truth for the owner's rules in force (owner 16.11.2026: "you forget a lot and don't
// learn"; Claude + Codex agreed the order: one source per rule, re-load it in long sessions, turn
// owner corrections into behaviour checks, only then a nightly memory pass).
// The sheet is docs/operations/luat-dang-hieu-luc.md: one row per rule (id, scope, rule, source,
// effective date, what it replaces, state) and a `rules-facts` JSON block with the numbers the loop
// code also holds. Prompts, docs and agent memory point to rule ids instead of restating them.
// This script reads the sheet, gives it a version (content hash, used by the re-load hook) and
// checks that the facts equal the code constants, so a rule changed in one place only goes red.
// Usage: node scripts/collab-rules.mjs            (prints version + problems; exit 1 on a problem)
//        node scripts/collab-rules.mjs --version  (prints the version only)
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { codexDailyCap, cutoffAt, hhmmOf, lastStartAt, planOpensAt } from './collab-trust.mjs';
import { ownerKinds } from './collab-review-policy.mjs';
import { isMain } from './is-main.mjs';

const here = dirname(fileURLToPath(import.meta.url));
export const sheetRel = 'docs/operations/luat-dang-hieu-luc.md';
export const sheetPath = (root = join(here, '..')) => join(root, sheetRel);

export const rulesVersion = text => createHash('sha256').update(text).digest('hex').slice(0, 16);

// Rows of the main table: `| R1 | scope | rule | source | from | replaces | state |`.
export function parseRules(text) {
  const rows = [];
  for (const line of text.split('\n')) {
    const m = /^\|\s*(R\d+)\s*\|(.*)\|\s*$/.exec(line);
    if (!m) continue;
    const cells = m[2].split('|').map(c => c.trim());
    rows.push({ id: m[1], scope: cells[0], rule: cells[1], source: cells[2], from: cells[3], replaces: cells[4], state: cells[5], line });
  }
  const block = /```json rules-facts\n([\s\S]*?)\n```/.exec(text);
  let facts = null;
  try { facts = block ? JSON.parse(block[1]) : null; } catch { facts = null; }
  return { rows, facts };
}

export const codeFacts = () => ({
  codexDailyCap,
  planOpensAt: hhmmOf(planOpensAt),
  lastStartAt: hhmmOf(lastStartAt),
  cutoffAt: hhmmOf(cutoffAt),
  ownerKinds: [...ownerKinds],
});

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

// Problems with the sheet: shape (every row complete, ids unique and in order) and facts that differ
// from the code. Report slots are checked against the scheduled-task prompts (collab-ops-wrapper).
export function problems(text, code = codeFacts()) {
  const out = [];
  const { rows, facts } = parseRules(text);
  if (!rows.length) out.push('không thấy dòng luật nào (| R1 | … |)');
  const seen = new Set();
  rows.forEach((r, i) => {
    if (seen.has(r.id)) out.push(`${r.id}: Id trùng`);
    seen.add(r.id);
    if (r.id !== `R${i + 1}`) out.push(`${r.id}: Id phải theo thứ tự (chờ R${i + 1}); không đánh lại số, chỉ thêm ở cuối`);
    for (const k of ['scope', 'rule', 'source', 'from', 'replaces', 'state']) if (!r[k]) out.push(`${r.id}: thiếu cột ${k}`);
    if (r.state && !/^(chạy|đã quyết)/.test(r.state)) out.push(`${r.id}: trạng thái phải bắt đầu bằng "chạy" hoặc "đã quyết"`);
    if (r.from && !/\d{1,2}\.\d{1,2}(\.\d{4})?/.test(r.from)) out.push(`${r.id}: thiếu ngày hiệu lực`);
  });
  if (!facts) { out.push('thiếu hoặc hỏng khối ```json rules-facts'); return out; }
  for (const [k, v] of Object.entries(code)) {
    if (!same(facts[k], v)) out.push(`rules-facts.${k} = ${JSON.stringify(facts[k])} nhưng code = ${JSON.stringify(v)}`);
  }
  // The table and the facts block must say the same thing (Codex r1: no second source inside the file).
  const row = id => rows.find(r => r.id === id)?.rule ?? '';
  const mentions = [
    ['R8', String(facts.codexDailyCap)],
    ['R9', facts.cutoffAt], ['R9', facts.lastStartAt],
    ...(Array.isArray(facts.reportSlots) ? facts.reportSlots.map(s => ['R5', s]) : []),
  ];
  for (const [id, value] of mentions) if (value && !row(id).includes(value)) out.push(`${id}: bảng không nhắc ${value} như khối rules-facts`);
  for (const k of ['reportSlots', 'retiredReportSlots']) {
    if (!Array.isArray(facts[k]) || facts[k].some(s => !/^\d{2}:\d{2}$/.test(s))) out.push(`rules-facts.${k} phải là danh sách HH:MM`);
  }
  return out;
}

export function readSheet(root) {
  const text = readFileSync(sheetPath(root), 'utf8');
  return { text, version: rulesVersion(text), ...parseRules(text) };
}

if (isMain(import.meta.url)) {
  const sheet = readSheet();
  if (process.argv.includes('--version')) {
    console.log(sheet.version);
  } else {
    const bad = problems(sheet.text);
    console.log(`luật đang hiệu lực: ${sheet.rows.length} dòng, bản ${sheet.version}`);
    for (const b of bad) console.log(`- ${b}`);
    process.exitCode = bad.length ? 1 : 0;
  }
}
