// Nightly audit, part (a): the facts for the 3+3 day workflow experiment
// (docs/operations/workflow-experiment-2026-11.md, lesson L21). No AI here: every number comes
// from GitHub, the loop's own state files and the local Codex output files, with its source.
// A source that cannot be read gives `value: null` and a reason, never 0. Part (b) (L21b) hands
// these facts and the day's owner reports to Codex for M1 and the judgement calls.
// Plan critiqued by Codex before building (13.11): provisional before the day ends, final after;
// a hand-written verdict with the review marker is not a real receipt.
// Usage: node scripts/collab-audit.mjs [--date YYYY-MM-DD]   (prints JSON, writes experiment/<date>.json)
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { clean, dayStatePath, integration, makeGh, readJson, repo, reviewState, stateDir, vnNow } from './collab-trust.mjs';

export const experimentDir = join(stateDir, 'experiment');
const reason = error => clean(String(error?.message ?? error).split('\n')[0], 160);
export const unmeasured = why => ({ value: null, missing: clean(why || 'không rõ lý do', 300) });
// One Codex run a day is kept back from reviews and the copy batch, so the night audit (L21b) is
// not starved by a busy day (Codex 14.11). Every automatic path stops at codexDailyCap - auditReserve.
export const auditReserve = 1;
// The promise register and the disagreement log are measured from the first experiment day. Before
// it (the 11–13.11 baseline) they did not exist in this form, so M4 and M8 are "chưa đo được",
// never 0 or a value rebuilt from today's register (Codex 14.11, L23).
export const logsStart = '2026-11-14';
const median = xs => { const s = [...xs].sort((a, b) => a - b); const m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
export const dayRange = date => `${date}T00:00:00+07:00..${date}T23:59:59+07:00`;

// A real review receipt: the last trusted verdict before the merge is Codex's automatic APPROVE of
// the merged head, and its "Output SHA-256" matches a local Codex output file for that PR and head.
// The marker alone can be typed by anyone posting as the owner (Codex 13.11).
export function receipt(pr, outputs) {
  const before = { ...pr, comments: (pr.comments ?? []).filter(c => !pr.mergedAt || String(c.createdAt) <= String(pr.mergedAt)) };
  const last = reviewState(before).last;
  if (!last) return { ok: false, why: 'không có verdict' };
  if (!last.auto) return { ok: false, why: 'verdict không phải review tự động' };
  if (last.verdict.verdict !== 'APPROVE') return { ok: false, why: `verdict cuối là ${last.verdict.verdict}` };
  if (last.verdict.sha !== pr.headRefOid) return { ok: false, why: 'APPROVE không phải của head đã merge' };
  const digest = /Output SHA-256: `([0-9a-f]{64})`/.exec(String(last.body ?? ''))?.[1];
  if (!digest) return { ok: false, why: 'verdict không có mã băm output' };
  const match = outputs.find(o => o.pr === pr.number && o.head12 === pr.headRefOid.slice(0, 12) && o.digest === digest);
  if (!match) return { ok: false, why: 'không có file output Codex khớp mã băm' };
  return { ok: true };
}

// Local Codex outputs written by codex-review.mjs: logs/codex-<date>-pr<N>-<head12>-<ms>.json.
export function readOutputs(dir = join(stateDir, 'logs')) {
  if (!existsSync(dir)) return [];
  const pattern = /^codex-\d{4}-\d{2}-\d{2}-pr(\d+)-([0-9a-f]{12})-\d+\.json$/;
  return readdirSync(dir).map(name => ({ name, m: pattern.exec(name) })).filter(x => x.m)
    .map(({ name, m }) => ({ pr: Number(m[1]), head12: m[2], digest: createHash('sha256').update(readFileSync(join(dir, name))).digest('hex') }));
}

export function collectFacts({ date, gh = makeGh(), now = new Date(), outputs = () => readOutputs(), day = d => readJson(dayStatePath(d), null),
  lessons = null, disagreements = null } = {}) {
  const final = vnNow(now).date > date;
  const facts = { date, final, collectedAt: now.toISOString(), metrics: {} };
  const M = facts.metrics;

  let merged = null;
  try {
    merged = gh.json(['pr', 'list', '--repo', repo, '--base', integration, '--state', 'merged', '--search', `merged:${dayRange(date)}`,
      '--limit', '200', '--json', 'number,title,headRefOid,createdAt,mergedAt,comments']);
  } catch (error) { merged = null; facts.mergedError = reason(error); }
  const tooMany = Array.isArray(merged) && merged.length >= 200;

  // M2: merges without a real review receipt.
  if (!merged) M.M2 = unmeasured(`không đọc được PR đã merge: ${facts.mergedError}`);
  else {
    let outs;
    try { outs = outputs(); } catch (error) { outs = null; M.M2 = unmeasured(`không đọc được file output Codex: ${reason(error)}`); }
    if (outs) {
      const items = merged.map(pr => ({ pr: pr.number, ...receipt(pr, outs) })).filter(r => !r.ok).map(({ pr, why }) => ({ pr, why }));
      M.M2 = { value: items.length, of: merged.length, items, ...(tooMany ? { missing: 'có thể thiếu PR (chạm giới hạn 200)' } : {}) };
    }
  }

  // M3: escape candidates (reverts merged, ops alerts opened). Codex links them to approved PRs in
  // part (b); a fix-forward issue opened at review time is not an escape.
  try {
    const alerts = gh.json(['issue', 'list', '--repo', repo, '--label', 'ops-alert', '--state', 'all', '--search', `created:${dayRange(date)}`, '--limit', '100', '--json', 'number,title,createdAt']);
    const reverts = (merged ?? []).filter(pr => /^revert\b/i.test(pr.title ?? '')).map(pr => ({ pr: pr.number, title: clean(pr.title, 120) }));
    M.M3 = merged ? { value: null, candidates: { reverts, alerts: alerts.map(a => ({ issue: a.number, title: clean(a.title, 120) })) }, missing: 'chờ Codex nối với PR đã duyệt (L21b)' }
      : unmeasured(`không đọc được PR đã merge: ${facts.mergedError}`);
  } catch (error) { M.M3 = unmeasured(`không đọc được ops-alert: ${reason(error)}`); }

  // M4: promises (scripts/collab-lessons.mjs when present).
  if (date < logsStart) M.M4 = unmeasured('giai đoạn nền: sổ lời hứa chưa có, không dựng lại từ sổ hôm nay');
  else try {
    const s = lessons ? lessons() : null;
    M.M4 = s ? { value: { done: s.done, open: s.open, overdue: s.overdue, owner: s.owner, unconfirmed: s.unconfirmed } } : unmeasured('chưa có sổ lời hứa ở bản này');
  } catch (error) { M.M4 = unmeasured(`không đọc được sổ lời hứa: ${reason(error)}`); }

  // M5: work items meeting their acceptance criteria. Not measurable yet: the plan stores PR
  // numbers, not task ids with criteria (Codex 13.11). Counting PRs here would inflate it.
  M.M5 = unmeasured('plan ngày chưa có mã việc và tiêu chí đạt; không đếm PR thay cho việc');

  // M6: median hours from open to merge, PRs merged this day only (fixed window).
  if (!merged) M.M6 = unmeasured(`không đọc được PR đã merge: ${facts.mergedError}`);
  else {
    const hours = merged.map(p => (Date.parse(p.mergedAt) - Date.parse(p.createdAt)) / 3600000).filter(h => Number.isFinite(h) && h >= 0);
    M.M6 = hours.length ? { value: Math.round(median(hours) * 10) / 10, count: hours.length } : { value: null, missing: 'không có PR merge trong ngày' };
  }

  // M7: trusted automatic verdicts before the merge, per merged PR.
  if (!merged) M.M7 = unmeasured(`không đọc được PR đã merge: ${facts.mergedError}`);
  else {
    const rounds = merged.map(pr => ({ pr: pr.number, rounds: reviewState({ ...pr, comments: (pr.comments ?? []).filter(c => String(c.createdAt) <= String(pr.mergedAt)) }).trusted.filter(c => c.auto && c.verdict).length }));
    M.M7 = rounds.length ? { value: Math.round(median(rounds.map(r => r.rounds)) * 10) / 10, items: rounds } : { value: null, missing: 'không có PR merge trong ngày' };
  }

  // M8: disagreements recorded today (arm 1: Claude records them; Codex checks for gaps in part b).
  if (date < logsStart) M.M8 = unmeasured('giai đoạn nền: chưa có sổ bất đồng');
  else if (!disagreements) M.M8 = unmeasured('chưa có sổ bất đồng ở bản này');
  else try {
    const all = disagreements().filter(d => d.date === date);
    const entries = all.filter(d => d.type !== 'override');
    M.M8 = { value: entries.length, codex: entries.filter(d => d.winner === 'codex').length, claude: entries.filter(d => d.winner === 'claude').length,
      owner: entries.filter(d => d.winner === 'owner').length, overrides: all.filter(d => d.type === 'override').length };
  } catch (error) { M.M8 = unmeasured(`không đọc được sổ bất đồng: ${reason(error)}`); }

  // M9: Codex runs the loop counted (runs outside the counter are not seen).
  const state = (() => { try { return day(date); } catch { return null; } })();
  // Baseline runs made on this day stay in M9 and are shown apart (Codex 14.11), never subtracted.
  M.M9 = state && Number.isInteger(state.codexRuns) ? { value: state.codexRuns, ...(state.baselineRuns ? { baseline: state.baselineRuns } : {}), missing: 'chỉ tính lượt được vòng ghi nhận' } : unmeasured('không có file trạng thái ngày');

  // M10: stalls and owner questions need an event history the loop does not keep yet.
  M.M10 = unmeasured('watchdog chỉ giữ beat mới nhất; chưa có lịch sử kẹt và câu hỏi gửi owner');

  M.M1 = unmeasured('chờ Codex đối chiếu báo cáo với dữ kiện (L21b)');
  return facts;
}

// The record = facts of part (a) + Codex's judgement (part b, collab-audit-night.mjs); M1 and M3
// in `metrics` come from the judgement.
export function withJudgement(facts, judgement) {
  const metrics = { ...facts.metrics };
  if (judgement?.result) {
    metrics.M1 = judgement.result.M1;
    metrics.M3 = { ...judgement.result.M3, candidates: facts.metrics.M3?.candidates };
  } else if (judgement?.missing) {
    metrics.M1 = unmeasured(judgement.missing);
    metrics.M3 = { ...unmeasured(judgement.missing), candidates: facts.metrics.M3?.candidates };
  }
  return { ...facts, metrics, ...(judgement ? { judgement } : {}) };
}

// Same date, same file: a re-run replaces the provisional facts, never duplicates them, and a
// final record is never replaced by a provisional one. A re-run by hand keeps Codex's judgement
// and the posted comment of part (b).
export function saveFacts(facts, dir = experimentDir) {
  mkdirSync(dir, { recursive: true });
  const path = join(dir, `${facts.date}.json`);
  const old = existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : null;
  if (old?.final && !facts.final) return { path, kept: true };
  const record = old?.judgement ? { ...withJudgement(facts, old.judgement), posted: old.posted ?? null } : facts;
  writeFileSync(path, `${JSON.stringify(record, null, 1)}\n`);
  return { path, kept: false };
}

// The register and the disagreement log arrive in other PRs (#481); without them M4/M8 stay
// unmeasured. lessons(date) returns the register summary for that day.
export async function loadAuditDeps() {
  let lessons = null;
  try {
    const mod = await import('./collab-lessons.mjs');
    lessons = date => { const reg = mod.readRegister(); return mod.summarize(reg, { today: date, verified: mod.verify(reg) }); };
  } catch { lessons = null; }
  let disagreements = null;
  try { const mod = await import('./collab-disagree.mjs'); disagreements = () => mod.read(); } catch { disagreements = null; }
  return { lessons, disagreements };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const args = process.argv.slice(2);
    const date = args.includes('--date') ? args[args.indexOf('--date') + 1] : vnNow().date;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date ?? '')) throw new Error('--date YYYY-MM-DD');
    const deps = await loadAuditDeps();
    const lessons = deps.lessons ? () => deps.lessons(date) : null;
    const facts = collectFacts({ date, lessons, disagreements: deps.disagreements });
    const saved = saveFacts(facts);
    process.stdout.write(`${JSON.stringify({ ...facts, saved })}\n`);
  } catch (error) { process.stderr.write(`collab-audit failed: ${reason(error)}\n`); process.exitCode = 1; }
}
