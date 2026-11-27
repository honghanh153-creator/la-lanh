// Antigravity as the second critic (owner 22.11.2026, L70: "tôi vừa bật antigravity
// trên máy cũng có thể sử dụng để phản biện ... ưu tiên anti hơn gemini"). Antigravity is Google's agent
// app on the owner's Mac; it answers without Claude tokens, so the loop can run it while Claude is out.
// L71 (owner 22.11 "okie 1-2-3"): it critiques every ready PR, not only the ones Codex fixed. PRs Codex
// fixed come first (their merge waits for it), then PRs at Codex review or merge with no critic yet.
// One step per tick: start a conversation for one PR, or read the answer of the one started.
// - Start: `agentapi new-conversation` (the app's own CLI) with the public PR diff only (R14).
// - Read: the app's local HTTP API (GetCascadeTrajectorySteps). The CSRF token comes from the app's
//   daemon file into the child env only; it is never printed, logged or posted.
// - An answer counts only when the critic used no tool (no command, no file, no browser): the brief
//   asks for text only, and any other step drops the answer. A wrong format or a slow answer (20 min)
//   is dropped too; retries have a cooldown and a per-head limit so other PRs can proceed.
//   node scripts/collab-antigravity.mjs --step       one step (what the tick runs)
import { execFileSync, spawnSync } from 'node:child_process';
import { readdirSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { boundedTimeout, clean, isOwnPr, makeGh, readJson, repo, stateDir, writeJson } from './collab-trust.mjs';
import { cutoffLeft, lastSecond, secondReviewProblem } from './codex-fallback.mjs';
import { briefComplete, briefLimit, postSecond, secondBrief } from './collab-second-review.mjs';
import { isMain } from './is-main.mjs';

export const reviewer = 'Antigravity';
export const answerLimitMs = 20 * 60000;
export const retryDelayMs = 10 * 60000;
export const maxAttempts = 2;
export const statePath = (home = stateDir) => join(home, 'state', 'antigravity-reviews.json');
// When the app last started or answered a critique (ms). Queued PRs are held only while it answers.
export const alivePath = (home = stateDir) => join(home, 'state', 'antigravity-alive.json');
const markAlive = (home, nowMs) => writeJson(alivePath(home), { at: nowMs });
const appHome = (user = homedir()) => join(user, '.gemini', 'antigravity');
const textOnly = 'Chỉ đọc và trả lời bằng chữ. Không chạy lệnh, không mở hay sửa file, không dùng trình duyệt hay công cụ nào: câu trả lời có dùng công cụ sẽ bị bỏ.';

export const antigravityBrief = (pr, diff) => `${secondBrief(pr, diff)}\n\n${textOnly}`;

// The steps of one conversation → the final text, whether it is finished, and any tool steps.
const chat = new Set(['CORTEX_STEP_TYPE_USER_INPUT', 'CORTEX_STEP_TYPE_PLANNER_RESPONSE']);
export function readAnswer(steps = []) {
  const tools = [...new Set(steps.map(s => s.type).filter(t => !chat.has(t)))];
  const last = steps.at(-1);
  const done = Boolean(last) && last.type === 'CORTEX_STEP_TYPE_PLANNER_RESPONSE' && last.status === 'CORTEX_STEP_STATUS_DONE'
    && steps.every(s => s.status === 'CORTEX_STEP_STATUS_DONE');
  const modified = last?.plannerResponse?.modifiedResponse;
  const text = String(typeof modified === 'string' && modified.trim() ? modified : last?.plannerResponse?.response ?? '');
  return { done, text, tools };
}

// The verdict is the first line "Kết luận: APPROVE|REQUEST_CHANGES" (bold marks allowed). Nothing else.
export function parseCritic(text) {
  const first = String(text ?? '').split('\n').map(l => l.trim()).find(Boolean) ?? '';
  const m = /^\**\s*Kết luận:\s*\**\s*(APPROVE|REQUEST_CHANGES)\s*\**\s*$/.exec(first);
  return m ? m[1] : null;
}

// Open PRs with no second critic for their head, in the order Antigravity takes them.
const readyTurns = new Set(['codex-review', 'merge']);
export function secondTargets(prs = [], turns = []) {
  const ready = new Set(turns.filter(t => readyTurns.has(t.turn)).map(t => t.number));
  const open = prs.filter(pr => !lastSecond(pr));
  const held = open.filter(pr => secondReviewProblem(pr)?.turn === 'hold');
  // Only the owner's own branches (never a fork): the diff goes to an agent that may run commands.
  return [...held, ...open.filter(pr => ready.has(pr.number) && isOwnPr(pr) && !held.includes(pr))];
}

// Codex r1 on #899 (P1): a critique started for the live head holds the merge until it is read, or
// until its 20 minutes pass (a stopped app never holds a PR for longer). A diff too long to send holds nothing.
// Codex auto-3 on #899 (P1): every PR waiting for a critique is queued with its head, so a second
// ready PR is held until its own critique, not only the one under way. A queue holds only while the app
// answers: 20 minutes after its last start or answer (app stopped or never reached), nothing is held.
export function criticPending(pr, { home = stateDir, nowMs = Date.now() } = {}) {
  const job = readJson(statePath(home), {})[String(pr?.number)];
  if (!job || job.tooLong || job.head !== pr.headRefOid) return null;
  if (job.queued) {
    const alive = readJson(alivePath(home), {}).at;
    return Number.isFinite(alive) && nowMs - alive <= answerLimitMs ? 'Antigravity chưa phản biện head này (đang xếp hàng): chờ tới lượt' : null;
  }
  if (!job.id || !Number.isFinite(job.at) || nowMs - job.at > answerLimitMs) return null;
  return 'Antigravity đang phản biện head này: chờ câu trả lời (tối đa 20 phút)';
}

// One tick step. Returns what it did, or null when no PR waits for a second critic.
export function antigravityStep({ gh, prs = [], turns = [], start, steps, home = stateDir, nowMs = Date.now(), left, log = () => {} }) {
  const waiting = secondTargets(prs, turns);
  const all = readJson(statePath(home), {});
  const save = () => writeJson(statePath(home), all);
  const live = new Map(prs.filter(pr => !lastSecond(pr)).map(pr => [String(pr.number), pr]));
  for (const n of Object.keys(all)) if (live.get(n)?.headRefOid !== all[n].head) { delete all[n]; log(`antigravity #${n}: head moved or PR no longer waiting, dropped`); }
  const attempts = job => job.attempts == null ? (job.queued ? 0 : 1) : Number.isInteger(job.attempts) && job.attempts >= 0 ? job.attempts : maxAttempts;
  const drop = (n, job, reason) => {
    all[n] = { head: job.head, attempts: attempts(job), retryAt: nowMs + retryDelayMs, reason };
    save();
    log(`antigravity #${n}: ${reason}; ${all[n].attempts >= maxAttempts ? 'hết lượt thử ở head này, chờ phản biện khác' : 'chờ thử lại; PR khác đi tiếp'}`);
    return { status: 'dropped', pr: Number(n), reason };
  };
  // Every waiting head is queued before anything else, so the merge gate holds it this tick.
  for (const p of waiting) all[String(p.number)] ??= { head: p.headRefOid, queued: true, attempts: 0, at: nowMs };
  save();
  const [n, job] = Object.entries(all).find(([, j]) => j.id && !j.tooLong) ?? [];
  if (job) {
    if (!Number.isFinite(job.at) || nowMs < job.at || nowMs - job.at > answerLimitMs) return drop(n, job, 'quá 20 phút chưa trả lời hoặc thời gian phiên không hợp lệ');
    let answer;
    try { answer = readAnswer(steps(job.id)); }
    catch { return drop(n, job, 'không đọc được phiên Antigravity; không tính review'); }
    markAlive(home, nowMs);
    if (answer.tools.length) return drop(n, job, `Antigravity dùng công cụ (${answer.tools.join(', ')}): không tính`);
    if (!answer.done) { save(); return { status: 'waiting', pr: Number(n) }; }
    const verdict = parseCritic(answer.text);
    if (!verdict) return drop(n, job, 'câu trả lời không theo mẫu "Kết luận: ..."');
    let posted;
    try { posted = postSecond({ gh, number: Number(n), reviewer, verdict, head: job.head, notes: answer.text, ...(left ? { left } : {}) }); }
    catch { return drop(n, job, 'chưa đăng được review hợp lệ; PR vẫn chờ kiểm'); }
    delete all[n]; save();
    return { status: 'posted', pr: Number(n), verdict, url: posted.url };
  }
  // A diff longer than the brief is not sent: Antigravity would read a cut copy (Codex r1 on #894).
  // The PR is remembered for its head and waits for Claude; the next waiting PR goes instead.
  const pr = waiting.find(p => all[String(p.number)]?.queued && attempts(all[String(p.number)]) === 0) ?? waiting.find(p => {
    const job = all[String(p.number)];
    return !job.tooLong && attempts(job) < maxAttempts && Number.isFinite(job.retryAt) && nowMs >= job.retryAt;
  });
  if (!pr) { save(); return null; }
  const key = String(pr.number);
  const next = { head: pr.headRefOid, attempts: all[key] ? attempts(all[key]) + 1 : 1, retryAt: nowMs + retryDelayMs };
  all[key] = next; save();
  let diff;
  try { diff = String(gh.raw(['pr', 'diff', key, '--repo', repo])); }
  catch { return drop(key, next, 'không đọc được diff đầy đủ; không gửi review'); }
  if (!briefComplete(diff)) {
    all[key] = { ...next, tooLong: true, at: nowMs };
    save();
    return { status: 'skipped', pr: pr.number, reason: `diff dài hơn ${briefLimit} ký tự: chờ Claude phản biện` };
  }
  let id;
  try { id = start(antigravityBrief(pr, diff), `Phản biện PR #${pr.number}`); }
  catch { return drop(key, next, 'không mở được phiên Antigravity; PR vẫn chờ phản biện'); }
  markAlive(home, nowMs);
  all[key] = { ...next, id, at: nowMs };
  save();
  return { status: 'started', pr: pr.number };
}

// The app's local address and token, read from its daemon file into an env object (never printed).
export function appEnv(user = homedir()) {
  const dir = join(appHome(user), 'daemon');
  const hubs = readdirSync(dir).filter(f => /^hub_.*\.json$/.test(f)).flatMap(file => {
    try { const path = join(dir, file); return [{ path, at: statSync(path).mtimeMs }]; } catch { return []; }
  }).sort((a, b) => b.at - a.at || a.path.localeCompare(b.path));
  for (const { path } of hubs) {
    const hub = readJson(path, {});
    if (Number.isInteger(hub.httpPort) && hub.httpPort > 0 && hub.httpPort <= 65535 && typeof hub.csrfToken === 'string' && hub.csrfToken) {
      return { ANTIGRAVITY_LS_ADDRESS: `127.0.0.1:${hub.httpPort}`, ANTIGRAVITY_CSRF_TOKEN: hub.csrfToken };
    }
  }
  throw new Error('Antigravity chưa có daemon hợp lệ');
}

export function startConversation(brief, title, { env = appEnv(), bin = join(appHome(), 'bin', 'agentapi'), left = () => Infinity, run = execFileSync } = {}) {
  const out = run(bin, ['new-conversation', '--model=pro', `--title=${title}`, brief], { env: { ...process.env, ...env }, encoding: 'utf8', timeout: boundedTimeout(60000, left), maxBuffer: 4 * 1024 * 1024 });
  const id = JSON.parse(out)?.response?.newConversation?.conversationId;
  if (!/^[0-9a-f-]{36}$/.test(String(id))) throw new Error('Antigravity không trả mã cuộc trò chuyện');
  return id;
}

// A child node does the HTTP call so the tick stays synchronous; the token travels in its env.
const fetchScript = `const [id]=process.argv.slice(1);fetch('http://'+process.env.ANTIGRAVITY_LS_ADDRESS+'/exa.language_server_pb.LanguageServerService/GetCascadeTrajectorySteps',{method:'POST',headers:{'Content-Type':'application/json','Connect-Protocol-Version':'1','x-codeium-csrf-token':process.env.ANTIGRAVITY_CSRF_TOKEN},body:JSON.stringify({cascadeId:id}),signal:AbortSignal.timeout(20000)}).then(async r=>{if(!r.ok)throw new Error('HTTP '+r.status);process.stdout.write(await r.text())}).catch(e=>{console.error(e.message);process.exit(1)})`;
export function conversationSteps(id, { env = appEnv(), left = () => Infinity } = {}) {
  const r = spawnSync(process.execPath, ['-e', fetchScript, id], { env: { ...process.env, ...env }, encoding: 'utf8', timeout: boundedTimeout(30000, left), maxBuffer: 16 * 1024 * 1024 });
  if (r.status !== 0) throw new Error(`không đọc được câu trả lời Antigravity: ${clean(r.stderr, 200)}`);
  return JSON.parse(r.stdout)?.steps ?? [];
}

// `left`: time to the tick's absolute deadline (Codex r1 on #894); every call is bounded by it.
// Codex auto-3 on #894 (P1): the GitHub calls (diff, post) are bounded by the same deadline; without one, by 23:59.
export const runAntigravity = ({ gh, prs, turns, log, left = cutoffLeft() }) => antigravityStep({ gh: gh.withDeadline?.(left) ?? gh, prs, turns, log, left, start: (b, t) => startConversation(b, t, { left }), steps: id => conversationSteps(id, { left }) });

if (isMain(import.meta.url)) {
  if (process.argv.includes('--step')) {
    const gh = makeGh();
    console.log(JSON.stringify(runAntigravity({ gh, prs: gh.openPrs(), log: m => console.error(m) })));
  } else { console.error('dùng --step'); process.exit(2); }
}
