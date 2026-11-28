// One bounded task for Anti (Antigravity), carried out by the trusted host (Codex r1 on #955, P1).
// Anti stays review-only: it never gets write or command tools and never touches a checkout.
// One step per call; the job lives in <home>/state/anti-job.json (one job at a time).
// 1. open: the host adds its own worktree <home>/anti-jobs/<issue>-<slug> on `agent/anti/<issue>-<slug>`
//    from a fixed base commit (trusted git), checks it (preflight profile `anti`: own worktree, right
//    branch, clean, not a shared clone), builds the public snapshot from the allowlist itself and
//    sends Anti a text-only brief.
// 2. read: an answer counts only when it is finished, has no tool step and its whole text is a valid
//    bundle of `message` events and exactly one `patch` event that edits files Anti was shown.
//    Anything else, or no answer in 20 minutes, drops the job and removes its worktree.
// 3. apply: the host applies the patch all or nothing in that worktree and commits it there (hooks
//    off) with `Implemented-By: Antigravity (host-applied patch)`. No push, no PR, no verdict:
//    Claude reads the branch and opens the PR through the normal gates (Author check, Codex review).
//    A write that could not be undone marks the job `invalid`; its worktree is never reused.
// The transport ({ start(brief, title) → id, read(id) → { done, text, tools } }) is injected. The
// real one is the Antigravity bridge (scripts/collab-antigravity.mjs, PR #894/#899, waiting for the
// owner: cost/access). Until that file is on collab/integration the CLI reports `blocked`.
//   node scripts/collab-anti-job.mjs --open --issue N --slug s --scope a/,b.md --task-file f --base SHA
//   node scripts/collab-anti-job.mjs --step | --status
import { existsSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { antiJobsDir, applyPatch, buildSnapshot, parseEvents, parsePatch, pathReasons, privateReasons, trustedGit } from './collab-anti-patch.mjs';
import { preflightWorkspace } from './collab-dispatch.mjs';
import { clean, readJson, stateDir, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const answerLimitMs = 20 * 60000;
export const taskChars = 2000;
export const trailer = 'Implemented-By: Antigravity (host-applied patch)';
export const jobPath = (home = stateDir) => join(home, 'state', 'anti-job.json');
const hostName = 'La Lanh host (Anti patch)';
const hostEmail = 'anti-host@la-lanh.invalid';

export const antiTaskBrief = ({ issue, task, items }) => [
  `Việc #${issue} của repo Lá Lành. Bạn chỉ đọc và trả lời bằng chữ. Không chạy lệnh, không mở hay sửa file, không dùng trình duyệt hay công cụ nào: câu trả lời có dùng công cụ sẽ bị bỏ.`,
  '',
  'Yêu cầu:',
  task,
  '',
  'Trả lời chỉ bằng các dòng JSON, mỗi dòng một object, không có chữ nào khác:',
  '{"type":"message","text":"<giải thích ngắn>"}',
  '{"type":"patch","text":"*** Edit: <đường dẫn>\\n<<<<<<< FIND\\n<đoạn cũ, xuất hiện đúng 1 lần>\\n=======\\n<đoạn mới>\\n>>>>>>> REPLACE"}',
  'Đúng một dòng patch. Chỉ sửa các file dưới đây.',
  '',
  ...items.flatMap(it => [`===== FILE ${it.path} =====`, it.text, `===== HẾT ${it.path} =====`]),
].join('\n');

// What the host accepts back. Returns { ok, patch, reasons }.
export function checkAnswer(answer, shown) {
  if (!answer || typeof answer !== 'object') return { ok: false, reasons: ['không có câu trả lời'] };
  if (answer.tools?.length) return { ok: false, reasons: [`Anti dùng công cụ (${clean(answer.tools.join(', '), 120)}): không tính`] };
  const ev = parseEvents(answer.text);
  if (!ev.ok) return { ok: false, reasons: ev.reasons };
  if (ev.events.some(e => e.type === 'tool_call')) return { ok: false, reasons: ['câu trả lời có tool_call: việc Anti chỉ nhận chữ'] };
  const patches = ev.events.filter(e => e.type === 'patch');
  if (patches.length !== 1) return { ok: false, reasons: [`cần đúng 1 patch, có ${patches.length}`] };
  const patch = parsePatch(patches[0].text);
  if (!patch.ok) return { ok: false, reasons: patch.reasons };
  const unseen = patch.files.filter(f => !shown.includes(f.path)).map(f => `${clean(f.path, 80)}: Anti không được xem file này`);
  return unseen.length ? { ok: false, reasons: unseen } : { ok: true, patch, reasons: [] };
}

// A directory scope is allowed; the snapshot then refuses it whole if it holds a protected file.
const scopeReasons = scope => (!Array.isArray(scope) || !scope.length || scope.length > 20)
  ? ['phạm vi phải có 1–20 mục']
  : scope.flatMap(s => pathReasons(String(s).replace(/\/$/, '')));

function removeWorktree(job, { repoRoot, git, home }) {
  try { git(['worktree', 'remove', '--force', job.dir], { cwd: repoRoot }); } catch { /* fall through */ }
  if (existsSync(job.dir) && job.dir.startsWith(`${antiJobsDir(home)}/`)) rmSync(job.dir, { recursive: true, force: true });
  try { git(['worktree', 'prune'], { cwd: repoRoot }); git(['branch', '-D', job.branch], { cwd: repoRoot }); } catch { /* branch may be gone */ }
}

// Opens a job. Returns { status: 'started' | 'refused' | 'busy' | 'blocked', ... }.
export function openJob({ issue, slug, scope, task, base, repoRoot, transport, home = stateDir, nowMs = Date.now(), git = trustedGit, preflight = preflightWorkspace }) {
  if (!transport) return { status: 'blocked', reason: 'chưa có cầu nối Antigravity trên collab/integration (PR #894/#899 chờ owner)' };
  const live = readJson(jobPath(home), null);
  if (live?.status === 'asked') return { status: 'busy', job: `${live.issue}-${live.slug}` };
  const reasons = [];
  if (!Number.isInteger(issue) || issue < 1) reasons.push('thiếu số issue');
  if (!/^[a-z0-9][a-z0-9-]{0,39}$/.test(String(slug ?? ''))) reasons.push('slug chỉ gồm a-z, 0-9, -');
  if (!/^[0-9a-f]{40}$/.test(String(base ?? ''))) reasons.push('base phải là SHA đầy đủ');
  reasons.push(...scopeReasons(scope));
  const text = String(task ?? '').trim();
  if (!text || text.length > taskChars) reasons.push(`yêu cầu rỗng hoặc dài quá ${taskChars} ký tự`);
  reasons.push(...privateReasons(text, 'yêu cầu'));
  if (reasons.length) return { status: 'refused', reasons };
  const id = `${issue}-${slug}`;
  const job = { issue, slug, scope, base, dir: join(antiJobsDir(home), id), branch: `agent/anti/${id}`, repoRoot, at: nowMs };
  if (existsSync(job.dir)) return { status: 'refused', reasons: ['worktree việc này đã có'] };
  try {
    git(['rev-parse', '--verify', `${base}^{commit}`], { cwd: repoRoot });
    git(['worktree', 'add', '-q', '-b', job.branch, job.dir, base], { cwd: repoRoot, timeout: 60000 });
  } catch { return { status: 'refused', reasons: ['không tạo được worktree từ base'] }; }
  const fail = reasons2 => { removeWorktree(job, { repoRoot, git, home }); return { status: 'refused', reasons: reasons2 }; };
  const pre = preflight({ dir: job.dir, branch: job.branch, profile: 'anti', path: '/usr/bin:/bin', git: args => git(args, { cwd: job.dir }).trim() });
  if (pre.status !== 'PASS') return fail(pre.reasons.map(r => `preflight: ${r}`));
  const snap = buildSnapshot({ root: job.dir, allow: scope, git });
  if (!snap.ok) return fail(snap.reasons);
  let conversation;
  try { conversation = transport.start(antiTaskBrief({ issue, task: text, items: snap.items }), `Anti việc #${issue}`); }
  catch { return fail(['không mở được phiên Antigravity']); }
  if (!/^[0-9a-f-]{36}$/.test(String(conversation))) return fail(['Antigravity không trả mã phiên hợp lệ']);
  writeJson(jobPath(home), { ...job, shown: snap.items.map(i => i.path), conversation, status: 'asked' });
  return { status: 'started', job: id, branch: job.branch, files: snap.items.map(i => i.path) };
}

// Reads the answer of the open job and applies it. Returns { status, ... } or null with no job.
export function stepJob({ transport, home = stateDir, nowMs = Date.now(), git = trustedGit, preflight = preflightWorkspace, io }) {
  const job = readJson(jobPath(home), null);
  if (!job || job.status !== 'asked') return null;
  const save = (status, extra = {}) => { writeJson(jobPath(home), { ...job, status, ...extra }); return { status, job: `${job.issue}-${job.slug}`, ...extra }; };
  const drop = reasons => { removeWorktree(job, { repoRoot: job.repoRoot, git, home }); return save('dropped', { reasons: reasons.map(r => clean(r, 200)).slice(0, 10) }); };
  if (!transport) return { status: 'blocked', reason: 'chưa có cầu nối Antigravity' };
  if (!Number.isFinite(job.at) || nowMs < job.at || nowMs - job.at > answerLimitMs) return drop(['quá 20 phút chưa trả lời']);
  let answer;
  try { answer = transport.read(job.conversation); } catch { return drop(['không đọc được phiên Antigravity']); }
  if (answer?.tools?.length) return drop(checkAnswer(answer, job.shown).reasons);
  if (!answer?.done) return { status: 'waiting', job: `${job.issue}-${job.slug}` };
  const checked = checkAnswer(answer, job.shown);
  if (!checked.ok) return drop(checked.reasons);
  const pre = preflight({ dir: job.dir, branch: job.branch, profile: 'anti', path: '/usr/bin:/bin', git: args => git(args, { cwd: job.dir }).trim() });
  if (pre.status !== 'PASS') return drop(pre.reasons.map(r => `preflight: ${r}`));
  const applied = applyPatch({ root: job.dir, patch: checked.patch, scope: job.scope, home, ...(io ? { io } : {}) });
  if (applied.invalid) return save('invalid', { reasons: applied.reasons });
  if (!applied.ok) return drop(applied.reasons);
  try {
    git(['add', '--', ...applied.written], { cwd: job.dir });
    const msg = `feat(anti): #${job.issue} ${job.slug}\n\n${trailer}\nApplied-By: trusted host (scripts/collab-anti-job.mjs)`;
    git(['-c', `user.name=${hostName}`, '-c', `user.email=${hostEmail}`, 'commit', '-q', '--no-verify', '-m', msg], { cwd: job.dir });
    const changed = git(['diff', '--name-only', '-z', `${job.base}..HEAD`], { cwd: job.dir }).split('\0').filter(Boolean);
    if (git(['status', '--porcelain', '--untracked-files=all'], { cwd: job.dir }).trim() || changed.sort().join('\n') !== [...applied.written].sort().join('\n')) return save('invalid', { reasons: ['commit khác các file đã áp'] });
    return save('applied', { commit: git(['rev-parse', 'HEAD'], { cwd: job.dir }).trim(), branch: job.branch, files: applied.written });
  } catch { return save('invalid', { reasons: ['không commit được trong worktree việc'] }); }
}

// The real bridge, only when it exists on this checkout.
export async function antigravityTransport() {
  if (!existsSync(new URL('./collab-antigravity.mjs', import.meta.url))) return null;
  const m = await import('./collab-antigravity.mjs');
  return { start: (brief, title) => m.startConversation(brief, title, { left: () => 60000 }), read: id => m.readAnswer(m.conversationSteps(id, { left: () => 30000 })) };
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const val = k => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : undefined; };
  const transport = await antigravityTransport();
  let out;
  if (args.includes('--status')) out = readJson(jobPath(), null) ?? { status: 'none' };
  else if (args.includes('--step')) out = stepJob({ transport }) ?? { status: 'none' };
  else if (args.includes('--open')) {
    const repoRoot = trustedGit(['rev-parse', '--show-toplevel'], { cwd: process.cwd() }).trim();
    out = openJob({ issue: Number(val('--issue')), slug: val('--slug'), scope: String(val('--scope') ?? '').split(',').filter(Boolean), task: val('--task-file') ? readFileSync(val('--task-file'), 'utf8') : '', base: val('--base'), repoRoot, transport });
  } else { process.stderr.write('dùng --open | --step | --status\n'); process.exit(2); }
  process.stdout.write(`${JSON.stringify(out)}\n`);
  process.exitCode = out.status === 'blocked' ? 3 : 0;
}
