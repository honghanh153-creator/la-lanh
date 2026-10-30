// Author check: run `pnpm check` on the exact PR head in this checkout, then post the receipt line.
// Usage: node scripts/collab-check.mjs --pr N
import { spawnSync, execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { agentMarker, clean, isSha, makeGh } from './collab-trust.mjs';

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

export function runCheck(number, { gh = makeGh(), git = args => String(execFileSync('/usr/bin/git', args, { encoding: 'utf8' })).trim(), spawn = spawnSync, now = () => Date.now() } = {}) {
  const pr = gh.pr(number);
  const head = git(['rev-parse', 'HEAD']);
  if (!isSha(pr.headRefOid) || head !== pr.headRefOid) return { status: 'refused', reason: `HEAD ${head.slice(0, 12)} không phải head của PR ${String(pr.headRefOid).slice(0, 12)}` };
  if (git(['status', '--porcelain'])) return { status: 'refused', reason: 'checkout có thay đổi chưa commit' };
  const started = now();
  const result = spawn('pnpm', ['check'], { stdio: 'inherit', timeout: 90 * 60000 });
  const exitCode = result.status ?? 1;
  // A file the check rewrote means the receipt would not describe the committed head.
  const dirty = Boolean(git(['status', '--porcelain']));
  const status = exitCode === 0 && !dirty && git(['rev-parse', 'HEAD']) === head ? 'PASS' : 'FAIL';
  gh.comment('pr', pr.number, renderCheck({ head, status, exitCode, seconds: Math.round((now() - started) / 1000), date: new Date(started).toISOString() }));
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
