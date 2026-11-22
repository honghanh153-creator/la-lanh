// Outcome numbers for the status board and the 12:00/22:00 digest (owner 12.11.2026).
// Every number comes from a real source: the copy registry in this checkout (the ops clone is
// pinned to collab/integration), git refs and merged PRs on GitHub. A source that cannot be read
// prints "chưa đo được (lý do)"; nothing is estimated.
import { execFileSync } from 'node:child_process';
import { digest, ownerOnly, readLocalRegistry, root } from './codex-copy-review.mjs';
import { wipCount, wipLimit } from './collab-buffer.mjs';
import { clean, integration, makeGh, repo, trustedComments } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';
import { lessonsLine, prFields } from './collab-lessons.mjs';

// Same rule as CopyEntry.servable and approved_bundles() in apps/api/app/domains/content/copy_approval.py.
export const bundlePrefix = 'daily.bundle.';
export const bundleParts = ['headline', 'scene', 'action'];
export function servable(e) {
  return e?.status === 'approved' && ['codex', 'owner'].includes(e.approver) && Boolean(e.date)
    && String(e.text ?? '').trim() !== '' && e.digest === digest(e.text)
    && !(ownerOnly.has(e.category) && e.approver !== 'owner');
}

export function bundleMetric(registry) {
  const byId = new Map((registry?.entries ?? []).map(e => [e.id, e]));
  const groups = new Set([...byId.keys()].filter(id => id.startsWith(bundlePrefix)).map(id => id.split('.').slice(0, 4).join('.')));
  const ready = [...groups].filter(g => bundleParts.every(part => servable(byId.get(`${g}.${part}`)))).length;
  return { ready, total: groups.size };
}

export function copyMetric(registry) {
  const entries = registry?.entries ?? [];
  const approvedBy = who => entries.filter(e => servable(e) && e.approver === who).length;
  return { total: entries.length, codex: approvedBy('codex'), owner: approvedBy('owner'), pending: entries.filter(e => e.status === 'pending').length };
}

const dayMs = 86400000;
// Median hours from PR opened to merged into integration, over PRs merged in the last 7 days.
export function leadTimeMetric(prs, nowMs = Date.now()) {
  const hours = (prs ?? []).filter(p => p.baseRefName === undefined || p.baseRefName === integration)
    .map(p => ({ opened: Date.parse(p.createdAt), merged: Date.parse(p.mergedAt) }))
    .filter(p => Number.isFinite(p.opened) && Number.isFinite(p.merged) && nowMs - p.merged <= 7 * dayMs && p.merged >= p.opened)
    .map(p => (p.merged - p.opened) / 3600000).sort((a, b) => a - b);
  if (!hours.length) return { error: 'không có PR nào merge vào integration trong 7 ngày qua' };
  const mid = Math.floor(hours.length / 2);
  return { hours: hours.length % 2 ? hours[mid] : (hours[mid - 1] + hours[mid]) / 2, count: hours.length };
}

// Loop speed (research item 5, owner approved 21.11.2026; DORA-style flow numbers: lead time split by
// the stage that waited, review rounds and first-pass rate), this week against the week before, so
// the board shows whether the loop got faster or slower. From each merged PR's own trusted comments:
// opened → first Author check PASS → last APPROVE → merged. A stage without its comment is left out.
const median = xs => { if (!xs.length) return null; const s = [...xs].sort((a, b) => a - b); const m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
export function flowStages(pr) {
  const before = trustedComments((pr.comments ?? []).filter(c => String(c.createdAt) <= String(pr.mergedAt)));
  const at = c => (c ? Date.parse(c.createdAt) : NaN);
  const hours = (a, b) => (Number.isFinite(a) && Number.isFinite(b) && b >= a ? (b - a) / 3600000 : null);
  const opened = Date.parse(pr.createdAt);
  const merged = Date.parse(pr.mergedAt);
  const pass = at(before.find(c => c.check?.status === 'PASS'));
  const approve = at(before.filter(c => c.verdict?.verdict === 'APPROVE').at(-1));
  return {
    lead: hours(opened, merged), toCheck: hours(opened, pass), toApprove: hours(pass, approve), toMerge: hours(approve, merged),
    rounds: before.filter(c => c.verdict && c.auto).length, firstTime: !before.some(c => c.verdict?.verdict === 'REQUEST_CHANGES'),
  };
}
export function flowMetric(prs, nowMs = Date.now()) {
  const inWindow = (from, to) => (prs ?? []).filter(p => (p.baseRefName === undefined || p.baseRefName === integration))
    .filter(p => { const m = Date.parse(p.mergedAt); return Number.isFinite(m) && m > from && m <= to; }).map(flowStages);
  const sum = rows => {
    const pick = k => median(rows.map(r => r[k]).filter(v => v !== null));
    return { count: rows.length, lead: pick('lead'), toCheck: pick('toCheck'), toApprove: pick('toApprove'), toMerge: pick('toMerge'),
      rounds: median(rows.map(r => r.rounds)), firstTimePct: rows.length ? Math.round((rows.filter(r => r.firstTime).length / rows.length) * 100) : null };
  };
  const week = sum(inWindow(nowMs - 7 * dayMs, nowMs));
  if (!week.count) return { error: 'không có PR nào merge vào integration trong 7 ngày qua' };
  return { week, before: sum(inWindow(nowMs - 14 * dayMs, nowMs - 7 * dayMs)) };
}

const reason = error => clean(String(error?.message ?? error).split('\n')[0], 120);
const measure = fn => { try { return fn(); } catch (error) { return { error: reason(error) }; } };

// Sources. `run` is execFileSync-shaped; tests pass their own.
export function collectMetrics({ registry = readLocalRegistry, run = execFileSync, gh = makeGh(), prs = [], turns = [], nowMs = Date.now(),
  lessons = () => lessonsLine({ view: n => gh.json(['pr', 'view', String(n), '--repo', repo, '--json', prFields]) }) } = {}) {
  const git = args => String(run('/usr/bin/git', args, { cwd: root, encoding: 'utf8', timeout: 60000, stdio: ['ignore', 'pipe', 'pipe'] })).trim();
  const reg = measure(() => ({ value: registry() }));
  const fromRegistry = fn => (reg.error ? { error: `không đọc được kho câu chữ: ${reg.error}` } : measure(() => fn(reg.value)));
  // The tick's clone fetches only collab/integration; main is fetched here so the gap is current.
  const fetched = measure(() => { git(['fetch', '--quiet', 'origin', 'main', integration]); return {}; });
  const refs = fn => (fetched.error ? { error: `không lấy được nhánh từ GitHub: ${fetched.error}` } : measure(fn));
  // Two weeks of merged PRs with their comments: lead time reads the last 7 days, the flow line both.
  const since = new Date(nowMs - 14 * dayMs).toISOString().slice(0, 10);
  const merged = measure(() => ({ value: gh.json(['pr', 'list', '--repo', repo, '--base', integration, '--state', 'merged',
    '--search', `merged:>=${since}`, '--limit', '300', '--json', 'number,createdAt,mergedAt,baseRefName,comments']) }));
  const fromMerged = fn => (merged.error ? { error: merged.error } : measure(() => fn(merged.value)));
  return {
    bundles: fromRegistry(bundleMetric),
    copy: fromRegistry(copyMetric),
    ahead: refs(() => {
      const n = Number(git(['rev-list', '--count', `origin/main..origin/${integration}`]));
      if (!Number.isInteger(n)) throw new Error('git không trả về số commit');
      return { commits: n };
    }),
    mainAge: refs(() => {
      const at = Number(git(['log', '-1', '--format=%ct', 'origin/main'])) * 1000;
      if (!Number.isFinite(at) || at <= 0) throw new Error('git không trả về ngày commit');
      return { days: Math.max(0, Math.floor((nowMs - at) / dayMs)) };
    }),
    leadTime: fromMerged(list => leadTimeMetric(list, nowMs)),
    flow: fromMerged(list => flowMetric(list, nowMs)),
    wip: measure(() => wipCount(prs, turns)),
    // Owner 13.11.2026: workflow promises (scripts/collab-lessons.mjs), with overdue items named.
    lessons: lessons(),
  };
}

const unmeasured = m => `chưa đo được (${m.error})`;
const oneDecimal = n => n.toFixed(1).replace('.', ',');

// Two lanes (owner 16.11, #604): the limit is per lane, so the totals are shown against the sum of the
// lane limits, with each lane's counts after them (fix-forward #615: "2/1" was shown).
const laneText = { plan7w: 'kế hoạch 7 tuần', daily: 'Daily', process: 'quy trình' };
function wipText(w) {
  if (!w.lanes) return `${w.inProgress}/${wipLimit.inProgress}, đang chờ review: ${w.inReview}/${wipLimit.inReview}`;
  const names = Object.keys(w.lanes);
  const per = names.map(l => `${laneText[l] ?? l} ${w.lanes[l].inProgress}/${wipLimit.inProgress} và ${w.lanes[l].inReview}/${wipLimit.inReview}`).join('; ');
  return `${w.inProgress}/${wipLimit.inProgress * names.length}, đang chờ review: ${w.inReview}/${wipLimit.inReview * names.length} (${per})`;
}

const hoursText = n => (n === null || n === undefined ? 'chưa đo' : `${oneDecimal(n)} giờ`);
const was = (now, before, fmt) => `${fmt(now)} (${before === null || before === undefined ? 'chưa có' : fmt(before)})`;
function flowText({ week: w, before: b }) {
  return [
    `mở tới merge trung vị ${was(w.lead, b.count ? b.lead : null, hoursText)}`,
    `chờ check ${hoursText(w.toCheck)}, chờ duyệt ${hoursText(w.toApprove)}, chờ merge ${hoursText(w.toMerge)}`,
    `${was(w.rounds, b.count ? b.rounds : null, n => `${oneDecimal(n)} vòng duyệt/PR`)}`,
    `${was(w.firstTimePct, b.count ? b.firstTimePct : null, n => `${n}% được duyệt ngay lần đầu`)}`,
    `${w.count} PR`,
  ].join('; ');
}

// One short plain line per metric.
export function renderMetrics(m) {
  if (!m) return [];
  const { bundles: b, copy: c, ahead: a, mainAge: g, leadTime: l, wip: w, flow: f } = m;
  return [
    `Bộ Daily phục vụ được: ${b?.error ? unmeasured(b) : `${b.ready}/${b.total} bộ`}.`,
    `Câu đã duyệt: ${c?.error ? unmeasured(c) : `${c.codex + c.owner}/${c.total} câu (Codex duyệt ${c.codex}, owner duyệt ${c.owner}, còn chờ ${c.pending})`}.`,
    `Khoảng cách tới người dùng: ${a?.error ? unmeasured(a) : `${a.commits} commit ở integration chưa lên main`}; ${g?.error ? `ngày cập nhật main ${unmeasured(g)}` : `main cập nhật lần cuối ${g.days} ngày trước`}.`,
    `Thời gian từ mở PR tới merge vào integration (7 ngày qua): ${l?.error ? unmeasured(l) : `trung vị ${oneDecimal(l.hours)} giờ (${l.count} PR)`}.`,
    ...(f ? [`Tốc độ vòng (7 ngày qua; trong ngoặc là 7 ngày trước): ${f.error ? unmeasured(f) : flowText(f)}.`] : []),
    `Việc đang làm: ${w?.error ? unmeasured(w) : wipText(w)}.`,
    ...(typeof m.lessons === 'string' ? [m.lessons] : []),
  ];
}

if (isMain(import.meta.url)) {
  try {
    const gh = makeGh();
    const { turnsFor } = await import('./collab-turn.mjs');
    const prs = gh.openPrs();
    process.stdout.write(`${renderMetrics(collectMetrics({ gh, prs, turns: turnsFor(prs) })).join('\n')}\n`);
  } catch (error) { process.stderr.write(`collab-metrics failed: ${clean(error.message, 300)}\n`); process.exitCode = 1; }
}
