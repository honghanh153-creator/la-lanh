// Repeated check failures become an incident (three-agent dispatch 28.11.2026, part E).
// From 26.11 10:28 the Mac could not reach the server for the inside check six runs in a row and no
// incident was opened: each failed or refused run only wrote its done beat. Now every run of a
// check records its outcome here:
//   node scripts/collab-check-streak.mjs --record <check> --ok|--fail|--blocked
// `blocked` (the check could not run: network, SSH refused) counts like a failure: a check that
// cannot run is not a passing check. At `streakN` failures in a row one incident issue opens
// (labels `incident` + `ops-alert`, no severity, so the planner puts it first: L60). A pass closes it
// with a comment. One issue per check while it is open; a retry or a crash between the GitHub call
// and the state write finds the open issue by its exact title instead of opening a second one.
// Privacy: the repo is public. The issue holds only the check name, outcome kind, count and times;
// any detail text (hosts, error output) stays in the local state file.
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { clean, readJson, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { withFileLock } from './collab-lock.mjs';
import { isMain } from './is-main.mjs';

export const streakN = 3;
const repo = 'honghanh153-creator/la-lanh';
export const streakPath = () => join(stateDir, 'state', 'check-streaks.json');
export const outcomes = ['ok', 'fail', 'blocked'];
export const validCheck = name => /^[a-z0-9][a-z0-9-]{0,40}$/.test(String(name ?? ''));
const kindText = { fail: 'lỗi', blocked: 'không chạy được' };
const hhmm = t => { const v = vnNow(new Date(t)); return `${v.date.slice(8)}.${v.date.slice(5, 7)} ${String(v.hour).padStart(2, '0')}:${String(v.minute).padStart(2, '0')}`; };

export const issueTitle = check => `[ops-alert] kiểm tra ${check} lỗi nhiều lần liên tiếp`;
export function issueBody(check, s) {
  const kinds = [...new Set(s.recent.map(r => kindText[r.outcome]).filter(Boolean))].join(', ');
  return [
    `Kiểm tra \`${check}\` ${kinds} ${s.fails} lần liên tiếp, từ ${hhmm(s.firstFailAtMs)} tới ${hhmm(s.lastAtMs)}.`,
    'Máy tự mở sự cố này (#948, phần E). Chi tiết lỗi nằm trong file trạng thái trên máy, không đăng lên GitHub.',
    '',
    '## Tiêu chí đạt',
    `- AC1: kiểm tra \`${check}\` đạt lại ít nhất một lần (máy tự đóng issue khi đạt).`,
    '- AC2: ghi rõ nguyên nhân và cách tránh lặp lại (bài học hoặc kiểm tra bằng máy, R17).',
    '',
    '<!-- la-lanh-agent ops-alert check-streak -->',
  ].join('\n');
}

// Pure step. Returns { state, action: 'open' | 'resolve' | 'none', entry }.
export function recordCheck(state, check, outcome, { nowMs = Date.now(), detail = '', n = streakN } = {}) {
  if (!validCheck(check)) throw new Error(`tên kiểm tra không hợp lệ: ${clean(check, 60)}`);
  if (!outcomes.includes(outcome)) throw new Error(`kết quả không hợp lệ: ${clean(outcome, 20)}`);
  const prev = state?.[check] ?? { fails: 0, issue: null, recent: [] };
  const recent = [...(prev.recent ?? []), { outcome, atMs: nowMs, detail: clean(detail, 300) }].slice(-10);
  if (outcome === 'ok') {
    const entry = { fails: 0, issue: null, firstFailAtMs: null, lastAtMs: nowMs, lastOutcome: 'ok', recent, resolving: prev.issue ?? prev.resolving ?? null };
    return { state: { ...state, [check]: entry }, action: prev.issue ? 'resolve' : 'none', entry };
  }
  const fails = (prev.fails ?? 0) + 1;
  // A failure while a close is still pending keeps that issue open and counts on it.
  const issue = prev.issue ?? prev.resolving ?? null;
  const entry = { ...prev, fails, issue, firstFailAtMs: prev.fails ? prev.firstFailAtMs : nowMs, lastAtMs: nowMs, lastOutcome: outcome, recent, resolving: null };
  return { state: { ...state, [check]: entry }, action: fails >= n && !issue ? 'open' : 'none', entry };
}

// gh with fixed argv; `run(args, input)` returns stdout.
export function ghStreakIssues(run) {
  return {
    find: title => JSON.parse(run(['issue', 'list', '--repo', repo, '--label', 'ops-alert', '--state', 'open', '--search', `"${title}" in:title`, '--json', 'number,title', '--limit', '20']) || '[]').find(i => i.title === title)?.number ?? null,
    create: (title, body) => {
      const url = run(['issue', 'create', '--repo', repo, '--title', title, '--label', 'ops-alert', '--label', 'incident', '--body-file', '-'], body);
      return Number(String(url).trim().split('/').pop()) || null;
    },
    close: (number, body) => run(['issue', 'close', String(number), '--repo', repo, '--comment', body]),
  };
}

// Record one run, then act. The state is written before the GitHub call; a failed call is retried
// at the next record (open: the entry has no issue yet; resolve: `resolving` stays set).
export function record(check, outcome, { issues, path = streakPath(), nowMs = Date.now(), detail = '', n = streakN } = {}) {
  return withFileLock(`${path}.lock`, { staleMs: 60000, waitMs: 10000, busy: { status: 'busy' } }, () => {
    const step = recordCheck(readJson(path, {}), check, outcome, { nowMs, detail, n });
    writeJson(path, step.state);
    const entry = step.state[check];
    let issue = null;
    let error = null;
    try {
      if (step.action === 'open' || (entry.fails >= n && !entry.issue)) {
        const title = issueTitle(check);
        issue = issues.find(title) ?? issues.create(title, issueBody(check, entry));
        if (issue) writeJson(path, { ...readJson(path, {}), [check]: { ...entry, issue } });
      } else if (entry.resolving) {
        issue = entry.resolving;
        issues.close(issue, `Kiểm tra \`${check}\` đạt lại lúc ${hhmm(nowMs)}. Máy đóng sự cố này.`);
        writeJson(path, { ...readJson(path, {}), [check]: { ...entry, resolving: null } });
      }
    } catch (e) { error = clean(e.message, 200); }
    return { status: error ? 'pending' : 'recorded', action: step.action, fails: entry.fails, issue, error };
  });
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const at = args.indexOf('--record');
  const check = at >= 0 ? args[at + 1] : null;
  const outcome = ['--ok', '--fail', '--blocked'].find(f => args.includes(f))?.slice(2);
  const detailAt = args.indexOf('--detail');
  if (!check || !outcome) {
    process.stderr.write('Usage: node scripts/collab-check-streak.mjs --record <check> --ok|--fail|--blocked [--detail "text kept on this Mac"]\n');
    process.exit(2);
  }
  const run = (argv, input) => execFileSync(process.env.LA_LANH_GH || 'gh', argv, { encoding: 'utf8', input, stdio: ['pipe', 'pipe', 'pipe'], timeout: 30000 });
  try {
    const r = record(check, outcome, { issues: ghStreakIssues(run), detail: detailAt >= 0 ? args[detailAt + 1] : '' });
    process.stdout.write(`${JSON.stringify(r)}\n`);
    process.exitCode = r.status === 'recorded' ? 0 : 3;
  } catch (error) { process.stderr.write(`${clean(error.message, 200)}\n`); process.exitCode = 1; }
}
