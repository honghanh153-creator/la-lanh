// The register of workflow promises (owner 13.11.2026: "Claude khá hờ hững trong việc sửa workflow").
// Codex's audit that day found that none of the 12 workflow changes agreed on 12.11 had reached
// "done": lessons were written down, not turned into running checks. This file makes the promise
// itself checkable, so follow-through no longer depends on Claude's discipline:
// - every lesson has an owner, a due date and a status: one file per lesson in scripts/lessons/
//   (scripts/lessons/L65.json), plus the older lessons still in scripts/collab-lessons.json (below);
// - "done" needs a regression test that exists in a file CI runs (pnpm collab:test), a caller
//   that wires the fix into the loop, and the PR that closed it; the tick then confirms on
//   GitHub that the PR was merged into collab/integration with a Codex APPROVE (Claude cannot
//   close a lesson by editing the file);
// - an open lesson past its due date is reported as overdue in the board and the owner digest.
// Usage: node scripts/collab-lessons.mjs   (prints the summary; exit 1 if the register is invalid)
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { clean, integration, makeGh, readJson, repo, reviewState, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

const here = dirname(fileURLToPath(import.meta.url));
export const root = join(here, '..');
export const registerPath = join(here, 'collab-lessons.json');
// declined-owner (owner 14.11.2026, Codex SỬA): the owner chose not to build it. Not done and not
// open: it needs the date, the owner's reason and the risk that stays, and the report names it.
export const statuses = ['open', 'waiting-owner', 'declined-owner', 'done'];
const noDue = new Set(['waiting-owner', 'declined-owner']);
const isDate = s => /^\d{4}-\d{2}-\d{2}$/.test(s ?? '');

// One file per lesson (22.11.2026, L65). Every lesson PR appended to the end of collab-lessons.json,
// so each merged lesson put every other open lesson PR in conflict, and each resync cost a new check
// and review (#838, #843, #864, #872 and the #850 stack on 22.11). New lessons go in
// scripts/lessons/<id>.json, one object each. The old file stays readable while open PRs that append
// to it drain; its entries move to the folder in a later small PR. Both sources form one register:
// the same checks (shape, evidence, due date, Codex-confirmed close) run over all of it, and an id
// in both, or a file not named after its id, is a problem (`problems`), never silently merged.
export const lessonsDir = join(here, 'lessons');
const sourceOf = new WeakMap();
export const lessonSource = l => sourceOf.get(l) ?? 'collab-lessons.json';
export function readRegister(path = registerPath, dir = lessonsDir) {
  const reg = JSON.parse(readFileSync(path, 'utf8'));
  const files = existsSync(dir) ? readdirSync(dir).filter(f => f.endsWith('.json')).sort() : [];
  const extra = files.map(f => {
    let lesson;
    try { lesson = JSON.parse(readFileSync(join(dir, f), 'utf8')); } catch (error) { throw new Error(`lessons/${f}: ${error.message}`); }
    if (!lesson || typeof lesson !== 'object' || Array.isArray(lesson)) throw new Error(`lessons/${f}: must hold one lesson object`);
    sourceOf.set(lesson, `lessons/${f}`);
    return lesson;
  });
  return { ...reg, lessons: [...(reg.lessons ?? []), ...extra] };
}

// Test files that CI runs: a lesson's test must be one of them, or it never runs.
export function ciTestFiles(pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')), { base = root, scan = pyScan } = {}) {
  const files = new Set(String(pkg.scripts?.['collab:test'] ?? '').split(/\s+/).filter(f => f.endsWith('.test.mjs')));
  for (const f of playwrightCiFiles(pkg, { base })) files.add(f);
  for (const f of pytestCiFiles(pkg, { base, scan })) files.add(f);
  return files;
}

// #672 (Codex on #668): pytest config and markers are read with real parsers (tomllib, ast) in
// scripts/collab-pytest-scan.py, run with `python3 -I`. It needs Python 3.11+ (tomllib); the Mac's
// /usr/bin/python3 is 3.9, so the first interpreter that can import tomllib is used. No such
// interpreter means nothing can be proven: pytest files are not counted and every pytest lesson
// test is treated as skipped (fail closed), never as passing.
export const pytestScanScript = join(here, 'collab-pytest-scan.py');
const pythonCandidates = () => [process.env.LA_LANH_PYTHON, 'python3', 'python3.13', 'python3.12', 'python3.11',
  ...['python3.13', 'python3.12', 'python3.11'].map(p => join(homedir(), '.local', 'bin', p))].filter(Boolean);
let foundPython;
export function findPython(candidates = pythonCandidates()) {
  for (const py of candidates) {
    try { execFileSync(py, ['-I', '-c', 'import tomllib, ast'], { stdio: 'ignore', timeout: 10_000 }); return py; } catch {}
  }
  return null;
}
// One JSON answer from the scan script, or null when there is no usable Python or the scan fails.
export function pyScan(args, { python } = {}) {
  const py = python === undefined ? (foundPython === undefined ? (foundPython = findPython()) : foundPython) : python;
  if (!py) return null;
  try { return JSON.parse(execFileSync(py, ['-I', pytestScanScript, ...args], { encoding: 'utf8', timeout: 20_000, stdio: ['ignore', 'pipe', 'ignore'] })); } catch { return null; }
}

// #661 (17.11.2026): a lesson test may be an API pytest, but only through the chain CI really runs:
// `pnpm check` runs `api:test`, which is exactly `uv run --directory apps/api pytest` (no path or
// -k filter), and apps/api/pyproject.toml collects `testpaths = ["tests"]` with no option or setting
// that drops tests (#667, #672: the full addopts value, string or array). Each `test_*.py` under
// apps/api/tests counts; a skipped test is caught in problems().
export function pytestCiFiles(pkg, { base = root, scan = pyScan } = {}) {
  const check = String(pkg.scripts?.check ?? '');
  const api = String(pkg.scripts?.['api:test'] ?? '').trim();
  if (!/\bpnpm api:test\b/.test(check) || api !== 'uv run --directory apps/api pytest' || !existsSync(join(base, 'apps/api/pyproject.toml'))) return [];
  if (scan(['config', join(base, 'apps/api')])?.ok !== true) return [];
  const found = [];
  const walk = dir => {
    for (const entry of readdirSync(join(base, dir), { withFileTypes: true })) {
      if (entry.isDirectory()) walk(`${dir}/${entry.name}`);
      else if (/^test_.*\.py$/.test(entry.name)) found.push(`${dir}/${entry.name}`);
    }
  };
  if (existsSync(join(base, 'apps/api/tests'))) walk('apps/api/tests');
  return found;
}

// L08 (Codex 14.11): a lesson test may be a Playwright spec, but only one CI really runs. The proof
// is the chain itself: `pnpm check` (CI pr-check) runs `web:e2e`, which runs the web package's
// `e2e` script, `playwright test`, whose config collects `*.spec.ts` from its testDir. Each spec
// in that directory counts; a skipped test inside it is caught in problems().
export const webConfig = 'apps/web/playwright.config.ts';
export function playwrightCiFiles(pkg, { base = root } = {}) {
  const check = String(pkg.scripts?.check ?? '');
  const e2e = String(pkg.scripts?.['web:e2e'] ?? '');
  const web = read(base, 'apps/web/package.json');
  const config = read(base, webConfig);
  if (!/\bpnpm web:e2e\b/.test(check) || !/--filter @la-lanh\/web e2e\b/.test(e2e) || !web || !config) return [];
  if (!/^playwright test$/.test(String(JSON.parse(web).scripts?.e2e ?? '').trim())) return [];
  if (/\btestMatch\b|\btestIgnore\b|\bgrep(Invert)?\b/.test(config)) return [];
  const dir = /testDir:\s*["']\.\/([\w/-]+)["']/.exec(config)?.[1];
  if (!dir) return [];
  const full = join(base, 'apps/web', dir);
  if (!existsSync(full)) return [];
  return readdirSync(full).filter(f => f.endsWith('.spec.ts')).map(f => `apps/web/${dir}/${f}`);
}
// A Playwright test that is skipped, marked fixme or focused never proves anything in CI.
const skipped = text => /\btest\.(skip|fixme|only)\s*\(|\btest\.describe\.(skip|fixme|only)\s*\(/.test(code(text));

const read = (base, file) => { const p = join(base, file); return existsSync(p) ? readFileSync(p, 'utf8') : null; };
// A test is found by its exact name in a test('…') call, not by any matching text.
const code = text => text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
const hasTest = (text, name) => [...code(text).matchAll(/\btest\(\s*(['"`])((?:\\.|(?!\1).)*)\1/g)].some(m => m[2].includes(name));
// A pytest test is found by its exact module-level function name (ast); a skip/skipif/xfail marker on
// it, a module `pytestmark` that skips (any assignment), or a pytest.skip/xfail/importorskip call
// means CI never proves it. No answer from the scan counts as "not found".
const pyTest = (file, name, scan) => (/^test_\w+$/.test(name) ? scan(['test', file, name]) : { exists: false, skipped: false });

// Offline problems: shape, and for "done" the evidence that exists in this checkout.
export function problems(register, { base = root, ciFiles = ciTestFiles(), scan = pyScan } = {}) {
  const out = [];
  const ids = new Map();
  for (const l of register.lessons ?? []) {
    const at = `lesson ${l?.id ?? '?'}`;
    if (!/^L\d{2,}$/.test(l?.id ?? '')) { out.push(`${at}: id must look like L01`); continue; }
    if (ids.has(l.id)) out.push(`${at}: duplicate id (${ids.get(l.id)} and ${lessonSource(l)})`);
    else ids.set(l.id, lessonSource(l));
    if (lessonSource(l).startsWith('lessons/') && lessonSource(l) !== `lessons/${l.id}.json`) out.push(`${at}: ${lessonSource(l)} must be named lessons/${l.id}.json`);
    if (!String(l.title ?? '').trim()) out.push(`${at}: no title`);
    if (!['claude', 'codex', 'owner'].includes(l.who)) out.push(`${at}: who must be claude, codex or owner`);
    if (!statuses.includes(l.status)) out.push(`${at}: status must be one of ${statuses.join(', ')}`);
    if (!noDue.has(l.status) && !isDate(l.due)) out.push(`${at}: due date YYYY-MM-DD required`);
    if (l.status === 'declined-owner') {
      if (!isDate(l.declined?.on)) out.push(`${at}: declined-owner needs declined.on YYYY-MM-DD`);
      if (!String(l.declined?.reason ?? '').trim()) out.push(`${at}: declined-owner needs the owner's reason`);
      if (!String(l.declined?.risk ?? '').trim()) out.push(`${at}: declined-owner needs the risk that stays`);
    }
    if (l.status !== 'done') continue;
    const testText = l.test?.file ? read(base, l.test.file) : null;
    if (!l.test?.file || !l.test?.name) out.push(`${at}: done without a regression test`);
    else if (testText === null) out.push(`${at}: test file ${l.test.file} does not exist`);
    else if (l.test.file.endsWith('.py')) {
      const py = pyTest(join(base, l.test.file), l.test.name, scan);
      if (!py) out.push(`${at}: ${l.test.file} could not be checked (no Python 3.11+ for the pytest scan), so it proves nothing`);
      else if (!py.exists) out.push(`${at}: no test named "${l.test.name}" in ${l.test.file}`);
      else if (!ciFiles.has(l.test.file)) out.push(`${at}: ${l.test.file} is not in pnpm collab:test, so CI never runs it`);
      else if (py.skipped) out.push(`${at}: ${l.test.name} in ${l.test.file} is skipped or xfail, so CI does not prove it`);
    } else if (!hasTest(testText, l.test.name)) out.push(`${at}: no test named "${l.test.name}" in ${l.test.file}`);
    else if (!ciFiles.has(l.test.file)) out.push(`${at}: ${l.test.file} is not in pnpm collab:test, so CI never runs it`);
    else if (l.test.file.endsWith('.spec.ts') && skipped(testText)) out.push(`${at}: ${l.test.file} skips, marks fixme or focuses a test, so CI does not run all of it`);
    const callerText = l.caller?.file ? read(base, l.caller.file) : null;
    if (!l.caller?.file || !l.caller?.contains) out.push(`${at}: done without a caller in the loop`);
    else if (callerText === null) out.push(`${at}: caller file ${l.caller.file} does not exist`);
    else if (!callerText.includes(l.caller.contains)) out.push(`${at}: ${l.caller.file} does not contain "${l.caller.contains}"`);
    if (!Number.isInteger(l.closedBy?.pr)) out.push(`${at}: done without the PR that closed it`);
  }
  return out;
}

// Online check, run by the tick: the closing PR is merged into integration and carries a trusted
// Codex APPROVE. Results are cached per lesson and PR, so each PR is read from GitHub once.
export const verifiedPath = join(stateDir, 'lessons-verified.json');
// Codex 13.11: any earlier APPROVE is not enough. The last trusted verdict must be Codex's
// automatic APPROVE of the head that was merged.
export function confirmClosed(pr) {
  const merged = pr?.state === 'MERGED' && pr?.baseRefName === integration;
  const last = reviewState({ ...pr, comments: pr?.comments ?? [] }).last;
  return merged && Boolean(last?.auto) && last.verdict?.verdict === 'APPROVE' && last.verdict.sha === pr?.headRefOid;
}

// The cache key includes the evidence, so changing the test, the caller or the PR asks GitHub again.
const evidenceKey = l => `${l.id}:${createHash('sha256').update(JSON.stringify([l.test ?? null, l.caller ?? null, l.closedBy ?? null])).digest('hex').slice(0, 16)}`;

// `number` lets reviewState match the verdict's receipt to this PR (#456).
export const prFields = 'number,state,baseRefName,headRefOid,comments';
export function verify(register, { view = n => makeGh().json(['pr', 'view', String(n), '--repo', repo, '--json', prFields]), cachePath = verifiedPath } = {}) {
  const cache = readJson(cachePath, {});
  let changed = false;
  for (const l of register.lessons ?? []) {
    if (l.status !== 'done' || !Number.isInteger(l.closedBy?.pr)) continue;
    const key = evidenceKey(l);
    if (cache[key] === true) continue;
    cache[key] = confirmClosed(view(l.closedBy.pr));
    changed = true;
  }
  if (changed) writeJson(cachePath, cache);
  return cache;
}

export function summarize(register, { today = vnNow().date, verified = null, invalid = [] } = {}) {
  const lessons = register.lessons ?? [];
  // Without the online check (verified === null) nothing counts as running: offline output must
  // never say "đã chạy thật" (Codex 13.11).
  const confirmed = l => verified !== null && verified[evidenceKey(l)] === true;
  const done = lessons.filter(l => l.status === 'done' && confirmed(l));
  const unconfirmed = lessons.filter(l => l.status === 'done' && !confirmed(l));
  const owner = lessons.filter(l => l.status === 'waiting-owner');
  const declined = lessons.filter(l => l.status === 'declined-owner');
  const open = lessons.filter(l => l.status === 'open' || unconfirmed.includes(l));
  const overdue = open.filter(l => isDate(l.due) && l.due < today);
  return { total: lessons.length, done: done.length, open: open.length, owner: owner.length, declined: declined.map(l => l.id), overdue: overdue.map(l => l.id), unconfirmed: unconfirmed.map(l => l.id), invalid: invalid.length, offline: verified === null };
}

export function renderLessons(s) {
  if (s.invalid) return `Lời hứa sửa quy trình: sổ đang sai ${s.invalid} chỗ, cần sửa trước khi tính.`;
  const parts = [s.offline ? `chưa xác minh trên GitHub (${s.unconfirmed.length} mục ghi xong)` : `${s.done}/${s.total} đã chạy thật (đã merge, Codex duyệt)`, `${s.open} đang làm`];
  if (s.owner) parts.push(`${s.owner} chờ owner`);
  if (s.declined?.length) parts.push(`${s.declined.length} owner quyết không làm, rủi ro vẫn còn (${s.declined.join(', ')})`);
  parts.push(s.overdue.length ? `**${s.overdue.length} quá hạn** (${s.overdue.join(', ')})` : 'không có mục quá hạn');
  if (s.unconfirmed.length && !s.offline) parts.push(`ghi xong nhưng chưa có bằng chứng merge + Codex duyệt: ${s.unconfirmed.join(', ')}`);
  return `Lời hứa sửa quy trình: ${parts.join(', ')}.`;
}

// The line for the board and the owner digest; never throws.
export function lessonsLine({ register = () => readRegister(), online = true, today = vnNow().date, view } = {}) {
  try {
    const reg = register();
    const invalid = problems(reg);
    const verified = online && !invalid.length ? verify(reg, view ? { view } : {}) : null;
    return renderLessons(summarize(reg, { today, verified, invalid }));
  } catch (error) { return `Lời hứa sửa quy trình: chưa đo được (${clean(error.message, 120)}).`; }
}

if (isMain(import.meta.url)) {
  const reg = readRegister();
  const bad = problems(reg);
  for (const p of bad) process.stderr.write(`collab-lessons: ${p}\n`);
  process.stdout.write(`${renderLessons(summarize(reg, { invalid: bad }))}\n`);
  if (bad.length) process.exitCode = 1;
}
