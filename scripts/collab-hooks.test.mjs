import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { chmodSync, cpSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, symlinkSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
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

// Codex r1 on #482 (P1): Git expands '~' in core.hooksPath and resolves a relative path from the
// worktree root; a hand-made join pointed install and verify at a directory Git never runs.
test('the hook directory is the one Git really runs: ~, relative, absolute, worktree', () => {
  const clone = realpathSync(repoDir());
  const git = (...args) => execFileSync('/usr/bin/git', args, { cwd: clone, encoding: 'utf8' }).trim();
  assert.equal(hooksDir(clone), join(clone, '.git', 'hooks'));
  git('config', 'core.hooksPath', '~/.config/git/hooks');
  assert.equal(hooksDir(clone), join(homedir(), '.config', 'git', 'hooks'), 'never <clone>/~/…');
  git('config', 'core.hooksPath', 'tools/hooks');
  mkdirSync(join(clone, 'apps', 'web'), { recursive: true });
  assert.equal(hooksDir(join(clone, 'apps', 'web')), join(clone, 'tools', 'hooks'), 'relative to the worktree root, not the cwd');
  const abs = mkdtempSync(join(tmpdir(), 'hooks-abs-'));
  git('config', 'core.hooksPath', abs);
  assert.equal(hooksDir(clone), abs);
  // Installed where Git looks: a real push from the clone runs it.
  installHook(clone);
  assert.deepEqual(verifyHook(clone), []);
  git('config', '--unset', 'core.hooksPath');
  assert.match(verifyHook(clone).join('\n'), /chưa cài/, 'the hook in the old directory no longer counts');
  git('-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '--allow-empty', '-m', 'x');
  const wt = join(mkdtempSync(join(tmpdir(), 'hooks-wt-')), 'wt');
  git('worktree', 'add', '-q', '-b', 'side', wt);
  assert.equal(realpathSync(hooksDir(wt)), realpathSync(join(clone, '.git', 'hooks')), 'a worktree shares the clone hooks');
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

// L12 (thỏa thuận 12.11 mục L): the loop plan must describe the author check the cron really runs.
// Since 12.11 the cron reads the CI pr-check job; the doc still said "pnpm check" on the Mac.
test('the loop plan describes the author check the cron really runs', async () => {
  const root = join(dirname(fileURLToPath(import.meta.url)), '..');
  const cron = readFileSync(join(root, 'scripts', 'collab-cron.sh'), 'utf8');
  const doc = readFileSync(join(root, 'docs', 'operations', 'collab-auto-loop-plan.md'), 'utf8');
  const { checkSource } = await import('./collab-check.mjs');
  const exported = cron.match(/^export LA_LANH_CHECK_SOURCE=(\S+)/m)?.[1];
  assert.equal(checkSource({ LA_LANH_CHECK_SOURCE: exported }), 'ci', 'the cron reads CI');
  const flow = doc.slice(doc.indexOf('## 3. Luồng chuẩn'), doc.indexOf('## 4.'));
  assert.match(flow, /CI pr-check chạy trên đúng head/);
  assert.doesNotMatch(flow, /pnpm check trên đúng head/, 'the old local check is not the described flow');
  assert.match(doc, /LA_LANH_CHECK_SOURCE=ci/);
  // L07: the doc promises a pre-push hook with the locked lint; the hook really runs it.
  assert.match(doc, /collab-hooks\.mjs --install/);
  assert.match(prePushHook, /collab-preflight\.mjs" --lint/);
});
