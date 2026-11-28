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
import { codexDailyCap, codexFallbackCap, cutoffAt, hhmmOf, lastStartAt, planOpensAt } from './collab-trust.mjs';
import { fallbackAt, savingAt } from './collab-usage.mjs';
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
  claudeSavingAt: savingAt,
  claudeFallbackAt: fallbackAt,
  codexFallbackCap,
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
    // L68: the Claude usage thresholds and the fallback sub-cap.
    ['R1', `${facts.claudeSavingAt}%`], ['R1', `${facts.claudeFallbackAt}%`], ['R8', `${facts.codexFallbackCap} lần`],
    ['R9', facts.cutoffAt], ['R9', facts.lastStartAt],
    ...(Array.isArray(facts.reportSlots) ? facts.reportSlots.map(s => ['R5', s]) : []),
  ];
  for (const [id, value] of mentions) if (value && !row(id).includes(value)) out.push(`${id}: bảng không nhắc ${value} như khối rules-facts`);
  for (const k of ['reportSlots', 'retiredReportSlots']) {
    if (!Array.isArray(facts[k]) || facts[k].some(s => !/^\d{2}:\d{2}$/.test(s))) out.push(`rules-facts.${k} phải là danh sách HH:MM`);
  }
  out.push(...valueProblems(row, facts));
  return out;
}

// Fix-forward #643: a mention is not enough. Every value the rule text states must equal the facts,
// so "Trần 60 lượt" beside an unchanged "base: 80" is red, as are a dropped owner kind, an empty slot
// list or a retired slot that is still scheduled. Only the rule column is read: the "Thay thế" column
// is history and keeps the old values on purpose.
const kindWords = { cost_access: /chi phí/i, release: /phát hành/i, sensitive_copy: /privacy/i, data_collection: /thu dữ liệu/i };
const times = text => [...String(text).matchAll(/(?<!\d)(\d{1,2}:\d{2})(?!\d)/g)].map(m => m[1].padStart(5, '0'));
const clauses = text => String(text).split(/[.;](?:\s+|$)/);
const dropped = /không có|(?<!\p{L})bỏ(?!\p{L})/iu;
export function valueProblems(row, facts) {
  const out = [];
  const r8 = row('R8');
  for (const m of r8.matchAll(/(\d+)\s*lượt|base:\s*(\d+)/g)) {
    const n = Number(m[1] ?? m[2]);
    if (n !== facts.codexDailyCap) out.push(`R8: bảng ghi ${m[0]}, khối rules-facts là ${facts.codexDailyCap}`);
  }
  const r9 = new Set([facts.lastStartAt, facts.cutoffAt]);
  for (const t of times(row('R9'))) if (!r9.has(t)) out.push(`R9: bảng ghi giờ ${t}, khối rules-facts chỉ có ${[...r9].join(', ')}`);
  const slots = Array.isArray(facts.reportSlots) ? facts.reportSlots : [];
  const retiredSlots = Array.isArray(facts.retiredReportSlots) ? facts.retiredReportSlots : [];
  if (!slots.length) out.push('rules-facts.reportSlots không được rỗng');
  for (const s of retiredSlots) if (slots.includes(s)) out.push(`rules-facts: ${s} vừa là giờ báo cáo vừa là giờ đã bỏ`);
  for (const clause of clauses(row('R5'))) {
    const gone = dropped.test(clause);
    for (const t of times(clause)) {
      if (gone && !retiredSlots.includes(t)) out.push(`R5: bảng ghi đã bỏ bản ${t}, khối rules-facts không có trong retiredReportSlots`);
      if (!gone && !slots.includes(t)) out.push(`R5: bảng ghi báo cáo ${t}, khối rules-facts không có trong reportSlots`);
    }
  }
  const kinds = Array.isArray(facts.ownerKinds) ? facts.ownerKinds : [];
  const r2 = row('R2');
  const count = r2.match(/Chỉ\s+(\d+)\s+loại/i);
  if (!count || Number(count[1]) !== kinds.length) out.push(`R2: bảng phải ghi "Chỉ ${kinds.length} loại" như ownerKinds`);
  // Fix-forward #654: the items must be exactly (1)…(N), and each kind is read inside its own item, in
  // the order of ownerKinds, so a word that also appears in another item does not hide a missing one.
  const marks = [...r2.matchAll(/\((\d+)\)/g)];
  const numbers = marks.map(m => Number(m[1]));
  if (numbers.join(',') !== kinds.map((_, i) => i + 1).join(',')) out.push(`R2: bảng liệt kê các mục (${numbers.join(', ')}), ownerKinds cần (${kinds.map((_, i) => i + 1).join(', ')})`);
  const itemText = i => {
    const at = marks.findIndex(m => Number(m[1]) === i + 1);
    if (at < 0) return '';
    const end = marks[at + 1]?.index ?? r2.slice(marks[at].index).search(/\.\s/) + marks[at].index;
    return r2.slice(marks[at].index, end > marks[at].index ? end : undefined);
  };
  kinds.forEach((k, i) => { if (!kindWords[k]?.test(itemText(i))) out.push(`R2: mục (${i + 1}) không nêu loại ${k}`); });
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
