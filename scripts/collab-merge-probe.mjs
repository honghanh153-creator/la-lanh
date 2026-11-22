// Same-file holds, observed with a trial merge (S29, retro 17.11; 3+3 review 21.11, owner approved
// research item 2 on 21.11.2026). Observe only: nothing here changes a turn, a hold or a merge.
// fileBlocker (collab-turn.mjs) holds a PR while an earlier PR changes one of the same files. A shared
// file does not mean a conflict, and a conflict can happen without one. Once an hour the tick takes
// every PR held as "chờ PR #N cùng file", fetches both heads into the ops clone and runs
// `git merge-tree --write-tree` on them. Each (PR head, blocker head) pair is written once to
// merge-probe.jsonl with the integration tip, the shared files and the result: clean, conflict or
// unknown. A missing object or any other error is "unknown", never "clean" (3+3 review).
// Pre-registered measures (docs/reviews/2026-11-20-workflow-experiment-review.md): share of same-file
// holds whose trial merge is clean, per week; read with --report before any rule changes.
// Usage: node scripts/collab-merge-probe.mjs --report [--days 7]
import { execFileSync } from 'node:child_process';
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { clean, readJson, stateDir, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const probeLogPath = () => join(stateDir, 'merge-probe.jsonl');
export const probeStatePath = () => join(stateDir, 'state', 'merge-probe.json');
export const probeEveryMs = 60 * 60000;
export const holdReason = /^chờ PR #(\d+) cùng file$/;
const opsDir = () => join(stateDir, 'ops');

const prFiles = pr => (pr.files ?? []).map(f => f?.path ?? f).filter(p => typeof p === 'string' && p);
const readLog = path => (existsSync(path) ? readFileSync(path, 'utf8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean) : []);

// The pairs held only because of a shared file, from the turns the loop computed.
export function sameFileHolds(prs, turns) {
  const byNumber = new Map(prs.map(p => [p.number, p]));
  return turns.filter(t => t.turn === 'hold').map(t => ({ t, m: holdReason.exec(String(t.reason ?? '')) })).filter(x => x.m)
    .map(({ t, m }) => ({ pr: byNumber.get(t.number), blocker: byNumber.get(Number(m[1])) }))
    .filter(x => x.pr && x.blocker);
}

// git merge-tree: exit 0 clean, 1 conflict, anything else unknown. Both heads are fetched first.
export function trialMerge(a, b, { dir = opsDir(), run = execFileSync } = {}) {
  const git = (args, opts = {}) => run('/usr/bin/git', ['-C', dir, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 120000, ...opts });
  try {
    // --no-write-fetch-head (Codex r1 on #850): the ops clone is shared, and ops-run.sh and
    // collab-cron.sh pick the reviewed code to run by reading FETCH_HEAD right after their own fetch of
    // collab/integration. A probe fetch that rewrote FETCH_HEAD in between would hand them a PR head.
    git(['fetch', '--quiet', '--no-tags', '--no-write-fetch-head', 'origin',`+refs/pull/${a.number}/head:refs/probe/${a.number}`, `+refs/pull/${b.number}/head:refs/probe/${b.number}`]);
  } catch (error) { return { result: 'unknown', why: `fetch: ${clean(String(error.stderr ?? error.message).split('\n')[0], 160)}` }; }
  try {
    git(['cat-file', '-e', `${a.headRefOid}^{commit}`]);
    git(['cat-file', '-e', `${b.headRefOid}^{commit}`]);
  } catch { return { result: 'unknown', why: 'head đã đổi hoặc không có trong clone' }; }
  try {
    git(['merge-tree', '--write-tree', '--no-messages', a.headRefOid, b.headRefOid]);
    return { result: 'clean' };
  } catch (error) {
    if (error.status === 1) return { result: 'conflict' };
    return { result: 'unknown', why: clean(String(error.stderr ?? error.message).split('\n')[0], 160) };
  }
}

// Called by the tick entry. Runs at most once an hour; returns the new entries.
export function probeHolds({ list, trial = trialMerge, nowMs = Date.now(), path = probeLogPath(), statePath = probeStatePath(), log = () => {} } = {}) {
  const state = readJson(statePath, {});
  if (Number.isFinite(state.lastRunMs) && nowMs - state.lastRunMs < probeEveryMs) return [];
  writeJson(statePath, { lastRunMs: nowMs });
  const { prs, turns } = list();
  const seen = new Set(readLog(path).map(e => `${e.pr}@${e.head}|${e.blocker}@${e.blockerHead}`));
  const added = [];
  for (const { pr, blocker } of sameFileHolds(prs, turns)) {
    const key = `${pr.number}@${pr.headRefOid}|${blocker.number}@${blocker.headRefOid}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const shared = prFiles(pr).filter(f => prFiles(blocker).includes(f));
    const out = trial(pr, blocker);
    const entry = { at: new Date(nowMs).toISOString(), pr: pr.number, head: pr.headRefOid, blocker: blocker.number, blockerHead: blocker.headRefOid,
      base: pr.baseTipOid ?? null, shared: shared.slice(0, 20), result: out.result, ...(out.why ? { why: out.why } : {}) };
    mkdirSync(dirname(path), { recursive: true });
    appendFileSync(path, `${JSON.stringify(entry)}\n`);
    added.push(entry);
  }
  if (added.length) log(`merge probe: ${added.length} cặp giữ vì cùng file — sạch ${added.filter(e => e.result === 'clean').length}, xung đột ${added.filter(e => e.result === 'conflict').length}, không kiểm được ${added.filter(e => e.result === 'unknown').length}`);
  return added;
}

// The pre-registered measure: of the same-file holds seen in the window, how many would merge cleanly.
export function probeReport(entries, { nowMs = Date.now(), days = 7 } = {}) {
  const since = nowMs - days * 86400000;
  const recent = entries.filter(e => Date.parse(e.at) >= since);
  const count = r => recent.filter(e => e.result === r).length;
  const pairs = new Set(recent.map(e => `${e.pr}|${e.blocker}`)).size;
  const judged = count('clean') + count('conflict');
  return { days, observed: recent.length, pairs, clean: count('clean'), conflict: count('conflict'), unknown: count('unknown'),
    cleanShare: judged ? Math.round((count('clean') / judged) * 1000) / 10 : null };
}

export function renderReport(r) {
  return [
    `Thử merge các PR bị giữ vì cùng file, ${r.days} ngày qua (chỉ quan sát, không đổi luật):`,
    `- Lần thử: ${r.observed} trên ${r.pairs} cặp PR.`,
    `- Sạch: ${r.clean}; xung đột: ${r.conflict}; không kiểm được: ${r.unknown}.`,
    r.cleanShare === null ? '- Tỉ lệ sạch: chưa đo được (chưa có lần thử nào kiểm được).' : `- Tỉ lệ sạch trong các lần kiểm được: ${r.cleanShare}%.`,
  ].join('\n');
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.includes('--report')) {
    const days = Number(args[args.indexOf('--days') + 1]) || 7;
    process.stdout.write(`${renderReport(probeReport(readLog(probeLogPath()), { days }))}\n`);
  } else process.stdout.write('Usage: node scripts/collab-merge-probe.mjs --report [--days 7]\n');
}

