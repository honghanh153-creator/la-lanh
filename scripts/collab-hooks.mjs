// The pre-push hook of Claude's clone (lesson L07, owner 13.11.2026).
// docs/operations/collab-auto-loop-plan.md has said since 03.11 that Claude's clone runs the
// private-data guard as a pre-push hook, and since 05.11 that ruff runs before push; on 13.11 no
// hook was installed at all. This file installs the hook, and the tick reports when it is missing.
// The hook runs the scripts of the ops clone (reviewed collab/integration code), never the branch
// being pushed, so a branch cannot switch off its own check.
// Usage: node scripts/collab-hooks.mjs --install [clone]   |   --verify [clone]
import { execFileSync } from 'node:child_process';
import { chmodSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export const claudeClone = process.env.LA_LANH_CLAUDE_CLONE || join(homedir(), 'Documents', 'New project', 'la-lanh-claude');
export const hookMarker = '# la-lanh pre-push';
const hookVersion = `${hookMarker} v2`;

export const prePushHook = [
  '#!/bin/bash',
  hookVersion,
  '# Installed by scripts/collab-hooks.mjs. Runs the reviewed scripts of the ops clone.',
  'set -uo pipefail',
  `ops="\${LA_LANH_COLLAB_HOME:-$HOME/.cache/la-lanh-collab}/ops"`,
  'runtime="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"',
  'export PATH="$runtime/node/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"',
  'if [ ! -f "$ops/scripts/collab-check.mjs" ] || [ ! -f "$ops/scripts/collab-preflight.mjs" ]; then',
  '  echo "pre-push: không thấy script kiểm ở $ops; chặn push cho tới khi clone ops có mặt" >&2; exit 1',
  'fi',
  'refs="$(cat)"',
  '# Private-data guard: every commit the remote does not have yet.',
  '# Fail closed: only an explicit "private-guard: ok" lets the push through (a script that ran',
  '# nothing and exited 0 must not count as a pass).',
  'guard="$(printf \'%s\\n\' "$refs" | node "$ops/scripts/collab-check.mjs" --guard)" || { printf \'%s\\n\' "$guard"; exit 1; }',
  'printf \'%s\\n\' "$guard"',
  'case "$guard" in *"private-guard: ok"*) ;; *) echo "pre-push: quét dữ liệu riêng tư không trả kết quả rõ ràng; chặn push" >&2; exit 1 ;; esac',
  '# Ruff and mypy on changed Python files, with the locked tool versions CI uses.',
  'node "$ops/scripts/collab-preflight.mjs" --lint || { echo "pre-push: lint trượt, sửa rồi push lại" >&2; exit 1; }',
  '',
].join('\n');

// The hooks directory Git really uses for this clone. Git resolves it itself: core.hooksPath with
// `~` expanded, relative to the worktree root, or the common .git/hooks (Codex r1 on #482: a
// hand-made join turned '~/.config/git/hooks' into '<clone>/~/.config/git/hooks', so install and
// verify passed for a hook Git never ran).
export function hooksDir(clone, run = (args, cwd) => String(execFileSync('/usr/bin/git', args, { cwd, encoding: 'utf8' })).trim()) {
  const path = run(['rev-parse', '--git-path', 'hooks'], clone);
  if (!path) throw new Error('git không trả thư mục hook');
  return resolve(clone, path);
}

export function verifyHook(clone = claudeClone, { dir = () => hooksDir(clone) } = {}) {
  if (!existsSync(clone)) return [`không thấy clone của Claude ở ${clone}`];
  let path;
  try { path = join(dir(), 'pre-push'); } catch (error) { return [`không đọc được thư mục hook: ${error.message}`]; }
  if (!existsSync(path)) return ['chưa cài hook trước push (quét dữ liệu riêng tư + lint)'];
  if (readFileSync(path, 'utf8') !== prePushHook) return ['hook trước push khác bản chuẩn, cần cài lại'];
  if (!(statSync(path).mode & 0o100)) return ['hook trước push không có quyền chạy'];
  return [];
}

export function installHook(clone = claudeClone, { dir = () => hooksDir(clone) } = {}) {
  const target = join(dir(), 'pre-push');
  mkdirSync(dirname(target), { recursive: true });
  // Keep any other hook the owner put there: refuse to overwrite a pre-push we did not write.
  if (existsSync(target) && !readFileSync(target, 'utf8').includes(hookMarker)) {
    throw new Error(`${target} đã có hook khác; không ghi đè`);
  }
  writeFileSync(target, prePushHook);
  chmodSync(target, 0o755);
  return target;
}

// One board line for the tick; never throws.
export function hookHealth(clone = claudeClone, opts) {
  try {
    const bad = verifyHook(clone, opts);
    return bad.length ? [`- ⚠️ Hook trước push ở clone Claude: ${bad.join('; ')}`] : ['- ✅ Hook trước push ở clone Claude: đã cài'];
  } catch (error) { return [`- ⚠️ Hook trước push ở clone Claude: chưa kiểm được (${error.message})`]; }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const clone = args.find(a => !a.startsWith('--')) ?? claudeClone;
  if (args.includes('--install')) {
    process.stdout.write(`installed ${installHook(clone)}\n`);
  } else if (args.includes('--verify')) {
    const bad = verifyHook(clone);
    process.stdout.write(bad.length ? `${bad.join('\n')}\n` : 'pre-push hook ok\n');
    if (bad.length) process.exitCode = 1;
  } else { process.stderr.write('Usage: node scripts/collab-hooks.mjs --install|--verify [clone]\n'); process.exitCode = 2; }
}
