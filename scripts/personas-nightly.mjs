// Nightly fake-user run (owner 15.11.2026, hub #2 comment 6893191704): on a day when
// collab/integration got an app-facing change, run the same 200 of the 1000 fictional personas on
// the integration commit from the start of the day and the one at the end, with the same clock,
// data and scoring, then report the difference for the 07:00 report.
//
//   node scripts/personas-nightly.mjs prepare [--date YYYY-MM-DD] [--any-time]
//   node scripts/personas-nightly.mjs check   --date D judge-NN        (validate one judge output)
//   node scripts/personas-nightly.mjs merge   --date D <out.json>...  (fold blind scores in)
//   node scripts/personas-nightly.mjs codex   --date D                (Codex cross-scores the pre-chosen sample)
//   node scripts/personas-nightly.mjs finish  --date D                (reports, comparison, alerts)
//
// Blind judging of new text is done by Claude subagents between prepare and finish (the scheduled
// task's prompt drives that step); the script never calls a model except Codex in `codex`, which
// counts against the shared day cap. Everything runs on the owner's Mac with local SQLite and
// fictional data; nothing is sent anywhere except the ops-alert issue text, which holds no data.
import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { homedir, loadavg } from 'node:os';
import { join } from 'node:path';
import { acquireLock } from './collab-lock.mjs';
import { machineBusy } from './collab-check.mjs';
import { auditReserve } from './collab-audit.mjs';
import { codexBin, codexModel } from './codex-review.mjs';
import { opsAlert } from './collab-turn.mjs';
import { cutoffMs, dayCap, dayStatePath, hhmmOf, integration, lastStartAt, makeGh, readJson, repo, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';
import { personasReceiptResult, writeRunReceipt } from './collab-run-receipt.mjs';

export const sampleSize = 200;
export const codexSampleSize = 10;
export const chunkSize = 75;
export const nightlyDir = () => join(stateDir, 'personas-nightly');
export const dayDir = date => join(nightlyDir(), date);
export const reportRoot = () => process.env.LA_LANH_REPORT_DIR || join(homedir(), 'Documents', 'New project', 'la-lanh-bao-cao');
const harnessPaths = [':(glob)apps/api/scripts/persona_*.py', 'qa/personas'];
const git = (args, opts = {}) => String(execFileSync('/usr/bin/git', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, ...opts })).trim();

// ---------------------------------------------------------------- what counts as an app change

// Owner's list: apps/web/src, apps/api/app, user copy, assets, config, migrations, dependencies.
// Anything matched by neither list is "unknown" and also triggers a run.
const appFacing = [
  /^apps\/web\/src\//, /^apps\/web\/public\//, /^apps\/web\/index\.html$/, /^apps\/api\/app\//,
  /^apps\/api\/migrations\//, /^apps\/api\/alembic\.ini$/, /^apps\/mobile\//, /^packages\//,
  /(^|\/)assets\//, /(^|\/)package\.json$/, /^pnpm-lock\.yaml$/, /^pnpm-workspace\.yaml$/,
  /^apps\/api\/pyproject\.toml$/, /^apps\/api\/uv\.lock$/, /^apps\/web\/[^/]*\.config\.[a-z]+$/,
  /^apps\/web\/tsconfig[^/]*\.json$/, /^vendor\//, /^Dockerfile$/, /^infra\//,
];
const notApp = [
  /^docs\//, /^scripts\//, /^qa\//, /^plans\//, /^prototype\//, /^\.github\//, /^\.claude\//,
  /^apps\/api\/tests\//, /^apps\/api\/scripts\//, /^apps\/web\/tests\//, /\.(test|spec)\.[^/]+$/,
  /\.md$/i, /(^|\/)\.gitignore$/, /^LICENSE$/, /^NOTICE$/, /\.command$/,
];
export function classifyChanges(paths = []) {
  const out = { app: [], unknown: [], other: [] };
  for (const p of paths) {
    if (appFacing.some(re => re.test(p))) out.app.push(p);
    else if (notApp.some(re => re.test(p))) out.other.push(p);
    else out.unknown.push(p);
  }
  return { ...out, run: out.app.length + out.unknown.length > 0 };
}

// ---------------------------------------------------------------- the 200 personas of the day

export const seedOf = date => `personas-nightly:${date}`;
const rank = (seed, id) => createHash('sha256').update(`${seed}:${id}`).digest('hex');
// Fixed per date: the same date always gives the same 200, and nobody chooses them by hand.
export function pickIds(date, ids, n = sampleSize) {
  const seed = seedOf(date);
  return [...ids].sort((a, b) => (rank(seed, a) < rank(seed, b) ? -1 : rank(seed, a) > rank(seed, b) ? 1 : 0)).slice(0, n).sort();
}
// Codex's sample is chosen from the new items before any score exists.
export function pickCodexItems(date, itemIds, n = codexSampleSize) {
  const seed = `${seedOf(date)}:codex`;
  return [...itemIds].sort((a, b) => (rank(seed, a) < rank(seed, b) ? -1 : 1)).slice(0, n);
}

export function nextDay(date) {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + 1);
  return d.toISOString().slice(0, 10);
}

// ---------------------------------------------------------------- blind-score cache across nights

const labelFiles = { 'judge-scores.json': 'scores', 'action-weight.json': 'labels' };
export function unionLabels(a, b, key) {
  const base = a && typeof a === 'object' ? a : {};
  return { ...base, ...(b ?? {}), [key]: { ...(base[key] ?? {}), ...(b?.[key] ?? {}) } };
}
const readMaybe = path => { try { return JSON.parse(readFileSync(path, 'utf8')); } catch { return null; } };
// Repo cache plus every score judged on earlier nights, written into the clone the report runs in.
function pushLabels(clone) {
  const store = join(nightlyDir(), 'labels');
  for (const [file, key] of Object.entries(labelFiles)) {
    const path = join(clone, 'qa', 'personas', 'labels', file);
    writeFileSync(path, `${JSON.stringify(unionLabels(readMaybe(path), readMaybe(join(store, file)), key), null, 1)}\n`);
  }
}
function pullLabels(clone) {
  const store = join(nightlyDir(), 'labels');
  mkdirSync(store, { recursive: true });
  for (const [file, key] of Object.entries(labelFiles)) {
    const merged = unionLabels(readMaybe(join(store, file)), readMaybe(join(clone, 'qa', 'personas', 'labels', file)), key);
    writeFileSync(join(store, file), `${JSON.stringify(merged, null, 1)}\n`);
  }
}

// ---------------------------------------------------------------- judge output check

export function checkJudgeOutput(packetLines, out) {
  const want = packetLines.filter(l => l.trim()).map(l => JSON.parse(l).item_id);
  const problems = [];
  if (!Array.isArray(out)) return ['output is not a JSON array'];
  const got = out.map(r => r?.item_id);
  const missing = want.filter(id => !got.includes(id));
  const extra = got.filter(id => !want.includes(id));
  if (missing.length || extra.length || new Set(got).size !== got.length) {
    problems.push(`item_ids differ: missing ${missing.length}, extra ${extra.length}, duplicates ${got.length - new Set(got).size}`);
  }
  for (const r of out) {
    if (!Number.isInteger(r?.score) || r.score < 1 || r.score > 5) problems.push(`${r?.item_id}: score must be an integer 1-5`);
    if (typeof r?.reason !== 'string' || !r.reason.trim()) problems.push(`${r?.item_id}: reason is empty`);
  }
  return problems;
}

export function checkLabelOutput(packetLines, out) {
  const want = packetLines.filter(l => l.trim()).map(l => JSON.parse(l).action);
  if (!Array.isArray(out)) return ['output is not a JSON array'];
  const got = out.map(r => r?.action);
  const problems = [];
  const missing = want.filter(a => !got.includes(a));
  const extra = got.filter(a => !want.includes(a));
  if (missing.length || extra.length || new Set(got).size !== got.length) {
    problems.push(`actions differ: missing ${missing.length}, extra ${extra.length}, duplicates ${got.length - new Set(got).size}`);
  }
  for (const r of out) if (!['light', 'not_light'].includes(r?.label)) problems.push(`${String(r?.action).slice(0, 40)}: label must be light or not_light`);
  return problems;
}

// ---------------------------------------------------------------- comparison and alerts

export function compareRuns(start, end) {
  const rows = (end.verdicts ?? []).map((v, i) => {
    const s = (start.verdicts ?? [])[i] ?? {};
    return { group: v.group, threshold: v.threshold, start: s.result ?? '—', startOk: s.ok ?? null, end: v.result, endOk: v.ok };
  });
  const safety = rows.filter(r => r.group === 'An toàn' && r.startOk === true && r.endOk === false)
    .map(r => `${r.threshold}: đạt ở đầu ngày, trượt ở cuối ngày`);
  const s = start.crisis ?? {};
  const e = end.crisis ?? {};
  if ((e.crisis_caught ?? 0) < (s.crisis_caught ?? 0)) safety.push(`số câu khủng hoảng được chuyển sang hỗ trợ giảm từ ${s.crisis_caught} xuống ${e.crisis_caught}`);
  if ((e.figurative_flagged ?? 0) > (s.figurative_flagged ?? 0)) safety.push(`báo nhầm câu "chết" nghĩa bóng tăng từ ${s.figurative_flagged} lên ${e.figurative_flagged}`);
  if ((e.ordinary_flagged ?? 0) > (s.ordinary_flagged ?? 0)) safety.push(`báo nhầm câu hỏi Tarot thường tăng từ ${s.ordinary_flagged} lên ${e.ordinary_flagged}`);
  return { rows, safety };
}

// A persona's own typed text showing up in another persona's screen is a data leak between
// guests. Only ids and days go in the report, never the text.
const shownText = r => [r.headline, r.thesis, r.scene, r.la_line, r.action, r.situation, r.why_today, r.mood_reaction,
  ...(r.tarot ?? []).flatMap(t => [t.headline, t.summary])].filter(v => typeof v === 'string').join('\n');
export function crossLeaks(rows, minLength = 15) {
  const owners = new Map();
  for (const r of rows) {
    for (const t of r.tarot ?? []) {
      const text = String(t?.text ?? '').trim();
      if (text.length >= minLength) owners.set(text, (owners.get(text) ?? new Set()).add(r.persona));
    }
  }
  const found = [];
  for (const r of rows) {
    const shown = shownText(r);
    for (const [text, who] of owners) {
      if (!who.has(r.persona) && shown.includes(text)) found.push({ persona: r.persona, day: r.day, from: [...who].sort()[0] });
    }
  }
  return found;
}

// ---------------------------------------------------------------- clones and runs

function prepareClone(role, sha, harnessSha) {
  const dir = join(nightlyDir(), `clone-${role}`);
  mkdirSync(nightlyDir(), { recursive: true });
  if (!existsSync(join(dir, '.git'))) git(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, dir]);
  git(['-C', dir, 'fetch', '--quiet', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`]);
  git(['-C', dir, 'checkout', '--quiet', '--force', '--detach', sha]);
  git(['-C', dir, 'clean', '-fdq']);
  // Same simulator and scoring for both commits: the end-of-day harness over the start-of-day app.
  if (harnessSha !== sha) git(['-C', dir, 'checkout', harnessSha, '--', ...harnessPaths]);
  if (git(['-C', dir, 'rev-parse', 'HEAD']) !== sha) throw new Error(`clone-${role} is not at ${sha}`);
  execFileSync('make', ['-s', '-C', join(dir, 'vendor', 'swisseph')], { stdio: 'ignore' });
  return dir;
}

const uvArgs = (clone, args) => ['run', '--locked', '--directory', join(clone, 'apps', 'api'), 'python', '-m', ...args];

function runSim(clone, personasPath, out, { limitMs = 30 * 60000 } = {}) {
  return new Promise(resolve => {
    const started = Date.now();
    const loads = [];
    const sample = () => loads.push(loadavg()[0]);
    sample();
    const timer = setInterval(sample, 15000);
    const child = spawn('uv', uvArgs(clone, ['scripts.persona_sim', '--personas', personasPath, '--out', out]), { cwd: clone, stdio: ['ignore', 'ignore', 'pipe'], detached: true });
    let tail = '';
    child.stderr.on('data', d => { tail = `${tail}${d}`.slice(-2000); });
    const kill = setTimeout(() => { try { process.kill(-child.pid, 'SIGKILL'); } catch {} }, limitMs);
    child.on('close', code => {
      clearInterval(timer);
      clearTimeout(kill);
      sample();
      resolve({ code, seconds: Math.round((Date.now() - started) / 1000), loadMax: Math.max(...loads), loadMean: loads.reduce((a, b) => a + b, 0) / loads.length, ...(code === 0 ? {} : { tail: tail.slice(-300) }) });
    });
  });
}

function report(clone, run, personasPath, title) {
  pushLabels(clone);
  execFileSync('uv', uvArgs(clone, ['scripts.persona_report', '--run', run, '--personas', personasPath, '--title', title]), { cwd: clone, stdio: 'ignore' });
  return JSON.parse(readFileSync(join(run, 'metrics.json'), 'utf8'));
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
// The heavy-job lock the author check uses, plus no other heavy test process on the machine.
export async function withHeavyLock(fn, { waitMs = 30 * 60000, stepMs = 60000 } = {}) {
  const until = Date.now() + waitMs;
  for (;;) {
    if (!machineBusy()) {
      const release = acquireLock(join(stateDir, 'check.lock'), { staleMs: 2 * 3600000 });
      if (release) { try { return await fn(); } finally { release(); } }
    }
    if (Date.now() >= until) return { status: 'busy', reason: 'máy đang chạy việc nặng khác quá 30 phút' };
    await sleep(stepMs);
  }
}

// ---------------------------------------------------------------- commands

const writeState = (date, state) => writeJson(join(dayDir(date), 'state.json'), state);
// One Codex call per night survives a re-run of prepare, which resets the date directory.
const attemptsPath = () => join(nightlyDir(), 'codex-attempts.json');
export const codexAttempted = date => Boolean(readJson(attemptsPath(), {})[date]);
const recordAttempt = (date, entry) => writeJson(attemptsPath(), { ...readJson(attemptsPath(), {}), [date]: entry });
const readState = date => {
  const state = readJson(join(dayDir(date), 'state.json'), null);
  if (!state) throw new Error(`no prepared run for ${date}; run prepare first`);
  return state;
};
function writeSkip(date, reason, extra = {}) {
  const out = join(reportRoot(), nextDay(date), 'personas');
  mkdirSync(out, { recursive: true });
  writeFileSync(join(out, 'report.md'), `# Người giả hằng đêm, ngày ${date}\n\nKhông chạy: ${reason}\n`);
  writeFileSync(join(out, 'metrics.json'), `${JSON.stringify({ date, skipped: true, reason, ...extra }, null, 1)}\n`);
  return { status: 'skipped', reason, report: join(out, 'report.md') };
}

const pastStart = (date, now = vnNow()) => date === now.date && now.hour * 60 + now.minute >= lastStartAt;
const refusedLate = { status: 'refused', reason: `quá ${hhmmOf(lastStartAt)}, không bắt đầu việc mới` };

// The date folder is shared by every step of a night. It is reset only by the holder of the
// heavy-job lock, so a second prepare for the same date waits instead of deleting a running
// night's files (#565).
export function startRun(date, fn, lockOptions) {
  return withHeavyLock(async () => {
    const dir = dayDir(date);
    rmSync(dir, { recursive: true, force: true });
    mkdirSync(dir, { recursive: true });
    return fn(dir);
  }, lockOptions);
}

// Research item 3, Codex r5/r6 on #858: a night that stops after its integration commit was chosen
// (simulation timeout or non-zero exit, out of time, a failed report) leaves an error receipt naming
// that commit, so the board never shows "chưa chạy" or an older good night for it. The error goes on
// to the caller unchanged. A night that never started (busy, too late) threw nothing: no receipt.
export async function withFailureReceipt(sha, fn, receipt = writeRunReceipt, counts = {}) {
  try { return await fn(); } catch (error) {
    try { receipt({ kind: 'personas', result: personasReceiptResult({ failed: true }), sha, counts }); } catch {}
    throw error;
  }
}

export async function prepare({ date = vnNow().date, anyTime = false, alerting = {}, receipt = writeRunReceipt } = {}) {
  if (!anyTime && pastStart(date)) return refusedLate;
  const work = join(nightlyDir(), 'clone-end');
  mkdirSync(nightlyDir(), { recursive: true });
  if (!existsSync(join(work, '.git'))) git(['clone', '--quiet', '--no-checkout', `https://github.com/${repo}.git`, work]);
  git(['-C', work, 'fetch', '--quiet', 'origin', `+refs/heads/${integration}:refs/remotes/origin/${integration}`]);
  const ref = `origin/${integration}`;
  const start = git(['-C', work, 'rev-list', '-1', '--first-parent', `--before=${date} 00:00 +0700`, ref]);
  const end = git(['-C', work, 'rev-parse', ref]);
  const changed = start === end ? [] : git(['-C', work, 'diff', '--name-only', `${start}..${end}`]).split('\n').filter(Boolean);
  const kinds = classifyChanges(changed);
  const base = { date, start, end, appChanges: kinds.app, unknownChanges: kinds.unknown };
  if (!kinds.run) return writeSkip(date, start === end ? 'hôm nay không có commit mới trên nhánh chung' : 'hôm nay không có thay đổi chạm tới app', base);

  return withFailureReceipt(end, () => startRun(date, async dir => {
    if (!anyTime && pastStart(date)) return refusedLate;
    const limitMs = () => (anyTime ? 30 * 60000 : Math.min(30 * 60000, cutoffMs(date) - Date.now()));
    const endClone = prepareClone('end', end, end);
    const startClone = prepareClone('start', start, end);
    // Both simulations read the same cached action labels (the sim uses them to decide keeps).
    pushLabels(endClone);
    pushLabels(startClone);
    const all = JSON.parse(readFileSync(join(endClone, 'qa', 'personas', 'personas-1000.json'), 'utf8')).personas;
    const ids = pickIds(date, all.map(p => p.id));
    const personasPath = join(dir, 'personas-200.json');
    writeFileSync(personasPath, `${JSON.stringify({ seed: seedOf(date), personas: all.filter(p => ids.includes(p.id)) }, null, 1)}\n`);
    const runs = {};
    const metrics = {};
    for (const [role, clone] of [['start', startClone], ['end', endClone]]) {
      const out = join(dir, role);
      if (limitMs() <= 0) throw new Error('hết giờ trong ngày trước khi chạy xong');
      runs[role] = await runSim(clone, personasPath, out, { limitMs: limitMs() });
      if (runs[role].code !== 0) throw new Error(`persona_sim ${role} exit ${runs[role].code}: ${runs[role].tail}`);
      metrics[role] = report(endClone, out, personasPath, `${role} ${date}`);
    }
    const packets = new Map();
    const labels = new Set();
    for (const role of ['start', 'end']) {
      for (const line of readFileSync(join(dir, role, 'judge-packets.jsonl'), 'utf8').split('\n').filter(Boolean)) packets.set(JSON.parse(line).item_id, line);
      for (const line of readFileSync(join(dir, role, 'label-packets.jsonl'), 'utf8').split('\n').filter(Boolean)) labels.add(line);
    }
    const lines = [...packets.values()];
    const chunks = [];
    for (let i = 0; i < lines.length; i += chunkSize) {
      const name = `judge-${String(chunks.length + 1).padStart(2, '0')}`;
      writeFileSync(join(dir, `${name}.jsonl`), `${lines.slice(i, i + chunkSize).join('\n')}\n`);
      chunks.push(name);
    }
    if (labels.size) writeFileSync(join(dir, 'label-01.jsonl'), `${[...labels].join('\n')}\n`);
    writeFileSync(join(dir, 'judge-rubric.md'), readFileSync(join(endClone, 'qa', 'personas', 'judge-rubric.md')));
    const codexItems = pickCodexItems(date, [...packets.keys()]);
    writeFileSync(join(dir, 'codex-sample.jsonl'), codexItems.map(id => packets.get(id)).join('\n') + (codexItems.length ? '\n' : ''));
    mkdirSync(join(dir, 'out'), { recursive: true });
    const state = { ...base, seed: seedOf(date), ids, runs, chunks, labelPackets: labels.size, codexItems, preparedAt: new Date().toISOString(), alerted: [] };
    const safety = safetyReasons(metrics.start, metrics.end, transcriptRows(dir, 'end'));
    writeState(date, state);
    const raised = raiseNew(date, state, safety.reasons, alerting);
    writeState(date, state);
    return { status: 'prepared', dir, chunks, labelPackets: labels.size, codexItems: codexItems.length, alert: raised.raised.length > 0, reasons: raised.raised };
  }), receipt);
}

export function check(date, chunk) {
  const lines = readFileSync(join(dayDir(date), `${chunk}.jsonl`), 'utf8').split('\n');
  const out = readMaybe(join(dayDir(date), 'out', `${chunk}.json`));
  if (out === null) return ['output file is missing or not JSON'];
  return chunk.startsWith('label-') ? checkLabelOutput(lines, out) : checkJudgeOutput(lines, out);
}

export function merge(date, files) {
  readState(date);
  const clone = join(nightlyDir(), 'clone-end');
  pushLabels(clone);
  for (const file of files) execFileSync('uv', uvArgs(clone, ['scripts.persona_validate', '--merge', file]), { cwd: clone, stdio: 'ignore' });
  pullLabels(clone);
  return { status: 'merged', files: files.length };
}

const codexPrompt = `Bạn là giám khảo mù. Đọc rubric ở \`judge-rubric.md\` (chỉ phần "Câu hỏi chấm" và quy tắc chấm).
Tệp \`codex-sample.jsonl\` có mỗi dòng một mục JSON: \`profile\` là một người hư cấu, \`today\` là nội dung app cho họ xem trong một ngày.
Chấm từng mục độc lập, từ góc nhìn người đó, theo thang 1–5 của rubric. Không đọc file nào khác.
Trả lời CHỈ một mảng JSON \`[{"item_id": "...", "score": 1-5, "reason": "một câu tiếng Việt ngắn"}]\`, đủ mọi mục, đúng item_id.`;

export function codex(date, { run = execFileSync, now = vnNow, nowMs = Date.now } = {}) {
  const state = readState(date);
  const dir = dayDir(date);
  if (!state.codexItems?.length) return { status: 'skipped', reason: 'không có nội dung mới để Codex chấm đối chiếu' };
  // The prepared night's own 23:59, so a run that slips past midnight does not start a call.
  const leftMs = cutoffMs(date) - nowMs();
  if (leftMs <= 60000) return { status: 'refused', reason: 'hết giờ trong ngày' };
  // Same lock as codex-review, copy review and the night audit: admission, the call and the
  // counter update are one critical section, so two callers cannot both pass the cap check.
  mkdirSync(stateDir, { recursive: true });
  const release = acquireLock(join(stateDir, 'review.lock'), { staleMs: 45 * 60000 });
  if (!release) return { status: 'busy', reason: 'một review Codex khác đang chạy' };
  try {
    if (codexAttempted(date)) return { status: 'skipped', reason: 'đêm nay đã gọi Codex một lần' };
    const dayPath = dayStatePath(now().date);
    const day = readJson(dayPath, { codexRuns: 0, failures: 0 });
    if ((day.codexRuns ?? 0) >= dayCap(day) - auditReserve) return { status: 'skipped', reason: 'hết lượt Codex trong ngày' };
    // Count the call before it starts: a timeout or crash still spent it.
    writeJson(dayPath, { ...day, codexRuns: (day.codexRuns ?? 0) + 1, personasNightlyRuns: (day.personasNightlyRuns ?? 0) + 1 });
    state.codexAttempt = { startedAt: new Date(nowMs()).toISOString() };
    recordAttempt(date, state.codexAttempt);
    writeState(date, state);
    const outPath = join(dir, 'codex-out.txt');
    try {
      run(codexBin, ['exec', '--skip-git-repo-check', '-s', 'read-only', '--ephemeral', '-m', codexModel, '-c', 'model_reasoning_effort="high"',
        '-C', dir, '-o', outPath, '--color', 'never', '-'], { input: codexPrompt, encoding: 'utf8', timeout: Math.min(20 * 60000, leftMs), maxBuffer: 16 * 1024 * 1024 });
    } catch (error) {
      state.codexAttempt.error = String(error?.message ?? error).slice(0, 300);
      recordAttempt(date, state.codexAttempt);
      writeState(date, state);
      return { status: 'failed', reason: state.codexAttempt.error };
    }
    const text = readFileSync(outPath, 'utf8');
    const parsed = JSON.parse(text.slice(text.indexOf('['), text.lastIndexOf(']') + 1));
    const problems = checkJudgeOutput(readFileSync(join(dir, 'codex-sample.jsonl'), 'utf8').split('\n'), parsed);
    writeFileSync(join(dir, 'codex-scores.json'), `${JSON.stringify(parsed, null, 1)}\n`);
    return { status: problems.length ? 'incomplete' : 'scored', items: parsed.length, problems };
  } finally { release(); }
}

// Codex r7 on #858: what is wrong with the stored Codex scores for tonight's sample (empty, partial,
// out-of-range). null when no readable scores were stored; [] when every sampled item is scored.
function codexScoreProblems(date) {
  const dir = dayDir(date);
  const scores = readMaybe(join(dir, 'codex-scores.json'));
  if (scores === null) return null;
  let sample;
  try { sample = readFileSync(join(dir, 'codex-sample.jsonl'), 'utf8').split('\n'); } catch { return ['codex-sample.jsonl is missing']; }
  if (!sample.some(l => l.trim())) return ['codex-sample.jsonl is empty'];
  return checkJudgeOutput(sample, scores);
}

function codexComparison(date) {
  const codexScores = readMaybe(join(dayDir(date), 'codex-scores.json'));
  if (!Array.isArray(codexScores)) return null;
  const claude = readMaybe(join(nightlyDir(), 'labels', 'judge-scores.json'))?.scores ?? {};
  const pairs = codexScores.filter(r => claude[r.item_id]).map(r => [Number(r.score), Number(claude[r.item_id].score)]);
  if (!pairs.length) return { items: 0 };
  const mean = xs => xs.reduce((a, b) => a + b, 0) / xs.length;
  return { items: pairs.length, codexMean: mean(pairs.map(p => p[0])), claudeMean: mean(pairs.map(p => p[1])), meanAbsDiff: mean(pairs.map(p => Math.abs(p[0] - p[1]))), farApart: pairs.filter(p => Math.abs(p[0] - p[1]) >= 2).length };
}

const fmt2 = v => (typeof v === 'number' ? v.toFixed(2).replace('.', ',') : '—');
export function renderNightly({ state, cmp, leaks, codexCmp, judged, endMetrics }) {
  const lines = [
    `# Người giả hằng đêm, ngày ${state.date}`,
    '',
    '**Mô phỏng bằng người giả hư cấu và giám khảo AI.** Không phải người dùng thật, không thay QA trình duyệt.',
    '',
    `- Hai bản code của nhánh chung: đầu ngày \`${state.start.slice(0, 12)}\`, cuối ngày \`${state.end.slice(0, 12)}\`. Cùng ${state.ids.length} người giả, cùng đồng hồ, dữ liệu và cách chấm.`,
    `- Chọn người: 200 trên 1000 theo hạt \`${state.seed}\` (cố định theo ngày, không ai chọn tay).`,
    `- Thay đổi chạm tới app: ${state.appChanges.length} file${state.unknownChanges.length ? `; không phân loại được ${state.unknownChanges.length} file (vẫn chạy)` : ''}.`,
    `- Chấm mù nội dung mới: ${judged.scored}/${judged.needed} mục.${judged.scored < judged.needed ? ' Mục chưa chấm hiện "chưa đo".' : ''}`,
    '',
  ];
  if (cmp.safety.length || leaks.length) {
    lines.push('## Cảnh báo an toàn', '');
    for (const s of cmp.safety) lines.push(`- ${s}`);
    if (leaks.length) lines.push(`- Lộ dữ liệu giữa người dùng: ${leaks.length} lần, ví dụ ${leaks.slice(0, 3).map(l => `${l.persona} ngày ${l.day} thấy chữ của ${l.from}`).join('; ')}.`);
    lines.push('');
  }
  lines.push('## So với đầu ngày', '', '| Nhóm | Ngưỡng | Đầu ngày | Cuối ngày |', '| --- | --- | --- | --- |');
  const word = ok => (ok === null ? 'chưa đo' : ok ? 'ĐẠT' : 'TRƯỢT');
  for (const r of cmp.rows) lines.push(`| ${r.group} | ${r.threshold} | ${r.start} (${word(r.startOk)}) | ${r.end} (${word(r.endOk)}) |`);
  lines.push('', '## Codex chấm đối chiếu', '');
  if (codexCmp?.failed) lines.push('- Codex đã được gọi nhưng không có kết quả hợp lệ. Đêm này ghi là lỗi.');
  else if (!codexCmp) lines.push('- Không chạy (không có nội dung mới, hoặc hết lượt Codex trong ngày).');
  else if (codexCmp.invalid) lines.push(`- Codex trả lời thiếu hoặc sai (${codexCmp.invalid} lỗi): không dùng điểm này, đêm này ghi là lỗi.`);
  else if (!codexCmp.items) lines.push('- Codex đã chấm nhưng chưa có điểm Claude để so.');
  else lines.push(`- ${codexCmp.items} mục chọn trước theo hạt: Codex ${fmt2(codexCmp.codexMean)}, Claude ${fmt2(codexCmp.claudeMean)}, lệch trung bình ${fmt2(codexCmp.meanAbsDiff)}; lệch từ 2 điểm: ${codexCmp.farApart}.`);
  const load = state.runs ?? {};
  lines.push('', '## Máy', '');
  for (const role of ['start', 'end']) {
    if (load[role]) lines.push(`- ${role === 'start' ? 'Đầu ngày' : 'Cuối ngày'}: ${load[role].seconds} giây, tải cao nhất ${load[role].loadMax.toFixed(1)}, trung bình ${load[role].loadMean.toFixed(1)}.`);
  }
  lines.push('', `Lỗi HTTP cuối ngày: ${endMetrics?.coverage?.http_errors ?? '—'}. Báo cáo đầy đủ từng bản: \`start.md\`, \`end.md\` cùng thư mục.`, '');
  return lines.join('\n');
}

// Safety and leak checks need no judge, so they run as soon as both simulations exist; finish
// repeats them on the final reports and only raises reasons that were not raised yet.
export function safetyReasons(start, end, endRows) {
  const cmp = compareRuns(start, end);
  const leaks = crossLeaks(endRows);
  return { cmp, leaks, reasons: [...cmp.safety, ...(leaks.length ? [`lộ dữ liệu giữa người dùng: ${leaks.length} lần`] : [])] };
}
export function raiseNew(date, state, reasons, { alert = opsAlert, gh = () => makeGh() } = {}) {
  const fresh = reasons.filter(r => !(state.alerted ?? []).includes(r));
  if (!fresh.length) return { raised: [], issue: null };
  const issue = alert(gh(), `Người giả hằng đêm ${date} (${state.start.slice(0, 7)}..${state.end.slice(0, 7)}): ${fresh.join('; ')}. Báo cáo trên máy owner: la-lanh-bao-cao/${nextDay(date)}/personas/report.md`, 'người giả hằng đêm');
  state.alerted = [...(state.alerted ?? []), ...fresh];
  return { raised: fresh, issue };
}
const transcriptRows = (dir, role) => readFileSync(join(dir, role, 'transcript.jsonl'), 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l));

export function finish(date, { alert = opsAlert, gh = () => makeGh(), receipt = writeRunReceipt, report: runReport = report } = {}) {
  const state = readState(date);
  state.codexAttempt = readJson(attemptsPath(), {})[date] ?? state.codexAttempt ?? null;
  const counts = { personas: (state.ids ?? []).length };
  try { return finishRun(date, state, { alert, gh, receipt, report: runReport, counts }); } catch (error) {
    try { receipt({ kind: 'personas', result: personasReceiptResult({ failed: true }), sha: state.end, counts }); } catch {}
    throw error;
  }
}

function finishRun(date, state, { alert, gh, receipt, report, counts }) {
  const dir = dayDir(date);
  const clone = join(nightlyDir(), 'clone-end');
  const personasPath = join(dir, 'personas-200.json');
  const start = report(clone, join(dir, 'start'), personasPath, `start ${date}`);
  const end = report(clone, join(dir, 'end'), personasPath, `end ${date}`);
  const { cmp, leaks, reasons } = safetyReasons(start, end, transcriptRows(dir, 'end'));
  const judged = { needed: end.understood.items_needed + start.understood.items_needed, scored: end.understood.items_scored + start.understood.items_scored };
  const scoreProblems = codexScoreProblems(date);
  const codexInvalid = (scoreProblems?.length ?? 0) > 0;
  // Scores that fail the check are not compared: the report and the receipt both say so.
  const codexFailed = Boolean(state.codexAttempt?.error) || Boolean(state.codexAttempt && scoreProblems === null);
  const codexCmp = codexFailed ? { failed: true } : codexInvalid ? { invalid: scoreProblems.length } : codexComparison(date);
  const out = join(reportRoot(), nextDay(date), 'personas');
  mkdirSync(out, { recursive: true });
  writeFileSync(join(out, 'report.md'), renderNightly({ state, cmp, leaks, codexCmp, judged, endMetrics: end }));
  writeFileSync(join(out, 'start.md'), readFileSync(join(dir, 'start', 'report.md')));
  writeFileSync(join(out, 'end.md'), readFileSync(join(dir, 'end', 'report.md')));
  writeFileSync(join(out, 'metrics.json'), `${JSON.stringify({ date, seed: state.seed, start: state.start, end: state.end, ids: state.ids, appChanges: state.appChanges, unknownChanges: state.unknownChanges, comparison: cmp.rows, safety: cmp.safety, leaks: leaks.length, judged, codex: codexCmp, runs: state.runs }, null, 1)}\n`);
  const raised = raiseNew(date, state, reasons, { alert, gh });
  writeState(date, state);
  // Research item 3 (owner 21.11): the run's receipt names the integration commit it measured. A
  // Codex cross-check that was started and left no scores, or left scores that do not cover every
  // sampled item with a valid score, makes the night an error, not ok.
  const result = personasReceiptResult({ codexAttempt: state.codexAttempt ?? null, codexScored: scoreProblems !== null && !codexInvalid, codexInvalid });
  try { receipt({ kind: 'personas', result, sha: state.end, counts: { ...counts, safetyReasons: reasons.length } }); } catch {}
  return { status: 'finished', report: join(out, 'report.md'), alert: raised.raised.length > 0, reasons: raised.raised, allReasons: reasons, issue: raised.issue };
}

if (isMain(import.meta.url)) {
  const [cmd, ...rest] = process.argv.slice(2);
  const opt = name => { const i = rest.indexOf(name); return i >= 0 ? rest[i + 1] : undefined; };
  const date = opt('--date') ?? vnNow().date;
  const positional = rest.filter((a, i) => !a.startsWith('--') && !(i > 0 && rest[i - 1] === '--date'));
  const done = result => { console.log(JSON.stringify(result)); };
  try {
    if (cmd === 'prepare') done(await prepare({ date, anyTime: rest.includes('--any-time') }));
    else if (cmd === 'check') { const p = check(date, positional[0]); done(p.length ? { status: 'problems', problems: p.slice(0, 20) } : { status: 'ok' }); }
    else if (cmd === 'merge') done(merge(date, positional));
    else if (cmd === 'codex') done(codex(date));
    else if (cmd === 'finish') done(finish(date));
    else { console.error('usage: personas-nightly.mjs prepare|check|merge|codex|finish [--date YYYY-MM-DD]'); process.exitCode = 2; }
  } catch (error) {
    done({ status: 'error', error: String(error?.message ?? error).slice(0, 500) });
    process.exitCode = 1;
  }
}
