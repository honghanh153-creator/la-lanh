// Throughput on the loop board (owner 22.11.2026 "okie 1-2-3", plan item 3; L72). Shows whether the
// work keeps moving while Claude is short, in percents and counts only (R14: no amounts):
// - Claude today against the daily budget: weekly points used today vs (100 − 5% reserve − used) ÷
//   days to the weekly reset. The reset time comes with the weekly % (`resetsAt` in
//   state/claude-usage.json, written by the autopilot); without it the budget is unknown.
// - Lá Lành: PRs merged into collab/integration today (Vietnam day) and Claude points per merged PR.
// - Gỡ Vướng: lots passed today per stream, backlog and missed schedules (target 0), from the status
//   file its coordinator writes: state/go-vuong-status.json =
//   {"at": ISO, "streams": [{"name", "passedToday", "backlog", "missedSchedules"}]}. Older than 3 hours
//   is shown as old; missing is said, never guessed.
// - First-pass acceptance over 7 days: a Codex fix (fallback-runs.jsonl) passes when no later Codex fix
//   was needed on that PR and no review asked for changes on its head; an Antigravity critic run
//   (antigravity-runs.jsonl) passes when its answer was counted, not dropped.
// - Share of today's Claude spend by what started the turn (collab-usage.mjs `triggerOf`), by the
//   context each call carried, and the costliest pairs (owner plan 22.11 "cắt tự chạy và nhắn qua lại",
//   L73). Target: calls above 500k context under 10% of spend. Per merged PR and per passed lot use
//   only that project's share of today's spend.
import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { lastSecond } from './codex-fallback.mjs';
import { integration, parseVerdict, readJson, repo, stateDir, trustedComments, vnNow } from './collab-trust.mjs';
import { usagePath } from './collab-usage.mjs';

export const reservePct = 5;
export const windowDays = 7;
export const goVuongPath = (home = stateDir) => join(home, 'state', 'go-vuong-status.json');
export const antigravityRunsPath = (home = stateDir) => join(home, 'antigravity-runs.jsonl');
export const fallbackRunsPath = (home = stateDir) => join(home, 'fallback-runs.jsonl');
const dayMs = 86400000;
const staleMs = 3 * 3600 * 1000;
const pct = x => `${Math.round(x * 100)}%`;
const pts = x => `${Math.round(x * 10) / 10}`;

// Weekly points used today and the even daily budget left until the reset.
export function claudeBudget(usage, { resetsAt = null, now = new Date() } = {}) {
  if (!usage || !Number.isFinite(usage.percent)) return { today: null, daily: null };
  const today = usage.dayStart && usage.dayStart.day === vnNow(now).date ? Math.max(0, usage.percent - usage.dayStart.percent) : null;
  const reset = Date.parse(resetsAt ?? '');
  if (!Number.isFinite(reset) || reset <= now.getTime()) return { today, daily: null };
  const days = Math.max(1, (reset - now.getTime()) / dayMs);
  return { today, daily: Math.max(0, 100 - reservePct - usage.percent) / days };
}

export function readLines(path) {
  if (!existsSync(path)) return [];
  return readFileSync(path, 'utf8').split('\n').filter(Boolean).flatMap(l => { try { return [JSON.parse(l)]; } catch { return []; } });
}
const recent = (rows, now) => rows.filter(r => now.getTime() - Date.parse(r.at ?? '') <= windowDays * dayMs);

// Codex fixes that needed nothing more. A run on a PR no longer open counts as passed only when no
// later fix followed (it merged or was closed); an open one waits for its verdict.
export function codexFirstPass(runs, openPrs = []) {
  let pass = 0, fail = 0;
  runs.forEach((r, i) => {
    if (runs.slice(i + 1).some(x => x.pr === r.pr)) { fail++; return; }
    const pr = (openPrs ?? []).find(p => p.number === r.pr);
    if (!pr) { pass++; return; }
    if (pr.headRefOid === r.head && lastSecond(pr)?.s.verdict === 'REQUEST_CHANGES') { fail++; return; }
    const v = trustedComments(pr.comments).map(c => parseVerdict(c.body)).filter(x => x?.sha === r.head).at(-1);
    if (v?.verdict === 'APPROVE') pass++;
    else if (v?.verdict === 'REQUEST_CHANGES') fail++;
  });
  return { pass, fail };
}
export const antigravityFirstPass = runs => ({ pass: runs.filter(r => r.status === 'posted').length, fail: runs.filter(r => r.status === 'dropped').length });

export function readGoVuong(home = stateDir, now = new Date()) {
  const raw = readJson(goVuongPath(home), null);
  if (!raw || !Array.isArray(raw.streams)) return null;
  const at = Date.parse(raw.at ?? '');
  const streams = raw.streams.filter(s => s && typeof s.name === 'string').slice(0, 8).map(s => ({
    name: s.name.replace(/[^\p{L}\p{N} ._-]/gu, '').slice(0, 30), passedToday: Number(s.passedToday) || 0, backlog: Number(s.backlog) || 0, missedSchedules: Number(s.missedSchedules) || 0,
  }));
  return { old: !Number.isFinite(at) || now.getTime() - at > staleMs, streams };
}

export function mergedToday(gh, now = new Date()) {
  const today = vnNow(now).date;
  const since = new Date(now.getTime() - dayMs).toISOString().slice(0, 10);
  const rows = JSON.parse(String(gh.raw(['pr', 'list', '--repo', repo, '--state', 'merged', '--base', integration, '--search', `merged:>=${since}`, '--json', 'number,mergedAt', '--limit', '100'])) || '[]');
  return rows.filter(r => vnNow(new Date(r.mergedAt)).date === today).length;
}

const rate = ({ pass, fail }) => (pass + fail ? `${pct(pass / (pass + fail))} (${pass}/${pass + fail})` : 'chưa có lượt');

// The board lines. Every input is optional; a missing number is said, not guessed.
export const TRIGGER_NAMES = { task: 'việc nền xong', session: 'tin phiên khác', owner: 'owner', schedule: 'lịch', autofix: 'Autofix', subagent: 'trợ lý', other: 'khác' };
export const CTX_NAMES = { '<100k': 'dưới 100k', '100-200k': '100–200k', '200-500k': '200–500k', '>500k': 'trên 500k' };
export const bigCtxTarget = 0.1;
const listShares = (shares, names) => Object.entries(names).filter(([k]) => shares[k] > 0.005).map(([k, n]) => `${n} ${pct(shares[k])}`).join(' · ') || 'chưa có';
export function throughputLines({ budget = {}, merged = null, goVuong = null, codex = null, antigravity = null, split = null, projectShares = null }) {
  const share = name => (projectShares ? projectShares.find(p => p.project === name)?.share ?? 0 : null);
  const out = [];
  const { today, daily } = budget;
  out.push(`Claude hôm nay: ${today === null || today === undefined ? 'chưa có số' : `${pts(today)} điểm tuần`} / ngân sách ngày ${daily === null || daily === undefined ? 'chưa biết (thiếu giờ đặt lại)' : `${pts(daily)} điểm`}${Number.isFinite(today) && Number.isFinite(daily) && today > daily ? ' ⚠️ vượt' : ''}`);
  const la = share('la-lanh');
  if (merged === null) out.push('Lá Lành: chưa đọc được số PR merge hôm nay');
  else out.push(`Lá Lành: ${merged} PR merge hôm nay${merged && Number.isFinite(today) && la !== null ? ` · ${pts(today * la / merged)} điểm Claude mỗi PR` : ''}`);
  if (!goVuong) out.push('Gỡ Vướng: chưa có file trạng thái');
  else {
    const lots = goVuong.streams.reduce((a, s) => a + s.passedToday, 0);
    const other = share('dự án khác');
    const perLot = lots && Number.isFinite(today) && other !== null ? ` · ${pts(today * other / lots)} điểm Claude mỗi lô đạt` : '';
    out.push(`Gỡ Vướng${goVuong.old ? ' (số cũ hơn 3 giờ)' : ''}: ${goVuong.streams.map(s => `${s.name} qua ${s.passedToday} lô, tồn ${s.backlog}, lỡ lịch ${s.missedSchedules}${s.missedSchedules ? ' ⚠️' : ''}`).join('; ') || 'không có luồng'}${perLot}`);
  }
  out.push(`Đạt ngay lần đầu (7 ngày): Codex sửa ${codex ? rate(codex) : 'chưa có số'} · Antigravity phản biện ${antigravity ? rate(antigravity) : 'chưa có số'}`);
  if (!split) { out.push('Claude hôm nay theo nguồn: chưa có số'); return out; }
  out.push(`Claude hôm nay theo nguồn: ${listShares(split.triggerShares ?? {}, TRIGGER_NAMES)}`);
  const big = split.ctxShares?.['>500k'] ?? 0;
  out.push(`Theo độ dài phiên: ${listShares(split.ctxShares ?? {}, CTX_NAMES)}${big >= bigCtxTarget ? ` ⚠️ trên 500k cần dưới ${pct(bigCtxTarget)}` : ''}`);
  const top = Object.entries(split.cellShares ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 3).filter(([, v]) => v > 0.005)
    .map(([k, v]) => { const [t, b] = k.split('|'); return `${TRIGGER_NAMES[t] ?? t} × ${CTX_NAMES[b] ?? b} ${pct(v)}`; });
  if (top.length) out.push(`Tốn nhất: ${top.join(' · ')}`);
  return out;
}

// What one tick needs. `usageNote` is the tick's usage reading (collab-usage.mjs usageTick).
export function throughputTick(opts) {
  try { return throughputRead(opts); } catch (error) { opts?.log?.(`throughput failed: ${String(error.message).slice(0, 200)}`); return ['Năng suất: chưa đọc được số (xem log tick)']; }
}
function throughputRead({ gh, prs = [], usageNote = null, home = stateDir, now = new Date(), log = () => {} }) {
  const resetsAt = readJson(usagePath(home), null)?.resetsAt ?? null;
  let merged = null;
  try { merged = mergedToday(gh, now); } catch (error) { log(`throughput merged read failed: ${String(error.message).slice(0, 200)}`); }
  return throughputLines({
    budget: claudeBudget(usageNote?.usage, { resetsAt, now }),
    merged,
    goVuong: readGoVuong(home, now),
    codex: codexFirstPass(recent(readLines(fallbackRunsPath(home)), now), prs),
    antigravity: antigravityFirstPass(recent(readLines(antigravityRunsPath(home)), now)),
    split: usageNote?.today?.measured ? usageNote.today : null,
    projectShares: usageNote?.today?.measured ? usageNote.today.shares : null,
  });
}
