// PR size cap and repeat-fix sweep (owner 05.11.2026, fix C). Larger agent PRs merge less
// (arXiv 2602.19441) and review finds fewer defects past about 400 lines (SmartBear/Cisco), so
// preflight asks to split a PR with more than 400 changed code lines. Tests, docs and lockfiles do
// not count. A body line `Size-exception: <reason>` lets a PR that cannot be split through.
// The median PR needs two revision rounds (HF 2509.14745): past that, a fix should sweep the same
// kind of fault across the repo before pushing instead of fixing one finding per round.
import { reviewState } from './collab-trust.mjs';

export const sizeCap = 400;
const isTest = p => /(^|\/)(tests?|__tests__)\/|\.(test|spec)\.[^/]+$|(^|\/)test_[^/]+\.py$/.test(p);
const isDoc = p => /^docs\/|\.md$/i.test(p);
const isLock = p => /(^|\/)(pnpm-lock\.yaml|package-lock\.json|yarn\.lock|uv\.lock|poetry\.lock|Cargo\.lock)$/.test(p);

export const codeLines = (files = []) => files
  .filter(f => f?.path && !isTest(f.path) && !isDoc(f.path) && !isLock(f.path))
  .reduce((n, f) => n + (Number(f.additions) || 0) + (Number(f.deletions) || 0), 0);

// Horizontal whitespace only (#254): `\s` crossed the newline and took the next body line as the reason.
export function sizeProblem(pr) {
  if (/^[ \t]*[-*]?[ \t]*Size-exception:[ \t]*\S/m.test(String(pr.body ?? ''))) return null;
  const n = codeLines(pr.files ?? []);
  return n > sizeCap ? `PR quá lớn (${n} dòng mã) — tách nhỏ hoặc ghi \`Size-exception: <lý do>\` trong body` : null;
}

export function repeatFixReason(pr) {
  const rounds = reviewState({ ...pr, headRefOid: pr.headRefOid ?? '' }).trusted.filter(c => c.verdict?.verdict === 'REQUEST_CHANGES').length;
  return rounds >= 2 ? `đã ${rounds} lần REQUEST_CHANGES: rà cùng loại lỗi toàn repo trước khi push` : null;
}

// The one call collab-turn makes: a claude-fix turn on a PR with two or more change requests.
export function withRepeatNote(turn, pr) {
  const note = turn.turn === 'claude-fix' ? repeatFixReason(pr) : null;
  return note ? { ...turn, reason: `${turn.reason}; ${note}` } : turn;
}

// Mass-deletion guard (owner 08.11.2026). An agent that "cleans up" can delete working code and the
// reviewer may approve it. A PR that removes many files or many more lines than it adds is never
// auto-merged: it waits until the owner adds the `owner-ok-deletion` label. Lockfiles do not count.
export const deletionCap = { files: 10, lines: 500 };
export const deletionOkLabel = 'owner-ok-deletion';
// A file counts as deleted by its status (GitHub changeType DELETED, git --name-status D), never by its
// line counts: a deleted binary has 0/0 lines, and an edit that only removes lines is not a deletion.
export const isDeletedFile = f => /^(deleted|d)$/i.test(String(f?.changeType ?? f?.status ?? ''));

export function deletionProblem(pr) {
  const labels = (pr.labels ?? []).map(l => l.name ?? l);
  if (labels.includes(deletionOkLabel)) return null;
  const files = (pr.files ?? []).filter(f => f?.path && !isLock(f.path));
  const removed = files.filter(isDeletedFile).length;
  const del = files.reduce((n, f) => n + (Number(f.deletions) || 0), 0);
  const add = files.reduce((n, f) => n + (Number(f.additions) || 0), 0);
  if (removed > deletionCap.files) return `PR xoá ${removed} file — chờ owner gắn label ${deletionOkLabel}`;
  if (del > deletionCap.lines && del > 2 * add) return `PR xoá ${del} dòng (thêm ${add}) — chờ owner gắn label ${deletionOkLabel}`;
  return null;
}

// CI: node scripts/collab-size.mjs --deletion <base> <head> '<labels json>'  (exit 1 on a mass deletion)
if (process.argv[2] === '--deletion') {
  const { execFileSync } = await import('node:child_process');
  const [base, head, labelsJson = '[]'] = process.argv.slice(3);
  const diff = args => execFileSync('git', ['-c', 'core.quotePath=false', 'diff', '-z', '--no-renames', ...args, base, head], { encoding: 'utf8' }).split('\0');
  const deleted = new Set(diff(['--name-only', '--diff-filter=D']).filter(Boolean));
  // -z numstat: "added\tdeleted\tpath" then NUL; binary files report "-\t-".
  const files = diff(['--numstat']).filter(Boolean).map(l => l.split('\t')).map(([a, d, path]) =>
    ({ path, additions: Number(a) || 0, deletions: Number(d) || 0, changeType: deleted.has(path) ? 'DELETED' : 'MODIFIED' }));
  const why = deletionProblem({ files, labels: JSON.parse(labelsJson) });
  console.log(why ?? 'deletion guard: ok');
  if (why) process.exit(1);
}
