import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawn, spawnSync } from 'node:child_process';
import { chmodSync, cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { installWrapper, installedPath, reportConsumers, verifyReportPrompts, verifyWrapper, wrapperHealth } from './collab-ops-wrapper.mjs';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
// Scheduled-task prompts as the owner's machine has them since 15.11 (both call their snapshot step).
function prompts({ owner = 'Run `/x/ops-run.sh snapshot 08` (or `14`, `22`).', retro = 'First run `/x/ops-run.sh snapshot retro`.' } = {}) {
  const dir = realpathSync(mkdtempSync(join(tmpdir(), 'prompts-')));
  for (const [task, text] of [['la-lanh-owner-report', owner], ['la-lanh-retro-2026-11-02', retro]]) {
    if (text === null) continue;
    mkdirSync(join(dir, task));
    writeFileSync(join(dir, task, 'SKILL.md'), `${text}\n`);
  }
  return dir;
}
const git = (cwd, ...args) => execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();

// A home with a real ops clone of a fake origin, a fake `node` that records its argv and cwd, and
// a Claude clone whose path has a space.
function world() {
  const base = realpathSync(mkdtempSync(join(tmpdir(), 'ops wrapper ')));
  const origin = join(base, 'origin.git');
  const seed = join(base, 'seed');
  git(base, 'init', '-q', '--bare', origin);
  git(base, 'init', '-q', '-b', 'collab/integration', seed);
  mkdirSync(join(seed, 'scripts'));
  cpSync(join(repoRoot, 'scripts', 'ops-run.sh'), join(seed, 'scripts', 'ops-run.sh'));
  git(seed, 'add', '.');
  git(seed, 'commit', '-q', '-m', 'seed');
  git(seed, 'push', '-q', origin, 'collab/integration');
  const home = join(base, 'collab home');
  mkdirSync(home);
  git(base, 'clone', '-q', '-b', 'collab/integration', origin, join(home, 'ops'));
  const clone = join(base, 'New project', 'la-lanh-claude');
  mkdirSync(clone, { recursive: true });
  const bin = join(base, 'bin');
  mkdirSync(bin);
  const log = join(base, 'node.log');
  writeFileSync(join(bin, 'node'), `#!/bin/bash\nprintf '%s|%s\\n' "$PWD" "$*" >> "${log}"\nexit "\${FAKE_NODE_EXIT:-0}"\n`);
  chmodSync(join(bin, 'node'), 0o755);
  return { base, origin, home, clone, bin, log };
}

const run = (w, args, env = {}) => spawnSync('/bin/bash', [join(repoRoot, 'scripts', 'ops-run.sh'), ...args], {
  cwd: tmpdir(), encoding: 'utf8',
  env: { HOME: w.base, PATH: `${w.bin}:/usr/bin:/bin`, LA_LANH_COLLAB_HOME: w.home, LA_LANH_CLAUDE_CLONE: w.clone, ...env },
});
const calls = w => { try { return readFileSync(w.log, 'utf8').trim().split('\n').filter(Boolean); } catch { return []; } };

test('ops wrapper runs from another cwd with spaced paths and preserves failures', () => {
  const w = world();
  const report = run(w, ['report']);
  assert.equal(report.status, 0, report.stderr);
  const [reported] = calls(w);
  const runDir = new RegExp(`^${w.clone.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\|${join(w.home, 'ops-runs').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/report-\\d{14}-\\d+/scripts/collab-turn\\.mjs --report$`);
  assert.match(reported, runDir, 'runs in the Claude clone with the script of its own pinned copy, both paths with spaces');
  assert.equal(run(w, ['busy'], { FAKE_NODE_EXIT: '1' }).status, 1, 'a failing step keeps its exit status');
  assert.equal(run(w, ['beat', 'la-lanh-autopilot', 'done']).status, 0);
  assert.match(calls(w).at(-1), /collab-watchdog\.mjs --beat la-lanh-autopilot done$/);
  assert.equal(run(w, ['preflight', '42']).status, 0);
  assert.match(calls(w).at(-1), /collab-preflight\.mjs --pr 42$/);
  const before = calls(w).length;
  for (const bad of [[], ['rm'], ['beat'], ['beat', 'other', 'done'], ['beat', 'la-lanh-x', 'later'], ['preflight'], ['preflight', '0'], ['preflight', '-3'], ['preflight', '4;id']]) {
    assert.equal(run(w, bad).status, 2, `refused: ${bad.join(' ')}`);
  }
  assert.equal(calls(w).length, before, 'a refused step runs nothing');
  git(w.base, '--git-dir', w.origin, 'update-ref', '-d', 'refs/heads/collab/integration');
  const failed = run(w, ['status']);
  assert.notEqual(failed.status, 0, 'a failed fetch stops the step');
  assert.equal(calls(w).length, before, 'and nothing runs after it');
});

test('Codex #487: install reads the reviewed integration revision; a local edit or another revision is refused', () => {
  const w = world();
  const ops = join(w.home, 'ops');
  const reviewed = readFileSync(join(ops, 'scripts', 'ops-run.sh'), 'utf8');
  // A local edit in the ops clone is never installed.
  writeFileSync(join(ops, 'scripts', 'ops-run.sh'), `${reviewed}\necho unreviewed\n`);
  assert.throws(() => installWrapper({ root: ops, home: w.home }), /thay đổi chưa commit/);
  git(ops, 'checkout', '-q', '--', 'scripts/ops-run.sh');
  // A local commit that is not the reviewed revision is refused too.
  writeFileSync(join(ops, 'scripts', 'ops-run.sh'), `${reviewed}\necho task commit\n`);
  git(ops, '-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '-am', 'local');
  assert.throws(() => installWrapper({ root: ops, home: w.home }), /không phải bản collab\/integration đã review/);
  git(ops, 'reset', '-q', '--hard', 'origin/collab/integration');
  // At the reviewed revision the installed bytes are the reviewed ones.
  installWrapper({ root: ops, home: w.home });
  assert.equal(readFileSync(installedPath(w.home), 'utf8'), reviewed);
  // A working-tree edit after install is drift against the reviewed revision, not a match.
  writeFileSync(join(ops, 'scripts', 'ops-run.sh'), `${reviewed}\necho later edit\n`);
  writeFileSync(installedPath(w.home), `${reviewed}\necho later edit\n`);
  assert.match(verifyWrapper({ root: ops, home: w.home }).join(), /khác bản đã review/);
  // A newer reviewed revision on origin that the clone has not checked out is refused.
  git(ops, 'checkout', '-q', '--', 'scripts/ops-run.sh');
  const seed = join(w.base, 'seed');
  writeFileSync(join(seed, 'scripts', 'ops-run.sh'), `${reviewed}\n# newer\n`);
  git(seed, 'commit', '-q', '-am', 'newer');
  git(seed, 'push', '-q', w.origin, 'collab/integration');
  assert.throws(() => installWrapper({ root: ops, home: w.home }), /không phải bản collab\/integration đã review/);
});

test('L19: the wrapper exposes the shared slot snapshot step and refuses any other slot', () => {
  const w = world();
  for (const slot of ['08', '14', '22', 'retro']) {
    const res = run(w, ['snapshot', slot]);
    assert.equal(res.status, 0, res.stderr);
    const [cwd, cmd] = calls(w).at(-1).split('|');
    assert.equal(cwd, w.clone);
    assert.ok(cmd.startsWith(join(w.home, 'ops-runs', 'snapshot-')) && cmd.endsWith(`/scripts/collab-snapshot.mjs --slot ${slot}`), cmd);
  }
  const before = calls(w).length;
  for (const bad of [['snapshot'], ['snapshot', '12'], ['snapshot', '08;id'], ['snapshot', 'retro x']]) assert.equal(run(w, bad).status, 2, `refused: ${bad.join(' ')}`);
  assert.equal(calls(w).length, before, 'a refused slot runs nothing');
});

test('the wrapper installs only from the ops clone, atomically, and drift is reported', () => {
  const w = world();
  assert.throws(() => installWrapper({ root: repoRoot, home: w.home }), /chỉ cài từ clone ops/, 'an unreviewed checkout never installs');
  assert.match(verifyWrapper({ root: join(w.home, 'ops'), home: w.home }).join(), /chưa cài/);
  assert.equal(installWrapper({ root: join(w.home, 'ops'), home: w.home }), installedPath(w.home));
  assert.deepEqual(verifyWrapper({ root: join(w.home, 'ops'), home: w.home }), []);
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home, prompts: prompts() })[0], /✅/);
  writeFileSync(installedPath(w.home), '#!/bin/zsh\necho old\n');
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home, prompts: prompts() })[0], /⚠️.*khác bản đã review/);
});

// Codex auto-1 on #552: the consumers themselves are checked. A report prompt that stops calling the
// snapshot step (or is missing) turns the tick's health line into a warning.
test('L19: both scheduled reports must call their snapshot step; a disconnected one is reported', () => {
  assert.deepEqual(verifyReportPrompts({ dir: prompts() }), []);
  assert.deepEqual(reportConsumers.map(c => c.task), ['la-lanh-owner-report', 'la-lanh-retro-2026-11-02']);
  assert.match(verifyReportPrompts({ dir: prompts({ owner: 'Count merged PRs with gh pr list.' }) }).join(), /báo cáo owner 08\/14\/22 không gọi bước bản chụp chung/);
  assert.match(verifyReportPrompts({ dir: prompts({ retro: 'Facts from tick logs.' }) }).join(), /retro 23:35 không gọi bước bản chụp chung/);
  assert.match(verifyReportPrompts({ dir: prompts({ retro: null }) }).join(), /không đọc được prompt retro/);
  const w = world();
  installWrapper({ root: join(w.home, 'ops'), home: w.home });
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home, prompts: prompts({ owner: 'no snapshot' }) })[0], /⚠️.*báo cáo owner/);
});

// Owner 16.11.2026 (5-fix package item 3c, Codex C2): a report, status or snapshot never re-checks-out
// the shared ops tree a tick may be running from; each run uses its own pinned copy and removes it.
test('E: each ops run uses its own pinned copy of the reviewed commit and never moves the shared ops tree', () => {
  const w = world();
  const ops = join(w.home, 'ops');
  const first = git(ops, 'rev-parse', 'HEAD');
  // origin moves on after the ops tree was checked out
  const seed = join(w.base, 'seed');
  writeFileSync(join(seed, 'scripts', 'new.txt'), 'x\n');
  git(seed, 'add', '.');
  git(seed, 'commit', '-q', '-m', 'next');
  git(seed, 'push', '-q', w.origin, 'collab/integration');
  const latest = git(seed, 'rev-parse', 'HEAD');
  // the fake node records which commit its script came from
  writeFileSync(join(w.bin, 'node'), `#!/bin/bash\nprintf '%s|%s\\n' "$(/usr/bin/git -C "$(dirname "$(dirname "$1")")" rev-parse HEAD)" "$1" >> "${w.log}"\n`);
  chmodSync(join(w.bin, 'node'), 0o755);
  // a leftover copy whose run is gone is swept; a copy whose run is alive is kept
  const runs = join(w.home, 'ops-runs');
  mkdirSync(runs, { recursive: true });
  for (const [name, pid] of [['report-dead-1', '999999999'], ['report-live-2', String(process.pid)], ['tick-orphan-3', '999999998']]) {
    git(ops, 'worktree', 'add', '-q', '--detach', join(runs, name), first);
    writeFileSync(join(runs, `.${name}.pid`), `${pid}\n`);
  }
  // Codex r1 on #603: the wrapper of tick-orphan-3 was killed, but its node still runs from the tree.
  const child = spawn(process.execPath, ['-e', 'setTimeout(() => {}, 60000)', join(runs, 'tick-orphan-3', 'scripts', 'collab-tick.mjs')], { stdio: 'ignore' });
  for (const step of [['report'], ['status'], ['snapshot', '14']]) {
    const out = run(w, step);
    assert.equal(out.status, 0, out.stderr);
  }
  const lines = calls(w);
  assert.equal(lines.length, 3);
  for (const line of lines) assert.match(line, new RegExp(`^${latest}\\|${runs.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/(report|status|snapshot)-\\d{14}-\\d+/scripts/`), 'the run used a fresh copy at the latest reviewed commit');
  assert.equal(git(ops, 'rev-parse', 'HEAD'), first, 'the shared ops tree was not moved');
  assert.deepEqual(readdirSync(runs).filter(n => !n.startsWith('.')).sort(), ['report-live-2', 'tick-orphan-3'], 'each run removed its copy; the dead leftover was swept; a live run and a tree a live process still uses were kept');
  assert.ok(!existsSync(join(runs, '.report-dead-1.pid')));
  child.kill('SIGKILL');
  for (let i = 0; i < 50 && child.exitCode === null && child.signalCode === null; i++) execFileSync('/bin/sleep', ['0.1']);
  assert.equal(run(w, ['status']).status, 0);
  assert.deepEqual(readdirSync(runs).filter(n => !n.startsWith('.')), ['report-live-2'], 'once nothing uses the orphaned tree it is swept');
});

test('E: the scheduled tick runs from its own pinned copy and keeps the shared tree current for the hooks', () => {
  const w = world();
  const ops = join(w.home, 'ops');
  const seed = join(w.base, 'seed');
  writeFileSync(join(seed, 'scripts', 'next.txt'), 'y\n');
  git(seed, 'add', '.');
  git(seed, 'commit', '-q', '-m', 'next');
  git(seed, 'push', '-q', w.origin, 'collab/integration');
  const latest = git(seed, 'rev-parse', 'HEAD');
  const localBin = join(w.base, '.local', 'bin');
  mkdirSync(localBin, { recursive: true });
  writeFileSync(join(localBin, 'node'), `#!/bin/bash\nprintf '%s|%s\\n' "$(/usr/bin/git -C "$(dirname "$(dirname "$1")")" rev-parse HEAD)" "$1" >> "${w.log}"\n`);
  chmodSync(join(localBin, 'node'), 0o755);
  const out = spawnSync('/bin/bash', [join(repoRoot, 'scripts', 'collab-cron.sh')], { cwd: tmpdir(), encoding: 'utf8', env: { HOME: w.base, LA_LANH_COLLAB_HOME: w.home, PATH: '/usr/bin:/bin' } });
  assert.equal(out.status, 0, out.stderr + readFileSync(join(w.home, 'logs', readdirSync(join(w.home, 'logs'))[0]), 'utf8'));
  const [line] = calls(w);
  assert.match(line, new RegExp(`^${latest}\\|${join(w.home, 'ops-runs').replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}/tick-\\d{14}-\\d+/scripts/collab-tick\\.mjs$`));
  assert.equal(git(ops, 'rev-parse', 'HEAD'), latest, 'the shared tree the hooks read is current');
  assert.deepEqual(readdirSync(join(w.home, 'ops-runs')).filter(n => !n.startsWith('.')), [], 'the tick removed its copy');
});
