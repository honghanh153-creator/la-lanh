// Count work by criteria met, not by PRs (lesson L11; agreement of 12.11, item J: "Nhiều PR cho
// cùng task chỉ tính một task hoàn tất; merge và phát hành được ghi riêng").
// Plan critiqued by Codex on 14.11 (SỬA), points taken:
// - an item is a task issue; its criteria are the lines of the issue's "## Tiêu chí đạt" section.
//   A PR saying "xong" proves nothing on its own: the item is met only when every criterion is
//   claimed by a merged PR that carries Codex's automatic APPROVE of its merged head. No criteria
//   listed, or one criterion left, means not met;
// - the item is met at the merge time of the PR that completed it. An item met on an earlier day
//   is not counted again because a follow-up PR merged today;
// - the items of the day are recorded when the plan is made, so editing a PR body later does not
//   change the count of items picked;
// - PRs with no item are reported on their own line, never as finished items.
// A PR names its item and the criteria it meets in its body:
//   Việc: #123
//   Tiêu chí đạt: TC1, TC2      (or the ids the issue uses, e.g. AC01)
import { confirmClosed } from './collab-lessons.mjs';
import { integration, repo, vnNow } from './collab-trust.mjs';

const labelled = (body, label) => {
  const m = new RegExp(`^[ \\t]*[-*]?[ \\t]*\\**${label}[ \\t]*:\\**[ \\t]*(.*)$`, 'mu').exec(String(body ?? '').normalize('NFC'));
  return m ? m[1].replace(/[*_`]/g, '').trim() : null;
};

// The task issue a PR works on, or null.
export function workRef(body) {
  const m = /^#(\d+)\b/.exec(labelled(body, 'Việc') ?? '');
  return m ? Number(m[1]) : null;
}

// The criteria ids a PR says it meets.
export function claimedCriteria(body) {
  const value = labelled(body, 'Tiêu chí đạt') ?? '';
  return new Set(value.split(/[,;]/).map(s => s.trim().split(/\s+/).at(-1)?.toUpperCase()).filter(id => /^(TC\d+|AC[\w-]*\d+)$/.test(id ?? '')));
}

// The criteria of a task issue: each list item under "## Tiêu chí đạt". An item that names an id
// (AC01, TC2) keeps it; otherwise it is TC<n> by position. An empty template line is not a criterion.
export function issueCriteria(body) {
  const lines = String(body ?? '').normalize('NFC').split('\n');
  const start = lines.findIndex(l => /^##\s+Tiêu chí đạt\s*$/u.test(l.trim()));
  if (start < 0) return [];
  const ids = [];
  for (const line of lines.slice(start + 1)) {
    if (/^##\s/.test(line.trim())) break;
    const m = /^\s*[-*]\s*(\[[ xX]\]\s*)?(.*)$/.exec(line);
    if (!m || !m[2].trim()) continue;
    const named = /\b(AC[\w-]*\d+|TC\d+)\b/.exec(m[2]);
    ids.push(named ? named[1].toUpperCase() : `TC${ids.length + 1}`);
  }
  return [...new Set(ids)];
}

// One item: met when every criterion is claimed by a reviewed merged PR; metAt is the merge time
// of the PR that completed the set (PRs are taken in merge order).
export function itemStatus(issueBody, prs, { reviewed = confirmClosed } = {}) {
  const criteria = issueCriteria(issueBody);
  const met = new Set();
  let metAt = null;
  const counted = [];
  for (const pr of [...prs].filter(p => p.mergedAt).sort((a, b) => Date.parse(a.mergedAt) - Date.parse(b.mergedAt))) {
    if (!reviewed(pr)) continue;
    counted.push(pr.number);
    for (const id of claimedCriteria(pr.body)) if (criteria.includes(id)) met.add(id);
    if (!metAt && criteria.length && criteria.every(id => met.has(id))) metAt = pr.mergedAt;
  }
  return { criteria, met: [...met], missing: criteria.filter(id => !met.has(id)), metAt, prs: counted };
}

// The day's items, recorded at plan time: one entry per item, and one per PR with no item.
export function plannedWork(turns) {
  const out = [];
  const seen = new Set();
  for (const t of turns) {
    const key = t.item ? `#${t.item}` : `pr${t.number}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(t.item ? { item: t.item } : { pr: t.number });
  }
  return out;
}

// Progress of the day's items. fetch(n) → { body, prs } for task issue n (prs: merged PRs into
// integration that name it). A fetch that fails leaves the day unmeasured instead of reading as 0.
export function workProgress({ date, planned = [], fetch, reviewed = confirmClosed }) {
  const items = planned.filter(p => p.item);
  const unlinked = planned.filter(p => !p.item).map(p => p.pr);
  const finished = [];
  const open = [];
  try {
    for (const { item } of items) {
      const { body, prs } = fetch(item);
      const s = itemStatus(body, prs, { reviewed });
      if (s.metAt && vnNow(new Date(s.metAt)).date === date) finished.push(item);
      else if (!s.metAt) open.push({ item, missing: s.criteria.length ? s.missing : ['chưa có tiêu chí'] });
    }
  } catch (error) { return { unmeasured: String(error?.message ?? error).slice(0, 200), picked: items.length, unlinked }; }
  return { picked: items.length, finished, open, unlinked };
}

export function renderProgress(p) {
  if (!p) return null;
  if (p.unmeasured) return `Việc đạt tiêu chí: chưa đo được (${p.unmeasured}).`;
  const parts = [p.picked ? `${p.finished.length}/${p.picked} việc đã chọn đạt đủ tiêu chí` : 'chưa chọn việc nào có mã việc'];
  if (p.unlinked.length) parts.push(`${p.unlinked.length} PR chưa gắn việc (${p.unlinked.map(n => `#${n}`).join(', ')}), không tính`);
  return `Việc đạt tiêu chí: ${parts.join('; ')}.`;
}

// The real fetch: the issue body and the merged PRs into integration that name it.
export function ghFetch(gh) {
  return item => {
    const issue = gh.json(['issue', 'view', String(item), '--repo', repo, '--json', 'body']);
    const found = gh.json(['pr', 'list', '--repo', repo, '--state', 'merged', '--base', integration, '--limit', '50',
      '--search', `"Việc: #${item}" in:body`, '--json', 'number,body,state,baseRefName,headRefOid,comments,mergedAt']);
    return { body: issue.body, prs: found.filter(pr => workRef(pr.body) === item) };
  };
}
