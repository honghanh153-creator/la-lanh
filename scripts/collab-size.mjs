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

export function sizeProblem(pr) {
  if (/^\s*[-*]?\s*Size-exception:\s*\S/m.test(String(pr.body ?? ''))) return null;
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
