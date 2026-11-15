// The day's work list with seats kept for the 7-week plan (owner 15.11.2026, "Bắt đầu": at least 2
// of the 3–5 daily items come from docs/plans/2026-11-15-ke-hoach-7-tuan-moc-do.md; a serious
// incident may still go first). One list per day: the morning list is used when it passes the same
// rules, otherwise the machine picks with the same function and says why.
// Plan critiqued by Codex on 15.11 (SỬA), points taken:
// - seats are counted per work item (`Việc: #N`), not per PR: two PRs of one item take one seat;
// - one candidate set for every path: workable PRs and 7-week task issues with no PR yet;
// - the 7-week class comes from GitHub labels read here, never from what the morning list claims;
// - tracker issues (no "## Tiêu chí đạt") are not items; drafts, needs-owner and other holds are
//   not candidates;
// - a label read that fails leaves the quota unknown (said so), never "no 7-week items";
// - serious incidents (issue labelled `incident` + `severity:P0|P1`, or a PR doing such an issue)
//   go first and are listed apart, outside the 3–5 count, so they never take a kept seat; overload
//   is reported, not silently resolved.
import { agentMarker, isTrusted, repo } from './collab-trust.mjs';
import { issueCriteria, workRef } from './collab-work.mjs';
import { isMain } from './is-main.mjs';

export const label7w = 'ke-hoach-7-tuan';
export const min7w = 2;
export const planCap = 5;
const names = labels => (labels ?? []).map(l => l?.name ?? l);
const serious = labels => { const n = names(labels); return n.includes('incident') && (n.includes('severity:P0') || n.includes('severity:P1')); };

// Open issues that matter to the quota: 7-week items and serious incidents. Throws on a failed read.
export function quotaIssues(gh) {
  const read = label => gh.json(['issue', 'list', '--repo', repo, '--state', 'open', '--label', label, '--limit', '200', '--json', 'number,title,labels,body']);
  const byNumber = new Map();
  for (const label of [label7w, 'incident']) for (const i of read(label) ?? []) byNumber.set(i.number, i);
  return [...byNumber.values()];
}

// Work units in priority order (turns are already sorted). One unit per `Việc: #N` (else per PR);
// a unit is 7-week or an incident when any of its PRs or its item issue carries the label.
// Issue-only units (7-week task issues with criteria, no open PR, not needs-owner) come after PRs.
export function workUnits({ turns, prs, issues }) {
  const prLabels = new Map((prs ?? []).map(p => [p.number, names(p.labels)]));
  const issueBy = new Map((issues ?? []).map(i => [i.number, i]));
  const units = new Map();
  for (const t of turns) {
    const key = t.item ? `item:${t.item}` : `pr:${t.number}`;
    const labels = [...(prLabels.get(t.number) ?? []), ...names(issueBy.get(t.item)?.labels)];
    const u = units.get(key) ?? { key, item: t.item ?? null, prs: [], turns: [], plan7w: false, incident: false, area: t.area, title: t.title };
    u.prs.push(t.number);
    u.turns.push(t);
    u.plan7w ||= labels.includes(label7w);
    u.incident ||= serious(labels.map(name => ({ name })));
    units.set(key, u);
  }
  const out = [...units.values()].map(u => ({ ...u, ready: u.turns.some(t => t.turn !== 'hold') }));
  const named = new Set(out.filter(u => u.item).map(u => u.item));
  for (const i of issues ?? []) {
    const n = names(i.labels);
    if (named.has(i.number) || n.includes('needs-owner') || !issueCriteria(i.body).length) continue;
    if (!n.includes(label7w) && !serious(i.labels)) continue;
    out.push({ key: `item:${i.number}`, item: i.number, prs: [], turns: [], plan7w: n.includes(label7w), incident: serious(i.labels), area: 'feature', title: i.title, ready: true, start: true });
  }
  return out;
}

// The day's list. Incidents first and apart; then min(2, ready 7-week units) kept seats; then the
// rest by priority, up to the cap. `fixed` (keys already picked, e.g. after `Bỏ #N`) stay first.
export function pickPlan(units, { cap = planCap, need = min7w, fixed = [] } = {}) {
  const ready = units.filter(u => u.ready);
  const incidents = ready.filter(u => u.incident);
  const pool = ready.filter(u => !u.incident);
  const keep = pool.filter(u => fixed.includes(u.key));
  const rest = pool.filter(u => !fixed.includes(u.key));
  const available7w = pool.filter(u => u.plan7w).length;
  const want = Math.min(need, available7w);
  const picked = [...keep];
  for (const u of rest.filter(u => u.plan7w)) if (picked.filter(p => p.plan7w).length < want && picked.length < cap) picked.push(u);
  for (const u of rest) if (!picked.includes(u) && picked.length < cap) picked.push(u);
  const order = new Map(pool.map((u, i) => [u.key, i]));
  picked.sort((a, b) => order.get(a.key) - order.get(b.key));
  return { items: picked, incidents, available7w, want, short7w: Math.max(0, want - picked.filter(p => p.plan7w).length) };
}

// The morning list (trusted comment with `morning-prep date=D` and `items=pr:N,item:M,...`), checked
// against the same units: every ref resolves to a ready unit, no unit twice, within the cap, and at
// least min(2, ready 7-week units) 7-week units by the labels read here.
export function prepRefs(comments, date) {
  const c = (comments ?? []).filter(x => isTrusted(x) && String(x.body ?? '').includes(`${agentMarker} morning-prep date=${date}`)).at(-1);
  if (!c) return null;
  const m = /items=([\w:,]+)/.exec(String(c.body));
  if (!m) return { refs: null };
  return { refs: m[1].split(',').filter(Boolean) };
}

export function checkPrep(refs, units, { cap = planCap, need = min7w } = {}) {
  const reasons = [];
  if (!Array.isArray(refs) || !refs.length) return { ok: false, reasons: ['danh sách sáng không có phần máy đọc được (items=)'] };
  const picked = [];
  for (const ref of refs) {
    const m = /^(pr|item):(\d+)$/.exec(ref);
    if (!m) { reasons.push(`không hiểu "${ref}"`); continue; }
    const n = Number(m[2]);
    const u = m[1] === 'pr' ? units.find(x => x.prs.includes(n)) : units.find(x => x.item === n);
    if (!u) { reasons.push(`${ref} không có trong danh sách việc mở`); continue; }
    if (!u.ready) { reasons.push(`${ref} đang giữ, chưa làm được`); continue; }
    if (picked.includes(u)) { reasons.push(`${ref} trùng việc ${u.key}`); continue; }
    picked.push(u);
  }
  const counted = picked.filter(u => !u.incident);
  if (counted.length > cap) reasons.push(`quá ${cap} việc`);
  const available7w = units.filter(u => u.ready && !u.incident && u.plan7w).length;
  const want = Math.min(need, available7w);
  const have = counted.filter(u => u.plan7w).length;
  if (have < want) reasons.push(`chỉ có ${have} việc kế hoạch 7 tuần, cần ${want}`);
  return { ok: reasons.length === 0, reasons, items: counted, incidents: picked.filter(u => u.incident), available7w, want, short7w: Math.max(0, want - have) };
}

// The one list of the day: the morning list when it passes, else the machine's pick, with a note.
export function dayList({ units, comments, date }) {
  const prep = prepRefs(comments, date);
  if (prep) {
    const c = checkPrep(prep.refs, units);
    if (c.ok) return { source: 'prep', note: 'Theo danh sách chuẩn bị buổi sáng.', ...c };
    return { source: 'machine', note: `Máy chọn lại vì danh sách buổi sáng chưa đạt: ${c.reasons.join('; ')}.`, ...pickPlan(units) };
  }
  return { source: 'machine', note: 'Chưa có danh sách buổi sáng; máy chọn theo cùng luật.', ...pickPlan(units) };
}

// What is recorded in the day state (L11: fixed at plan time).
export const plannedEntry = u => ({ ...(u.item ? { item: u.item } : { pr: u.prs[0] }), plan7w: Boolean(u.plan7w), ...(u.incident ? { incident: true } : {}), ...(u.start ? { start: true } : {}) });

if (isMain(import.meta.url)) {
  // Morning-prep self-check: node scripts/collab-quota.mjs --check "pr:491,item:512"
  const at = process.argv.indexOf('--check');
  if (at < 0) { process.stderr.write('Usage: node scripts/collab-quota.mjs --check "pr:N,item:M,..."\n'); process.exit(2); }
  const { makeGh } = await import('./collab-trust.mjs');
  const { turnsFor } = await import('./collab-turn.mjs');
  try {
    const gh = makeGh();
    const prs = gh.openPrs();
    const units = workUnits({ turns: turnsFor(prs, { baseFiles: gh.compareFiles }), prs, issues: quotaIssues(gh) });
    const r = checkPrep(String(process.argv[at + 1] ?? '').split(',').filter(Boolean), units);
    process.stdout.write(`${JSON.stringify({ ok: r.ok, reasons: r.reasons, plan7w: r.items?.filter(u => u.plan7w).map(u => u.key), want: r.want })}\n`);
    process.exitCode = r.ok ? 0 : 3;
  } catch (error) { process.stderr.write(`chưa xác định được quota: ${String(error.message).slice(0, 200)}\n`); process.exitCode = 1; }
}
