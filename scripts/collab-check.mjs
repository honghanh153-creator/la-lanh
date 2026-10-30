// Author check: offline preflight on the diff, then `pnpm check` on the exact PR head under the
// machine-wide heavy lock, then post the receipt line (collab-auto-loop-plan.md 4.4).
// Usage: node scripts/collab-check.mjs --pr N
import { spawnSync, execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { heldEnv, waitForCool, withHeavyLock } from './collab-heavy.mjs';
import { renderFindings, runPreflight } from './collab-preflight.mjs';
import { agentMarker, clean, isSha, makeGh } from './collab-trust.mjs';

export function renderCheck({ head, status, exitCode, seconds, date, preflight = null, cool = null }) {
  const command = exitCode === 'preflight'
    ? 'Dừng ở soát nhanh, chưa chạy `pnpm check`.'
    : `Lệnh: \`pnpm check\` · exit ${exitCode} · ${seconds}s · ${date}. Chạy trên checkout sạch, \`HEAD == ${head.slice(0, 12)}\`.`;
  return [
    `Author check: ${status} @ ${head}`,
    '',
    command,
    ...(cool?.waitedMs ? [`Đã chờ máy hết nóng ${Math.round(cool.waitedMs / 60000)} phút (${clean(cool.reason, 80)}).`] : []),
    status === 'PASS' ? 'Đây là bằng chứng của tác giả, không thay review.' : 'Lượt tiếp theo là Claude sửa.',
    ...(preflight ? ['', preflight] : []),
    '',
    `${agentMarker} author-check sha=${head} -->`,
  ].join('\n');
}

const safeRef = ref => /^[A-Za-z0-9._][A-Za-z0-9._\/-]*$/.test(String(ref ?? '')) && !String(ref).includes('..');

export function runCheck(number, { gh = makeGh(), git = args => String(execFileSync('/usr/bin/git', args, { encoding: 'utf8' })).trim(), spawn = spawnSync, now = () => Date.now(),
  preflight = runPreflight, heavy = withHeavyLock, cool = waitForCool } = {}) {
  const pr = gh.pr(number);
  const head = git(['rev-parse', 'HEAD']);
  if (!isSha(pr.headRefOid) || head !== pr.headRefOid) return { status: 'refused', reason: `HEAD ${head.slice(0, 12)} không phải head của PR ${String(pr.headRefOid).slice(0, 12)}` };
  if (git(['status', '--porcelain'])) return { status: 'refused', reason: 'checkout có thay đổi chưa commit' };
  if (!safeRef(pr.baseRefName)) return { status: 'refused', reason: 'tên base không hợp lệ' };

  // Cheap checks first: a leaked key or personal data in a log fails in seconds, before the heavy run.
  git(['fetch', '--quiet', 'origin', `+refs/heads/${pr.baseRefName}:refs/remotes/origin/${pr.baseRefName}`]);
  const pre = preflight({ base: `origin/${pr.baseRefName}`, head });
  if (pre.status !== 'PASS') {
    gh.comment('pr', pr.number, renderCheck({ head, status: 'FAIL', exitCode: 'preflight', preflight: renderFindings(pre) }));
    return { status: 'FAIL', preflight: pre.findings.length };
  }

  // One heavy job on the machine at a time; a run that never gets the lock posts nothing.
  const outcome = heavy('collab-check', () => {
    const cooled = cool();
    const started = now();
    const result = spawn('pnpm', ['check'], { stdio: 'inherit', timeout: 90 * 60000, env: { ...process.env, [heldEnv]: String(process.pid) } });
    return { cooled, started, exitCode: result.status ?? 1 };
  });
  if (outcome.status === 'busy') return { status: 'busy', reason: `máy đang chạy việc nặng khác: ${clean(outcome.holder?.job, 80)}` };
  const { cooled, started, exitCode } = outcome;
  // A file the check rewrote means the receipt would not describe the committed head.
  const dirty = Boolean(git(['status', '--porcelain']));
  const status = exitCode === 0 && !dirty && git(['rev-parse', 'HEAD']) === head ? 'PASS' : 'FAIL';
  gh.comment('pr', pr.number, renderCheck({ head, status, exitCode, seconds: Math.round((now() - started) / 1000), date: new Date(started).toISOString(), preflight: renderFindings(pre), cool: cooled }));
  return { status, exitCode, dirty };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const number = Number(args[args.indexOf('--pr') + 1]);
  if (!args.includes('--pr') || !Number.isInteger(number) || number <= 0) {
    process.stderr.write('Usage: node scripts/collab-check.mjs --pr N\n'); process.exit(2);
  }
  try {
    const result = runCheck(number);
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status !== 'PASS') process.exitCode = 3;
  } catch (error) { process.stderr.write(`collab-check failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
