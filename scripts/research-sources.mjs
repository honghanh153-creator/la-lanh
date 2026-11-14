// Every research conclusion points to a source that was read (lesson L09; agreement 12.11 item G:
// "Kết luận không được nguồn hỗ trợ bị bác dù có nhiều URL").
// A research file (docs/research/*.md) states its conclusions under "## Kết luận", each with at
// least one key [S1]; every key is listed under "## Nguồn đã đọc" as
//   - S1: <https URL or a path in this repo> — đọc: <the part read: section, page, table, quote>
// Conclusions with no source go under "## Bị bác / chưa có nguồn" and are not conclusions.
// Plan critiqued by Codex on 14.11 (SỬA), points taken:
// - no date written in the file exempts it: every new research file is checked in full; in an
//   older file every added or changed line is checked (it must sit under "## Kết luận" with a key,
//   or in the source or rejected sections);
// - CI runs this on every PR (the pr-check scope job), not only the loop preflight;
// - paragraphs count as conclusions too; a source must be a real URL or an existing repo path with
//   a specific place read;
// - this checks structure only. Whether a source supports its conclusion is the reviewer's job
//   (codex-review-prompt.md); nothing here reports a source as "verified".
// Usage: node scripts/research-sources.mjs --base <sha> [--head <sha>]   |   --file <path>
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

export const researchDir = 'docs/research/';
const CONCLUSIONS = /^##\s+Kết luận\s*$/u;
const SOURCES = /^##\s+Nguồn đã đọc\s*$/u;
const REJECTED = /^##\s+Bị bác/u;
const KEY = /\[S(\d+)\]/g;

// Sections by line: the name of the "##" section each line belongs to.
function sectionsOf(lines) {
  let current = null;
  return lines.map(line => {
    const t = line.normalize('NFC').trim();
    if (/^##\s/.test(t)) { current = CONCLUSIONS.test(t) ? 'conclusions' : SOURCES.test(t) ? 'sources' : REJECTED.test(t) ? 'rejected' : 'other'; return 'heading'; }
    if (/^#\s/.test(t)) { current = null; return 'heading'; }
    return current;
  });
}

// Units of a conclusions section: a list item (with its continuation lines), a table row, or a
// paragraph. Table header and separator rows are not conclusions.
function units(lines, from, to) {
  const out = [];
  let open = null;
  const flush = () => { if (open) out.push(open); open = null; };
  const item = t => /^([-*+]|\d+[.)])\s/.test(t);
  for (let i = from; i < to; i += 1) {
    const raw = lines[i];
    const t = raw.trim();
    if (!t) { flush(); continue; }
    if (/^\|/.test(t)) {
      flush();
      const next = lines[i + 1]?.trim() ?? '';
      if (/^\|[\s:|-]+\|$/.test(t) || /^\|[\s:|-]+\|$/.test(next)) continue; // separator, or the header above it
      out.push({ line: i + 1, lines: [i + 1], text: t });
      continue;
    }
    if (item(t) || !open) { flush(); open = { line: i + 1, lines: [i + 1], text: t }; continue; }
    open.lines.push(i + 1);
    open.text += ` ${t}`;
  }
  flush();
  return out;
}

const keysIn = text => [...String(text).matchAll(KEY)].map(m => `S${m[1]}`);

// The sources list: key → { target, read, line }.
function sourcesOf(lines, section) {
  const map = new Map();
  lines.forEach((line, i) => {
    if (section[i] !== 'sources') return;
    const m = /^\s*[-*]\s*\**(S\d+)\**\s*:\s*(.+)$/u.exec(line.normalize('NFC'));
    if (!m) return;
    const [, key, rest] = m;
    const read = /—\s*đọc\s*:\s*(.+)$|-\s*đọc\s*:\s*(.+)$/u.exec(rest);
    const target = (read ? rest.slice(0, read.index) : rest).trim().replace(/^<|>$/g, '').replace(/^\[[^\]]*\]\((.*)\)$/, '$1');
    map.set(key, { target, read: (read?.[1] ?? read?.[2] ?? '').trim(), line: i + 1 });
  });
  return map;
}

const realTarget = (target, root) => {
  if (/^https?:\/\/[^\s/]+\.[^\s/]+\S*$/.test(target)) return true;
  if (/^(docs|apps|scripts|packages|vendor)\/\S+$/.test(target)) return existsSync(join(root, target.split('#')[0]));
  return false;
};

// Problems of one file. `added` (Set of 1-based line numbers) limits the check to those lines in an
// older file; null checks the whole file.
export function researchProblems(text, { path = 'file', added = null, root = process.cwd() } = {}) {
  const lines = String(text).split('\n');
  const section = sectionsOf(lines);
  const problems = [];
  const at = n => `${path}:${n}`;
  const sources = sourcesOf(lines, section);
  const whole = added === null;
  const hasConclusions = lines.some(l => CONCLUSIONS.test(l.normalize('NFC').trim()));
  if (whole && !hasConclusions) problems.push(`${path}: thiếu mục "## Kết luận"`);
  if (whole && !lines.some(l => SOURCES.test(l.normalize('NFC').trim()))) problems.push(`${path}: thiếu mục "## Nguồn đã đọc"`);
  // Conclusions: every unit needs a key that is listed.
  // Every "## Kết luận" section (a file may have more than one).
  for (let start = section.indexOf('conclusions'); start >= 0; start = section.indexOf('conclusions', start + 1)) {
    if (section[start - 1] === 'conclusions') continue;
    let end = start;
    while (end < lines.length && section[end] === 'conclusions') end += 1;
    for (const unit of units(lines, start, end)) {
      const span = unit.line;
      if (!whole && !unit.lines.some(n => added.has(n))) continue;
      const keys = keysIn(unit.text);
      if (!keys.length) { problems.push(`${at(span)}: kết luận không trỏ tới nguồn [S…] (nhiều URL không thay được nguồn đã đọc)`); continue; }
      for (const key of keys) if (!sources.has(key)) problems.push(`${at(span)}: ${key} không có trong "Nguồn đã đọc"`);
    }
  }
  // Sources: a real target and a specific place read.
  for (const [key, s] of sources) {
    if (!whole && !added.has(s.line)) continue;
    if (!realTarget(s.target, root)) problems.push(`${at(s.line)}: ${key} phải là URL https hoặc đường dẫn có thật trong repo`);
    if (s.read.length < 8) problems.push(`${at(s.line)}: ${key} thiếu "— đọc: <phần đã đọc>" cụ thể`);
  }
  // Older file: an added line outside conclusions, sources and rejected is a conclusion with no home.
  if (!whole) {
    for (const n of added) {
      const kind = section[n - 1];
      const t = (lines[n - 1] ?? '').trim();
      if (!t || kind === 'heading' || kind === 'conclusions' || kind === 'sources' || kind === 'rejected') continue;
      problems.push(`${at(n)}: dòng mới ở file nghiên cứu cũ phải nằm trong "## Kết luận" (có [S…]), "## Nguồn đã đọc" hoặc "## Bị bác / chưa có nguồn"`);
    }
  }
  return problems;
}

const git = (args, cwd) => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 }));

// Changed research files between base and head (merge base, so commits on the base branch after
// the branch point are not counted): added files in full, modified files by their added lines.
export function changedResearch({ base, head = 'HEAD', root = process.cwd(), run = git }) {
  const out = [];
  for (const row of run(['diff', '--name-status', '--no-renames', `${base}...${head}`, '--', researchDir], root).split('\n').filter(Boolean)) {
    const [status, path] = row.split('\t');
    if (!path?.endsWith('.md') || status === 'D') continue;
    const text = run(['show', `${head}:${path}`], root);
    if (status === 'A') { out.push({ path, text, added: null }); continue; }
    const added = new Set();
    for (const hunk of run(['diff', '-U0', `${base}...${head}`, '--', path], root).matchAll(/^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@/gm)) {
      const from = Number(hunk[1]);
      const count = hunk[2] === undefined ? 1 : Number(hunk[2]);
      for (let n = from; n < from + count; n += 1) added.add(n);
    }
    out.push({ path, text, added });
  }
  return out;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const flag = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
  const root = process.cwd();
  const files = flag('--file') ? [{ path: flag('--file'), text: readFileSync(flag('--file'), 'utf8'), added: null }]
    : flag('--base') ? changedResearch({ base: flag('--base'), head: flag('--head') ?? 'HEAD', root }) : null;
  if (!files) { process.stderr.write('Usage: research-sources.mjs --base <sha> [--head <sha>] | --file <path>\n'); process.exit(2); }
  const problems = files.flatMap(f => researchProblems(f.text, { path: f.path, added: f.added, root }));
  for (const p of problems) process.stdout.write(`${p}\n`);
  process.stdout.write(`research-sources: ${files.length} file, ${problems.length} lỗi\n`);
  process.exitCode = problems.length ? 1 : 0;
}
