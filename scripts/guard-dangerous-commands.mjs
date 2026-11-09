#!/usr/bin/env node
// Claude Code PreToolUse hook (owner 08.11.2026): blocks shell commands that can wipe work that is not
// on GitHub yet — hard reset, clean, recursive force delete outside throwaway folders, force push,
// forced worktree removal, discarding all local changes. Exit 2 = blocked; the reason goes to the agent.
// Installed in .claude/settings.json; a copy lives in ~/.claude/hooks/ for every clone.
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const tempRoots = ['/tmp/', '/private/tmp/', '/private/var/folders/', '$TMPDIR/', '${TMPDIR}/'];
const generated = new Set(['node_modules', 'dist', 'build', '.next', '.turbo', 'coverage', 'test-results', 'playwright-report']);

// A deletion target is throwaway only when its path components say so: a temp root, a path inside
// node_modules, or a path whose last component is a generated folder. `..` anywhere is never throwaway,
// so `node_modules/../apps` and look-alike names such as `node_modules-backup` stay blocked.
export function isThrowaway(target = '') {
  const t = String(target);
  const parts = t.split('/').filter(p => p && p !== '.');
  if (!parts.length || parts.includes('..')) return false;
  if (tempRoots.some(r => t.startsWith(r) && t.length > r.length)) return true;
  if (/[*?[\]{}$~`]/.test(t)) return false;
  return parts.includes('node_modules') || generated.has(parts.at(-1));
}

const shells = /(^|[\s|;&(])(bash|sh|zsh|dash|ksh|eval|source|\.|xargs|env)(\s|$)/;
const runsCode = s => /\$\(|`/.test(s);
const messageFlag = /(\s(?:-m|--message|--title|--body|-t|-b|--notes|--subject)(?:=|\s+))("(?:[^"\\]|\\.)*"|'[^']*')/g;

const rules = [
  [/\bgit\s+(-C\s+\S+\s+)?reset\s+[^;&|]*--hard\b/, 'git reset --hard xoá thay đổi chưa commit'],
  [/\bgit\s+(-C\s+\S+\s+)?clean\s+[^;&|]*-[a-zA-Z]*f/, 'git clean -f xoá file chưa commit'],
  [/\bgit\s+(-C\s+\S+\s+)?push\b[^;&|]*(--force(?!-with-lease)\b|\s-f\b|\s\+\S)/, 'push --force ghi đè lịch sử trên GitHub'],
  [/\bgit\s+(-C\s+\S+\s+)?push\b[^;&|]*(--delete\b|\s:\S)/, 'xoá nhánh trên GitHub'],
  [/\bgit\s+(-C\s+\S+\s+)?worktree\s+remove\s+[^;&|]*(--force|-f\b)/, 'xoá worktree kèm thay đổi chưa commit'],
  [/\bgit\s+(-C\s+\S+\s+)?(checkout|restore)\b[^;&|]*(\s--\s+\.|\s\.)(\s|$|;|&)/, 'bỏ toàn bộ thay đổi chưa commit'],
  [/\bgit\s+(-C\s+\S+\s+)?branch\s+[^;&|]*-D\b/, 'xoá nhánh chưa merge'],
];

export function blockReason(command = '') {
  // Only text that is provably inert is dropped: a message-flag value (-m, --body, …) and a heredoc fed
  // to a non-shell command, both only when they hold no $(…)/backtick substitution. Every other quoted
  // string is unquoted and inspected, because `bash -c '…'`, `git restore "."` and `"$(…)"` do run.
  // This guards against accidents, not a hostile agent.
  const cmd = String(command)
    .replace(/(^|\n)([^\n]*?)<<-?\s*(['"]?)(\w+)\3([^\n]*)\n([\s\S]*?)\n\s*\4(?=\s|$)/g,
      (all, lead, before, quote, _tag, after, body) =>
        shells.test(`${before} ${after}`) || (!quote && runsCode(body)) ? `${lead}${before} ${after}\n${body}` : `${lead}${before}<<HEREDOC${after}`)
    .replace(messageFlag, (all, flag, value) => (value.startsWith('"') && runsCode(value) ? all : `${flag}""`))
    .replace(/"((?:[^"\\]|\\.)*)"|'([^']*)'/g, (all, dq, sq) => (dq ?? sq).replace(/\\(.)/g, '$1'));
  for (const [re, why] of rules) if (re.test(cmd)) return why;
  for (const seg of cmd.split(/&&|\|\||;|\n|\||\$\(|`|\)/)) {
    const words = seg.trim().split(/\s+/);
    const i = words.findIndex(w => w === 'rm' || w.endsWith('/rm'));
    if (i < 0) continue;
    const args = words.slice(i + 1);
    const flags = args.filter(a => a.startsWith('-')).join('');
    if (!/r|R|recursive/.test(flags) || !/f|force/.test(flags)) continue;
    const targets = args.filter(a => !a.startsWith('-'));
    if (!targets.length || targets.some(t => !isThrowaway(t))) return 'rm -rf ngoài thư mục tạm';
  }
  return null;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  let input = {};
  try { input = JSON.parse(readFileSync(0, 'utf8') || '{}'); } catch { process.exit(0); }
  const why = blockReason(input?.tool_input?.command);
  if (why) {
    process.stderr.write(`Đã chặn: ${why}. Lệnh này có thể làm mất code chưa lên GitHub. Hãy commit hoặc sao lưu trước, hoặc nhờ owner tự chạy.\n`);
    process.exit(2);
  }
}
