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

// A range of criteria in one entry: "AC1–AC5", "AC1–5", "AC1..AC5", "TC1 — TC3", "AC1-AC5" (#948).
// An en/em dash or ".." may drop the second prefix; a plain hyphen needs it, because "AC1-5" can be
// one id ([\w-]* allows hyphens). Both ends share one prefix, the start is not above the end, and a
// range wider than rangeLimit claims nothing: a typo must not mark a whole issue met.
export const rangeLimit = 30;
const rangeRe = /^(TC|AC[\w-]*?)(\d+)\s*(?:(?:[–—]|\.\.)\s*(?:(TC|AC[\w-]*?))?|-\s*(TC|AC[\w-]*?))(\d+)$/;
function expandRange(entry) {
  const m = rangeRe.exec(entry);
  if (!m) return null;
  const [, prefix, from, dashPrefix, hyphenPrefix, to] = m;
  const end = dashPrefix ?? hyphenPrefix ?? prefix;
  if (end !== prefix) return [];
  const a = Number(from), b = Number(to);
  if (a > b || b - a + 1 > rangeLimit) return [];
  const width = from.startsWith('0') ? from.length : 0;
  return Array.from({ length: b - a + 1 }, (_, i) => `${prefix}${String(a + i).padStart(width, '0')}`);
}

// The criteria ids a PR says it meets: a list split by commas or semicolons, each entry one id
// (its last word, so "xong AC2" counts) or one range.
export function claimedCriteria(body) {
  const value = labelled(body, 'Tiêu chí đạt') ?? '';
  const ids = value.split(/[,;]/).flatMap(s => {
    const entry = s.trim().toUpperCase();
    const range = expandRange(entry.replace(/^.*\s(?=(TC|AC)[\w-]*?\d+\s*(?:[–—]|\.\.|-))/u, ''));
    return range ?? [entry.split(/\s+/).at(-1)];
  });
  return new Set(ids.filter(id => /^(TC\d+|AC[\w-]*\d+)$/.test(id ?? '')));
}

// The criteria of a task issue: each list item under "## Tiêu chí đạt". An item that names an id
// (AC01, TC2) keeps it; otherwise it is TC<n> by position. An empty template line is not a criterion.
// Two criteria with one id (a repeated id, or a positional TC<n> that another line names) are
// ambiguous: a PR claiming that id would meet both (Codex r1 on #496), so they are reported.
function parseCriteria(body) {
  const lines = String(body ?? '').normalize('NFC').split('\n');
  const start = lines.findIndex(l => /^##\s+Tiêu chí đạt\s*$/u.test(l.trim()));
  if (start < 0) return { ids: [], repeated: [] };
  const ids = [];
  for (const line of lines.slice(start + 1)) {
    if (/^##\s/.test(line.trim())) break;
    const m = /^\s*[-*]\s*(\[[ xX]\]\s*)?(.*)$/.exec(line);
    if (!m || !m[2].trim()) continue;
    const named = /\b(AC[\w-]*\d+|TC\d+)\b/.exec(m[2]);
    ids.push(named ? named[1].toUpperCase() : `TC${ids.length + 1}`);
  }
  return { ids: [...new Set(ids)], repeated: [...new Set(ids.filter((id, i) => ids.indexOf(id) !== i))] };
}
export const issueCriteria = body => parseCriteria(body).ids;

// One item: met when every criterion is claimed by a reviewed merged PR; metAt is the merge time
// of the PR that completed the set (PRs are taken in merge order). Ambiguous criteria are never met.
export function itemStatus(issueBody, prs, { reviewed = confirmClosed } = {}) {
  const { ids: criteria, repeated } = parseCriteria(issueBody);
  if (repeated.length) return { criteria, met: [], missing: criteria, metAt: null, prs: [], ambiguous: repeated };
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
// integration that name it). A fetch that fails leaves the day unmeasured instead of reading as 0;
// an item with ambiguous criteria is unmeasured on its own (unclear) and never counts as finished.
export function workProgress({ date, planned = [], fetch, reviewed = confirmClosed }) {
  const items = planned.filter(p => p.item);
  const unlinked = planned.filter(p => !p.item).map(p => p.pr);
  const finished = [];
  const open = [];
  const unclear = [];
  try {
    for (const { item } of items) {
      const { body, prs } = fetch(item);
      const s = itemStatus(body, prs, { reviewed });
      if (s.ambiguous) unclear.push({ item, ids: s.ambiguous });
      else if (s.metAt && vnNow(new Date(s.metAt)).date === date) finished.push(item);
      else if (!s.metAt) open.push({ item, missing: s.criteria.length ? s.missing : ['chưa có tiêu chí'] });
    }
  } catch (error) { return { unmeasured: String(error?.message ?? error).slice(0, 200), picked: items.length, unlinked }; }
  // Owner 15.11: the 7-week share, as classified when the plan was made (never re-read from labels).
  const marked = planned.filter(p => p.plan7w);
  const w7 = planned.some(p => 'plan7w' in p) ? { picked: marked.length, finished: marked.filter(p => p.item && finished.includes(p.item)).length } : null;
  return { picked: items.length, finished, open, unlinked, unclear, w7 };
}

export function renderProgress(p) {
  if (!p) return null;
  if (p.unmeasured) return `Việc đạt tiêu chí: chưa đo được (${p.unmeasured}).`;
  const parts = [p.picked ? `${p.finished.length}/${p.picked} việc đã chọn đạt đủ tiêu chí` : 'chưa chọn việc nào có mã việc'];
  if (p.unclear?.length) parts.push(`${p.unclear.length} việc chưa đo được vì có tiêu chí trùng mã (${p.unclear.map(u => `#${u.item}: ${u.ids.join(', ')}`).join('; ')})`);
  if (p.unlinked.length) parts.push(`${p.unlinked.length} PR chưa gắn việc (${p.unlinked.map(n => `#${n}`).join(', ')}), không tính`);
  const w7 = p.w7 ? `\n- Việc kế hoạch 7 tuần: đã chọn ${p.w7.picked} (tối thiểu 2 khi có việc sẵn sàng), đạt ${p.w7.finished}.` : '';
  return `Việc đạt tiêu chí: ${parts.join('; ')}.${w7}`;
}

// The real fetch: the issue body and the merged PRs into integration that name it. gh pr list
// returns at most `limit` PRs; a full page may hide older PRs, so it is unmeasured, not complete
// (Codex r1 on #496).
export const workHistoryLimit = 50;
export function ghFetch(gh, { limit = workHistoryLimit } = {}) {
  return item => {
    const issue = gh.json(['issue', 'view', String(item), '--repo', repo, '--json', 'body']);
    const found = gh.json(['pr', 'list', '--repo', repo, '--state', 'merged', '--base', integration, '--limit', String(limit),
      '--search', `"Việc: #${item}" in:body`, '--json', 'number,body,state,baseRefName,headRefOid,comments,mergedAt']);
    if (found.length >= limit) throw new Error(`việc #${item} có từ ${limit} PR trở lên, chưa đọc hết`);
    return { body: issue.body, prs: found.filter(pr => workRef(pr.body) === item) };
  };
}
