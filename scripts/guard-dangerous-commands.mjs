#!/usr/bin/env node
// Claude Code PreToolUse hook (owner 08.11.2026): blocks shell commands that can wipe work that is not
// on GitHub yet — hard reset, clean, recursive force delete outside throwaway folders, force push,
// forced worktree removal, discarding all local changes. Exit 2 = blocked; the reason goes to the agent.
// Installed in .claude/settings.json; a copy lives in ~/.claude/hooks/ for every clone.
// Best-effort layer behind the sandbox and the main ruleset: a shell parser cannot be complete, so a new
// bypass class is a follow-up issue, not a reason to trust this hook alone.
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

// A pathspec covers the whole tree when, after pathspec magic (`:/`, `:(top)`) and `.`/`..` are resolved,
// nothing but globs is left: `.`, `./`, `:/`, `:(top)`, `*`, `apps/..`, `../..`. An exclude pathspec
// (`:!apps`, `:^apps`, `:(exclude)apps`) means "everything else", so it counts as whole tree too (Codex #354).
export function isWholeTree(spec = '') {
  let p = String(spec);
  if (p.startsWith(':')) {
    const magic = p.match(/^:(\([^)]*\)|[/!^]*)/)[0];
    if (/[!^]|exclude/.test(magic)) return true;
    p = p.slice(magic.length);
  }
  const stack = [];
  for (const seg of p.split('/')) if (seg === '..') stack.pop(); else if (seg && seg !== '.') stack.push(seg);
  return stack.every(s => /^\*+$/.test(s));
}

// A heredoc is inert only when the command that reads it is a known data consumer and every later pipe
// stage is one too. Anything else (bash, python3, node, ruby, perl, php, deno, bun, osascript, sudo, env,
// an empty command, …) may execute the body, so the body is inspected (Codex #354, inverted rule).
const dataCommands = new Set(['cat', 'tee', 'jq', 'wc', 'grep']);
const commandName = seg => {
  const words = seg.trim().split(/\s+/).filter(Boolean);
  let i = 0;
  while (i < words.length && /^\w+=/.test(words[i])) i++;
  return (words[i] ?? '').replace(/["'\\]/g, '').replace(/^.*\//, '');
};
const readsDataOnly = seg => {
  const [name, s] = [commandName(seg), ` ${seg} `];
  if (dataCommands.has(name)) return true;
  if (name === 'gh') return /\s(--body-file|-F|--input)(=|\s+)-\s/.test(s);
  if (name === 'git') return /\scommit\s/.test(s) && /\s(-F|--file)(=|\s+)-\s/.test(s);
  return false;
};
const heredocIsData = (before, after) => {
  const consumer = before.split(/&&|\|\||[|;&(){}`]/).at(-1);
  const downstream = after.split(/&&|\|\||;|&(?!>)|\)/)[0].split('|').slice(1);
  return readsDataOnly(consumer) && downstream.every(readsDataOnly);
};

// Every $(…), <(…), >(…) and `…` body is returned so it is inspected as its own command before any
// normalisation drops it (Codex #354: `git -C "$(git reset --hard)" status`). Quotes are ignored on
// purpose: `bash -c '…'` runs single-quoted substitutions too, and over-blocking prose is cheap.
export function substitutions(text = '') {
  const s = String(text);
  const out = [];
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '\\') { i++; continue; }
    if ('$<>'.includes(c) && s[i + 1] === '(') {
      let depth = 0;
      let j = i + 1;
      for (; j < s.length; j++) {
        if (s[j] === '\\') j++;
        else if (s[j] === '(') depth++;
        else if (s[j] === ')' && --depth === 0) break;
      }
      out.push(s.slice(i + 2, j));
      i = j;
    } else if (c === '`') {
      let j = i + 1;
      while (j < s.length && s[j] !== '`') j += s[j] === '\\' ? 2 : 1;
      out.push(s.slice(i + 1, j));
      i = j;
    }
  }
  return out;
}

// String literals inside code an interpreter runs, one by one and joined per line, so program and
// arguments split across literals are seen together: os.system('git reset --hard'), execSync("rm -rf apps"),
// subprocess.run(['git', 'reset', '--hard']), execFileSync('git', ['clean', '-fd']).
const literal = String.raw`"((?:[^"\\\n]|\\.)*)"|'((?:[^'\\\n]|\\.)*)'`;
const unescape = s => s.replace(/\\(.)/g, '$1');
const stringLiterals = body => [...String(body).matchAll(new RegExp(literal, 'g'))].map(m => unescape(m[1] ?? m[2]));
const literalLists = text => [...String(text).matchAll(new RegExp(String.raw`[[(]\s*((?:${literal})(?:\s*,\s*(?:${literal}))+)\s*,?\s*[\])]`, 'g'))]
  .map(m => stringLiterals(m[1]).join(' '));

const messageFlag = /(\s(?:-m|--message|--title|--body|-t|-b|--notes|--subject)(?:=|\s+))("(?:[^"\\]|\\.)*"|'[^']*')/g;

// Git global options before the subcommand (-C path, -c k=v, --git-dir, --work-tree, --no-pager, -P, …)
// are dropped so every rule sees `git <subcommand>` (Codex #354). A value may be quoted or hold escaped
// spaces; the pass runs before and after unquoting so `-C "New project/x"` and `"--no-pager"` both go.
// Substitutions and `-c` values are inspected first, because the shell runs them before git starts.
const gitValue = String.raw`(?:"(?:[^"\\]|\\.)*"|'[^']*'|\\.|[^\s;&|()"'\`])+`;
const gitGlobals = new RegExp(String.raw`\bgit(?:\s+(?:--(?:git-dir|work-tree|namespace|config-env|attr-source|super-prefix)(?:=${gitValue}|\s+${gitValue})|--[\w-]+(?:=${gitValue})?|-[Cc]\s*${gitValue}|-[pP]))+(?=\s)`, 'g');
export const dropGitGlobals = text => String(text).replace(gitGlobals, 'git');
// `-c core.pager=…`, `-c alias.x=!…` and `bash -c '…'` all run their value.
const dashCValues = text => [...String(text).matchAll(new RegExp(String.raw`(?:^|[\s;&|(])-c\s*(${gitValue})`, 'g'))]
  .map(m => m[1].replace(/"((?:[^"\\]|\\.)*)"|'([^']*)'/g, (all, dq, sq) => (dq ?? sq)).replace(/^[\w.-]+=/, '').replace(/^!/, ''));

const rules = [
  [/\bgit\s+reset\s+[^;&|]*--hard\b/, 'git reset --hard xoá thay đổi chưa commit'],
  [/\bgit\s+clean\s+[^;&|]*-[a-zA-Z]*f/, 'git clean -f xoá file chưa commit'],
  [/\bgit\s+push\b[^;&|]*(--force(?!-with-lease)\b|\s-f\b|\s\+\S)/, 'push --force ghi đè lịch sử trên GitHub'],
  [/\bgit\s+push\b[^;&|]*(--delete\b|\s:\S)/, 'xoá nhánh trên GitHub'],
  [/\bgit\s+worktree\s+remove\s+[^;&|]*(--force|-f\b)/, 'xoá worktree kèm thay đổi chưa commit'],
  [/\bgit\s+branch\s+[^;&|]*-D\b/, 'xoá nhánh chưa merge'],
];

// Git argv is parsed, not matched by spelling: combined short flags (`-vf`, `-df`, `-ff`), split flags
// (`-d -f`), long forms (`--delete --force`), delete refspecs (`:ref`, `-d ref`) and whole-tree
// pathspecs (`./`, `:/`, `:(top)`, `*`) all reach the same decision (Codex #354).
const gitOptsWithValue = new Set(['-C', '-c', '--git-dir', '--work-tree', '--namespace', '--config-env', '--attr-source', '--super-prefix', '--exec-path']);
function gitReason(argv) {
  let i = 0;
  while (i < argv.length && argv[i].startsWith('-')) i += gitOptsWithValue.has(argv[i]) ? 2 : 1;
  let sub = argv[i];
  let args = argv.slice(i + 1);
  if (sub === 'worktree' && args[0] === 'remove') [sub, args] = ['worktree remove', args.slice(1)];
  const dd = args.indexOf('--');
  const opts = dd < 0 ? args : args.slice(0, dd);
  const short = new Set(opts.filter(a => /^-[^-]/.test(a)).flatMap(a => [...a.slice(1)]));
  const long = new Set(opts.filter(a => a.startsWith('--')).map(a => a.split('=')[0]));
  const has = (letters, ...longs) => [...letters].some(c => short.has(c)) || longs.some(l => long.has(l));
  const positional = opts.filter(a => !a.startsWith('-'));
  const paths = dd < 0 ? positional : args.slice(dd + 1);
  switch (sub) {
    case 'reset': return has('', '--hard') ? 'git reset --hard xoá thay đổi chưa commit' : null;
    case 'clean': return has('f', '--force') ? 'git clean -f xoá file chưa commit' : null;
    case 'push':
      if (has('f', '--force') || positional.some(a => a.startsWith('+'))) return 'push --force ghi đè lịch sử trên GitHub';
      if (has('d', '--delete', '--mirror', '--prune') || positional.some(a => /^:./.test(a))) return 'xoá nhánh trên GitHub';
      return null;
    case 'worktree remove': return has('f', '--force') ? 'xoá worktree kèm thay đổi chưa commit' : null;
    case 'branch':
      return has('D') || (has('d', '--delete') && has('f', '--force')) ? 'xoá nhánh chưa merge' : null;
    case 'checkout':
      return has('f', '--force') || paths.some(isWholeTree) ? 'bỏ toàn bộ thay đổi chưa commit' : null;
    case 'switch':
      return has('f', '--force', '--discard-changes') ? 'bỏ toàn bộ thay đổi chưa commit' : null;
    case 'restore': {
      const stagedOnly = has('S', '--staged') && !has('W', '--worktree');
      return !stagedOnly && paths.some(isWholeTree) ? 'bỏ toàn bộ thay đổi chưa commit' : null;
    }
    default: return null;
  }
}

export function blockReason(command = '', depth = 0) {
  if (depth > 8) return null; // nested substitutions deeper than this are not inspected
  // Only text that is provably inert is dropped: a message-flag value (-m, --body, …) without $(…) or
  // backticks, and a heredoc read by a data consumer. Every other quoted string is unquoted and
  // inspected, because `bash -c '…'`, `git restore "."` and `"$(…)"` do run.
  const extras = [];
  let text = String(command)
    .replace(/(^|\n)([^\n]*?)<<-?\s*(['"]?)(\w+)\3([^\n]*)\n([\s\S]*?)\n\s*\4(?=\s|$)/g,
      (all, lead, before, quote, _tag, after, body) => {
        if (heredocIsData(before, after)) {
          if (!quote) extras.push(...substitutions(body));
          return `${lead}${before}<<HEREDOC${after}`;
        }
        extras.push(...stringLiterals(body), ...body.split('\n').map(line => stringLiterals(line).join(' ')));
        return `${lead}${before} ${after}\n${body}`;
      })
    .replace(messageFlag, (all, flag, value) => (value.startsWith('"') && /\$\(|`/.test(value) ? all : `${flag}""`));
  extras.push(...substitutions(text), ...dashCValues(text), ...literalLists(text));
  for (const extra of extras) {
    const why = extra.trim() && extra !== command ? blockReason(extra, depth + 1) : null;
    if (why) return why;
  }
  // Nested quotes (`bash -c 'git "--no-pager" reset --hard'`) are peeled one layer per pass.
  let cmd = dropGitGlobals(text);
  for (let i = 0, prev = ''; i < 4 && cmd !== prev; i++) {
    prev = cmd;
    cmd = dropGitGlobals(cmd.replace(/"((?:[^"\\]|\\.)*)"|'([^']*)'/g, (all, dq, sq) => (dq ?? sq).replace(/\\(.)/g, '$1')));
  }
  for (const [re, why] of rules) if (re.test(cmd)) return why;
  // Parentheses of pathspec magic (`:(top)`, `:(exclude)x`) are not command boundaries.
  for (const seg of cmd.split(/&&|\|\||[;\n|&{}`]|\$\(|(?<!:)\(|\)(?<!:\([^()\s]*\))/)) {
    const words = seg.trim().split(/\s+/).filter(Boolean);
    for (let g = 0; g < words.length; g++) {
      if (words[g] !== 'git' && !words[g].endsWith('/git')) continue;
      const why = gitReason(words.slice(g + 1));
      if (why) return why;
    }
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
