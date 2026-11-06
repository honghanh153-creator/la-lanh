// Failure logs and the agent test guard for the author check (05.11.2026: a FAIL on #248 kept no
// log, and an agent's tests probably ran during the check).
// - The full `pnpm check` output goes to logs/check-<pr>-<sha12>.log (last 30 kept); a FAIL
//   receipt names the failing `pnpm <step>` and quotes the last 40 scrubbed lines.
// - scripts/collab-test-guard.mjs holds test-guard.lock while an agent's tests run; the author
//   check waits up to 5 minutes for it, and the guard refuses while check.lock is held.
import { closeSync, existsSync, linkSync, mkdirSync, openSync, readFileSync, readdirSync, renameSync, rmSync, statSync, writeSync } from 'node:fs';
import { join } from 'node:path';
import { stateDir } from './collab-trust.mjs';

export const logDir = () => join(stateDir, 'logs');
export const keepLogs = 30;
export const tailLines = 40;
export const checkLockPath = () => join(stateDir, 'check.lock');
export const guardLockPath = () => join(stateDir, 'test-guard.lock');
export const guardWaitMs = 5 * 60000;

const alive = pid => { if (!Number.isInteger(pid) || pid <= 0) return false; try { process.kill(pid, 0); return true; } catch { return false; } };
export function lockHolder(path) {
  try { const pid = Number(readFileSync(path, 'utf8')); return alive(pid) ? pid : null; } catch { return null; }
}

// The steps of the `check` script, in order: `pnpm a && pnpm b` -> ['a', 'b'].
export function checkSteps(script = '') {
  return String(script).split('&&').map(part => /^\s*pnpm\s+(?:run\s+)?(\S+)/.exec(part)?.[1]).filter(Boolean);
}
// pnpm prints `> pkg@version step /path` before each script; the last header seen is the step that
// was running when the chain stopped. Without headers the step is unknown.
export function failedStep(output = '', steps = []) {
  let last = null;
  for (const line of String(output).split('\n')) {
    const match = /^> \S+ (\S+)(\s|$)/.exec(line.trim());
    if (match && (!steps.length || steps.includes(match[1]))) last = match[1];
  }
  return last;
}

// Secrets never reach a public comment: the owner's private terms become [ẩn], and any line that
// looks like an environment assignment, a token or an authorization header is dropped.
// Matched anywhere in the line, quoted or not (#258 r1: `TOKEN=…`, JSON headers, `postgresql+asyncpg://u:p@`).
const secretLine = [
  /(^|[^A-Za-z])[A-Za-z0-9_-]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|PASS|PWD|DSN|URL|AUTH|CREDENTIALS?|COOKIE|SESSION)[A-Za-z0-9_-]*["']?\s*[=:]/i,
  /\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|sk-[A-Za-z0-9_-]{16,}|xox[abpr]-[\w-]{10,}|AKIA[0-9A-Z]{16}|eyJ[\w-]{10,}\.[\w-]{10,})/,
  /\bbearer\s+\S/i,
  /\bbasic\s+[A-Za-z0-9+/=]{8,}/i,
  // Any URL with a user or password, whatever the scheme or driver suffix.
  /[A-Za-z][\w+.-]*:\/\/[^\s/@]*@/,
];
const escapeRe = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export function scrubLines(text = '', terms = []) {
  const ansi = new RegExp(`${String.fromCharCode(27)}\\[[0-9;]*[A-Za-z]`, 'g');
  return String(text).normalize('NFC').replace(ansi, '').split('\n')
    .map(line => terms.reduce((out, term) => out.replace(new RegExp(escapeRe(term), 'gi'), '[ẩn]'), line))
    .map(line => (secretLine.some(re => re.test(line)) ? '[dòng ẩn: có thể chứa bí mật]' : line))
    .map(line => line.replaceAll('```', "'''"));
}
export const lastLines = (text, terms, n = tailLines) => scrubLines(String(text).replace(/\n+$/, ''), terms).slice(-n);

// Markdown for the FAIL receipt: the step and the scrubbed tail, plus where the full log is kept.
export function failDetails({ output = '', steps = [], terms = [], tail: withTail = true, logPath = null }) {
  const step = failedStep(output, steps);
  const tail = withTail ? lastLines(output, terms) : [];
  return [
    `Bước lỗi: ${step ? `\`pnpm ${step}\`` : 'không xác định'}.${logPath ? ` Log đầy đủ trên máy owner: \`${logPath.replace(/^.*\/(logs\/[^/]+)$/, '~/.cache/la-lanh-collab/$1')}\`.` : ''}`,
    ...(withTail ? ['', `${tail.length} dòng cuối (đã ẩn bí mật):`, '```text', ...tail, '```'] : ['', 'Không đăng dòng log: danh sách ẩn dữ liệu riêng tư không đọc được.']),
  ];
}

export const logName = (pr, sha) => `check-${Number(pr)}-${String(sha).slice(0, 12)}.log`;
// Keep the newest `keep` check logs; older ones are removed.
export function rotateLogs(dir = logDir(), keep = keepLogs) {
  let files = [];
  try { files = readdirSync(dir).filter(name => /^check-\d+-[0-9a-f]{12}\.log$/.test(name)); } catch { return []; }
  const sorted = files.map(name => ({ name, at: statSync(join(dir, name)).mtimeMs })).sort((a, b) => b.at - a.at || b.name.localeCompare(a.name));
  const removed = sorted.slice(keep).map(({ name }) => name);
  for (const name of removed) rmSync(join(dir, name), { force: true });
  return removed;
}
// A temp file that receives the check's stdout and stderr; keep() moves it to its final name.
export function openCheckLog(pr, sha, dir = logDir()) {
  mkdirSync(dir, { recursive: true, mode: 0o700 });
  const temp = join(dir, `.running-${process.pid}.log`);
  const fd = openSync(temp, 'w', 0o600);
  const final = join(dir, logName(pr, sha));
  return {
    fd, path: final,
    read() { try { return readFileSync(temp, 'utf8'); } catch { return ''; } },
    close() { try { closeSync(fd); } catch {} },
    keep() { this.close(); renameSync(temp, final); rotateLogs(dir); return final; },
    drop() { this.close(); rmSync(temp, { force: true }); },
  };
}

// The author check waits for an agent's guarded tests to finish, at most `limitMs`.
export function waitForGuard({ limitMs = guardWaitMs, holder = () => lockHolder(guardLockPath()), sleep = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms), now = Date.now, stepMs = 5000 } = {}) {
  const until = now() + limitMs;
  for (;;) {
    const pid = holder();
    if (!pid) return null;
    if (now() >= until) return pid;
    sleep(Math.min(stepMs, Math.max(1, until - now())));
  }
}

// Guard side: take test-guard.lock only while no author check holds check.lock.
// Returns { status: 'ok', release } | { status: 'check' } | { status: 'held', pid }.
export function takeGuardLock({ checkHolder = () => lockHolder(checkLockPath()), path = guardLockPath() } = {}) {
  mkdirSync(stateDir, { recursive: true });
  if (checkHolder()) return { status: 'check' };
  if (existsSync(path) && !lockHolder(path)) rmSync(path, { force: true });
  // The PID is written to a private temp file first and linked into place, so the lock never exists
  // empty and another caller cannot mistake a lock being created for a stale one (#258 r1).
  const temp = `${path}.${process.pid}.tmp`;
  const fd = openSync(temp, 'w', 0o600);
  writeSync(fd, String(process.pid)); closeSync(fd);
  try { linkSync(temp, path); } catch { return { status: 'held', pid: lockHolder(path) }; } finally { rmSync(temp, { force: true }); }
  // A check that started in the gap between the two looks wins; the guard steps back.
  if (checkHolder()) { rmSync(path, { force: true }); return { status: 'check' }; }
  return { status: 'ok', release: () => { if (lockHolder(path) === process.pid) rmSync(path, { force: true }); } };
}
