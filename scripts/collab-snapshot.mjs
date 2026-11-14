// One source snapshot per report slot (lesson L19; owner 13.11 "báo cáo trung thực", lát 5 of
// docs/operations/codex-controls-claude-executes.md). Before this, the 12:00/22:00 digest counted
// the tick's own merges, the 08/14/22 report asked `gh pr list --limit 30` and counted again, the
// retro read its own logs, so one day could carry three different "merged" numbers.
// Plan critiqued by Codex on 14.11 (SỬA), points taken:
// - the day is the Vietnam day; the snapshot records its cut-off time, the integration head and the
//   state of every source; a source that fails is "chưa đo được", never 0;
// - a slot is written once, atomically (link, no overwrite): every report of the slot reads the
//   same file and prints its digest;
// - open incidents (ops-alert issues) are read from GitHub, so a clean tick that resets the
//   failure counter cannot make an incident disappear; only closing the issue does, and the loop
//   closes one only with recovery evidence (the watchdog: a new done beat of the stalled task).
// Slots: 08, 14, 22 (owner reports; the tick digest uses 14 and 22) and retro (23:35).
// Usage: node scripts/collab-snapshot.mjs --slot 14 [--date YYYY-MM-DD]   (takes or reads, prints)
import { createHash } from 'node:crypto';
import { linkSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { lessonsLine, prFields } from './collab-lessons.mjs';
import { clean, codexDailyCap, dayStatePath, integration, makeGh, readJson, repo, stateDir, vnNow } from './collab-trust.mjs';
import { ghFetch, renderProgress, workProgress } from './collab-work.mjs';

export const slots = ['08', '14', '22', 'retro'];
export const snapshotDir = () => join(stateDir, 'snapshots');
export const snapshotPath = (date, slot, dir = snapshotDir()) => join(dir, `${date}-${slot}.json`);

const hhmm = t => `${String(t.hour).padStart(2, '0')}:${String(t.minute).padStart(2, '0')}`;
const why = error => `chưa đo được: ${clean(String(error?.message ?? error), 160)}`;
// Each source is read on its own; a failure is recorded, never turned into an empty list.
const read = (sources, name, fn) => { try { const v = fn(); sources[name] = 'ok'; return v; } catch (error) { sources[name] = why(error); return null; } };
export const snapshotDigest = snap => createHash('sha256').update(JSON.stringify({ ...snap, digest: undefined })).digest('hex').slice(0, 12);

export function collect({ date, slot, gh, clock = () => new Date(), base, merged, openPrs, alerts, day, lessons, work }) {
  const at = clock();
  const sources = {};
  const snap = { version: 1, date, slot, takenAt: at.toISOString(), takenVn: hhmm(vnNow(at)) };
  snap.base = read(sources, 'base', base);
  // Merged into integration on the Vietnam day, up to the cut-off. A full page means the list may
  // be cut, which is not a number either.
  snap.merged = read(sources, 'merged', () => {
    const list = merged().filter(p => p.mergedAt && Date.parse(p.mergedAt) <= at.getTime() && vnNow(new Date(p.mergedAt)).date === date);
    return list.map(p => ({ number: p.number, title: clean(p.title ?? '', 120), mergedAt: p.mergedAt }));
  });
  snap.open = read(sources, 'open', () => {
    const prs = openPrs();
    return { count: prs.length, needsOwner: prs.filter(p => (p.labels ?? []).some(l => (l.name ?? l) === 'needs-owner')).map(p => p.number) };
  });
  snap.alerts = read(sources, 'alerts', () => alerts().map(i => ({ number: i.number, title: clean(i.title ?? '', 120), createdAt: i.createdAt })));
  snap.day = read(sources, 'day', () => { const d = day(); return { codexRuns: d.codexRuns ?? 0, failures: d.failures ?? 0, plannedItems: d.plannedItems ?? [] }; });
  snap.lessons = read(sources, 'lessons', lessons);
  snap.work = read(sources, 'work', () => work(snap.day?.plannedItems ?? []));
  snap.sources = sources;
  snap.digest = snapshotDigest(snap);
  return snap;
}

// Writes the slot once: link() fails when the file exists, so two reports of one slot never
// overwrite each other; the second one reads the first.
export function saveOnce(snap, path) {
  mkdirSync(join(path, '..'), { recursive: true });
  const tmp = `${path}.${process.pid}.${Date.now()}.tmp`;
  writeFileSync(tmp, `${JSON.stringify(snap, null, 1)}\n`, { mode: 0o600 });
  try { linkSync(tmp, path); return snap; }
  catch (error) { if (error.code !== 'EEXIST') throw error; return JSON.parse(readFileSync(path, 'utf8')); }
  finally { rmSync(tmp, { force: true }); }
}

export function realSources(gh, date) {
  return {
    base: () => gh.json(['api', `repos/${repo}/git/ref/heads/${integration}`]).object.sha,
    merged: () => {
      const limit = 300;
      const list = gh.json(['pr', 'list', '--repo', repo, '--state', 'merged', '--base', integration, '--limit', String(limit),
        '--search', `merged:${date}T00:00:00+07:00..${date}T23:59:59+07:00`, '--json', 'number,title,mergedAt']);
      if (list.length >= limit) throw new Error(`danh sách đủ ${limit} PR, có thể bị cắt`);
      return list;
    },
    openPrs: () => gh.openPrs(),
    alerts: () => gh.json(['issue', 'list', '--repo', repo, '--label', 'ops-alert', '--state', 'open', '--limit', '100', '--json', 'number,title,createdAt']),
    day: () => readJson(dayStatePath(date), {}),
    lessons: () => lessonsLine({ view: n => gh.json(['pr', 'view', String(n), '--repo', repo, '--json', prFields]) }),
    work: planned => workProgress({ date, planned, fetch: ghFetch(gh) }),
  };
}

export function takeSnapshot({ slot, date = vnNow().date, gh = makeGh(), dir = snapshotDir(), sources = null, clock } = {}) {
  if (!slots.includes(slot)) throw new Error(`slot phải là một trong ${slots.join(', ')}`);
  const path = snapshotPath(date, slot, dir);
  try { return JSON.parse(readFileSync(path, 'utf8')); } catch {}
  return saveOnce(collect({ date, slot, clock, ...(sources ?? realSources(gh, date)) }), path);
}

const or = (value, render, source) => (value === null ? `chưa đo được (${String(source ?? '').replace(/^chưa đo được: /, '')})` : render(value));
const when = iso => { const t = vnNow(new Date(iso)); return `${t.date.slice(8)}/${t.date.slice(5, 7)} ${hhmm(t)}`; };
export const incidentLines = alerts => (alerts.length ? alerts.map(a => `#${a.number} ${a.title} (từ ${when(a.createdAt)})`) : []);

// The fixed block every report of the slot prints. The last line names the snapshot.
export function renderSnapshot(s) {
  const src = s.sources ?? {};
  return [
    `- Đã gộp vào integration hôm nay: ${or(s.merged, m => `${m.length} PR`, src.merged)}.`,
    `- ${s.work === null ? `Việc đạt tiêu chí: ${or(null, null, src.work)}.` : renderProgress(s.work)}`,
    `- PR đang mở: ${or(s.open, o => `${o.count}${o.needsOwner.length ? ` (chờ owner: ${o.needsOwner.map(n => `#${n}`).join(', ')})` : ''}`, src.open)}.`,
    `- Sự cố đang mở: ${or(s.alerts, a => (a.length ? incidentLines(a).join('; ') : 'không có'), src.alerts)}.`,
    `- Lượt Codex hôm nay: ${or(s.day, d => `${d.codexRuns}/${codexDailyCap}; lỗi liên tiếp: ${d.failures}`, src.day)}.`,
    `- ${s.lessons ?? `Lời hứa sửa quy trình: ${or(null, null, src.lessons)}.`}`,
    `Nguồn: bản chụp ${s.date} khung ${s.slot}, lấy lúc ${s.takenVn}${s.base ? `, integration ${String(s.base).slice(0, 7)}` : ''} · snapshot ${s.digest}`,
  ];
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const flag = name => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
  try {
    const snap = takeSnapshot({ slot: flag('--slot'), date: flag('--date') ?? vnNow().date });
    process.stdout.write(`${renderSnapshot(snap).join('\n')}\n`);
  } catch (error) { process.stderr.write(`collab-snapshot: ${error.message}\n`); process.exitCode = 1; }
}
