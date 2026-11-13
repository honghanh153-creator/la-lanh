// Preflight before the author check (owner 04.11.2026, fix A). It fails fast on what `pnpm check`
// cannot see or would only find after 15 minutes: a PR body without the G1–G10 template, the risk
// level or the G7 checklist, and mypy/ruff errors in the changed Python files.
// It never posts anything: the tick records the reason and the PR goes to claude-fix.
// Usage: node scripts/collab-preflight.mjs --pr N   (body + lint in this checkout, at the PR head)
//        node scripts/collab-preflight.mjs --lint   (lint only, changed files vs origin/collab/integration; pre-push)
import { execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { bodyHash, runGroup } from './collab-heal.mjs';
import { sizeProblem } from './collab-size.mjs';
import { clean, integration, makeGh, readJson, stateDir, writeJson } from './collab-trust.mjs';

export const gates = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10'];

// The value after `- Gn <name>:` on its own line; empty when the template line was left blank.
export const gateValue = (body, gate) => {
  const line = String(body ?? '').split('\n').find(row => new RegExp(`^\\s*[-*]?\\s*\\**${gate}\\b(?!\\d)`).test(row));
  if (line === undefined) return null;
  const at = line.indexOf(':');
  return at < 0 ? '' : line.slice(at + 1).replace(/[*_`]/g, '').trim();
};

// The G7 quick checklist (product-development-process.md §4): one answer on whether the change
// touches sessions, permissions, personal data or logs. A blank or "N/A" is not an answer.
export const g7Terms = /phiên|session|quyền|permission|auth|dữ liệu|data|log|bí mật|secret|token|csrf|không đụng|không chạm/i;

// Owner 12.11.2026: every PR says what the user gets, in one plain line. Docs and ops PRs write
// `Người dùng thấy gì: không trực tiếp (vận hành)`. The line must start with the label.
export function userSees(body) {
  const m = /^[ \t]*[-*]?[ \t]*\**Người dùng thấy gì[ \t]*:\**[ \t]*(.*)$/mu.exec(String(body ?? '').normalize('NFC'));
  const value = m ? m[1].replace(/[*_`]/g, '').trim() : '';
  return value || null;
}

export function bodyProblems(body) {
  const text = String(body ?? '');
  const problems = [];
  const missing = gates.filter(gate => !gateValue(text, gate));
  if (missing.length) problems.push(`PR body thiếu cổng ${missing.join(', ')}`);
  const level = /^\s*[-*]?\s*\**Mức\**\s*:\s*\**\s*([SML])\b(?!\s*\|)/m.exec(text);
  if (!level) problems.push('PR body thiếu mức rủi ro S/M/L');
  const g7 = gateValue(text, 'G7');
  if (g7 && !g7Terms.test(g7)) problems.push('G7 chưa trả lời checklist (phiên, quyền, dữ liệu cá nhân, log)');
  if (!userSees(text)) problems.push('PR body thiếu dòng "Người dùng thấy gì:"');
  return problems;
}

// Python files ruff and mypy can see: apps/api is the uv project; paths are passed relative to it.
export function changedPython(files = []) {
  return [...new Set(files.map(f => f.path ?? f).filter(p => /^apps\/api\/.+\.py$/.test(p)).map(p => p.slice('apps/api/'.length)))];
}

// The default runs each lint step as a process group, so a hung uv/mypy child dies with the step
// at the timeout (05.11.2026); tests inject a plain spawn.
export const groupSpawn = (cmd, args, { timeout, ...opts } = {}) => runGroup(cmd, args, { ...opts, stdio: 'pipe', timeoutMs: timeout });

// A deleted file is in the PR's file list but not on disk; ruff and mypy would fail on it.
export function lintProblems(pyFiles, { cwd = process.cwd(), spawn = groupSpawn, exists = existsSync, left = () => 600000 } = {}) {
  const files = pyFiles.filter(f => exists(join(cwd, 'apps/api', f)));
  if (!files.length) return [];
  const problems = [];
  for (const [name, args] of [['ruff', ['ruff', 'check', ...files]], ['ruff format', ['ruff', 'format', '--check', ...files]], ['mypy', ['mypy', ...files]]]) {
    const ms = Math.min(600000, left());
    if (ms <= 0) break;
    const result = spawn('uv', ['run', '--directory', 'apps/api', ...args], { cwd, encoding: 'utf8', timeout: ms });
    if (result.status !== 0) problems.push(`${name} lỗi: ${clean(`${result.stdout ?? ''}${result.stderr ?? ''}`, 300) || `exit ${result.status}`}`);
  }
  return problems;
}

export function runPreflight(pr, { cwd = null, spawn = groupSpawn, exists, left } = {}) {
  const problems = bodyProblems(pr.body);
  const size = sizeProblem(pr);
  if (size) problems.push(size);
  // Body problems are enough to stop: no need to start uv as well.
  if (!problems.length && cwd) problems.push(...lintProblems(changedPython(pr.files ?? []), { cwd, spawn, exists, left }));
  return problems.length ? { status: 'FAIL', reasons: problems, bodyHash: bodyHash(pr.body) } : { status: 'PASS', reasons: [] };
}

// The tick's record of preflight failures, per PR, head and PR body (05.11.2026): a new head or an
// edited body clears it. A lint-only record (no body hash) stays keyed by the head.
const recordPath = () => join(stateDir, 'preflight.json');
export const readPreflight = () => readJson(recordPath(), {});
export function recordPreflight(number, head, result) {
  const all = readPreflight();
  if (result.status === 'FAIL') all[number] = { head, ...(result.bodyHash ? { bodyHash: result.bodyHash } : {}), reasons: result.reasons, at: new Date().toISOString() };
  else delete all[number];
  writeJson(recordPath(), all);
}
export const isBodyReason = reason => /^(PR body|G7) /.test(String(reason ?? ''));
export const preflightFailure = (records, pr) => {
  const r = records?.[pr.number];
  if (!r || r.head !== pr.headRefOid) return null;
  // A record without a body hash (written before 05.11, or by an old caller) whose reasons are
  // about the body cannot tell whether the body changed: re-evaluate instead of staying stuck.
  if (!r.bodyHash) return (r.reasons ?? []).some(isBodyReason) ? null : r.reasons;
  return r.bodyHash === bodyHash(pr.body) ? r.reasons : null;
};

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  try {
    let result;
    if (args.includes('--lint')) {
      const diff = String(execFileSync('/usr/bin/git', ['diff', '--name-only', '--diff-filter=ACMR', `origin/${integration}...HEAD`], { encoding: 'utf8' })).split('\n').filter(Boolean);
      const reasons = lintProblems(changedPython(diff));
      result = reasons.length ? { status: 'FAIL', reasons } : { status: 'PASS', reasons: [] };
    } else if (args.includes('--pr')) {
      result = runPreflight(makeGh().pr(Number(args[args.indexOf('--pr') + 1])), { cwd: process.cwd() });
    } else { process.stderr.write('Usage: node scripts/collab-preflight.mjs --pr N | --lint\n'); process.exit(2); }
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status !== 'PASS') process.exitCode = 3;
  } catch (error) { process.stderr.write(`collab-preflight failed: ${clean(error.message, 300)}\n`); process.exitCode = 1; }
}
