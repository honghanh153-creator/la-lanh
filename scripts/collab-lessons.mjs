// The register of workflow promises (owner 13.11.2026: "Claude khá hờ hững trong việc sửa workflow").
// Codex's audit that day found that none of the 12 workflow changes agreed on 12.11 had reached
// "done": lessons were written down, not turned into running checks. This file makes the promise
// itself checkable, so follow-through no longer depends on Claude's discipline:
// - every lesson has an owner, a due date and a status in scripts/collab-lessons.json;
// - "done" needs a regression test that exists in a file CI runs (pnpm collab:test), a caller
//   that wires the fix into the loop, and the PR that closed it; the tick then confirms on
//   GitHub that the PR was merged into collab/integration with a Codex APPROVE (Claude cannot
//   close a lesson by editing the file);
// - an open lesson past its due date is reported as overdue in the board and the owner digest.
// Usage: node scripts/collab-lessons.mjs   (prints the summary; exit 1 if the register is invalid)
import { createHash } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { clean, integration, makeGh, readJson, repo, reviewState, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

const here = dirname(fileURLToPath(import.meta.url));
export const root = join(here, '..');
export const registerPath = join(here, 'collab-lessons.json');
export const statuses = ['open', 'waiting-owner', 'done'];
const isDate = s => /^\d{4}-\d{2}-\d{2}$/.test(s ?? '');

export const readRegister = (path = registerPath) => JSON.parse(readFileSync(path, 'utf8'));

// Test files that CI runs: a lesson's test must be one of them, or it never runs.
export function ciTestFiles(pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))) {
  return new Set(String(pkg.scripts?.['collab:test'] ?? '').split(/\s+/).filter(f => f.endsWith('.test.mjs')));
}

const read = (base, file) => { const p = join(base, file); return existsSync(p) ? readFileSync(p, 'utf8') : null; };
// A test is found by its exact name in a test('…') call, not by any matching text.
const code = text => text.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');
const hasTest = (text, name) => [...code(text).matchAll(/\btest\(\s*(['"`])((?:\\.|(?!\1).)*)\1/g)].some(m => m[2].includes(name));

// Offline problems: shape, and for "done" the evidence that exists in this checkout.
export function problems(register, { base = root, ciFiles = ciTestFiles() } = {}) {
  const out = [];
  const ids = new Set();
  for (const l of register.lessons ?? []) {
    const at = `lesson ${l?.id ?? '?'}`;
    if (!/^L\d{2,}$/.test(l?.id ?? '')) { out.push(`${at}: id must look like L01`); continue; }
    if (ids.has(l.id)) out.push(`${at}: duplicate id`);
    ids.add(l.id);
    if (!String(l.title ?? '').trim()) out.push(`${at}: no title`);
    if (!['claude', 'codex', 'owner'].includes(l.who)) out.push(`${at}: who must be claude, codex or owner`);
    if (!statuses.includes(l.status)) out.push(`${at}: status must be one of ${statuses.join(', ')}`);
    if (l.status !== 'waiting-owner' && !isDate(l.due)) out.push(`${at}: due date YYYY-MM-DD required`);
    if (l.status !== 'done') continue;
    const testText = l.test?.file ? read(base, l.test.file) : null;
    if (!l.test?.file || !l.test?.name) out.push(`${at}: done without a regression test`);
    else if (testText === null) out.push(`${at}: test file ${l.test.file} does not exist`);
    else if (!hasTest(testText, l.test.name)) out.push(`${at}: no test named "${l.test.name}" in ${l.test.file}`);
    else if (!ciFiles.has(l.test.file)) out.push(`${at}: ${l.test.file} is not in pnpm collab:test, so CI never runs it`);
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

export const prFields = 'state,baseRefName,headRefOid,comments';
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
  const open = lessons.filter(l => l.status === 'open' || unconfirmed.includes(l));
  const overdue = open.filter(l => isDate(l.due) && l.due < today);
  return { total: lessons.length, done: done.length, open: open.length, owner: owner.length, overdue: overdue.map(l => l.id), unconfirmed: unconfirmed.map(l => l.id), invalid: invalid.length, offline: verified === null };
}

export function renderLessons(s) {
  if (s.invalid) return `Lời hứa sửa quy trình: sổ đang sai ${s.invalid} chỗ, cần sửa trước khi tính.`;
  const parts = [s.offline ? `chưa xác minh trên GitHub (${s.unconfirmed.length} mục ghi xong)` : `${s.done}/${s.total} đã chạy thật (đã merge, Codex duyệt)`, `${s.open} đang làm`];
  if (s.owner) parts.push(`${s.owner} chờ owner`);
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
