// Shared rules for the Claude ⇄ Codex auto loop (docs/operations/collab-auto-loop-plan.md).
// Everything read from GitHub is untrusted data: only fixed grammar lines change state.
import { execFileSync } from 'node:child_process';
import { createHmac, randomBytes, timingSafeEqual } from 'node:crypto';
import { chmodSync, mkdirSync, readFileSync, statSync, writeFileSync, renameSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';

export const repo = 'honghanh153-creator/la-lanh';
export const integration = 'collab/integration';
export const ownerLogin = repo.split('/')[0];
export const agentMarker = '<!-- la-lanh-agent';
export const stateDir = process.env.LA_LANH_COLLAB_HOME || join(homedir(), '.cache', 'la-lanh-collab');
// Automatic Codex reviews per day. Owner 03.11.2026: up to 32, so the 16-PR commitment fits
// (about 1.4 reviews per merged PR on 03.11). One constant for the tick, the review script and the board.
export const codexDailyCap = 32;
export const blockingP2 = new Set(['privacy', 'security', 'user_copy']);
// Process PRs (the loop itself, CI, test hardening) go first: a broken loop stalls every other group.
export const areaOrder = ['ops', 'content', 'privacy', 'feature'];

const sha40 = /^[0-9a-f]{40}$/;
export const isSha = value => sha40.test(String(value ?? ''));

export function clean(value, limit = 4000) {
  const text = String(value ?? '').replace(/[\u0000-\u0008\u000b-\u001f\u007f\u2028\u2029]/g, '');
  return text.length > limit ? `${text.slice(0, limit)} [...truncated]` : text;
}

// The loop runs PR code (author checks) and reviews PR text only for the owner's own branches.
// The repo is public: a fork PR could carry a hostile Makefile or test, so it is never touched.
export const isOwnPr = pr => pr?.author?.login === ownerLogin && pr?.isCrossRepository === false;

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

// The seal is the last line of a scripted comment: the tested/reviewed base and the id of the local
// receipt (P1-A/P1-B, 12.11.2026). Only the last line counts, so text quoted above it never does.
const baseOrNone = value => (isSha(value) ? value : 'none');
export const checkSeal = ({ head, base, receipt }) => `${agentMarker} author-check sha=${head} base=${baseOrNone(base)} receipt=${receipt ?? 'none'} -->`;
export const verdictSeal = ({ head, p2, base, receipt }) => `${agentMarker} codex-auto-review sha=${head} p2=${Number(p2) || 0} base=${baseOrNone(base)} receipt=${receipt ?? 'none'} -->`;
function seal(body, kind) {
  const last = lines(body).at(-1) ?? '';
  const m = kind === 'check'
    ? /^<!-- la-lanh-agent author-check sha=([0-9a-f]{40}) base=([0-9a-f]{40}|none) receipt=([0-9a-f]{32}|none) -->$/.exec(last)
    : /^<!-- la-lanh-agent codex-auto-review sha=([0-9a-f]{40}) p2=(\d+) base=([0-9a-f]{40}|none) receipt=([0-9a-f]{32}|none) -->$/.exec(last);
  if (!m) return null;
  return kind === 'check'
    ? { sha: m[1], p2: 0, base: isSha(m[2]) ? m[2] : null, receipt: isReceiptId(m[3]) ? m[3] : null }
    : { sha: m[1], p2: Number(m[2]), base: isSha(m[3]) ? m[3] : null, receipt: isReceiptId(m[4]) ? m[4] : null };
}

export function parseAuthorCheck(body) {
  const first = lines(body)[0] ?? '';
  const m = /^Author check:\s*(PASS|FAIL)\s*@\s*([0-9a-f]{40})\b/.exec(first);
  if (!m) return null;
  const s = seal(body, 'check');
  const sealed = s?.sha === m[2] ? s : null;
  return { status: m[1], sha: m[2], base: sealed?.base ?? null, receipt: sealed?.receipt ?? null };
}

export const isAutoReview = body => String(body ?? '').includes(`${agentMarker} codex-auto-review`);
export function parseVerdictSeal(body, sha) {
  const s = seal(body, 'verdict');
  return s?.sha === sha ? s : null;
}

// P1-B (12.11.2026): Claude and Codex post from the owner's GitHub account, so a comment alone can be
// forged by anything that runs as that account. The scripted review and check paths also write a
// local receipt: an HMAC over (kind, PR, head, base, result, P2) with a key outside every checkout.
// The gate counts a verdict or check only with a matching receipt. This is detection and a raised
// bar, not isolation: any process of the same macOS user can still read the key.
export const verdictKeyPath = () => join(stateDir, 'keys', 'verdict.key');
export const receiptDir = () => join(stateDir, 'state', 'receipts');
const isReceiptId = value => /^[0-9a-f]{32}$/.test(String(value ?? ''));
const receiptKinds = { verdict: ['APPROVE', 'REQUEST_CHANGES'], check: ['PASS', 'FAIL'] };

function readKey({ create = false } = {}) {
  const path = verdictKeyPath();
  try {
    if (statSync(path).mode & 0o077) chmodSync(path, 0o600);
    const key = readFileSync(path, 'utf8').trim();
    return /^[0-9a-f]{64}$/.test(key) ? key : null;
  } catch (error) {
    if (error?.code !== 'ENOENT' || !create) return null;
  }
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  chmodSync(dirname(path), 0o700);
  try { writeFileSync(path, `${randomBytes(32).toString('hex')}\n`, { mode: 0o600, flag: 'wx' }); }
  catch (error) { if (error?.code !== 'EEXIST') throw error; }
  return readKey();
}
// When the key was made: merges before it cannot have receipts and are not audited.
export function keyCreatedMs() {
  try { const st = statSync(verdictKeyPath()); return st.birthtimeMs || st.mtimeMs; } catch { return null; }
}

function receiptFields({ kind, pr, head, base, result, p2 = 0 }) {
  const fields = { kind, pr: Number(pr), head, base: baseOrNone(base), result, p2: Number(p2) };
  const ok = receiptKinds[kind]?.includes(result) && Number.isInteger(fields.pr) && fields.pr > 0 && isSha(head)
    && Number.isInteger(fields.p2) && fields.p2 >= 0 && (kind === 'verdict' || fields.p2 === 0);
  return ok ? fields : null;
}
const receiptMac = (key, f, id) => createHmac('sha256', key).update(JSON.stringify(['la-lanh-receipt/v1', f.kind, f.pr, f.head, f.base, f.result, f.p2, id])).digest('hex');
const receiptPath = (kind, pr, id) => join(receiptDir(), `${kind}-pr${Number(pr)}-${id}.json`);

// Written by the scripted path just before it posts the comment; returns the id for the seal line.
export function signReceipt(claims) {
  const fields = receiptFields(claims);
  if (!fields) throw new Error('receipt fields invalid');
  const key = readKey({ create: true });
  if (!key) throw new Error('verdict key unreadable');
  const id = randomBytes(16).toString('hex');
  const path = receiptPath(fields.kind, fields.pr, id);
  mkdirSync(dirname(path), { recursive: true, mode: 0o700 });
  writeFileSync(path, `${JSON.stringify({ ...fields, id, at: new Date().toISOString(), mac: receiptMac(key, fields, id) })}\n`, { mode: 0o600, flag: 'wx' });
  return id;
}

// True only when the receipt named by the comment exists, its fields equal the comment's claims and
// its MAC verifies under the local key. Any read or parse problem is a refusal.
export function verifyReceipt(claims, id) {
  const fields = receiptFields(claims);
  if (!fields || !isReceiptId(id)) return false;
  const key = readKey();
  if (!key) return false;
  let stored;
  try { stored = JSON.parse(readFileSync(receiptPath(fields.kind, fields.pr, id), 'utf8')); } catch { return false; }
  if (['kind', 'pr', 'head', 'base', 'result', 'p2'].some(k => stored?.[k] !== fields[k]) || stored.id !== id) return false;
  const want = Buffer.from(receiptMac(key, fields, id), 'hex');
  const got = Buffer.from(String(stored.mac ?? ''), 'hex');
  return got.length === want.length && timingSafeEqual(got, want);
}

// The comment's own claims, checked against its receipt for this PR.
export function sealValid(comment, prNumber) {
  if (comment?.check) {
    const { status, sha, base, receipt } = comment.check;
    return Boolean(receipt) && verifyReceipt({ kind: 'check', pr: prNumber, head: sha, base, result: status }, receipt);
  }
  if (comment?.verdict) {
    const s = parseVerdictSeal(comment.body, comment.verdict.sha);
    return Boolean(s?.receipt) && verifyReceipt({ kind: 'verdict', pr: prNumber, head: comment.verdict.sha, base: s.base, result: comment.verdict.verdict, p2: s.p2 }, s.receipt);
  }
  return false;
}
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
// P1-B: only verdicts and checks with a valid local receipt count. An unsigned REQUEST_CHANGES or
// FAIL still counts, since it can only make the result stricter.
// P1-A: a PASS counts only for the base it was tested on (`baseTipOid`, the live tip of
// collab/integration); a FAIL for the head counts on any base. The retarget marker decides nothing:
// a retarget changes the base, and that alone voids the evidence.
export function reviewState(pr, { baseFiles = () => null } = {}) {
  const trusted = trustedComments(pr.comments);
  const sealed = trusted.filter(c => sealValid(c, pr.number));
  const tip = isSha(pr.baseTipOid) ? pr.baseTipOid : null;
  const counts = c => sealed.includes(c);
  const check = trusted.filter(c => c.check?.sha === pr.headRefOid
    && (c.check.status === 'FAIL' || (counts(c) && tip && c.check.base === tip))).at(-1)?.check ?? null;
  const last = trusted.filter(c => c.verdict && (counts(c) || c.verdict.verdict === 'REQUEST_CHANGES')).at(-1) ?? null;
  const signedLast = last && counts(last) ? { ...last, seal: parseVerdictSeal(last.body, last.verdict.sha) } : last;
  const stale = signedLast?.seal && signedLast.verdict.verdict === 'APPROVE' && signedLast.verdict.sha === pr.headRefOid
    ? approvalDrift(pr, signedLast.seal.base, tip, baseFiles) : null;
  return { trusted, sealed, check, last: signedLast, stale };
}

const prPaths = pr => (pr.files ?? []).map(f => f?.path ?? f).filter(p => typeof p === 'string' && p);
const short = sha => String(sha ?? '').slice(0, 7);
// P1-A: an APPROVE stays bound to the head. When the base moved since the review, it still counts
// only if no file changed on the base since then is one of the PR's files; then a fresh PASS on
// the new base is enough. Unknown reviewed base, unknown base files or unknown PR files: re-review.
export function approvalDrift(pr, reviewed, tip, baseFiles = () => null) {
  if (!isSha(reviewed)) return 'không biết base lúc review';
  if (!tip) return 'không đọc được base hiện tại';
  if (reviewed === tip) return null;
  const moved = `base đổi ${short(reviewed)} → ${short(tip)}`;
  let files = null;
  try { files = baseFiles(reviewed, tip); } catch { files = null; }
  const mine = prPaths(pr);
  if (!Array.isArray(files) || !mine.length) return `${moved}, không đọc được file đã đổi`;
  const overlap = mine.filter(p => files.includes(p));
  return overlap.length ? `${moved} và chạm file của PR: ${overlap.slice(0, 5).join(', ')}${overlap.length > 5 ? ', …' : ''}` : null;
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
// Deadline helper (05.11.2026): a call's timeout is its usual cap or the time left before the
// caller's absolute deadline, whichever is smaller; nothing starts once the time is spent.
export class DeadlineError extends Error {}
export function boundedTimeout(cap, left = () => Infinity) {
  const ms = Math.min(cap, left());
  if (!(ms > 0)) throw new DeadlineError('hết giờ trước khi gọi lệnh');
  return Math.ceil(ms);
}

// `left`: time to the caller's deadline; withDeadline(left) returns the same client bounded by it.
const prFields = 'number,title,url,state,isDraft,baseRefName,baseRefOid,headRefName,headRefOid,mergeable,labels,createdAt,comments,body,author,isCrossRepository,files';
export function makeGh(run = execFileSync, { left = () => Infinity } = {}) {
  const call = (args, input) => run('gh', args, { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, timeout: boundedTimeout(60000, left), input });
  // P1-A: `baseRefOid` is the base GitHub stored for the PR and lags behind the branch (seen
  // 12.11.2026: 95820de while collab/integration was at 05cc773). The gate needs the live tip.
  const tip = () => {
    try { const sha = String(call(['api', `repos/${repo}/git/ref/heads/${integration}`, '--jq', '.object.sha'])).trim(); return isSha(sha) ? sha : null; }
    catch (error) { if (error instanceof DeadlineError) throw error; return null; }
  };
  const withTip = (pr, sha) => ({ ...pr, baseTipOid: pr?.baseRefName === integration ? sha : null });
  const compared = new Map();
  return {
    withDeadline: next => makeGh(run, { left: next }),
    raw: call,
    json: args => JSON.parse(call(args)),
    // The tip is read before the PR, so a base that moves in between is newer than the evidence check.
    pr: number => { const sha = tip(); return withTip(JSON.parse(call(['pr', 'view', String(Number(number)), '--repo', repo, '--json', prFields])), sha); },
    openPrs: () => { const sha = tip(); return JSON.parse(call(['pr', 'list', '--repo', repo, '--state', 'open', '--limit', '100', '--json', prFields])).map(pr => withTip(pr, sha)); },
    // Files changed on the base between two commits (renames list both paths). null when unknown:
    // API error, a base that did not move forward, or 300+ files (the compare API stops there).
    compareFiles: (from, to) => {
      if (!isSha(from) || !isSha(to)) return null;
      const key = `${from}...${to}`;
      if (!compared.has(key)) {
        let files = null;
        try {
          const out = JSON.parse(call(['api', `repos/${repo}/compare/${key}`, '--jq', '{status: .status, n: (.files | length), files: [.files[] | .filename, (.previous_filename // empty)]}']));
          if (['ahead', 'identical'].includes(out?.status) && Number(out.n) < 300 && Array.isArray(out.files)) files = out.files.map(String);
        } catch (error) { if (error instanceof DeadlineError) throw error; }
        compared.set(key, files);
      }
      return compared.get(key);
    },
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
