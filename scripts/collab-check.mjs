// Author check: run `pnpm check` on the exact PR head, then post the receipt line.
// Usage: node scripts/collab-check.mjs --pr N           (this checkout, must be at the PR head)
//        node scripts/collab-check.mjs --pr N --clone   (dedicated clone ~/.cache/la-lanh-collab/author)
//        node scripts/collab-check.mjs --guard          (private-data scan of this branch, for pre-push)
// One check on the machine at a time: two checks share the API and e2e ports and give false receipts.
import { spawnSync, execFileSync } from 'node:child_process';
import { closeSync, existsSync, mkdirSync, openSync, readFileSync, rmSync, statSync, writeSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { agentMarker, boundedTimeout, clean, integration, isOwnPr, isSha, makeGh, repo, stateDir, vnNow } from './collab-trust.mjs';
import { runPreflight } from './collab-preflight.mjs';
import { runGroup, syncWithIntegration } from './collab-heal.mjs';
import { checkSteps, failDetails, openCheckLog, waitForGuard } from './collab-check-log.mjs';

// A heavy test process anywhere on the machine, matched on the program actually running.
// `pgrep -f` matched any command line that merely mentioned these words, including the agent
// shell that ran pgrep itself, so every caller saw the machine as busy (31.10.2026).
export const heavyPatterns = [
  // The `pnpm check` chain (package.json; today it starts with collab:test) and pnpm itself.
  /^(\S*\/)?sh -c .*\bpnpm (collab:test|contracts:check)\b/,
  /^(\S*\/)?pnpm\s+check(\s|$)/,
  /^(\S*\/)?node\s+\S*pnpm\S*\s+check(\s|$)/,
  // Test runners, bare or through node/python/uv.
  /^(\S*\/)?(vitest|playwright|pytest)(\s|$)/,
  /^(\S*\/)?node\s+\S*(vitest|playwright)\S*(\s|$)/,
  /^(\S*\/)?python[\d.]*\s+(\S*\/pytest(\s|$)|-m\s+pytest)/,
  /^(\S*\/)?uv\s+run\b.*\spytest(\s|$)/,
];
export const isHeavy = args => heavyPatterns.some(pattern => pattern.test(String(args).trim()));
export function machineBusy(run = execFileSync) {
  let table = '';
  try { table = String(run('ps', ['-Ao', 'pid=,args='], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 })); } catch { return null; }
  for (const line of table.split('\n')) {
    const match = /^\s*(\d+)\s+(.*)$/.exec(line);
    if (match && Number(match[1]) !== process.pid && isHeavy(match[2])) return `${match[1]} ${match[2]}`.slice(0, 120);
  }
  return null;
}

// Process-group runner (kills the whole tree at the deadline, stuck beat after 30 min): collab-heal.mjs.
export { runGroup };

// Automatic checks start nothing after 23:30 and end by 23:55 (plan §3.1); direct runs get 90 minutes.
// The budget ends at the exact 23:55:00 instant minus the cleanup reserve, so SIGTERM, the grace
// period and SIGKILL all finish before the cutoff (#140).
export const cleanupReserveMs = 15000;
export function checkBudgetMs({ auto, clock = vnNow, nowMs = Date.now }) {
  if (!auto) return 90 * 60000;
  const t = clock();
  const minute = t.hour * 60 + t.minute;
  if (minute < 8 * 60 + 50 || minute >= 23 * 60 + 30) return 0;
  const byMinute = Math.min(90, 23 * 60 + 55 - minute) * 60000;
  const cutoff = Date.parse(`${t.date}T23:55:00+07:00`);
  const exact = Number.isFinite(cutoff) ? cutoff - nowMs() : byMinute;
  return Math.max(0, Math.min(byMinute, exact) - cleanupReserveMs);
}

// launchd and agent shells can run with a narrow PATH; tests call system tools such as
// /sbin/sha256sum, and a missing tool gave false FAIL receipts on 31.10.2026 (#139, #120).
export const systemDirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin'];
export function withSystemPath(path = '') {
  const parts = String(path).split(':').filter(Boolean);
  return [...parts, ...systemDirs.filter(dir => !parts.includes(dir))].join(':');
}

const alive = pid => { try { process.kill(pid, 0); return true; } catch { return false; } };
// Fix E: the heavy-job lock is free when no live process holds check.lock and no heavy test runs.
export function heavyJobFree(busy = machineBusy) {
  try { const pid = Number(readFileSync(join(stateDir, 'check.lock'), 'utf8')); if (alive(pid)) return false; } catch {}
  return !busy();
}
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

// Private-data guard (owner data in public #179, 03.11.2026). The owner's terms live only on the
// owner's Mac, never in git: a hash of a birth date is as public as the date, since every date of
// a century can be tried in milliseconds. One term per line, `#` comments; `date:YYYY-MM-DD`
// also matches the usual Vietnamese, ISO and compact spellings. Receipts name the file and line,
// never the term.
export const guardPath = () => join(stateDir, 'private-guard.txt');
const pad = n => String(n).padStart(2, '0');
export function guardTerms(text = '') {
  return [...new Set(String(text).split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('#')).flatMap(line => {
    const date = /^date:(\d{4})-(\d{2})-(\d{2})$/.exec(line);
    if (!date) return [line.normalize('NFC').toLowerCase()];
    const [y, m, d] = date.slice(1).map(Number);
    return [`${y}-${pad(m)}-${pad(d)}`, `${pad(d)}/${pad(m)}/${y}`, `${d}/${m}/${y}`, `${pad(d)}.${pad(m)}.${y}`, `${d}.${m}.${y}`, `${pad(d)}-${pad(m)}-${y}`, `${y}${pad(m)}${pad(d)}`, `${y}/${pad(m)}/${pad(d)}`];
  }))];
}
// A missing list means no guard. Any other read failure (permissions, a directory at the path)
// must not silently switch the guard off, so it throws and the caller blocks.
export function readGuardTerms(path = guardPath()) {
  try { return guardTerms(readFileSync(path, 'utf8')); }
  catch (error) { if (error?.code === 'ENOENT') return []; throw new Error('private-guard list unreadable'); }
}
const escapeRe = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// File names go into public receipts too, so a term inside a path is masked before it is shown.
export const redact = (text, terms) => terms.reduce((out, term) => out.replace(new RegExp(escapeRe(term), 'gi'), '[ẩn]'), String(text ?? '').normalize('NFC'));
// Added lines of a unified diff (or of `git log -p`), then free text such as commit messages and
// the PR body. A path that holds a term is a hit itself.
export function guardHits(terms, { diff = '', texts = {} } = {}) {
  if (!terms.length) return [];
  const has = line => { const low = line.normalize('NFC').toLowerCase(); return terms.some(term => low.includes(term)); };
  const hits = [];
  let file = null;
  let line = 0;
  for (const row of String(diff).split('\n')) {
    if (row.startsWith('+++ ')) {
      const path = row.slice(4).replace(/^b\//, '');
      file = redact(path, terms);
      if (has(path)) hits.push(file);
      continue;
    }
    const hunk = /^@@ -\d+(?:,\d+)? \+(\d+)/.exec(row);
    if (hunk) { line = Number(hunk[1]); continue; }
    if (row.startsWith('+')) { if (has(row.slice(1))) hits.push(`${file}:${line}`); line += 1; }
    else if (!row.startsWith('-') && !row.startsWith('\\')) line += 1;
  }
  for (const [name, text] of Object.entries(texts)) if (String(text ?? '').split('\n').some(has)) hits.push(name);
  return hits;
}

export function renderCheck({ head, status, exitCode, seconds, date, guard = null, details = [] }) {
  return [
    `Author check: ${status} @ ${head}`,
    '',
    `Lệnh: \`pnpm check\` · exit ${exitCode} · ${seconds}s · ${date}. Chạy trên checkout sạch, \`HEAD == ${head.slice(0, 12)}\`.`,
    ...(guard?.length ? [`**Chặn: dữ liệu riêng tư** trong danh sách cục bộ của owner xuất hiện ở ${guard.slice(0, 20).map(h => `\`${clean(h, 120)}\``).join(', ')}. Không chạy \`pnpm check\`. Thay bằng dữ liệu giả, sửa cả lịch sử nhánh nếu nằm trong commit.`] : []),
    ...(status === 'FAIL' && details.length ? ['', ...details, ''] : []),
    status === 'PASS' ? 'Đây là bằng chứng của tác giả, không thay review.' : 'Lượt tiếp theo là Claude sửa.',
    '',
    `${agentMarker} author-check sha=${head} -->`,
  ].join('\n');
}

export function runCheck(number, { gh = makeGh(), cwd = process.cwd(), git = args => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })).trim(), spawn = spawnSync, now = () => Date.now(), busy = machineBusy, terms = readGuardTerms, waitGuard = waitForGuard } = {}) {
  return withCheckLock(() => checkOnce(number, { gh, cwd, git, spawn, now, busy, terms, waitGuard, budget: () => 90 * 60000 }));
}

// Git's pre-push input: `<local ref> <local sha> <remote ref> <remote sha>` per pushed ref. Each
// ref is scanned for every commit the remote does not have yet; a deleted ref sends nothing.
export function prePushRanges(input = '') {
  return String(input).split('\n').map(row => row.trim().split(/\s+/))
    .filter(parts => parts.length === 4 && !/^0+$/.test(parts[1]))
    .map(([, local]) => [local, '--not', '--remotes=origin']);
}

// What the PR (or a push) adds. Every outgoing commit's own patch is scanned, so a value added in
// one commit and removed in the next is still caught. `-m` adds a merge's diff against each parent
// (a conflict resolution can introduce text neither side had); `--no-renames` shows a renamed file
// as added; the separate `--name-only` pass catches paths with no content hunk at all (an empty
// file, a rename-only change). quotePath off keeps Vietnamese paths readable. Fails closed: with
// terms set and no readable history, or an unreadable list, the scan blocks.
export function privateHits(pr, git, terms, ranges = [[`origin/${integration}..HEAD`]]) {
  let list;
  try { list = terms(); } catch { return ['danh sách chặn không đọc được']; }
  if (!list.length) return [];
  try {
    const log = args => git(['-c', 'core.quotePath=false', 'log', '-m', '--no-renames', ...args]);
    const hits = ranges.flatMap(range => [
      ...guardHits(list, { diff: log(['-p', '--no-color', '--unified=0', '--format=', ...range]), texts: { 'commit message': log(['--format=%B', ...range]) } }),
      ...log(['--name-only', '--format=', ...range]).split('\n').filter(path => path && guardHits(list, { texts: { x: path } }).length).map(path => redact(path, list)),
    ]);
    if (pr.title || pr.body) hits.push(...guardHits(list, { texts: { 'PR title/body': `${pr.title ?? ''}\n${pr.body ?? ''}` } }));
    return [...new Set(hits)];
  } catch { return ['lịch sử nhánh không đọc được']; }
}

function checkOnce(number, { gh, cwd, git, spawn, now, busy, budget, terms = readGuardTerms, preflight = null, waitGuard = waitForGuard }) {
  const pr = gh.pr(number);
  if (!isOwnPr(pr)) return { status: 'refused', reason: 'PR không phải của owner hoặc từ fork: không chạy code của nó' };
  const head = git(['rev-parse', 'HEAD']);
  if (!isSha(pr.headRefOid) || head !== pr.headRefOid) return { status: 'refused', reason: `HEAD ${head.slice(0, 12)} không phải head của PR ${String(pr.headRefOid).slice(0, 12)}` };
  if (git(['status', '--porcelain'])) return { status: 'refused', reason: 'checkout có thay đổi chưa commit' };
  const other = busy();
  if (other) return { status: 'busy', reason: `máy đang chạy check khác: ${clean(other, 120)}` };
  const timeoutMs = budget();
  if (timeoutMs <= 0) return { status: 'refused', reason: 'ngoài giờ chạy tự động (sau 23:30)' };
  const started = now();
  const guard = privateHits(pr, git, terms);
  if (guard.length) {
    gh.comment('pr', pr.number, renderCheck({ head, status: 'FAIL', exitCode: 'guard', seconds: 0, date: new Date(started).toISOString(), guard }));
    return { status: 'FAIL', guard };
  }
  // Fix A (04.11.2026): template and changed-Python lint first. Nothing is posted; the tick
  // records the reasons and the PR goes to claude-fix without spending the 15-minute check.
  // The lint is bounded by the same deadline, and the budget is read again before pnpm (K: 23:55).
  const pre = preflight?.(pr, cwd, budget);
  const left = budget();
  if (left <= 0) return { status: 'refused', reason: 'hết giờ sau preflight (sau 23:30)' };
  if (pre?.status === 'FAIL') return { status: 'preflight', reasons: pre.reasons, ...(pre.bodyHash ? { bodyHash: pre.bodyHash } : {}) };
  // Agent tests run through collab-test-guard.mjs; wait up to 5 minutes for them (05.11.2026).
  const guarded = waitGuard();
  if (guarded) return { status: 'busy', reason: `test của agent đang chạy qua collab-test-guard (pid ${guarded})` };
  const out = openCheckLog(pr.number, head);
  // CI=1: Playwright starts its own preview server instead of reusing one left by another checkout.
  let result;
  try { result = runGroup('pnpm', ['check'], { cwd, timeoutMs: left, stdio: ['ignore', out.fd, out.fd], env: { ...process.env, CI: '1', PATH: withSystemPath(process.env.PATH) } }, spawn); } catch (error) { out.drop(); throw error; }
  const exitCode = result.status ?? 1;
  // A file the check rewrote means the receipt would not describe the committed head.
  const dirty = Boolean(git(['status', '--porcelain']));
  const status = exitCode === 0 && !dirty && git(['rev-parse', 'HEAD']) === head ? 'PASS' : 'FAIL';
  let details = [];
  if (status === 'FAIL') {
    let steps = [], list = [];
    try { steps = checkSteps(JSON.parse(readFileSync(join(cwd, 'package.json'), 'utf8')).scripts?.check); } catch {}
    try { list = terms(); } catch {}
    const output = out.read();
    details = failDetails({ output, steps, terms: list, logPath: out.keep() });
  } else out.drop();
  gh.comment('pr', pr.number, renderCheck({ head, status, exitCode, details, seconds: Math.round((now() - started) / 1000), date: new Date(started).toISOString() }));
  return { status, exitCode, dirty };
}

const git = (args, cwd, run, timeout = 600000) => String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout, maxBuffer: 64 * 1024 * 1024 })).trim();

// A clone only for author checks, so no agent checkout is switched under anyone.
// Ignored build outputs (node_modules, .venv, ephemeris build) are kept between runs.
export class DeadlineError extends Error {}

// Every preparation step is bounded by the time left before the absolute deadline;
// install and make run as process groups so nothing they start survives the cutoff.
export function prepareAuthorClone(number, head, run = execFileSync, { deadlineMs = Infinity, nowMs = Date.now, group = runGroup } = {}) {
  const left = cap => {
    const ms = Math.min(cap, deadlineMs - nowMs());
    if (ms <= 0) throw new DeadlineError('hết giờ khi đang chuẩn bị clone');
    return ms;
  };
  const step = (args, cwd, cap) => String(run('/usr/bin/git', args, { cwd, encoding: 'utf8', timeout: left(cap), maxBuffer: 64 * 1024 * 1024 })).trim();
  const build = (cmd, args, cap) => {
    const ok = group(cmd, args, { cwd: dir, timeoutMs: left(cap), stdio: 'ignore' }).status === 0;
    if (!ok && nowMs() >= deadlineMs) throw new DeadlineError('hết giờ khi đang chuẩn bị clone');
    return ok;
  };
  const dir = join(stateDir, 'author');
  if (!existsSync(join(dir, '.git'))) {
    mkdirSync(stateDir, { recursive: true });
    step(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, dir], stateDir, 600000);
  }
  step(['fetch', '--quiet', '--force', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`, `+refs/pull/${Number(number)}/head:refs/remotes/pr/${Number(number)}`], dir, 300000);
  step(['checkout', '--quiet', '--force', '--detach', head], dir, 120000);
  step(['clean', '-fdq'], dir, 120000);
  const actual = step(['rev-parse', 'HEAD'], dir, 60000);
  if (actual !== head) throw new Error(`Author clone is at ${actual}, not ${head}.`);
  if (!build('pnpm', ['install', '--frozen-lockfile', '--offline'], 900000)) {
    if (!build('pnpm', ['install', '--frozen-lockfile'], 900000)) throw new Error('pnpm install failed in the author clone');
  }
  if (!build('make', ['-C', 'vendor/swisseph'], 600000)) throw new Error('ephemeris build failed in the author clone');
  left(1);
  return dir;
}

export function runCheckInClone(number, { gh = makeGh(), run = execFileSync, auto = false, clock = vnNow, ...rest } = {}) {
  const pr = gh.pr(number);
  if (!isSha(pr.headRefOid)) throw new Error('PR head SHA unavailable.');
  // Never fetch, build or run a PR that is not the owner's own branch (fork or outside author).
  if (!isOwnPr(pr)) return { status: 'refused', reason: 'PR không phải của owner hoặc từ fork: không chạy code của nó' };
  if (checkBudgetMs({ auto, clock }) <= 0) return { status: 'refused', reason: 'ngoài giờ chạy tự động (sau 23:30)' };
  // Refuse before touching the clone when another check owns the machine.
  const other = (rest.busy ?? machineBusy)();
  if (other) return { status: 'busy', reason: `máy đang chạy check khác: ${clean(other, 120)}` };
  const nowMs = rest.nowMs ?? Date.now;
  const deadlineMs = nowMs() + checkBudgetMs({ auto, clock, nowMs });
  return withCheckLock(() => {
    let cwd;
    try { cwd = prepareAuthorClone(number, pr.headRefOid, run, { deadlineMs, nowMs, group: rest.group ?? runGroup }); }
    catch (error) { if (error instanceof DeadlineError) return { status: 'refused', reason: error.message }; throw error; }
    // A branch behind integration is merged and pushed first; the new head gets its own check.
    // Bounded by the same absolute deadline as the clone preparation, with the cleanup reserve.
    const leftMs = () => deadlineMs - nowMs() - cleanupReserveMs;
    // Every gh and git call after the clone is bounded by the same deadline (05.11.2026).
    const ghD = gh.withDeadline?.(leftMs) ?? gh;
    const gitD = args => git(args, cwd, run, boundedTimeout(600000, leftMs));
    const synced = syncWithIntegration(pr, { git: (args, ms) => git(args, cwd, run, ms), gh: ghD, left: leftMs });
    if (synced) return synced;
    // The clock is read again after the clone and install, which can take minutes.
    const budget = () => Math.min(checkBudgetMs({ auto, clock, nowMs }), deadlineMs - nowMs());
    return checkOnce(number, { gh: ghD, cwd, git: gitD, spawn: rest.spawn ?? spawnSync, now: rest.now ?? (() => Date.now()), busy: rest.busy ?? machineBusy, terms: rest.terms ?? readGuardTerms, budget, preflight: rest.preflight === undefined ? (p, dir, left) => runPreflight(p, { cwd: dir, left }) : rest.preflight });
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  // `--busy`: the one shared answer to "is a heavy check running?" for agents and schedules.
  if (args.includes('--busy')) {
    const busy = machineBusy();
    process.stdout.write(`${busy ? `busy: ${busy}` : 'free'}\n`);
    process.exit(busy ? 1 : 0);
  }
  // `--guard`: the same private-data scan before a push (local pre-push hook), so a term never
  // reaches the public remote. Prints file:line only.
  if (args.includes('--guard')) {
    const run = gitArgs => String(execFileSync('/usr/bin/git', gitArgs, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })).trim();
    // As a pre-push hook Git sends the refs on stdin; run by hand, the current branch is scanned.
    const input = process.stdin.isTTY ? '' : readFileSync(0, 'utf8');
    const ranges = input.trim() ? prePushRanges(input) : [['HEAD', '--not', '--remotes=origin']];
    const hits = privateHits({}, run, readGuardTerms, ranges);
    process.stdout.write(hits.length ? `private-guard: chặn, dữ liệu riêng tư ở ${hits.join(', ')}\n` : 'private-guard: ok\n');
    process.exit(hits.length ? 1 : 0);
  }
  const number = Number(args[args.indexOf('--pr') + 1]);
  if (!args.includes('--pr') || !Number.isInteger(number) || number <= 0) {
    process.stderr.write('Usage: node scripts/collab-check.mjs --pr N [--clone] | --busy | --guard\n'); process.exit(2);
  }
  try {
    const result = args.includes('--clone') ? runCheckInClone(number) : runCheck(number);
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status !== 'PASS') process.exitCode = 3;
  } catch (error) { process.stderr.write(`collab-check failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
