// Claude usage on the loop board (owner plan 22.11.2026, item 3; L67). The account's weekly Claude
// limit reached 80% in two days; the owner chose to see it every tick and to switch work to Codex
// when Claude is nearly used up ("chuyển qua codex khi claude gần hết. giữ 5% claude để duy trì nếu cần").
// - Weekly %: the autopilot scheduled task writes {"percent","at"} to state/claude-usage.json each run
//   (from the desktop app's "Weekly · all models" number). The loop cannot read that number itself.
// - Mode: below 85% normal, 85–94% saving (Claude only for incident or safety work), 95% or more
//   fallback (Claude-fix turns go to Codex; 5% stays in reserve). A reading older than 3 hours is
//   unknown: the last mode is kept, never a guess.
// - Today's share per project: local transcripts (~/.claude/projects) priced at the public per-model
//   API prices. Only a share is shown on the public board (no amounts, R14); other projects are one
//   bucket, without names.
// - Pace alert: one ops alert a day when the weekly % gained today passes 70% of an even weekly pace
//   (0.7 × 100/7 = 10 points in one Vietnam day).
import { closeSync, existsSync, openSync, readdirSync, readSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';

export const savingAt = 85;
export const fallbackAt = 95;
export const staleMs = 3 * 3600 * 1000;
export const pacePart = 0.7;
export const paceLimit = (pacePart * 100) / 7;

export const usagePath = (home = stateDir) => join(home, 'state', 'claude-usage.json');
export const modePath = (home = stateDir) => join(home, 'state', 'claude-mode.json');
export const scanPath = (home = stateDir) => join(home, 'state', 'claude-usage-scan.json');
export const projectsRoot = (user = homedir()) => join(user, '.claude', 'projects');

export const MODES = { normal: 'bình thường', saving: 'tiết kiệm', fallback: 'chuyển sang Codex' };
export function modeFor(percent) {
  if (!Number.isFinite(percent)) return null;
  return percent >= fallbackAt ? 'fallback' : percent >= savingAt ? 'saving' : 'normal';
}

// The current mode, from the latest reading. Writes the mode file only on a fresh reading, so a stale
// or missing one keeps the last mode. Also keeps the first reading of each Vietnam day (the pace base).
export function readUsage({ home = stateDir, now = new Date() } = {}) {
  const last = readJson(modePath(home), null);
  const raw = readJson(usagePath(home), null);
  const percent = Number(raw?.percent);
  const at = Date.parse(raw?.at ?? '');
  const fresh = Number.isFinite(percent) && percent >= 0 && percent <= 100 && Number.isFinite(at) && now - at <= staleMs && at - now <= 5 * 60000;
  if (!fresh) return { percent: Number.isFinite(percent) ? percent : null, at: raw?.at ?? null, fresh: false, mode: last?.mode ?? 'normal', dayStart: last?.dayStart ?? null };
  const day = vnNow(new Date(at)).date;
  // A drop means the weekly window reset: today's gain counts from zero.
  let dayStart = last?.dayStart?.day === day ? last.dayStart : { day, percent };
  if (percent < dayStart.percent) dayStart = { day, percent: 0 };
  const state = { mode: modeFor(percent), percent, at: raw.at, dayStart };
  if (JSON.stringify(state) !== JSON.stringify(last)) writeJson(modePath(home), state);
  return { percent, at: raw.at, fresh: true, mode: state.mode, dayStart };
}

// Public API prices per million tokens (claude-api skill table, cached 03.11.2026): input, output,
// cache read. A 5-minute cache write is 1.25 × input. Unknown models price as Opus (the safe side).
export const PRICES = [
  [/fable-5-2|mythos-5-2/, [8, 40, 0.2]],
  [/fable|mythos/, [10, 50, 1]],
  [/opus-5-5/, [4, 20, 0.2]],
  [/opus/, [5, 25, 0.5]],
  [/sonnet-5/, [2, 10, 0.1]],
  [/sonnet/, [3, 15, 0.3]],
  [/haiku-5/, [0.1, 0.5, 0.01]],
  [/haiku/, [1, 5, 0.1]],
];
export function costOf(model, u = {}) {
  const [input, output, read] = PRICES.find(([re]) => re.test(String(model ?? '')))?.[1] ?? [4, 20, 0.2];
  const n = k => Number(u[k]) || 0;
  return (n('input_tokens') * input + n('cache_creation_input_tokens') * input * 1.25 + n('cache_read_input_tokens') * read + n('output_tokens') * output) / 1e6;
}

// la-lanh checkouts and their worktrees are one project; every other folder is "dự án khác" on the board.
export const projectOf = dir => (/-la-lanh(?:$|-|--)/.test(dir) ? 'la-lanh' : 'dự án khác');

// Cost per Vietnam day for one transcript file, read from a saved offset so a long session is not
// parsed again every tick. One assistant message can span several lines with the same id and usage:
// the last ids seen are kept with the offset.
export const chunkBytes = 8 * 1024 * 1024;
export function scanFile(path, prev = null, { stat = statSync(path), chunk = chunkBytes } = {}) {
  const fresh = !prev || stat.size < prev.offset || stat.ino !== prev.ino;
  const rec = fresh ? { ino: stat.ino, offset: 0, days: {}, ids: [] } : { ...prev, days: { ...prev.days }, ids: [...prev.ids] };
  if (stat.size <= rec.offset) return rec;
  const seen = new Set(rec.ids);
  const fd = openSync(path, 'r');
  try {
    let carry = Buffer.alloc(0);
    let pos = rec.offset;
    while (pos < stat.size) {
      const buf = Buffer.alloc(Math.min(chunk, stat.size - pos));
      const got = readSync(fd, buf, 0, buf.length, pos);
      if (!got) break;
      pos += got;
      const data = carry.length ? Buffer.concat([carry, buf.subarray(0, got)]) : buf.subarray(0, got);
      const end = data.lastIndexOf(10);
      if (end < 0) { carry = data; continue; }
      for (const line of data.subarray(0, end).toString('utf8').split('\n')) {
        if (!line.includes('"usage"')) continue;
        let e;
        try { e = JSON.parse(line); } catch { continue; }
        const m = e?.message;
        if (e?.type !== 'assistant' || !m?.usage) continue;
        if (m.id) { if (seen.has(m.id)) continue; seen.add(m.id); rec.ids.push(m.id); }
        const t = Date.parse(e.timestamp ?? '');
        if (!Number.isFinite(t)) continue;
        const day = vnNow(new Date(t)).date;
        rec.days[day] = (rec.days[day] ?? 0) + costOf(m.model, m.usage);
      }
      rec.offset += end + 1;
      carry = data.subarray(end + 1);
    }
  } finally { closeSync(fd); }
  rec.ids = rec.ids.slice(-50);
  // Only the last week of days is kept per file.
  rec.days = Object.fromEntries(Object.entries(rec.days).sort().slice(-8));
  return rec;
}

function* transcripts(root) {
  let dirs = [];
  try { dirs = readdirSync(root, { withFileTypes: true }).filter(d => d.isDirectory()); } catch { return; }
  for (const d of dirs) {
    const stack = [join(root, d.name)];
    while (stack.length) {
      const dir = stack.pop();
      let items = [];
      try { items = readdirSync(dir, { withFileTypes: true }); } catch { continue; }
      for (const it of items) {
        if (it.isDirectory()) stack.push(join(dir, it.name));
        else if (it.name.endsWith('.jsonl')) yield { project: projectOf(d.name), path: join(dir, it.name) };
      }
    }
  }
}

// Today's API-price cost per project. Only files touched since the start of the day are read; the
// per-file record is cached locally (state dir, never pushed).
export function todayShares({ home = stateDir, root = projectsRoot(), now = new Date() } = {}) {
  const today = vnNow(now).date;
  const dayStartMs = now.getTime() - ((vnNow(now).hour * 60 + vnNow(now).minute) * 60000) - 60000;
  const cache = readJson(scanPath(home), {});
  const next = {};
  const cost = {};
  for (const { project, path } of transcripts(root)) {
    let stat;
    try { stat = statSync(path); } catch { continue; }
    if (stat.mtimeMs < dayStartMs) continue;
    let rec;
    try { rec = scanFile(path, cache[path], { stat }); } catch { continue; }
    next[path] = rec;
    if (rec.days[today]) cost[project] = (cost[project] ?? 0) + rec.days[today];
  }
  try { writeJson(scanPath(home), next); } catch {}
  const total = Object.values(cost).reduce((a, b) => a + b, 0);
  const shares = Object.entries(cost).sort((a, b) => (b[0] === 'la-lanh') - (a[0] === 'la-lanh')).map(([project, c]) => ({ project, share: total ? c / total : 0 }));
  return { day: today, shares, measured: total > 0 };
}

// One board line, and warnings for the "Cần xem" block.
export function usageLine(usage, today = null) {
  const week = usage.percent === null ? 'chưa có số' : `${usage.percent}%${usage.fresh ? '' : ' (số cũ hơn 3 giờ)'}`;
  const shares = today?.measured ? today.shares.map(s => `${s.project} ${Math.round(s.share * 100)}%`).join(', ') : 'chưa đo được';
  return `Claude tuần: ${week} · chế độ: ${MODES[usage.mode] ?? usage.mode} · hôm nay theo dự án: ${shares}`;
}
export function usageHealth(usage) {
  const out = [];
  if (!usage.fresh) out.push(`⚠️ Số lượt Claude ${usage.at ? 'cũ hơn 3 giờ' : 'chưa có'}: giữ chế độ ${MODES[usage.mode]}. Tác vụ autopilot ghi số mỗi lượt chạy.`);
  if (usage.mode === 'saving') out.push(`⚠️ Claude đã dùng ${usage.percent}% tuần: chỉ dùng Claude cho sự cố và việc an toàn.`);
  if (usage.mode === 'fallback') out.push(`⚠️ Claude đã dùng ${usage.percent}% tuần: lượt sửa của Claude chuyển sang Codex, giữ 5% cho việc gấp.`);
  return out;
}

// The weekly % gained today, when it passes 70% of an even pace. Null when below or unknown.
export function paceOver(usage) {
  if (!usage.fresh || !usage.dayStart) return null;
  const gained = usage.percent - usage.dayStart.percent;
  return gained > paceLimit ? { day: usage.dayStart.day, gained } : null;
}
export const paceSubject = 'Claude dùng nhanh hơn nhịp tuần';
export function paceWatch({ usage, alert, home = stateDir }) {
  const over = paceOver(usage);
  if (!over) return null;
  const sent = readJson(join(home, 'state', 'claude-pace-alert.json'), {});
  if (sent.day === over.day) return null;
  alert(`Hôm nay Claude đã dùng thêm ${Math.round(over.gained)}% giới hạn tuần (tuần đang ở ${usage.percent}%). Nhịp đều là ${Math.round(100 / 7)}% mỗi ngày; mức báo là ${Math.round(paceLimit)}%. Từ ${savingAt}% vòng chỉ dùng Claude cho sự cố, từ ${fallbackAt}% chuyển việc sửa sang Codex.`);
  writeJson(join(home, 'state', 'claude-pace-alert.json'), { day: over.day, gained: over.gained });
  return over;
}

export function hasUsageFile(home = stateDir) { return existsSync(usagePath(home)); }

// What one tick needs: the board line, the warnings, and the pace alert sent at most once a day.
export function usageTick({ alert, home = stateDir, root = projectsRoot(), now = new Date() } = {}) {
  const usage = readUsage({ home, now });
  let today = null;
  try { today = todayShares({ home, root, now }); } catch {}
  if (alert) paceWatch({ usage, alert, home });
  return { line: usageLine(usage, today), health: usageHealth(usage), mode: usage.mode };
}
