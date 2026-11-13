import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
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
  assert.match(prePushHook, /node "\$ops\/scripts\/collab-check\.mjs" --guard \|\| exit 1/);
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
  writeFileSync(join(home, 'ops', 'scripts', 'collab-preflight.mjs'), 'process.exit(3);\n');
  assert.equal(run().status, 1, 'a lint failure blocks the push');
  writeFileSync(join(home, 'ops', 'scripts', 'collab-preflight.mjs'), 'process.exit(0);\n');
  assert.equal(run().status, 0);
});
