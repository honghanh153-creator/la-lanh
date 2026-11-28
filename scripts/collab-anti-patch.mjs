// Anti (Antigravity) is review-only (three-agent dispatch 28.11.2026, part F, #948 AC6).
// Anti never writes to a checkout. What it may hand back is a bundle of JSONL events; the trusted
// host checks the bundle and applies a text patch itself, only in a temp fixture or in an Anti job
// worktree the host made (collab-anti-job.mjs).
// - Events: only `message`, `tool_call` (read-only tools) and `patch`, each with fixed fields.
//   Any unknown event type, tool, field or malformed line refuses the whole bundle.
// - Patch: `*** Edit: <path>` then FIND/REPLACE blocks. Each FIND must occur exactly once in the
//   file. Every file is computed in memory, staged next to its target, rechecked, then renamed;
//   a failure part way puts every file back (all or nothing, Codex r1 on #955).
// - Paths (one policy for patches and snapshots): repo-relative, NFC, exact case on disk, inside an
//   explicit scope; never under `.git`, `.github`, `.claude`, `node_modules`, tool config or `.env*`
//   at any depth; never a loop gate file (scripts/collab-*, codex-*, lessons) or owner rules/process
//   docs. Duplicates are found on the NFC + lower-case key (macOS folds both). No symlink on the path.
// - What goes to Anti (buildSnapshot): the host reads tracked regular files from its own git index
//   with trusted git (no repo hooks, fsmonitor or user config), checks each blob hash, strict UTF-8
//   and byte limits, then publicPayload: no home paths, private state paths, emails or secret-like
//   strings (R14). A refusal names the file and the kind, never the matched text.
import { execFileSync } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync, renameSync, statSync, unlinkSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, join, sep } from 'node:path';
import { clean, stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const antiRole = 'review';
export const eventFields = {
  message: ['type', 'text'],
  tool_call: ['type', 'name', 'args'],
  patch: ['type', 'text'],
};
export const readTools = { read_file: ['path'], list_dir: ['path'], grep: ['pattern', 'path'] };
export const limits = { events: 500, lineChars: 100000, patchChars: 200000, files: 20 };
export const snapshotLimits = { files: 40, fileBytes: 60000, totalBytes: 180000 };
// Where the host keeps Anti job worktrees (one directory per job).
export const antiJobsDir = (home = stateDir) => join(home, 'anti-jobs');

// Trusted git (Codex r1 on #955, P2): a fixed binary, no repo hooks or fsmonitor, no global/system
// config, no inherited GIT_* variables, a fixed PATH. Repo-local config cannot start a program.
export const gitBin = '/usr/bin/git';
export const gitFlags = ['-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-c', 'core.untrackedCache=false', '-c', 'core.pager=cat', '-c', 'protocol.allow=never'];
export const gitEnv = () => ({ PATH: '/usr/bin:/bin', GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_NOSYSTEM: '1', GIT_OPTIONAL_LOCKS: '0', GIT_TERMINAL_PROMPT: '0', LC_ALL: 'C' });
export const trustedGit = (args, { cwd, timeout = 20000 } = {}) => execFileSync(gitBin, [...gitFlags, ...args], {
  cwd, env: gitEnv(), encoding: 'utf8', timeout, maxBuffer: 16 * 1024 * 1024, stdio: ['ignore', 'pipe', 'ignore'],
});

// NFC + lower case: the key two names share when the file system folds them (APFS does both).
export const canonPath = p => String(p).normalize('NFC').toLowerCase();
const deniedDirs = new Set(['.git', '.github', '.claude', '.codex', '.gemini', '.husky', '.vscode', '.idea', '.ssh', '.gnupg', '.aws', '.config', '.cache', 'node_modules']);
const deniedFiles = new Set(['package.json', 'pnpm-lock.yaml', 'pnpm-workspace.yaml', '.npmrc', '.yarnrc', '.yarnrc.yml', '.nvmrc', '.gitattributes', '.gitignore', '.gitmodules', '.mailmap', 'codeowners', 'agents.md', 'claude.md']);
const deniedTrees = [
  [/^scripts\/(collab-|codex-|private-guard|is-main\.|lessons\/)/, 'file cổng của vòng tự động'],
  [/^docs\/operations\//, 'luật và quy trình chỉ đổi bằng PR riêng'],
];

// Why a canonical path is protected (shared by patches and snapshots), or null.
export function protectedReason(p) {
  const c = canonPath(p);
  const segs = c.split('/');
  if (segs.some(s => deniedDirs.has(s))) return 'thư mục bị cấm';
  if (segs.some(s => s.startsWith('.env'))) return 'file .env bị cấm';
  if (deniedFiles.has(segs.at(-1))) return 'file cấu hình công cụ hoặc chỉ dẫn agent bị cấm';
  for (const [re, why] of deniedTrees) if (re.test(c)) return why;
  return null;
}

// Reasons a repo-relative path is unsafe; [] when it is fine.
export function pathReasons(p) {
  if (typeof p !== 'string' || !p.length || p.length > 300) return ['đường dẫn rỗng hoặc quá dài'];
  const shown = clean(p, 80);
  const out = [];
  if (/[\u0000-\u001f\u007f\\]/.test(p)) out.push(`${shown}: có ký tự điều khiển hoặc dấu \\`);
  if (p !== p.normalize('NFC')) out.push(`${shown}: tên file không ở dạng NFC`);
  if (p.startsWith('/') || p.startsWith('~') || /^[A-Za-z]:/.test(p)) out.push(`${shown}: đường dẫn tuyệt đối`);
  if (p.split('/').some(s => s === '' || s === '.' || s === '..')) out.push(`${shown}: có đoạn rỗng, . hoặc ..`);
  const why = protectedReason(p);
  if (why) out.push(`${shown}: ${why}`);
  return out;
}

// A scope entry is a file or a directory (`dir/`). An empty scope allows nothing.
export function inScope(p, scope = []) {
  const c = canonPath(p);
  return scope.some(s => { const k = canonPath(s); return k.endsWith('/') ? c.startsWith(k) : c === k; });
}

function argReasons(name, args, at) {
  // Own keys only (Anti r1 on #955): `constructor`/`toString` must be an unknown tool, not a crash.
  const want = typeof name === 'string' && Object.hasOwn(readTools, name) ? readTools[name] : null;
  if (!want) return [`dòng ${at}: công cụ lạ ${clean(name, 40)}`];
  if (!isPlain(args)) return [`dòng ${at}: args phải là object`];
  const extra = Object.keys(args).filter(k => !want.includes(k));
  if (extra.length) return [`dòng ${at}: args lạ ${clean(extra.join(','), 60)}`];
  if (want.some(k => typeof args[k] !== 'string')) return [`dòng ${at}: thiếu args ${want.join(',')}`];
  // `.` is the repo root for list_dir/grep.
  return args.path === '.' ? [] : pathReasons(args.path).map(r => `dòng ${at}: ${r}`);
}
const isPlain = v => v !== null && typeof v === 'object' && !Array.isArray(v);

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
    const fields = typeof e.type === 'string' && Object.hasOwn(eventFields, e.type) ? eventFields[e.type] : null;
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
        // One destination, whatever its case or Unicode form (Codex r1 on #955).
        if (files.some(f => canonPath(f.path) === canonPath(path))) reasons.push(`dòng ${at}: ${clean(path, 80)} lặp lại`);
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

const real = p => { try { return realpathSync(p); } catch { return null; } };
const inside = (p, dir) => Boolean(p && dir) && p.startsWith(`${dir}${sep}`);
// A directory below the OS temp dir that is not inside a git checkout (a real checkout may also
// live under the temp dir, e.g. in CI).
export function isFixtureRoot(root) {
  const r = real(root);
  const t = real(tmpdir());
  if (!r || !inside(r, t)) return false;
  for (let d = r; inside(d, t); d = dirname(d)) if (existsSync(join(d, '.git'))) return false;
  return true;
}
// A job worktree the host made: a direct child of the Anti jobs directory.
export function isJobRoot(root, home = stateDir) {
  const r = real(root);
  const jobs = real(antiJobsDir(home));
  return Boolean(r && jobs && dirname(r) === jobs && existsSync(join(r, '.git')));
}

// Every segment must exist with exactly this name (no case/Unicode alias) and none may be a symlink.
function onDisk(base, path) {
  const segs = path.split('/');
  let dir = base;
  for (const s of segs) {
    let names;
    try { names = readdirSync(dir); } catch { return 'không có file'; }
    if (!names.includes(s)) return names.some(n => canonPath(n) === canonPath(s)) ? 'tên file khác chữ hoa/thường hoặc dạng Unicode' : 'không có file';
    dir = join(dir, s);
    if (lstatSync(dir).isSymbolicLink()) return 'có symlink trên đường dẫn';
  }
  return lstatSync(dir).isFile() ? null : 'không phải file thường';
}

// An empty needle never counts (Anti r1 on #955: it used to loop forever).
const count = (hay, needle) => { if (!needle) return 0; let n = 0; let i = hay.indexOf(needle); while (i !== -1) { n++; i = hay.indexOf(needle, i + needle.length); } return n; };
const sha256 = buf => createHash('sha256').update(buf).digest('hex');
export const fsIo = { readFileSync, writeFileSync, renameSync, unlinkSync };
const strict = new TextDecoder('utf-8', { fatal: true });

// Checks the patch, then writes every file or none. Returns { ok, written, reasons, rolledBack?, invalid? }.
// `invalid`: a failure part way could not be undone; the caller must never use this checkout again.
export function applyPatch({ root, patch, scope = [], home = stateDir, io = fsIo }) {
  if (!isFixtureRoot(root) && !isJobRoot(root, home)) return { ok: false, written: [], reasons: ['Anti chỉ review: máy chỉ áp patch trong fixture tạm hoặc worktree việc Anti do máy tạo'] };
  // Text only (Anti r1 on #955): a pre-parsed object skipped the FIND, path and size checks.
  if (typeof patch !== 'string') return { ok: false, written: [], reasons: ['patch phải là văn bản'] };
  const parsed = parsePatch(patch);
  if (!parsed?.ok) return { ok: false, written: [], reasons: parsed?.reasons ?? ['patch không hợp lệ'] };
  if (!scope.length) return { ok: false, written: [], reasons: ['chưa có phạm vi file'] };
  const base = realpathSync(root);
  const reasons = [];
  const out = [];
  for (const f of parsed.files) {
    const bad = pathReasons(f.path);
    if (bad.length) { reasons.push(...bad); continue; }
    const shown = clean(f.path, 80);
    if (!inScope(f.path, scope)) { reasons.push(`${shown}: ngoài phạm vi`); continue; }
    const why = onDisk(base, f.path);
    if (why) { reasons.push(`${shown}: ${why}`); continue; }
    const full = join(base, ...f.path.split('/'));
    const before = io.readFileSync(full);
    let text;
    try { text = strict.decode(before); } catch { reasons.push(`${shown}: không phải UTF-8 hợp lệ`); continue; }
    let ok = true;
    f.edits.forEach((e, k) => {
      const n = count(text, e.find);
      if (n !== 1) { reasons.push(`${shown} khối ${k + 1}: FIND gặp ${n} lần, cần đúng 1`); ok = false; return; }
      text = text.replace(e.find, () => e.replace);
    });
    if (ok) out.push({ path: f.path, full, text, before, hash: sha256(before), mode: statSync(full).mode & 0o777 });
  }
  if (reasons.length) return { ok: false, written: [], reasons };
  const tag = `${process.pid}-${randomBytes(6).toString('hex')}`;
  const staged = [];
  const drop = list => { for (const t of list) { try { io.unlinkSync(t); } catch { /* already gone */ } } };
  // 1. Stage every file under a fresh unique name; nothing is replaced yet.
  try {
    out.forEach((o, i) => { const t = join(dirname(o.full), `.anti-${tag}-${i}.tmp`); io.writeFileSync(t, o.text, { flag: 'wx', mode: o.mode }); staged.push(t); });
  } catch { drop(staged); return { ok: false, written: [], reasons: ['không ghi được file tạm; chưa đổi file nào'] }; }
  // 2. The files must still be what was checked.
  for (const o of out) {
    let now = null;
    try { now = sha256(io.readFileSync(o.full)); } catch { now = null; }
    if (now !== o.hash) { drop(staged); return { ok: false, written: [], reasons: [`${clean(o.path, 80)}: file đổi trong lúc áp; chưa đổi file nào`] }; }
  }
  // 3. Replace; on a failure put back every file already replaced.
  const done = [];
  try { out.forEach((o, i) => { io.renameSync(staged[i], o.full); done.push(i); }); }
  catch {
    let restored = true;
    for (const i of done.reverse()) {
      const t = join(dirname(out[i].full), `.anti-${tag}-${i}.back`);
      try { io.writeFileSync(t, out[i].before, { flag: 'wx', mode: out[i].mode }); io.renameSync(t, out[i].full); }
      catch { restored = false; drop([t]); }
    }
    drop(staged.filter((_, i) => !done.includes(i)));
    return restored
      ? { ok: false, written: [], reasons: ['ghi giữa chừng bị lỗi; đã trả mọi file về như cũ'], rolledBack: true }
      : { ok: false, written: [], reasons: ['ghi giữa chừng bị lỗi và không trả lại được; checkout này không được dùng nữa'], rolledBack: false, invalid: true };
  }
  return { ok: true, written: out.map(o => o.path), reasons: [] };
}

// Private markers that must never reach Anti, by kind. The matched text is never echoed.
const privateKinds = [
  ['đường dẫn máy riêng', text => [homedir(), stateDir].filter(p => p && p.length > 1).some(p => text.includes(p)) || /\/Users\/[A-Za-z0-9._-]+\/|\/home\/[A-Za-z0-9._-]+\/|[A-Za-z]:\\Users\\[^\\\s]+/i.test(text)],
  ['file riêng của agent', text => /~\/\.(claude|codex|gemini)\b|\.claude\/projects\/|\.codex\/(sessions|auth)|\.gemini\/|\.cache\/la-lanh-collab|side-session-notes/.test(text)],
  ['email', text => [...text.matchAll(/[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}/g)].some(m => !/^noreply@anthropic\.com$|@(example\.(com|org|net)|[A-Za-z0-9.-]+\.(test|invalid))$/i.test(m[0]))],
  ['chuỗi giống secret', text => /\b(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{35}|xox[abprs]-[A-Za-z0-9-]{10,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b|-----BEGIN [A-Z ]*PRIVATE KEY-----/.test(text)],
  ['URL có mật khẩu', text => /\b[a-z][a-z0-9+.-]*:\/\/[^\s/:@]+:[^\s/@]+@/i.test(text)],
];
export const privateReasons = (text, shown) => privateKinds.filter(([, hit]) => hit(String(text ?? ''))).map(([kind]) => `${shown}: có ${kind}`);

// items: [{ path, text }]; tracked: Set of `git ls-files` paths. Returns { ok, reasons }.
export function publicPayload(items, { tracked } = {}) {
  const reasons = [];
  for (const it of items ?? []) {
    const bad = pathReasons(it?.path);
    if (bad.length) { reasons.push(...bad); continue; }
    const shown = clean(it.path, 80);
    if (!tracked?.has(it.path)) { reasons.push(`${shown}: không phải file đã track trong repo`); continue; }
    reasons.push(...privateReasons(it.text, shown));
  }
  if (!(items ?? []).length) reasons.push('không có gì để gửi');
  return { ok: !reasons.length, reasons };
}

// Index entries (`git ls-files -s -z`): mode, blob id, stage, path.
export function indexEntries(root, git = trustedGit) {
  return git(['ls-files', '-s', '-z'], { cwd: root }).split('\0').filter(Boolean).map(line => {
    const m = /^(\d{6}) ([0-9a-f]{40}|[0-9a-f]{64}) (\d)\t([^]+)$/.exec(line);
    return m ? { mode: m[1], blob: m[2], stage: m[3], path: m[4] } : { bad: true, path: clean(line, 80) };
  });
}
export const trackedFiles = (cwd = process.cwd(), git = trustedGit) => new Set(indexEntries(cwd, git).map(e => e.path));
const blobId = (buf, len) => createHash(len === 64 ? 'sha256' : 'sha1').update(`blob ${buf.length}\0`).update(buf).digest('hex');

// The host builds what Anti may read (Codex r1 on #955, P2): tracked regular files inside `allow`,
// read from the worktree only when they equal the indexed blob. Returns { ok, items, reasons }.
export function buildSnapshot({ root, allow = [], git = trustedGit, max = snapshotLimits }) {
  const base = real(root);
  if (!base) return { ok: false, items: [], reasons: ['không có thư mục'] };
  if (!allow.length) return { ok: false, items: [], reasons: ['chưa có phạm vi file'] };
  let entries;
  try {
    if (real(git(['rev-parse', '--show-toplevel'], { cwd: base }).trim()) !== base) return { ok: false, items: [], reasons: ['không phải gốc checkout'] };
    entries = indexEntries(base, git);
  } catch { return { ok: false, items: [], reasons: ['không đọc được git index'] }; }
  const reasons = [];
  const items = [];
  const picked = entries.filter(e => inScope(e.path, allow));
  if (!picked.length) return { ok: false, items: [], reasons: ['phạm vi không có file đã track'] };
  if (picked.length > max.files) return { ok: false, items: [], reasons: [`quá ${max.files} file trong phạm vi`] };
  let total = 0;
  for (const e of picked) {
    const shown = clean(e.path, 80);
    if (e.bad) { reasons.push(`${shown}: dòng index lạ`); continue; }
    const bad = pathReasons(e.path);
    if (bad.length) { reasons.push(...bad); continue; }
    if (e.stage !== '0') { reasons.push(`${shown}: đang có conflict`); continue; }
    if (e.mode !== '100644' && e.mode !== '100755') { reasons.push(`${shown}: không phải file thường (symlink hoặc submodule)`); continue; }
    const why = onDisk(base, e.path);
    if (why) { reasons.push(`${shown}: ${why}`); continue; }
    const buf = readFileSync(join(base, ...e.path.split('/')));
    if (buf.length > max.fileBytes) { reasons.push(`${shown}: quá ${max.fileBytes} byte`); continue; }
    total += buf.length;
    if (blobId(buf, e.blob.length) !== e.blob) { reasons.push(`${shown}: khác bản trong git index`); continue; }
    if (buf.includes(0)) { reasons.push(`${shown}: file nhị phân`); continue; }
    let text;
    try { text = strict.decode(buf); } catch { reasons.push(`${shown}: không phải UTF-8 hợp lệ`); continue; }
    items.push({ path: e.path, text });
  }
  if (total > max.totalBytes) reasons.push(`tổng quá ${max.totalBytes} byte`);
  if (!reasons.length) reasons.push(...publicPayload(items, { tracked: new Set(entries.map(e => e.path)) }).reasons);
  return reasons.length ? { ok: false, items: [], reasons } : { ok: true, items, reasons: [] };
}

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
  process.stdout.write(`${JSON.stringify({ ok: !reasons.length, antiRole, files, reasons })}\n`);
  process.exitCode = reasons.length ? 1 : 0;
}
