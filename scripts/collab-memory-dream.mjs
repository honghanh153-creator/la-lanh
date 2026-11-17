// Nightly memory "dream" pass (owner 16.11.2026: "you forget a lot and don't learn"; idea from
// Kevin Chen, "Agents that remember", Code with Claude London 20.05.2026; order agreed with Codex:
// one rules source, re-load, behaviour checks, only then this pass).
// It reads Claude's local memory folder (the owner's machine; it holds her own words, so nothing
// leaves the machine: no network, no AI call, no GitHub) and PROPOSES a new store next to it:
// - stale: an entry already marked old, or one that states a Codex cap, stop time or report slot
//   that differs from the rules sheet (`rules-facts`), gets "[OLD → Rn]" on its index line;
// - duplicates: two entries whose word sets overlap above a threshold are listed for merging (never
//   merged or deleted here; 0.35 word-set overlap, the real store's top pair was 0.21 on 16.11);
// - reference check: an entry the rules pointer links to a rule id, with no contradicting number,
//   gets `rules-checked: <date> <sheet>@<version> (Rn)` in its metadata. It means only "the ids and
//   numbers agree with the sheet", not that the whole entry was verified (Codex r2);
// - index: entries missing from MEMORY.md get a line; index lines to missing files are listed.
// Output: <out>/memory (the proposed store), <out>/diff.patch and <out>/summary.json (counts and rule
// ids only, no memory text; the 07:00 report reads it). The real memory is never written: applying
// accepted changes is a separate step (--apply) that refuses a file whose source or rules version
// changed since the proposal. It never edits the rules sheet (PR only) or the rules pointer entry.
// Privacy (Codex r2): the proposal is private data like the memory itself: directories 0700, files
// 0600, symlinks in the memory folder are skipped, stdout carries counts only, proposals older than
// 14 days are removed.
// Usage: node scripts/collab-memory-dream.mjs --memory <dir> --out <dir> [--date YYYY-MM-DD] [--sheet <file>]
//        node scripts/collab-memory-dream.mjs --apply <out> --memory <dir> --accept a.md,MEMORY.md [--sheet <file>]
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { chmodSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, realpathSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { basename, dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { parseRules, rulesVersion, sheetPath, sheetRel } from './collab-rules.mjs';
import { isMain } from './is-main.mjs';

export const pointerName = 'luat-dang-hieu-luc.md';
const oldMark = /\[OLD\b|SUPERSEDED|RETIRED/i;

export function readStore(dir) {
  const entries = [];
  for (const file of readdirSync(dir).filter(f => f.endsWith('.md') && f !== 'MEMORY.md').sort()) {
    if (!lstatSync(join(dir, file)).isFile()) continue;
    const text = readFileSync(join(dir, file), 'utf8');
    const fm = /^---\n([\s\S]*?)\n---\n?/.exec(text);
    const front = fm ? fm[1] : '';
    const body = fm ? text.slice(fm[0].length) : text;
    const field = k => new RegExp(`^${k}:\\s*(.*)$`, 'm').exec(front)?.[1]?.replace(/^"|"$/g, '') ?? '';
    entries.push({ file, slug: file.replace(/\.md$/, ''), name: field('name'), description: field('description'), front, body, text });
  }
  const indexPath = join(dir, 'MEMORY.md');
  const index = existsSync(indexPath) && lstatSync(indexPath).isFile() ? readFileSync(indexPath, 'utf8') : '';
  return { entries, index };
}

// Statements that contradict the sheet's numbers. A line that itself says the value is old
// ("old", "cũ", "replaces", "superseded", "→") is history, not a claim.
const historyLine = /\b(old|OLD|retired|superseded|replaces|was|then|drop|dropped|no longer)\b|cũ|thay\s|bỏ|→|->/i;
// Codex r1 on #618: a time range ("08:00 → 23:59") is not replacement notation; only the arrows left
// after time ranges are removed mark a line as history.
const timeRange = /\b[0-2]?\d:[0-5]\d\s*(?:→|->)\s*[0-2]?\d:[0-5]\d\b/g;
export function contradictions(text, facts) {
  const out = [];
  for (const line of text.split('\n')) {
    if (historyLine.test(line.replace(timeRange, ' '))) continue;
    for (const m of line.matchAll(/(?:codex[^.\n]{0,40}?(?:cap|trần)|(?:cap|trần)[^.\n]{0,20}codex)[^.\n\d]{0,25}(\d{2,3})|(\d{2,3})\s*(?:codex runs|lượt codex)/gi)) {
      const n = Number(m[1] ?? m[2]);
      if (n !== facts.codexDailyCap) out.push({ rule: 'R8', says: String(n), sheet: String(facts.codexDailyCap) });
    }
    for (const m of line.matchAll(/(?:stop|stops|dừng|ngừng|không bắt đầu|no new work)[^.\n]{0,30}?\b([0-2]\d:[0-5]\d)/gi)) {
      if (![facts.lastStartAt, facts.cutoffAt].includes(m[1])) out.push({ rule: 'R9', says: m[1], sheet: `${facts.lastStartAt}/${facts.cutoffAt}` });
    }
    // A loop window that starts at another time than the plan (first review of a real proposal,
    // 16.11: an entry said "08:00–23:59" after the plan moved to 06:50).
    for (const m of line.matchAll(/\b([0-2]\d:[0-5]\d)\s*(?:–|-|→|to|tới|đến)\s*23:59/gi)) {
      if (m[1] !== facts.planOpensAt) out.push({ rule: 'R9', says: `${m[1]}–23:59`, sheet: `${facts.planOpensAt}–${facts.cutoffAt}` });
    }
    for (const slot of facts.retiredReportSlots ?? []) {
      if (new RegExp(`(report|báo cáo)[^.\\n]{0,30}${slot}|${slot}[^.\\n]{0,15}(report|báo cáo)`, 'i').test(line)) out.push({ rule: 'R5', says: slot, sheet: facts.reportSlots.join('/') });
    }
  }
  return out;
}

export const hash = text => createHash('sha256').update(text).digest('hex');
const words = text => new Set((text.toLowerCase().match(/[\p{L}\d]{4,}/gu) ?? []));
export function similarity(a, b) {
  const x = words(a);
  const y = words(b);
  let both = 0;
  for (const w of x) if (y.has(w)) both += 1;
  return both / Math.max(1, x.size + y.size - both);
}

// Rule ids linked from the pointer entry: a line "- R3: [[slug]] …" maps R3 to each linked slug.
export function ruleLinks(store) {
  const map = new Map();
  const pointer = store.entries.find(e => e.file === pointerName);
  if (!pointer) return map;
  for (const line of pointer.body.split('\n')) {
    const ids = line.match(/^\s*-\s*((?:R\d+)(?:\/R\d+)*)\s*:/)?.[1]?.split('/') ?? [];
    for (const [, slug] of line.matchAll(/\[\[([\w.-]+)\]\]/g)) for (const id of ids) map.set(slug, [...(map.get(slug) ?? []), id]);
  }
  return map;
}

export function propose(store, sheet, { date, duplicateAt = 0.35 } = {}) {
  const { rows, facts } = parseRules(sheet);
  const version = rulesVersion(sheet);
  const ruleIds = new Set(rows.map(r => r.id));
  const links = ruleLinks(store);
  const indexLines = store.index.split('\n');
  const byFile = new Map(indexLines.map((l, i) => [/\]\(([^)]+\.md)\)/.exec(l)?.[1], i]).filter(([f]) => f));
  const changes = { stale: [], duplicates: [], rulesChecked: [], indexAdded: [], indexMissingFile: [] };
  const files = new Map(store.entries.map(e => [e.file, e.text]));
  const index = [...indexLines];

  for (const e of store.entries) {
    if (e.file === pointerName) continue;
    const at = byFile.get(e.file);
    const marked = oldMark.test(e.description) || (at !== undefined && oldMark.test(index[at]));
    const bad = contradictions(`${e.description}\n${e.body}`, facts);
    const rule = bad[0]?.rule;
    if (bad.length && !marked) {
      changes.stale.push({ file: e.file, rules: [...new Set(bad.map(b => b.rule))], says: bad.map(b => `${b.rule}: ${b.says} ≠ ${b.sheet}`) });
      if (at !== undefined) index[at] = index[at].replace(/^(- \[[^\]]*)\]/, `$1 [OLD → ${rule}]]`);
    }
    const ids = (links.get(e.slug) ?? []).filter(id => ruleIds.has(id));
    if (ids.length && !bad.length && !marked) {
      // Inside the existing `metadata:` block (the memory format has name, description, metadata).
      const note = `  rules-checked: "${date} ${sheetRel}@${version} (${ids.join(', ')}; chỉ kiểm Id và số)"`;
      const text = files.get(e.file);
      const next = /^\s+rules-checked:.*$/m.test(e.front)
        ? text.replace(/^\s+rules-checked:.*$/m, note)
        : /^metadata:\s*$/m.test(e.front)
          ? text.replace(/^metadata:\s*$/m, `metadata:\n${note}`)
          : text.replace(/^(---\n[\s\S]*?)\n---/, `$1\nmetadata:\n${note}\n---`);
      if (next !== text) { files.set(e.file, next); changes.rulesChecked.push({ file: e.file, rules: ids }); }
    }
    if (at === undefined) {
      // Codex r1 on #618: a stale entry joins the index with its warning, never as a plain link.
      const mark = bad.length && !marked ? ` [OLD → ${rule}]` : '';
      index.push(`- [${e.name || e.slug}${mark}](${e.file}) — ${e.description.slice(0, 140)}`);
      changes.indexAdded.push(e.file);
    }
  }
  for (const [file] of byFile) if (!files.has(file) && file !== 'MEMORY.md') changes.indexMissingFile.push(file);
  const list = store.entries.filter(e => e.file !== pointerName);
  for (let i = 0; i < list.length; i += 1) {
    for (let j = i + 1; j < list.length; j += 1) {
      const s = similarity(list[i].body, list[j].body);
      if (s >= duplicateAt) changes.duplicates.push({ files: [list[i].file, list[j].file], similarity: Math.round(s * 100) / 100 });
    }
  }
  return { files, index: index.join('\n'), changes, version };
}

// Counts and rule ids only: this file may be quoted in the owner's report.
export function summarize({ changes, version }, date) {
  return {
    date, sheetVersion: version,
    stale: changes.stale.length, staleRules: [...new Set(changes.stale.flatMap(s => s.rules))].sort(),
    duplicates: changes.duplicates.length, rulesChecked: changes.rulesChecked.length,
    indexAdded: changes.indexAdded.length, indexMissingFile: changes.indexMissingFile.length,
  };
}

const writePrivate = (path, text) => { writeFileSync(path, text, { mode: 0o600 }); chmodSync(path, 0o600); };
const mkdirPrivate = path => { mkdirSync(path, { recursive: true, mode: 0o700 }); chmodSync(path, 0o700); };

// Codex r1 on #618 (P1): nothing is deleted unless it is provably a proposal this script wrote. A
// proposal folder is named YYYY-MM-DD and holds a manifest.json with this kind; the dream root and the
// memory folder never overlap in either direction.
export const proposalKind = 'la-lanh-memory-dream';
const dated = /^\d{4}-\d{2}-\d{2}$/;
function ownedProposal(path) {
  try {
    if (!lstatSync(path).isDirectory()) return false;
    return JSON.parse(readFileSync(join(path, 'manifest.json'), 'utf8')).kind === proposalKind;
  } catch { return false; }
}
// The real path of a folder that may not exist yet: its nearest existing parent, resolved, plus the rest.
function canonical(path) {
  const parts = [];
  let at = resolve(path);
  while (!existsSync(at)) { parts.unshift(basename(at)); const up = dirname(at); if (up === at) break; at = up; }
  return join(realpathSync(at), ...parts);
}
const within = (inner, outer) => { const rel = relative(outer, inner); return rel === '' || (!rel.startsWith('..') && !isAbsolute(rel)); };
export function overlaps(a, b) { const x = canonical(a); const y = canonical(b); return within(x, y) || within(y, x); }

// Proposals older than keepDays under the dream root are removed: only dated folders this script wrote,
// never the memory folder or anything holding it.
export function prune(root, today, keepDays = 14, { memory = null } = {}) {
  if (!existsSync(root)) return [];
  const cut = Date.parse(`${today}T00:00:00Z`) - keepDays * 86400000;
  const gone = [];
  for (const name of readdirSync(root)) {
    if (!dated.test(name) || Date.parse(`${name}T00:00:00Z`) >= cut) continue;
    const path = join(root, name);
    if (!ownedProposal(path) || (memory && overlaps(path, memory))) continue;
    rmSync(path, { recursive: true, force: true });
    gone.push(name);
  }
  return gone;
}

export function dream({ memory, out, sheet = readFileSync(sheetPath(), 'utf8'), date = new Date().toISOString().slice(0, 10) }) {
  if (!dated.test(String(date))) throw new Error('date must be YYYY-MM-DD');
  // Dated names only (Codex r1 P2): every proposal expires through prune.
  if (!dated.test(basename(resolve(out)))) throw new Error('the proposal folder must be named YYYY-MM-DD');
  if (overlaps(memory, out) || overlaps(memory, dirname(resolve(out)))) throw new Error('the proposal folder must be outside the memory folder, and the memory folder outside the dream root');
  if (existsSync(out) && !ownedProposal(out) && readdirSync(out).length) throw new Error('the proposal folder exists and is not a proposal of this script');
  const store = readStore(memory);
  const result = propose(store, sheet, { date });
  rmSync(out, { recursive: true, force: true });
  mkdirPrivate(dirname(out));
  mkdirPrivate(join(out, 'memory'));
  mkdirPrivate(join(out, 'before'));
  const sources = {};
  for (const e of store.entries) { writePrivate(join(out, 'before', e.file), e.text); sources[e.file] = hash(e.text); }
  writePrivate(join(out, 'before', 'MEMORY.md'), store.index);
  sources['MEMORY.md'] = hash(store.index);
  const proposed = new Map(result.files);
  proposed.set('MEMORY.md', result.index);
  const touched = [];
  for (const [file, text] of proposed) {
    writePrivate(join(out, 'memory', file), text);
    if (text !== (file === 'MEMORY.md' ? store.index : store.entries.find(e => e.file === file)?.text)) touched.push(file);
  }
  let patch = '';
  try { execFileSync('/usr/bin/diff', ['-ru', 'before', 'memory'], { cwd: out, encoding: 'utf8' }); } catch (error) { patch = String(error.stdout ?? ''); }
  writePrivate(join(out, 'diff.patch'), patch);
  rmSync(join(out, 'before'), { recursive: true, force: true });
  const summary = summarize(result, date);
  const manifest = { kind: proposalKind, date, sheetVersion: result.version, touched: touched.sort(), sources: Object.fromEntries(touched.map(f => [f, sources[f]])), proposed: Object.fromEntries(touched.map(f => [f, hash(proposed.get(f))])) };
  writePrivate(join(out, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  writePrivate(join(out, 'changes.json'), `${JSON.stringify(result.changes, null, 2)}\n`);
  writePrivate(join(out, 'summary.json'), `${JSON.stringify(summary, null, 2)}\n`);
  prune(dirname(out), date, 14, { memory });
  return summary;
}

// Applies only the accepted files, and only when neither the source file nor the rules sheet changed
// since the proposal (no blind copy of the whole proposed store). Returns what was applied or refused.
export function apply({ out, memory, accept, sheet = readFileSync(sheetPath(), 'utf8') }) {
  const manifest = JSON.parse(readFileSync(join(out, 'manifest.json'), 'utf8'));
  const result = { applied: [], refused: [] };
  if (rulesVersion(sheet) !== manifest.sheetVersion) {
    result.refused.push(...accept.map(file => ({ file, why: 'bảng luật đã đổi sau đề xuất' })));
    return result;
  }
  for (const file of accept) {
    const why = file === pointerName ? 'không sửa mục trỏ luật' : basename(file) !== file ? 'tên file không hợp lệ' : !manifest.touched.includes(file) ? 'không có trong đề xuất' : null;
    if (why) { result.refused.push({ file, why }); continue; }
    const target = join(memory, file);
    let current = '';
    try { current = lstatSync(target).isFile() ? readFileSync(target, 'utf8') : null; } catch { current = file === 'MEMORY.md' ? null : ''; }
    if (current === null || hash(current ?? '') !== manifest.sources[file]) { result.refused.push({ file, why: 'file gốc đã đổi sau đề xuất' }); continue; }
    const next = readFileSync(join(out, 'memory', file), 'utf8');
    if (hash(next) !== manifest.proposed[file]) { result.refused.push({ file, why: 'bản đề xuất đã bị sửa' }); continue; }
    const mode = existsSync(target) ? statSync(target).mode & 0o777 : 0o600;
    const tmp = `${target}.dream-tmp`;
    writeFileSync(tmp, next, { mode });
    renameSync(tmp, target);
    result.applied.push(file);
  }
  return result;
}

// "Trí nhớ đổi gì" for the 07:00 report, from summary.json.
export function reportLine(s) {
  if (!s) return 'Trí nhớ: đêm qua chưa chạy dọn.';
  return `Trí nhớ đổi gì: đề xuất đánh dấu ${s.stale} mục cũ${s.staleRules.length ? ` (${s.staleRules.join(', ')})` : ''}, ${s.duplicates} cặp trùng chờ gộp, ${s.rulesChecked} mục khớp Id và số với bảng luật, ${s.indexAdded} mục thêm vào chỉ mục.`;
}

if (isMain(import.meta.url)) {
  const arg = k => { const i = process.argv.indexOf(k); return i > 0 ? process.argv[i + 1] : undefined; };
  const memory = arg('--memory');
  const out = arg('--out') ?? arg('--apply');
  if (!memory || !out) { process.stderr.write('Usage: node scripts/collab-memory-dream.mjs --memory <dir> --out <dir> [--date YYYY-MM-DD] [--sheet <file>] | --apply <out> --memory <dir> --accept a.md,MEMORY.md\n'); process.exit(2); }
  const sheet = readFileSync(arg('--sheet') ?? sheetPath(), 'utf8');
  if (arg('--apply')) {
    const r = apply({ out, memory, accept: String(arg('--accept') ?? '').split(',').filter(Boolean), sheet });
    console.log(JSON.stringify({ applied: r.applied.length, refused: r.refused.map(x => x.why) }));
    process.exit(r.refused.length ? 1 : 0);
  }
  const summary = dream({ memory, out, sheet, date: arg('--date') });
  console.log(JSON.stringify(summary));
  console.log(reportLine(summary));
}
