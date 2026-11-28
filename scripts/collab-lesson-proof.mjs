// Lessons that prove themselves (research item 4, owner approved 21.11.2026; Anthropic "Demystifying
// evals for AI agents" 01.2026, Every "Compound engineering"). A lesson in collab-lessons.json names a
// regression test and the PR that closed it. That says the test exists and passes; it does not say
// the test would have caught the bug. Here a lesson is proved red → green:
// - red: integration just before the closing PR merged (the merge commit's first parent), with only
//   the lesson's test file taken from the merge, must FAIL that named test;
// - green: the merge commit itself must PASS it.
// A test file that cannot even load on the old code also fails, but that proves less, so it is
// recorded as `proved-load`. A test the closing PR did not have yet (added later) is `not-at-merge`:
// the lesson names the wrong PR or test (21.11: L13). A lesson may name a fragment of its test's name;
// it is resolved to the one full name it belongs to, and a fragment of several names is `ambiguous`.
// Green also needs the test process to end well (a hook failing after the passing line is not green).
// A Python test, or a lesson with no test or no closing PR, is `unsupported`: final for that evidence,
// never tried again. `unknown` (PR not merged yet, GitHub or git unreadable, run cut short) is tried
// again a day later, after every lesson not tried yet, so one such lesson never holds up the others
// (Codex on #860). Proofs are kept on the owner's Mac (lesson-proofs.json), keyed by the lesson's
// evidence, so a changed test or PR is proved again. The board line counts proved lessons.
// Usage: node scripts/collab-lesson-proof.mjs --prove L57 | --prove-all [--max 5] | --report
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { clean, makeGh, readJson, repo, stateDir, writeJson } from './collab-trust.mjs';
import { readRegister } from './collab-lessons.mjs';
import { isMain } from './is-main.mjs';

export const proofsPath = () => join(stateDir, 'lesson-proofs.json');
const opsDir = () => join(stateDir, 'ops');
const escapeRe = text => String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
export const evidenceKey = l => `${l.id}:${l.test?.file}:${l.test?.name}:${l.closedBy?.pr}`;

// One named test in one file, in a checkout. TAP tells a failing test from a file that did not load.
export function runNamedTest(dir, file, name, { spawn = spawnSync, node = process.execPath } = {}) {
  // NODE_TEST_CONTEXT (set when this runs under a test runner) would route the child's report to
  // the parent instead of stdout; the child always reports its own TAP.
  const { NODE_TEST_CONTEXT, ...env } = process.env;
  // The register may hold a fragment of the test's name (as `collab-lessons` accepts), so the filter
  // is not anchored; the fragment is resolved below to the one full name it belongs to.
  const r = spawn(node, ['--test', '--test-reporter=tap', `--test-name-pattern=${escapeRe(name)}`, file],
    { cwd: dir, encoding: 'utf8', timeout: 180000, env: { ...env, LA_LANH_COLLAB_HOME: mkdtempSync(join(tmpdir(), 'proof-home-')) } });
  // TAP escapes '#' and '\' in names (`\\#828: …`); lines are compared after unescaping. A line with a
  // SKIP or TODO directive is a test that did not run.
  const ran = `${r.stdout ?? ''}`.split('\n').map(l => /^\s*(not ok|ok) \d+ - (.*?)\s*$/.exec(l)).filter(Boolean)
    .filter(m => !/(?<!\\) # (?:SKIP|TODO)\b/i.test(m[2]))
    .map(m => ({ ok: m[1] === 'ok', name: m[2].replace(/\\([\\#])/g, '$1') }));
  const exact = ran.filter(t => t.name === name);
  const hits = exact.length ? exact : ran.filter(t => t.name.includes(name));
  const ended = !r.error && !r.signal && r.status === 0;
  if (new Set(hits.map(t => t.name)).size > 1) return 'ambiguous';
  if (hits.length) return hits.some(t => !t.ok) ? 'fail' : ended ? 'pass' : 'broken';
  if (r.error || r.signal) return 'error';
  return r.status === 0 ? 'missing' : 'load';
}

export function proveLesson(lesson, { gh = makeGh(), dir = opsDir(), run = execFileSync, test = runNamedTest } = {}) {
  if (!lesson?.test?.file || !lesson?.test?.name) return { result: 'unsupported', why: 'bài học không có test' };
  if (!/\.m?js$/.test(lesson.test.file)) return { result: 'unsupported', why: 'test Python: chưa kiểm được' };
  if (!Number.isInteger(lesson.closedBy?.pr)) return { result: 'unsupported', why: 'chưa có PR đóng' };
  let merge;
  try { merge = gh.json(['pr', 'view', String(lesson.closedBy.pr), '--repo', repo, '--json', 'mergeCommit,state'])?.mergeCommit?.oid; }
  catch (error) { return { result: 'unknown', why: `không đọc được PR: ${clean(error.message, 80)}` }; }
  if (!merge) return { result: 'unknown', why: 'PR đóng chưa merge' };
  const git = (args, cwd = dir) => String(run('/usr/bin/git', ['-C', cwd, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 120000 })).trim();
  const trees = [];
  const tree = ref => { const path = mkdtempSync(join(tmpdir(), 'lesson-proof-')); rmSync(path, { recursive: true, force: true }); git(['worktree', 'add', '--detach', '--quiet', path, ref]); trees.push(path); return path; };
  try {
    git(['fetch', '--quiet', '--no-tags', 'origin', merge]);
    const before = git(['rev-parse', `${merge}^1`]);
    const old = tree(before);
    git(['checkout', merge, '--', lesson.test.file], old);
    const red = test(old, lesson.test.file, lesson.test.name);
    const green = test(tree(merge), lesson.test.file, lesson.test.name);
    // A run cut short (timeout, signal) says nothing about either side: tried again later.
    if (red === 'error' || green === 'error') return { result: 'unknown', why: 'test không chạy xong (hết giờ hoặc bị dừng)', red, green, before, merge };
    const result = green === 'ambiguous' ? 'ambiguous' : green === 'missing' ? 'not-at-merge' : green !== 'pass' ? 'not-green'
      : red === 'fail' ? 'proved' : red === 'load' ? 'proved-load' : 'not-red';
    return { result, red, green, before, merge };
  } catch (error) {
    return { result: 'unknown', why: clean(String(error.stderr ?? error.message).split('\n')[0], 120) };
  } finally {
    for (const t of trees) { try { git(['worktree', 'remove', '--force', t]); } catch {} }
  }
}

export const retryMs = 24 * 3600000;
export function proveAll({ register = readRegister, prove = proveLesson, path = proofsPath(), max = 5, only = null, at = new Date() } = {}) {
  const proofs = readJson(path, {});
  const done = (register().lessons ?? []).filter(l => l.status === 'done' && (!only || l.id === only));
  // Lessons not tried yet go first, in register order. An `unknown` result waits `retryMs` and then
  // queues behind them, oldest attempt first; `unsupported` is final. `--prove Lx` retries at once.
  const last = l => proofs[evidenceKey(l)];
  const due = l => last(l)?.result === 'unknown' && (Boolean(only) || !(at.getTime() - Date.parse(last(l).at) < retryMs));
  const retry = done.filter(due).sort((a, b) => (Date.parse(last(a).at) || 0) - (Date.parse(last(b).at) || 0));
  const todo = [...done.filter(l => !last(l)), ...retry].slice(0, only ? 1 : max);
  for (const l of todo) proofs[evidenceKey(l)] = { id: l.id, at: at.toISOString(), ...prove(l) };
  writeJson(path, proofs);
  return todo.map(l => ({ id: l.id, ...proofs[evidenceKey(l)] }));
}

// The tick proves at most `perNight` lessons a night, while the loop is closed (00:00–06:50), so the
// old-code test runs never compete with checks and reviews.
export const perNight = 6;
export function nightlyProofs({ status, nowMs = Date.now(), statePath = join(stateDir, 'state', 'lesson-proof-run.json'), prove = proveAll, log = () => {} } = {}) {
  if (status !== 'closed') return null;
  const state = readJson(statePath, {});
  const night = new Date(nowMs + 7 * 3600000).toISOString().slice(0, 10);
  if ((state.night === night ? state.count ?? 0 : 0) >= perNight) return null;
  const done = prove({ max: 1 });
  writeJson(statePath, { night, count: (state.night === night ? state.count ?? 0 : 0) + 1 });
  for (const p of done) log(`lesson proof ${p.id}: ${p.result}${p.red ? ` (đỏ=${p.red}, xanh=${p.green})` : ''}`);
  return done;
}

export function proofSummary(register, proofs) {
  const done = (register.lessons ?? []).filter(l => l.status === 'done');
  const of = l => proofs[evidenceKey(l)]?.result;
  const count = r => done.filter(l => of(l) === r).length;
  return { done: done.length, proved: count('proved'), provedLoad: count('proved-load'), notRed: done.filter(l => of(l) === 'not-red').map(l => l.id),
    notGreen: done.filter(l => of(l) === 'not-green').map(l => l.id), notAtMerge: done.filter(l => of(l) === 'not-at-merge').map(l => l.id),
    ambiguous: done.filter(l => of(l) === 'ambiguous').map(l => l.id), unsupported: count('unsupported'),
    unchecked: done.filter(l => !of(l) || of(l) === 'unknown').length };
}

export function renderProofs(s) {
  const bad = [...(s.notRed.length ? [`test không đỏ trên code cũ: ${s.notRed.join(', ')}`] : []), ...(s.notGreen.length ? [`test không xanh trên code mới: ${s.notGreen.join(', ')}`] : []),
    ...(s.notAtMerge?.length ? [`PR đóng chưa có test bài học nêu: ${s.notAtMerge.join(', ')}`] : []),
    ...(s.ambiguous?.length ? [`tên test khớp nhiều test: ${s.ambiguous.join(', ')}`] : [])];
  return `Bài học có bằng chứng đỏ → xanh: ${s.proved}/${s.done}${s.provedLoad ? ` (thêm ${s.provedLoad} chỉ đỏ vì file test không chạy được trên code cũ)` : ''}; chưa kiểm ${s.unchecked}${s.unsupported ? `; không kiểm được ${s.unsupported}` : ''}${bad.length ? `; ${bad.join('; ')}` : ''}.`;
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const at = name => (args.includes(name) ? args[args.indexOf(name) + 1] : null);
  if (args.includes('--report')) process.stdout.write(`${renderProofs(proofSummary(readRegister(), readJson(proofsPath(), {})))}\n`);
  else if (args.includes('--prove') || args.includes('--prove-all')) {
    for (const p of proveAll({ only: at('--prove'), max: Number(at('--max')) || 5 })) process.stdout.write(`${p.id}: ${p.result}${p.why ? ` (${p.why})` : ''}${p.red ? ` đỏ=${p.red} xanh=${p.green}` : ''}\n`);
  } else process.stdout.write('Usage: node scripts/collab-lesson-proof.mjs --prove L57 | --prove-all [--max 5] | --report\n');
}
