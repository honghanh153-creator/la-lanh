// Outcome numbers for the status board and the 12:00/22:00 digest (owner 12.11.2026).
// Every number comes from a real source: the copy registry in this checkout (the ops clone is
// pinned to collab/integration), git refs and merged PRs on GitHub. A source that cannot be read
// prints "chưa đo được (lý do)"; nothing is estimated.
import { execFileSync } from 'node:child_process';
import { digest, ownerOnly, readLocalRegistry, root } from './codex-copy-review.mjs';
import { wipCount, wipLimit } from './collab-buffer.mjs';
import { clean, integration, makeGh, repo } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

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

const reason = error => clean(String(error?.message ?? error).split('\n')[0], 120);
const measure = fn => { try { return fn(); } catch (error) { return { error: reason(error) }; } };

// Sources. `run` is execFileSync-shaped; tests pass their own.
export function collectMetrics({ registry = readLocalRegistry, run = execFileSync, gh = makeGh(), prs = [], turns = [], nowMs = Date.now() } = {}) {
  const git = args => String(run('/usr/bin/git', args, { cwd: root, encoding: 'utf8', timeout: 60000, stdio: ['ignore', 'pipe', 'pipe'] })).trim();
  const reg = measure(() => ({ value: registry() }));
  const fromRegistry = fn => (reg.error ? { error: `không đọc được kho câu chữ: ${reg.error}` } : measure(() => fn(reg.value)));
  // The tick's clone fetches only collab/integration; main is fetched here so the gap is current.
  const fetched = measure(() => { git(['fetch', '--quiet', 'origin', 'main', integration]); return {}; });
  const refs = fn => (fetched.error ? { error: `không lấy được nhánh từ GitHub: ${fetched.error}` } : measure(fn));
  const since = new Date(nowMs - 7 * dayMs).toISOString().slice(0, 10);
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
    leadTime: measure(() => leadTimeMetric(gh.json(['pr', 'list', '--repo', repo, '--base', integration, '--state', 'merged',
      '--search', `merged:>=${since}`, '--limit', '200', '--json', 'number,createdAt,mergedAt,baseRefName']), nowMs)),
    wip: measure(() => wipCount(prs, turns)),
  };
}

const unmeasured = m => `chưa đo được (${m.error})`;
const oneDecimal = n => n.toFixed(1).replace('.', ',');

// One short plain line per metric.
export function renderMetrics(m) {
  if (!m) return [];
  const { bundles: b, copy: c, ahead: a, mainAge: g, leadTime: l, wip: w } = m;
  return [
    `Bộ Daily phục vụ được: ${b?.error ? unmeasured(b) : `${b.ready}/${b.total} bộ`}.`,
    `Câu đã duyệt: ${c?.error ? unmeasured(c) : `${c.codex + c.owner}/${c.total} câu (Codex duyệt ${c.codex}, owner duyệt ${c.owner}, còn chờ ${c.pending})`}.`,
    `Khoảng cách tới người dùng: ${a?.error ? unmeasured(a) : `${a.commits} commit ở integration chưa lên main`}; ${g?.error ? `ngày cập nhật main ${unmeasured(g)}` : `main cập nhật lần cuối ${g.days} ngày trước`}.`,
    `Thời gian từ mở PR tới merge vào integration (7 ngày qua): ${l?.error ? unmeasured(l) : `trung vị ${oneDecimal(l.hours)} giờ (${l.count} PR)`}.`,
    `Việc đang làm: ${w?.error ? unmeasured(w) : `${w.inProgress}/${wipLimit.inProgress}, đang chờ review: ${w.inReview}/${wipLimit.inReview}`}.`,
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
