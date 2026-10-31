// Author check: run `pnpm check` on the exact PR head, then post the receipt line.
// Usage: node scripts/collab-check.mjs --pr N           (this checkout, must be at the PR head)
//        node scripts/collab-check.mjs --pr N --clone   (dedicated clone ~/.cache/la-lanh-collab/author)
// One check on the machine at a time: two checks share the API and e2e ports and give false receipts.
import { spawnSync, execFileSync } from 'node:child_process';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, rmSync, statSync, writeSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { agentMarker, clean, integration, isSha, makeGh, repo, stateDir } from './collab-trust.mjs';

// Any heavy test process anywhere on the machine (pnpm check starts with contracts:check).
export const heavyPattern = 'contracts:check|vitest|pytest|playwright';
export function machineBusy(run = execFileSync) {
  try { return String(run('pgrep', ['-fl', heavyPattern], { encoding: 'utf8' })).trim().split('\n')[0].slice(0, 120) || null; }
  catch { return null; }
}

const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };
export function withCheckLock(fn) {
  mkdirSync(stateDir, { recursive: true });
  const path = join(stateDir, 'check.lock');
  try {
    const pid = Number(readFileSync(path, 'utf8'));
    if (!alive(pid) || Date.now() - statSync(path).mtimeMs > 2 * 3600000) rmSync(path);
  } catch {}
  let fd;
  try { fd = openSync(path, 'wx'); } catch { return { status: 'busy', reason: 'một author check khác đang chạy' }; }
  try { writeSync(fd, String(process.pid)); return fn(); } finally { closeSync(fd); rmSync(path, { force: true }); }
}

export function renderCheck({ head, status, exitCode, seconds, date }) {
  return [
    `Author check: ${status} @ ${head}`,
    '',
    `Lệnh: \`pnpm check\` · exit ${exitCode} · ${seconds}s · ${date}. Chạy trên checkout sạch, \`HEAD == ${head.slice(0, 12)}\`.`,
    status === 'PASS' ? 'Đây là bằng chứng của tác giả, không thay review.' : 'Lượt tiếp theo là Claude sửa.',
    '',
    `${agentMarker} author-check sha=${head} -->`,
  ].join('\n');
}

export function runCheck(number, { gh = makeGh(), cwd = process.cwd(), git = args => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8' })).trim(), spawn = spawnSync, now = () => Date.now(), busy = machineBusy } = {}) {
  return withCheckLock(() => checkOnce(number, { gh, cwd, git, spawn, now, busy }));
}

function checkOnce(number, { gh, cwd, git, spawn, now, busy }) {
  const pr = gh.pr(number);
  const head = git(['rev-parse', 'HEAD']);
  if (!isSha(pr.headRefOid) || head !== pr.headRefOid) return { status: 'refused', reason: `HEAD ${head.slice(0, 12)} không phải head của PR ${String(pr.headRefOid).slice(0, 12)}` };
  if (git(['status', '--porcelain'])) return { status: 'refused', reason: 'checkout có thay đổi chưa commit' };
  const other = busy();
  if (other) return { status: 'busy', reason: `máy đang chạy check khác: ${clean(other, 120)}` };
  const started = now();
  // CI=1: Playwright starts its own preview server instead of reusing one left by another checkout.
  const result = spawn('pnpm', ['check'], { cwd, stdio: 'inherit', timeout: 90 * 60000, env: { ...process.env, CI: '1' } });
  const exitCode = result.status ?? 1;
  // A file the check rewrote means the receipt would not describe the committed head.
  const dirty = Boolean(git(['status', '--porcelain']));
  const status = exitCode === 0 && !dirty && git(['rev-parse', 'HEAD']) === head ? 'PASS' : 'FAIL';
  gh.comment('pr', pr.number, renderCheck({ head, status, exitCode, seconds: Math.round((now() - started) / 1000), date: new Date(started).toISOString() }));
  return { status, exitCode, dirty };
}

const git = (args, cwd, run) => String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout: 600000, maxBuffer: 64 * 1024 * 1024 })).trim();

// A clone only for author checks, so no agent checkout is switched under anyone.
// Ignored build outputs (node_modules, .venv, ephemeris build) are kept between runs.
export function prepareAuthorClone(number, head, run = execFileSync) {
  const dir = join(stateDir, 'author');
  if (!existsSync(join(dir, '.git'))) {
    mkdirSync(stateDir, { recursive: true });
    git(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, dir], stateDir, run);
  }
  git(['fetch', '--quiet', '--force', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`, `+refs/pull/${Number(number)}/head:refs/remotes/pr/${Number(number)}`], dir, run);
  git(['checkout', '--quiet', '--force', '--detach', head], dir, run);
  git(['clean', '-fdq'], dir, run);
  const actual = git(['rev-parse', 'HEAD'], dir, run);
  if (actual !== head) throw new Error(`Author clone is at ${actual}, not ${head}.`);
  try { run('pnpm', ['install', '--frozen-lockfile', '--offline'], { cwd: dir, stdio: 'ignore', timeout: 900000 }); }
  catch { run('pnpm', ['install', '--frozen-lockfile'], { cwd: dir, stdio: 'ignore', timeout: 900000 }); }
  run('make', ['-C', 'vendor/swisseph'], { cwd: dir, stdio: 'ignore', timeout: 600000 });
  return dir;
}

export function runCheckInClone(number, { gh = makeGh(), run = execFileSync, ...rest } = {}) {
  const pr = gh.pr(number);
  if (!isSha(pr.headRefOid)) throw new Error('PR head SHA unavailable.');
  // Refuse before touching the clone when another check owns the machine.
  const other = (rest.busy ?? machineBusy)();
  if (other) return { status: 'busy', reason: `máy đang chạy check khác: ${clean(other, 120)}` };
  return withCheckLock(() => {
    const cwd = prepareAuthorClone(number, pr.headRefOid, run);
    return checkOnce(number, { gh, cwd, git: args => git(args, cwd, run), spawn: rest.spawn ?? spawnSync, now: rest.now ?? (() => Date.now()), busy: rest.busy ?? machineBusy });
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const number = Number(args[args.indexOf('--pr') + 1]);
  if (!args.includes('--pr') || !Number.isInteger(number) || number <= 0) {
    process.stderr.write('Usage: node scripts/collab-check.mjs --pr N\n'); process.exit(2);
  }
  try {
    const result = args.includes('--clone') ? runCheckInClone(number) : runCheck(number);
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status !== 'PASS') process.exitCode = 3;
  } catch (error) { process.stderr.write(`collab-check failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
