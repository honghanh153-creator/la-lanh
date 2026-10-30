// Fast, offline check of the lines a change adds: secrets, sensitive files, personal data in logs.
// Runs before `pnpm check` in collab-check and from the pre-push hook (collab-auto-loop-plan.md 4.4).
// Usage: node scripts/collab-preflight.mjs [--base REF] [--head REF] [--json]
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { clean, integration } from './collab-trust.mjs';

export const allowMarker = /collab-preflight:\s*allow\s+\S.{2,}/;

// Never echo a matched secret back: comments on this public repo only name the rule and place.
export const secretRules = [
  ['private-key', /-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----/],
  ['github-token', /\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b/],
  ['anthropic-key', /\bsk-ant-[A-Za-z0-9_-]{20,}/],
  ['openai-key', /\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}/],
  ['google-api-key', /\bAIza[0-9A-Za-z_-]{35}\b/],
  ['aws-access-key', /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/],
  ['slack-token', /\bxox[abprs]-[A-Za-z0-9-]{10,}/],
  ['stripe-live-key', /\b[rs]k_live_[A-Za-z0-9]{16,}/],
  ['jwt', /\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/],
];
const assigned = /\b(?:secret|password|passwd|token|api[_-]?key|private[_-]?key|client[_-]?secret|service[_-]?role[_-]?key)\b["']?\s*[:=]\s*["']([^"'\s]{16,})["']/i;
const placeholder = /example|placeholder|changeme|change-me|dummy|fake|redacted|synthetic|canary|sample|your[_-]|<|\$\{|\{\{|^x+$|^(.)\1+$|test/i;

const sensitiveFile = [
  [/(^|\/)\.env(\.[^/]*)?$/, p => !/\.(example|sample|template)$/.test(p)],
  [/\.(p12|pfx|jks|keystore|mobileprovision)$/i, () => true],
];
const keyFile = /\.(pem|key)$/i;

const testPath = /(^|\/)(tests?|__tests__|e2e|fixtures?|__mocks__)\/|\.(test|spec)\.[cm]?[jt]sx?$|(^|\/)test_[^/]+\.py$|_test\.py$/;
const docPath = /\.(md|mdx|txt|html|csv|xlsx)$/i;
const logCall = /\b(?:console\.(?:log|info|warn|error|debug|trace)|logger\.\w+|logging\.(?:debug|info|warning|warn|error|exception|critical)|log\.(?:debug|info|warn|warning|error)|print)\s*\(/;
const personal = /\b(?:birth_?(?:date|time|place|day)|birth(?:Date|Time|Place|Day)|birthplace|latitude|longitude|lat|lng|lon|coords?|coordinates|email|phone(?:_?number|Number)?|share_?token|shareToken|access_?token|accessToken|refresh_?token|refreshToken|id_?token|idToken|session_?token|sessionToken|password|mood|journal_?(?:entry|text|body|note)s?|journal(?:Entry|Text|Body|Note)s?)\b/i;

// Drop string contents but keep what is interpolated, so a message like "journal saved" is fine
// while f"{birth_date}" or `${user.email}` is not.
export function codeOnly(line) {
  let out = '';
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    const fString = (ch === '"' || ch === "'") && /[fF]$/.test(out);
    if (ch === '`' || ch === '"' || ch === "'") {
      const quote = ch;
      let j = i + 1;
      while (j < line.length && line[j] !== quote) {
        if (line[j] === '\\') { j += 2; continue; }
        const open = quote === '`' ? line.startsWith('${', j) : fString && line[j] === '{' && line[j + 1] !== '{';
        if (open) {
          const start = j + (quote === '`' ? 2 : 1);
          const end = line.indexOf('}', start);
          if (end < 0) break;
          out += ` ${line.slice(start, end)} `;
          j = end + 1;
          continue;
        }
        j++;
      }
      out += ' ';
      i = j;
      continue;
    }
    if (ch === '#' || line.startsWith('//', i)) break;
    out += ch;
  }
  return out;
}

// Added lines per file from a zero-context diff.
export function parseDiff(text) {
  const files = new Map();
  let file = null;
  let line = 0;
  for (const raw of String(text).split('\n')) {
    if (raw.startsWith('+++ ')) {
      file = raw === '+++ /dev/null' ? null : raw.slice(4).replace(/^b\//, '');
      if (file && !files.has(file)) files.set(file, []);
    } else if (raw.startsWith('@@')) {
      line = Number(/\+(\d+)/.exec(raw)?.[1] ?? 0);
    } else if (file && raw.startsWith('+')) {
      files.get(file).push({ line, text: raw.slice(1) });
      line++;
    } else if (file && raw.startsWith(' ')) line++;
  }
  return files;
}

export function scanLines(files) {
  const findings = [];
  for (const [file, lines] of files) {
    const code = !testPath.test(file) && !docPath.test(file);
    for (const { line, text } of lines) {
      if (allowMarker.test(text)) continue;
      const secret = secretRules.find(([, re]) => re.test(text))?.[0]
        ?? (assigned.test(text) && !placeholder.test(assigned.exec(text)[1]) && !/process\.env|os\.environ|getenv/.test(text) ? 'assigned-secret' : null);
      if (secret) { findings.push({ kind: 'secret', rule: secret, file, line }); continue; }
      if (code && logCall.test(text)) {
        const name = personal.exec(codeOnly(text))?.[0];
        if (name) findings.push({ kind: 'personal-log', rule: name, file, line, excerpt: clean(text.trim(), 140) });
      }
    }
  }
  return findings;
}

export function scanFiles(paths, readHead) {
  const findings = [];
  for (const file of paths) {
    const rule = sensitiveFile.find(([re, keep]) => re.test(file) && keep(file));
    if (rule) { findings.push({ kind: 'sensitive-file', rule: file.split('/').pop(), file, line: 0 }); continue; }
    // Public certificates (the committed Supabase root CA) are fine; private keys are not.
    if (keyFile.test(file) && secretRules[0][1].test(readHead(file))) findings.push({ kind: 'sensitive-file', rule: 'private-key-file', file, line: 0 });
  }
  return findings;
}

export function runPreflight({ base = `origin/${integration}`, head = 'HEAD', git = args => String(execFileSync('/usr/bin/git', args, { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 })) } = {}) {
  const mergeBase = git(['merge-base', base, head]).trim();
  const diff = git(['diff', '--no-color', '--no-ext-diff', '--unified=0', '--diff-filter=ACMR', mergeBase, head]);
  const changed = git(['diff', '--name-only', '--diff-filter=ACMR', mergeBase, head]).split('\n').filter(Boolean);
  const files = parseDiff(diff);
  const findings = [...scanFiles(changed, f => git(['show', `${head}:${f}`])), ...scanLines(files)];
  const added = [...files.values()].reduce((n, l) => n + l.length, 0);
  return { status: findings.length ? 'FAIL' : 'PASS', mergeBase, files: changed.length, added, findings };
}

const labels = { secret: 'Khóa bí mật', 'sensitive-file': 'File nhạy cảm', 'personal-log': 'Dữ liệu cá nhân trong log' };

export function renderFindings(result) {
  if (result.status === 'PASS') return `Soát nhanh: sạch (${result.files} file, ${result.added} dòng thêm, so với \`${result.mergeBase.slice(0, 12)}\`).`;
  const rows = result.findings.slice(0, 40).map(f => `| ${labels[f.kind]} | \`${clean(f.file, 200).replace(/\|/g, '\\|')}${f.line ? `:${f.line}` : ''}\` | ${clean(f.rule, 60)} |`);
  const leaked = result.findings.some(f => f.kind !== 'personal-log');
  return [
    `Soát nhanh: ${result.findings.length} lỗi (${result.files} file, ${result.added} dòng thêm). Chưa chạy \`pnpm check\`.`,
    '',
    '| Loại | Vị trí | Quy tắc |', '|---|---|---|', ...rows,
    ...(result.findings.length > 40 ? [`| … | còn ${result.findings.length - 40} lỗi | |`] : []),
    '',
    ...(leaked ? ['Nếu khóa hoặc file nhạy cảm đã push lên repo public: thu hồi/đổi khóa trước, rồi mới xóa khỏi branch.', ''] : []),
    'Nhận nhầm thì thêm `collab-preflight: allow <lý do>` trên chính dòng đó; Codex sẽ review chú thích này.',
  ].join('\n');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const opt = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
  try {
    const result = runPreflight({ base: opt('--base'), head: opt('--head') });
    process.stdout.write(args.includes('--json') ? `${JSON.stringify(result, null, 2)}\n` : `${renderFindings(result)}\n`);
    if (result.status !== 'PASS') process.exitCode = 4;
  } catch (error) { process.stderr.write(`collab-preflight failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
