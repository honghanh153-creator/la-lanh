// Anti (Antigravity) is review-only (three-agent dispatch 28.11.2026, part F, #948 AC6).
// Anti never writes to a checkout. What it may hand back is a bundle of JSONL events; the trusted
// host checks the bundle and, only inside an isolated fixture for now, applies a text patch.
// - Events: only `message`, `tool_call` (read-only tools) and `patch`, each with fixed fields.
//   Any unknown event type, tool, field or malformed line refuses the whole bundle.
// - Patch: `*** Edit: <path>` then FIND/REPLACE blocks. Each FIND must occur exactly once in the
//   file. Every file is computed in memory first; one failure writes nothing (all or nothing).
// - Paths: repo-relative, inside an explicit scope, never `.git`, `.github`, `.claude`, `.env*`,
//   `node_modules` or the owner rules file; no symlink anywhere on the path.
// - `antiWrites` stays false: applyPatch refuses any root outside the OS temp dir. Turning it on
//   needs its own PR with Codex approval after the fixture path has run (R1, R16).
// - What goes to Anti (publicPayload): tracked repo files only, with no home paths, private state
//   paths, emails or secret-like strings (R14). A refusal names the file and the kind, never the
//   matched text.
import { execFileSync } from 'node:child_process';
import { existsSync, lstatSync, readFileSync, realpathSync, renameSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, join, sep } from 'node:path';
import { clean, stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const antiWrites = false;
export const antiRole = 'review';
export const eventFields = {
  message: ['type', 'text'],
  tool_call: ['type', 'name', 'args'],
  patch: ['type', 'text'],
};
export const readTools = { read_file: ['path'], list_dir: ['path'], grep: ['pattern', 'path'] };
export const limits = { events: 500, lineChars: 100000, patchChars: 200000, files: 20 };
export const deniedFirst = ['.git', '.github', '.claude'];
export const deniedExact = ['docs/operations/luat-dang-hieu-luc.md'];

const isPlain = v => v !== null && typeof v === 'object' && !Array.isArray(v);

// Reasons a repo-relative path is unsafe; [] when it is fine.
export function pathReasons(p) {
  if (typeof p !== 'string' || !p.length || p.length > 300) return ['đường dẫn rỗng hoặc quá dài'];
  const shown = clean(p, 80);
  const out = [];
  if (/[\u0000-\u001f\u007f\\]/.test(p)) out.push(`${shown}: có ký tự điều khiển hoặc dấu \\`);
  if (p.startsWith('/') || p.startsWith('~') || /^[A-Za-z]:/.test(p)) out.push(`${shown}: đường dẫn tuyệt đối`);
  const segs = p.split('/');
  if (segs.some(s => s === '' || s === '.' || s === '..')) out.push(`${shown}: có đoạn rỗng, . hoặc ..`);
  if (deniedFirst.includes(segs[0]) || segs.includes('.git') || segs.includes('node_modules')) out.push(`${shown}: thư mục bị cấm`);
  if (segs.at(-1).startsWith('.env')) out.push(`${shown}: file .env bị cấm`);
  if (deniedExact.includes(p)) out.push(`${shown}: file luật của owner chỉ đổi bằng PR riêng`);
  return out;
}

// A scope entry is a file or a directory (`dir/`). An empty scope allows nothing.
export function inScope(p, scope = []) {
  return scope.some(s => (s.endsWith('/') ? p.startsWith(s) : p === s));
}

function argReasons(name, args, at) {
  const want = readTools[name];
  if (!want) return [`dòng ${at}: công cụ lạ ${clean(name, 40)}`];
  if (!isPlain(args)) return [`dòng ${at}: args phải là object`];
  const extra = Object.keys(args).filter(k => !want.includes(k));
  if (extra.length) return [`dòng ${at}: args lạ ${clean(extra.join(','), 60)}`];
  if (want.some(k => typeof args[k] !== 'string')) return [`dòng ${at}: thiếu args ${want.join(',')}`];
  // `.` is the repo root for list_dir/grep.
  return args.path === '.' ? [] : pathReasons(args.path).map(r => `dòng ${at}: ${r}`);
}

// Returns { ok, events, reasons }. Any reason refuses the whole bundle (events: []).
export function parseEvents(text) {
  const reasons = [];
  const events = [];
  const lines = String(text ?? '').split('\n');
  if (lines.filter(l => l.trim()).length > limits.events) return { ok: false, events: [], reasons: [`quá ${limits.events} sự kiện`] };
  lines.forEach((line, i) => {
    const at = i + 1;
    if (!line.trim()) return;
    if (line.length > limits.lineChars) { reasons.push(`dòng ${at}: quá dài`); return; }
    let e;
    try { e = JSON.parse(line); } catch { reasons.push(`dòng ${at}: không phải JSON`); return; }
    if (!isPlain(e)) { reasons.push(`dòng ${at}: không phải object`); return; }
    const fields = eventFields[e.type];
    if (!fields) { reasons.push(`dòng ${at}: loại sự kiện lạ ${clean(e.type, 40)}`); return; }
    const extra = Object.keys(e).filter(k => !fields.includes(k));
    if (extra.length) { reasons.push(`dòng ${at}: trường lạ ${clean(extra.join(','), 60)}`); return; }
    if (e.type === 'tool_call') { reasons.push(...argReasons(e.name, e.args, at)); }
    else if (typeof e.text !== 'string') { reasons.push(`dòng ${at}: thiếu text`); return; }
    events.push(e);
  });
  return reasons.length ? { ok: false, events: [], reasons } : { ok: true, events, reasons: [] };
}

const FIND = '<<<<<<< FIND';
const SPLIT = '=======';
const REPLACE = '>>>>>>> REPLACE';
const HEAD = '*** Edit: ';

// Returns { ok, files: [{ path, edits: [{ find, replace }] }], reasons }.
export function parsePatch(text) {
  const src = String(text ?? '');
  if (src.length > limits.patchChars) return { ok: false, files: [], reasons: ['patch quá dài'] };
  const reasons = [];
  const files = [];
  let file = null;
  let mode = 'out';
  let find = [];
  let repl = [];
  src.split('\n').forEach((line, i) => {
    const at = i + 1;
    if (mode === 'out') {
      if (line.startsWith(HEAD)) {
        const path = line.slice(HEAD.length);
        if (files.some(f => f.path === path)) reasons.push(`dòng ${at}: ${clean(path, 80)} lặp lại`);
        file = { path, edits: [] };
        files.push(file);
      } else if (line === FIND) {
        if (!file) reasons.push(`dòng ${at}: FIND trước *** Edit`);
        mode = 'find'; find = []; repl = [];
      } else if (line.trim()) reasons.push(`dòng ${at}: dòng lạ ngoài khối`);
    } else if (mode === 'find') {
      if (line === SPLIT) mode = 'replace';
      else if (line === FIND || line === REPLACE || line.startsWith(HEAD)) reasons.push(`dòng ${at}: khối FIND hỏng`);
      else find.push(line);
    } else if (line === REPLACE) {
      if (!find.length || !find.join('\n').length) reasons.push(`dòng ${at}: FIND rỗng`);
      file?.edits.push({ find: find.join('\n'), replace: repl.join('\n') });
      mode = 'out';
    } else if (line === FIND || line === SPLIT || line.startsWith(HEAD)) reasons.push(`dòng ${at}: khối REPLACE hỏng`);
    else repl.push(line);
  });
  if (mode !== 'out') reasons.push('khối chưa đóng');
  if (!files.length) reasons.push('patch không có file');
  if (files.length > limits.files) reasons.push(`quá ${limits.files} file`);
  for (const f of files) if (!f.edits.length) reasons.push(`${clean(f.path, 80)}: không có khối FIND/REPLACE`);
  return reasons.length ? { ok: false, files: [], reasons } : { ok: true, files, reasons: [] };
}

const realTmp = () => realpathSync(tmpdir());
// The only roots applyPatch accepts while antiWrites is false: a directory below the OS temp dir
// that is not inside a git checkout (a real checkout may also live under the temp dir, e.g. in CI).
export function isFixtureRoot(root) {
  try {
    const r = realpathSync(root);
    const t = realTmp();
    if (r === t || !r.startsWith(`${t}${sep}`)) return false;
    for (let d = r; d.startsWith(`${t}${sep}`); d = dirname(d)) if (existsSync(join(d, '.git'))) return false;
    return true;
  } catch { return false; }
}

const count = (hay, needle) => { let n = 0; let i = hay.indexOf(needle); while (i !== -1) { n++; i = hay.indexOf(needle, i + needle.length); } return n; };

// Checks the patch, then writes every file or none. Returns { ok, written, reasons }.
export function applyPatch({ root, patch, scope = [] }) {
  if (!antiWrites && !isFixtureRoot(root)) return { ok: false, written: [], reasons: ['Anti chỉ review: patch chỉ được áp trong fixture tạm'] };
  const parsed = typeof patch === 'string' ? parsePatch(patch) : patch;
  if (!parsed?.ok) return { ok: false, written: [], reasons: parsed?.reasons ?? ['patch không hợp lệ'] };
  if (!scope.length) return { ok: false, written: [], reasons: ['chưa có phạm vi file'] };
  const base = realpathSync(root);
  const reasons = [];
  const out = [];
  for (const f of parsed.files) {
    const bad = pathReasons(f.path);
    if (bad.length) { reasons.push(...bad); continue; }
    if (!inScope(f.path, scope)) { reasons.push(`${clean(f.path, 80)}: ngoài phạm vi`); continue; }
    const segs = f.path.split('/');
    let link = false;
    let missing = false;
    for (let k = 1; k <= segs.length; k++) {
      try { if (lstatSync(join(base, ...segs.slice(0, k))).isSymbolicLink()) link = true; } catch { missing = true; break; }
    }
    if (link) { reasons.push(`${clean(f.path, 80)}: có symlink trên đường dẫn`); continue; }
    const full = join(base, ...segs);
    if (missing || !lstatSync(full).isFile()) { reasons.push(`${clean(f.path, 80)}: không có file`); continue; }
    let text = readFileSync(full, 'utf8');
    let ok = true;
    f.edits.forEach((e, k) => {
      const n = count(text, e.find);
      if (n !== 1) { reasons.push(`${clean(f.path, 80)} khối ${k + 1}: FIND gặp ${n} lần, cần đúng 1`); ok = false; return; }
      text = text.replace(e.find, () => e.replace);
    });
    if (ok) out.push({ path: f.path, full, text });
  }
  if (reasons.length) return { ok: false, written: [], reasons };
  for (const o of out) {
    const tmp = join(dirname(o.full), `.anti-${process.pid}-${Date.now()}.tmp`);
    writeFileSync(tmp, o.text);
    renameSync(tmp, o.full);
  }
  return { ok: true, written: out.map(o => o.path), reasons: [] };
}

// Private markers that must never reach Anti, by kind. The matched text is never echoed.
const privateKinds = [
  ['đường dẫn máy riêng', text => [homedir(), stateDir].filter(p => p && p.length > 1).some(p => text.includes(p)) || /\/Users\/[A-Za-z0-9._-]+\//.test(text)],
  ['file riêng của agent', text => /~\/\.claude\b|\.claude\/projects\/|\.cache\/la-lanh-collab|side-session-notes/.test(text)],
  ['email', text => [...text.matchAll(/[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}/g)].some(m => !/^noreply@anthropic\.com$|@(example\.(com|org|net)|[A-Za-z0-9.-]+\.test)$/i.test(m[0]))],
  ['chuỗi giống secret', text => /\b(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b|-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(text)],
];

// items: [{ path, text }]; tracked: Set of `git ls-files` paths. Returns { ok, reasons }.
export function publicPayload(items, { tracked }) {
  const reasons = [];
  for (const it of items ?? []) {
    const bad = pathReasons(it?.path);
    if (bad.length) { reasons.push(...bad); continue; }
    const shown = clean(it.path, 80);
    if (!tracked?.has(it.path)) { reasons.push(`${shown}: không phải file đã track trong repo`); continue; }
    const text = String(it.text ?? '');
    for (const [kind, hit] of privateKinds) if (hit(text)) reasons.push(`${shown}: có ${kind}`);
  }
  if (!(items ?? []).length) reasons.push('không có gì để gửi');
  return { ok: !reasons.length, reasons };
}

export const trackedFiles = (cwd = process.cwd()) => new Set(execFileSync('git', ['ls-files', '-z'], { cwd, encoding: 'utf8' }).split('\0').filter(Boolean));

// Read-only check of a bundle Anti handed back: node scripts/collab-anti-patch.mjs --check <file.jsonl> --scope a/,b.mjs
if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const at = args.indexOf('--check');
  const scopeAt = args.indexOf('--scope');
  if (at < 0 || !args[at + 1]) {
    process.stderr.write('Usage: node scripts/collab-anti-patch.mjs --check <bundle.jsonl> [--scope dir/,file]\n');
    process.exit(2);
  }
  const scope = scopeAt >= 0 ? String(args[scopeAt + 1] ?? '').split(',').filter(Boolean) : [];
  const ev = parseEvents(readFileSync(args[at + 1], 'utf8'));
  const reasons = [...ev.reasons];
  const files = [];
  for (const e of ev.events.filter(x => x.type === 'patch')) {
    const p = parsePatch(e.text);
    reasons.push(...p.reasons);
    for (const f of p.files) {
      reasons.push(...pathReasons(f.path));
      if (!inScope(f.path, scope)) reasons.push(`${clean(f.path, 80)}: ngoài phạm vi`);
      files.push(f.path);
    }
  }
  process.stdout.write(`${JSON.stringify({ ok: !reasons.length, antiWrites, files, reasons })}\n`);
  process.exitCode = reasons.length ? 1 : 0;
}
