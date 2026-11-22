// Antigravity as the second critic for PRs Codex fixed (owner 22.11.2026, L70: "tôi vừa bật antigravity
// trên máy cũng có thể sử dụng để phản biện ... ưu tiên anti hơn gemini"). Antigravity is Google's agent
// app on the owner's Mac; it answers without Claude tokens, so the loop can run it while Claude is out.
// One step per tick: start a conversation for one waiting PR, or read the answer of the one started.
// - Start: `agentapi new-conversation` (the app's own CLI) with the public PR diff only (R14).
// - Read: the app's local HTTP API (GetCascadeTrajectorySteps). The CSRF token comes from the app's
//   daemon file into the child env only; it is never printed, logged or posted.
// - An answer counts only when the critic used no tool (no command, no file, no browser): the brief
//   asks for text only, and any other step drops the answer. A wrong format or a slow answer (20 min)
//   is dropped too; the PR stays held and the next tick starts again.
//   node scripts/collab-antigravity.mjs --step       one step (what the tick runs)
import { execFileSync, spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { clean, makeGh, readJson, repo, stateDir, writeJson } from './collab-trust.mjs';
import { secondReviewProblem } from './codex-fallback.mjs';
import { postSecond, secondBrief } from './collab-second-review.mjs';
import { isMain } from './is-main.mjs';

export const reviewer = 'Antigravity';
export const answerLimitMs = 20 * 60000;
export const statePath = (home = stateDir) => join(home, 'state', 'antigravity-reviews.json');
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
  const text = String(last?.plannerResponse?.modifiedResponse ?? last?.plannerResponse?.response ?? '');
  return { done, text, tools };
}

// The verdict is the first line "Kết luận: APPROVE|REQUEST_CHANGES" (bold marks allowed). Nothing else.
export function parseCritic(text) {
  const first = String(text ?? '').split('\n').map(l => l.trim()).find(Boolean) ?? '';
  const m = /^\**\s*Kết luận:\s*\**\s*(APPROVE|REQUEST_CHANGES)\s*\**\s*$/.exec(first);
  return m ? m[1] : null;
}

// One tick step. Returns what it did, or null when no PR waits for a second critic.
export function antigravityStep({ gh, prs = [], start, steps, home = stateDir, nowMs = Date.now(), log = () => {} }) {
  const waiting = prs.filter(pr => secondReviewProblem(pr)?.turn === 'hold');
  const all = readJson(statePath(home), {});
  const save = () => writeJson(statePath(home), all);
  const live = new Map(waiting.map(pr => [String(pr.number), pr]));
  for (const n of Object.keys(all)) if (live.get(n)?.headRefOid !== all[n].head) { delete all[n]; log(`antigravity #${n}: head moved or PR no longer waiting, dropped`); }
  const [n, job] = Object.entries(all)[0] ?? [];
  if (job) {
    const answer = readAnswer(steps(job.id));
    const drop = reason => { delete all[n]; save(); return { status: 'dropped', pr: Number(n), reason }; };
    if (answer.tools.length) return drop(`Antigravity dùng công cụ (${answer.tools.join(', ')}): không tính`);
    if (!answer.done) return nowMs - job.at > answerLimitMs ? drop('quá 20 phút chưa trả lời') : (save(), { status: 'waiting', pr: Number(n) });
    const verdict = parseCritic(answer.text);
    if (!verdict) return drop('câu trả lời không theo mẫu "Kết luận: ..."');
    const posted = postSecond({ gh, number: Number(n), reviewer, verdict, head: job.head, notes: answer.text });
    delete all[n]; save();
    return { status: 'posted', pr: Number(n), verdict, url: posted.url };
  }
  const pr = waiting[0];
  if (!pr) { save(); return null; }
  const diff = String(gh.raw(['pr', 'diff', String(pr.number), '--repo', repo]));
  const id = start(antigravityBrief(pr, diff), `Phản biện PR #${pr.number}`);
  all[String(pr.number)] = { head: pr.headRefOid, id, at: nowMs };
  save();
  return { status: 'started', pr: pr.number };
}

// The app's local address and token, read from its daemon file into an env object (never printed).
export function appEnv(user = homedir()) {
  const dir = join(appHome(user), 'daemon');
  const file = readdirSync(dir).filter(f => /^hub_.*\.json$/.test(f)).sort()[0];
  if (!file) throw new Error('Antigravity chưa chạy (không thấy daemon)');
  const hub = readJson(join(dir, file), {});
  if (!hub.httpPort || !hub.csrfToken) throw new Error('Antigravity daemon thiếu cổng hoặc token');
  return { ANTIGRAVITY_LS_ADDRESS: `127.0.0.1:${hub.httpPort}`, ANTIGRAVITY_CSRF_TOKEN: hub.csrfToken };
}

export function startConversation(brief, title, { env = appEnv(), bin = join(appHome(), 'bin', 'agentapi') } = {}) {
  const out = execFileSync(bin, ['new-conversation', '--model=pro', `--title=${title}`, brief], { env: { ...process.env, ...env }, encoding: 'utf8', timeout: 60000, maxBuffer: 4 * 1024 * 1024 });
  const id = JSON.parse(out)?.response?.newConversation?.conversationId;
  if (!/^[0-9a-f-]{36}$/.test(String(id))) throw new Error('Antigravity không trả mã cuộc trò chuyện');
  return id;
}

// A child node does the HTTP call so the tick stays synchronous; the token travels in its env.
const fetchScript = `const [id]=process.argv.slice(1);fetch('http://'+process.env.ANTIGRAVITY_LS_ADDRESS+'/exa.language_server_pb.LanguageServerService/GetCascadeTrajectorySteps',{method:'POST',headers:{'Content-Type':'application/json','Connect-Protocol-Version':'1','x-codeium-csrf-token':process.env.ANTIGRAVITY_CSRF_TOKEN},body:JSON.stringify({cascadeId:id}),signal:AbortSignal.timeout(20000)}).then(async r=>{if(!r.ok)throw new Error('HTTP '+r.status);process.stdout.write(await r.text())}).catch(e=>{console.error(e.message);process.exit(1)})`;
export function conversationSteps(id, { env = appEnv() } = {}) {
  const r = spawnSync(process.execPath, ['-e', fetchScript, id], { env: { ...process.env, ...env }, encoding: 'utf8', timeout: 30000, maxBuffer: 16 * 1024 * 1024 });
  if (r.status !== 0) throw new Error(`không đọc được câu trả lời Antigravity: ${clean(r.stderr, 200)}`);
  return JSON.parse(r.stdout)?.steps ?? [];
}

export const runAntigravity = ({ gh, prs, log }) => antigravityStep({ gh, prs, log, start: (b, t) => startConversation(b, t), steps: id => conversationSteps(id) });

if (isMain(import.meta.url)) {
  if (process.argv.includes('--step')) {
    const gh = makeGh();
    console.log(JSON.stringify(runAntigravity({ gh, prs: gh.openPrs(), log: m => console.error(m) })));
  } else { console.error('dùng --step'); process.exit(2); }
}
