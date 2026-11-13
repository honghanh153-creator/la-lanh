import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { chmodSync, cpSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { hookHealth, hookMarker, hooksDir, installHook, prePushHook, verifyHook } from './collab-hooks.mjs';

const repoDir = () => {
  const dir = mkdtempSync(join(tmpdir(), 'hooks-test-'));
  execFileSync('/usr/bin/git', ['init', '-q', dir]);
  return dir;
};

// 13.11.2026: the docs said Claude's clone ran the private-data guard and ruff before push; no hook
// was installed. The tick now reports a missing hook, and --install fixes it.
test('a clone without the pre-push hook is reported; installing it makes the check pass', () => {
  const clone = repoDir();
  assert.match(verifyHook(clone).join('\n'), /chưa cài hook trước push/);
  assert.match(hookHealth(clone)[0], /⚠️/);
  const path = installHook(clone);
  assert.equal(path, join(hooksDir(clone), 'pre-push'));
  assert.deepEqual(verifyHook(clone), []);
  assert.match(hookHealth(clone)[0], /✅/);
  writeFileSync(path, `${prePushHook}# edited\n`);
  assert.match(verifyHook(clone).join('\n'), /khác bản chuẩn/, 'an edited hook is not trusted');
  writeFileSync(path, prePushHook);
  chmodSync(path, 0o644);
  assert.match(verifyHook(clone).join('\n'), /không có quyền chạy/);
});

test('the installer never overwrites a pre-push hook it did not write', () => {
  const clone = repoDir();
  const path = join(hooksDir(clone), 'pre-push');
  mkdirSync(join(clone, '.git', 'hooks'), { recursive: true });
  writeFileSync(path, '#!/bin/sh\necho owner hook\n');
  assert.throws(() => installHook(clone), /không ghi đè/);
  assert.equal(readFileSync(path, 'utf8'), '#!/bin/sh\necho owner hook\n');
  writeFileSync(path, `#!/bin/bash\n${hookMarker}\nold\n`);
  installHook(clone);
  assert.equal(readFileSync(path, 'utf8'), prePushHook, 'our own older hook is upgraded');
});

test('the hook runs the guard and the lint from the ops clone and blocks when either fails', () => {
  assert.match(prePushHook, /node "\$ops\/scripts\/collab-check\.mjs" --guard\)" \|\| \{/);
  assert.match(prePushHook, /node "\$ops\/scripts\/collab-preflight\.mjs" --lint \|\|/);
  const home = mkdtempSync(join(tmpdir(), 'hooks-ops-'));
  const hook = join(home, 'pre-push');
  writeFileSync(hook, prePushHook);
  chmodSync(hook, 0o755);
  const run = env => spawnSync(hook, [], { input: '', encoding: 'utf8', env: { ...process.env, LA_LANH_COLLAB_HOME: home, ...env } });
  assert.equal(run().status, 1, 'no ops scripts: the push is blocked, not waved through');
  mkdirSync(join(home, 'ops', 'scripts'), { recursive: true });
  writeFileSync(join(home, 'ops', 'scripts', 'collab-check.mjs'), 'process.exit(1);\n');
  writeFileSync(join(home, 'ops', 'scripts', 'collab-preflight.mjs'), 'process.exit(0);\n');
  assert.equal(run().status, 1, 'a guard hit blocks the push');
  writeFileSync(join(home, 'ops', 'scripts', 'collab-check.mjs'), 'process.exit(0);\n');
  assert.equal(run().status, 1, 'a guard that exits 0 without saying ok does not pass (fail closed)');
  writeFileSync(join(home, 'ops', 'scripts', 'collab-check.mjs'), "process.stdout.write('private-guard: ok\\n');\n");
  writeFileSync(join(home, 'ops', 'scripts', 'collab-preflight.mjs'), 'process.exit(3);\n');
  assert.equal(run().status, 1, 'a lint failure blocks the push');
  writeFileSync(join(home, 'ops', 'scripts', 'collab-preflight.mjs'), 'process.exit(0);\n');
  assert.equal(run().status, 0);
});

// Codex 13.11 on #482: prove the installed hook really stops a push that carries a forbidden
// value, with the real guard script (synthetic value, never real data).
test('the real hook and the real guard block a push that adds a forbidden value', () => {
  const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
  // realpath: macOS tmpdir is itself behind a symlink (/var -> /private/var).
  const home = realpathSync(mkdtempSync(join(tmpdir(), 'hooks-e2e-')));
  // A real copy, as the ops clone is: a script reached through a symlink runs nothing (see below).
  mkdirSync(join(home, 'ops'));
  cpSync(join(repoRoot, 'scripts'), join(home, 'ops', 'scripts'), { recursive: true });
  writeFileSync(join(home, 'private-guard.txt'), 'ZZ-SYNTHETIC-FORBIDDEN-VALUE\n');
  const clone = repoDir();
  const git = args => execFileSync('/usr/bin/git', ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', ...args], { cwd: clone, encoding: 'utf8' }).trim();
  const hook = join(home, 'pre-push');
  writeFileSync(hook, prePushHook);
  chmodSync(hook, 0o755);
  const push = () => {
    const sha = git(['rev-parse', 'HEAD']);
    return spawnSync(hook, ['origin', 'https://example.invalid/repo.git'], { cwd: clone, input: `refs/heads/x ${sha} refs/heads/x ${'0'.repeat(40)}\n`, encoding: 'utf8', env: { ...process.env, LA_LANH_COLLAB_HOME: home } });
  };
  writeFileSync(join(clone, 'clean.txt'), 'nothing to see\n');
  git(['add', 'clean.txt']);
  git(['commit', '-q', '-m', 'clean']);
  assert.match(push().stdout, /private-guard: ok/, 'a clean push passes the guard');
  writeFileSync(join(clone, 'leak.txt'), 'note ZZ-SYNTHETIC-FORBIDDEN-VALUE\n');
  git(['add', 'leak.txt']);
  git(['commit', '-q', '-m', 'leak']);
  const blocked = push();
  assert.equal(blocked.status, 1, 'the push is blocked');
  assert.match(blocked.stdout, /private-guard: chặn, dữ liệu riêng tư ở leak\.txt/);
  assert.ok(!blocked.stdout.includes('ZZ-SYNTHETIC') && !blocked.stderr.includes('ZZ-SYNTHETIC'), 'the value itself is never printed');
});

test('a guard reached through a symlink runs nothing; the hook therefore refuses to pass it', () => {
  const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
  const home = mkdtempSync(join(tmpdir(), 'hooks-link-'));
  symlinkSync(repoRoot, join(home, 'ops'));
  const hook = join(home, 'pre-push');
  writeFileSync(hook, prePushHook);
  chmodSync(hook, 0o755);
  const clone = repoDir();
  const out = spawnSync(hook, [], { cwd: clone, input: '', encoding: 'utf8', env: { ...process.env, LA_LANH_COLLAB_HOME: home } });
  assert.equal(out.status, 1);
  assert.match(out.stderr, /không trả kết quả rõ ràng/);
});
