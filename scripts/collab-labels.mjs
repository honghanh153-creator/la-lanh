// Status labels on open PRs (owner 08.11.2026): one look at GitHub shows where each PR is stuck,
// without reading the loop log. The label follows the turn collab-turn already computes:
// cần sửa → đang kiểm tra → chờ review → đã duyệt; a failed review sends it back to cần sửa.
import { repo } from './collab-trust.mjs';

export const statusLabels = {
  'claude-fix': ['st: cần sửa', 'd93f0b', 'Claude đang sửa: review trượt, check trượt hoặc xung đột'],
  'claude-check': ['st: đang kiểm tra', 'fbca04', 'Đang chạy author check'],
  'codex-review': ['st: chờ review', '1d76db', 'Chờ Codex review head mới nhất'],
  merge: ['st: đã duyệt', '0e8a16', 'APPROVE @ head, chờ merge tự động'],
  hold: ['st: chờ owner', '5319e7', 'Dừng: cần owner (label, plan, xoá nhiều, base main...)'],
  // 18.11 (Codex hourly check on #723): a PR held only behind another PR is not waiting for the
  // owner. "st: chờ owner" there made the owner look like a gate (R2 lists four owner kinds only).
  wait: ['st: chờ PR khác', 'c5def5', 'Chờ PR khác merge trước (xếp chồng hoặc cùng file), không cần owner'],
};
// Hold reasons that only wait on another PR (collab-turn prTurn).
const waitsOnPr = /^(?:xếp chồng trên |chờ PR #\d+ cùng file)/;
export const labelKey = turn => (turn?.turn === 'hold' && waitsOnPr.test(String(turn.reason ?? '')) ? 'wait' : turn?.turn);
const all = Object.values(statusLabels).map(([name]) => name);

export function labelChange(pr, turn) {
  const want = statusLabels[labelKey(turn)]?.[0] ?? null;
  const have = (pr.labels ?? []).map(l => l.name ?? l).filter(n => all.includes(n));
  return { add: want && !have.includes(want) ? want : null, remove: have.filter(n => n !== want) };
}

export function syncStatusLabels(gh, prs, turns, { created = new Set() } = {}) {
  for (const t of turns) {
    const pr = prs.find(p => p.number === t.number);
    if (!pr) continue;
    const { add, remove } = labelChange(pr, t);
    if (!add && !remove.length) continue;
    if (add && !created.has(add)) {
      const [name, color, description] = Object.values(statusLabels).find(([n]) => n === add);
      gh.raw(['label', 'create', name, '--repo', repo, '--color', color, '--description', description, '--force']);
      created.add(add);
    }
    const args = ['pr', 'edit', String(pr.number), '--repo', repo];
    if (add) args.push('--add-label', add);
    for (const r of remove) args.push('--remove-label', r);
    gh.raw(args);
  }
}
