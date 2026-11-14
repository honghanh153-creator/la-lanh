import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { chmodSync, cpSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { installWrapper, installedPath, verifyWrapper, wrapperHealth } from './collab-ops-wrapper.mjs';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
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
  assert.deepEqual(calls(w), [`${w.clone}|${join(w.home, 'ops', 'scripts', 'collab-turn.mjs')} --report`], 'runs in the Claude clone with the ops script, both paths with spaces');
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

test('L19: the scheduled reports read the shared slot snapshot through the wrapper', () => {
  const w = world();
  for (const slot of ['08', '14', '22', 'retro']) {
    const res = run(w, ['snapshot', slot]);
    assert.equal(res.status, 0, res.stderr);
    assert.equal(calls(w).at(-1), `${w.clone}|${join(w.home, 'ops', 'scripts', 'collab-snapshot.mjs')} --slot ${slot}`);
  }
  const before = calls(w).length;
  for (const bad of [['snapshot'], ['snapshot', '12'], ['snapshot', '08;id'], ['snapshot', 'retro x']]) assert.equal(run(w, bad).status, 2, `refused: ${bad.join(' ')}`);
  assert.equal(calls(w).length, before, 'a refused slot runs nothing');
  // The owner report and the retro tasks call this step (their prompts live outside the repo).
  assert.match(readFileSync(join(repoRoot, 'docs', 'operations', 'collab-auto-loop-plan.md'), 'utf8'), /ops-run\.sh snapshot/);
});

test('the wrapper installs only from the ops clone, atomically, and drift is reported', () => {
  const w = world();
  assert.throws(() => installWrapper({ root: repoRoot, home: w.home }), /chỉ cài từ clone ops/, 'an unreviewed checkout never installs');
  assert.match(verifyWrapper({ root: join(w.home, 'ops'), home: w.home }).join(), /chưa cài/);
  assert.equal(installWrapper({ root: join(w.home, 'ops'), home: w.home }), installedPath(w.home));
  assert.deepEqual(verifyWrapper({ root: join(w.home, 'ops'), home: w.home }), []);
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home })[0], /✅/);
  writeFileSync(installedPath(w.home), '#!/bin/zsh\necho old\n');
  assert.match(wrapperHealth({ root: join(w.home, 'ops'), home: w.home })[0], /⚠️.*khác bản đã review/);
});
