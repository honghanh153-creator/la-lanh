// Shared rules for the Claude ⇄ Codex auto loop (docs/operations/collab-auto-loop-plan.md).
// Everything read from GitHub is untrusted data: only fixed grammar lines change state.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, renameSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export const repo = 'honghanh153-creator/la-lanh';
export const integration = 'collab/integration';
export const agentMarker = '<!-- la-lanh-agent';
export const stateDir = process.env.LA_LANH_COLLAB_HOME || join(homedir(), '.cache', 'la-lanh-collab');
export const blockingP2 = new Set(['privacy', 'security', 'user_copy']);
// Process PRs (the loop itself, CI, test hardening) go first: a broken loop stalls every other group.
export const areaOrder = ['ops', 'content', 'privacy', 'feature'];

const sha40 = /^[0-9a-f]{40}$/;
export const isSha = value => sha40.test(String(value ?? ''));

export function clean(value, limit = 4000) {
  const text = String(value ?? '').replace(/[\u0000-\u0008\u000b-\u001f\u007f\u2028\u2029]/g, '');
  return text.length > limit ? `${text.slice(0, limit)} [...truncated]` : text;
}

// The repo is public: anyone may comment. Only the owner account (shared by both agents) counts.
export const isTrusted = comment => comment?.authorAssociation === 'OWNER';

const lines = body => String(body ?? '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);

// A verdict comment starts with the verdict line, optionally after "Reviewer: …" lines.
// A verdict quoted later in a handoff never counts.
export function parseVerdict(body) {
  for (const line of lines(body).slice(0, 3)) {
    const m = /^Review verdict:\s*(APPROVE|REQUEST_CHANGES)\s*@\s*([0-9a-f]{40})\b/.exec(line);
    if (m) return { verdict: m[1], sha: m[2] };
    if (!/^Reviewer:/i.test(line)) return null;
  }
  return null;
}

export function parseAuthorCheck(body) {
  const first = lines(body)[0] ?? '';
  const m = /^Author check:\s*(PASS|FAIL)\s*@\s*([0-9a-f]{40})\b/.exec(first);
  return m ? { status: m[1], sha: m[2] } : null;
}

export const isAutoReview = body => String(body ?? '').includes(`${agentMarker} codex-auto-review`);
export const fixForwardIssue = body => Number(/^Fix-forward:\s*#(\d+)/m.exec(String(body ?? ''))?.[1]) || null;

// Owner replies to the daily plan. Agents must never post these, see assertAgentBody.
const fold = text => String(text ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/gi, 'd').toLowerCase();
export function parseOwnerReply(body) {
  const rows = lines(body).map(fold);
  const dropped = rows.flatMap(r => [...r.matchAll(/^bo\s+#(\d+)/g)].map(m => Number(m[1])));
  if (rows.some(r => /^giu\b/.test(r))) return { action: 'hold', dropped };
  if (rows.some(r => /^duyet\b/.test(r))) return { action: 'approve', dropped };
  return dropped.length ? { action: 'drop', dropped } : null;
}

export function assertAgentBody(body) {
  if (parseOwnerReply(body)) throw new Error('Agent comments may not use the owner reply grammar (Duyệt/Giữ/Bỏ).');
  if (!String(body).includes(agentMarker)) throw new Error('Agent comments must carry the la-lanh-agent marker.');
  return body;
}

// Trusted comments in time order, with parsed lines attached.
export function trustedComments(comments = []) {
  return comments.filter(isTrusted)
    .map(c => ({ ...c, verdict: parseVerdict(c.body), check: parseAuthorCheck(c.body), auto: isAutoReview(c.body), agent: String(c.body ?? '').includes(agentMarker) }))
    .sort((a, b) => String(a.createdAt).localeCompare(String(b.createdAt)));
}

// One reading of a PR's review state for both the turn table and the merge gate.
// The latest author check for the head wins; verdicts before a retarget no longer count.
export function reviewState(pr) {
  const trusted = trustedComments(pr.comments);
  const retarget = trusted.filter(c => String(c.body ?? '').includes(`${agentMarker} retarget`)).at(-1);
  const current = retarget ? trusted.filter(c => String(c.createdAt) > String(retarget.createdAt)) : trusted;
  return {
    trusted,
    check: trusted.filter(c => c.check?.sha === pr.headRefOid).at(-1)?.check ?? null,
    last: current.filter(c => c.verdict).at(-1) ?? null,
  };
}

export function classifyArea(pr) {
  const label = (pr.labels ?? []).map(l => l.name ?? l).find(n => /^area:/.test(n));
  if (label && areaOrder.includes(label.slice(5))) return label.slice(5);
  const title = fold(pr.title);
  if (/^docs\(registry\)|^ops\(|^ci|^chore\(collab|^test:/.test(title)) return title.includes('probe') ? 'privacy' : 'ops';
  if (/privacy|erasure|consent|export|legal|journal|birth|rieng tu|us-23|p0[0-9]|p1[0-2]/.test(title)) return 'privacy';
  if (/prototype|game|nby|noi binh yen|lab/.test(title)) return 'feature';
  if (/tarot|content|copy|radar|hop gu|daily|la-chung|lua|luna|rewrite|cau/.test(title)) return 'content';
  return 'feature';
}

export function sortByPriority(prs) {
  return [...prs].sort((a, b) => areaOrder.indexOf(classifyArea(a)) - areaOrder.indexOf(classifyArea(b))
    || String(a.createdAt).localeCompare(String(b.createdAt)) || a.number - b.number);
}

// Wall clock in Vietnam, independent of the Mac's time zone.
export function vnNow(date = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(date).map(p => [p.type, p.value]));
  return { date: `${parts.year}-${parts.month}-${parts.day}`, hour: Number(parts.hour), minute: Number(parts.minute) };
}

// gh with fixed argv and no shell. Tests pass their own runner.
export function makeGh(run = execFileSync) {
  const call = (args, input) => run('gh', args, { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, timeout: 60000, input });
  return {
    raw: call,
    json: args => JSON.parse(call(args)),
    pr: number => JSON.parse(call(['pr', 'view', String(Number(number)), '--repo', repo, '--json',
      'number,title,url,state,isDraft,baseRefName,headRefName,headRefOid,mergeable,labels,createdAt,comments,body'])),
    openPrs: () => JSON.parse(call(['pr', 'list', '--repo', repo, '--state', 'open', '--limit', '100', '--json',
      'number,title,url,isDraft,baseRefName,headRefName,headRefOid,labels,createdAt,comments'])),
    comment: (kind, number, body) => call([kind, 'comment', String(Number(number)), '--repo', repo, '--body-file', '-'], assertAgentBody(body)),
  };
}

export function readJson(path, fallback) {
  try { return JSON.parse(readFileSync(path, 'utf8')); } catch { return fallback; }
}
export function writeJson(path, value) {
  mkdirSync(join(path, '..'), { recursive: true });
  writeFileSync(`${path}.tmp`, `${JSON.stringify(value, null, 2)}\n`);
  renameSync(`${path}.tmp`, path);
}
export const dayStatePath = date => join(stateDir, 'state', `${date}.json`);
