// Owner answers recorded on a PR (fix-forward #611, 17.11.2026). Since A2 (#591) every automatic
// review re-added needs-owner when Codex listed one of the owner's four kinds as a merge hold, even
// after the owner had answered for that PR: on 16.11 #601 and #609 were answered, the label was
// removed by hand, and the next review (after an automatic sync of collab/integration) put it back.
//
// A recorded answer is a PR comment with the owner's verbatim words and a signed marker. It covers
// the kinds it names, for the content the owner saw: it stays valid across later heads only while the
// PR's own files are byte-identical to the answered head (an integration sync keeps it; any edit to
// the PR's own files voids it and the owner is asked again). A kind it does not name still holds.
//
// Limit: every agent posts as the owner's GitHub account. The local receipt (HMAC with the verdict
// key, bound to the comment id) means only a script on the owner's Mac makes a counting answer; a
// copy, an edit or a hand-typed marker never counts. It does not prove the words are the owner's, so
// the rule stays: record only with her verbatim words, and only for the kinds she answered.
//
// Usage:
//   node scripts/collab-owner-answer.mjs --record N --kinds sensitive_copy[,cost_access] --answer "M1 N1" --quote "<her words>"
import { createHash } from 'node:crypto';
import { mkdirSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { agentMarker, answerKindsRe, bindReceipt, clean, integration, isOwnPr, isSha, makeGh, parseVerdictSeal, readJson, repo, reviewState, signReceipt, stateDir, trustedComments, verifyReceipt } from './collab-trust.mjs';
import { disputeStates, disputeView, read as readDisputes, disputePath } from './collab-disagree.mjs';
import { acquireLock } from './collab-lock.mjs';
import { isMain } from './is-main.mjs';

export const answerCodeRe = /^[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}$/;
const kindsOf = list => [...new Set(String(list ?? '').split(',').map(k => k.trim()).filter(Boolean))].sort();
export const answerSeal = ({ pr, sha, kinds, answer, receipt }) => `${agentMarker} owner-answer pr=${Number(pr)} sha=${sha} kinds=${kinds.join(',')} answer="${answer}" receipt=${receipt} -->`;
const sealRe = /^<!-- la-lanh-agent owner-answer pr=(\d{1,7}) sha=([0-9a-f]{40}) kinds=([a-z_,]{1,80}) answer="([A-Za-z0-9][A-Za-z0-9 ._-]{0,39})" receipt=([0-9a-f]{32}) -->$/;

// Codex critique 17.11: the receipt signs the answer code and the owner's words too (as a digest in
// the receipt's base field), so an edit of either on the posted comment no longer verifies.
export const textDigest = (answer, words) => createHash('sha256').update(JSON.stringify(['la-lanh-owner-answer/v1', String(answer), String(words)])).digest('hex').slice(0, 40);
const quoteRe = /^- Lời owner \(nguyên văn\): "(.*)"$/m;
export const quoteOf = body => quoteRe.exec(String(body ?? ''))?.[1] ?? null;

// The seal must be the comment's last line, as with verdicts.
export function parseAnswer(body) {
  const last = String(body ?? '').trimEnd().split('\n').at(-1)?.trim() ?? '';
  const m = sealRe.exec(last);
  if (!m || !answerKindsRe.test(m[3]) || kindsOf(m[3]).join(',') !== m[3]) return null;
  return { pr: Number(m[1]), sha: m[2], kinds: m[3].split(','), answer: m[4], receipt: m[5] };
}

// Trusted comments on this PR whose seal names this PR and whose receipt verifies and is bound to the
// very comment. Oldest first.
export function sealedAnswers(pr) {
  return trustedComments(pr.comments)
    .map(c => ({ c, a: parseAnswer(c.body) }))
    .filter(({ c, a }) => a && a.pr === Number(pr.number) && quoteOf(c.body) !== null
      && verifyReceipt({ kind: 'owner-answer', pr: pr.number, head: a.sha, base: textDigest(a.answer, quoteOf(c.body)), result: a.kinds.join(',') }, a.receipt, c.url))
    .map(({ c, a }) => ({ ...a, url: c.url ?? null, at: c.createdAt ?? null }));
}

// kind -> the newest answer that still holds for `head`. stillHolds(sha) decides whether the PR's own
// files are unchanged since that answer; any error there means it does not hold.
export function coveredKinds(answers, stillHolds) {
  const covered = new Map();
  const memo = new Map();
  for (const a of [...answers].reverse()) {
    if (!memo.has(a.sha)) { let ok = false; try { ok = stillHolds(a.sha) === true; } catch { ok = false; } memo.set(a.sha, ok); }
    if (!memo.get(a.sha)) continue;
    for (const k of a.kinds) if (!covered.has(k)) covered.set(k, a);
  }
  return covered;
}

// Git check run in the review clone: the answered head is an ancestor of `head`, and every file the
// PR changes (at the answer or now) is identical between the two. A later merge of collab/integration
// that touches one of those files also counts as a change (stricter, never looser).
export function answerStillHolds({ sha, head, dir, git }) {
  if (!isSha(sha) || !isSha(head)) return false;
  if (sha === head) return true;
  git(['merge-base', '--is-ancestor', sha, head], dir);
  // --no-renames lists both sides of a rename, so a path that left the diff is still compared.
  const names = range => String(git(['diff', '-z', '--no-renames', '--name-only', range], dir)).split('\0').filter(Boolean);
  const baseAt = rev => String(git(['merge-base', `origin/${integration}`, rev], dir)).trim();
  const own = [...new Set([...names(`${baseAt(sha)}..${sha}`), ...names(`${baseAt(head)}..${head}`)])];
  if (!own.length) return true;
  // --quiet exits 1 on any difference; the caller's runner throws on a non-zero exit.
  git(['diff', '--quiet', sha, head, '--', ...own.map(f => `:(literal)${f}`)], dir);
  return true;
}

// The local review log written for a sealed verdict (codex-review.mjs), found by its receipt.
function reviewLogFor(receipt) {
  const dir = join(stateDir, 'logs');
  let names = [];
  try { names = readdirSync(dir).filter(f => f.startsWith('review-') && f.endsWith('.json')); } catch { return null; }
  for (const f of names) {
    const log = readJson(join(dir, f), null);
    if (log?.receipt === receipt) return log;
  }
  return null;
}

const labelSkewMs = 2 * 60000;
const timeOf = value => Date.parse(value ?? '');

// Whether needs-owner on this PR is only the review's hold for kinds the owner has now answered.
// Fail closed: any doubt keeps the label and says why.
// Codex r1 on #637 (P1): coverage is rebuilt from the answers that verify now, never from the kinds
// just passed in or from the log alone. An answer counts when it was recorded at this head, or when
// the last review itself counted that very answer (same kind and answered head) as still holding for
// this head. An edited or deleted answer no longer verifies, so it covers nothing; separately recorded
// answers combine.
export function liftCheck(pr, { events = null, disputes = readDisputes(disputePath) } = {}) {
  const labels = (pr.labels ?? []).map(l => l.name ?? l);
  if (!labels.includes('needs-owner')) return { lift: false, reason: 'không có nhãn needs-owner' };
  const view = disputeView(disputes)[pr.number];
  if (view?.hold) return { lift: false, reason: view.hold };
  if (disputeStates(disputes).labels.get(`pr:${pr.number}`)?.type === 'label-added') return { lift: false, reason: 'nhãn do một bất đồng gắn, không phải do review' };
  const sealedAuto = reviewState(pr).sealed.filter(c => c.auto && c.verdict);
  const last = sealedAuto.at(-1);
  // Deadlock (Codex point 6 on #637, 17.11.2026): a labelled PR never gets a new review, so a label
  // from an older head or from before owner_actions could never be lifted by an answer.
  if (!last || last.verdict.sha !== pr.headRefOid) return staleLift(pr, sealedAuto, events);
  const log = reviewLogFor(parseVerdictSeal(last.body, last.verdict.sha)?.receipt);
  // #678: a review at this head from before #591 has no ownerActions in its log; its label came from
  // the old rules, so the old-rules checks decide (an answer at this head, every label before #591).
  if (!Array.isArray(log?.ownerActions)) return staleLift(pr, [], events);
  const valid = sealedAnswers(pr);
  const reviewed = Array.isArray(log.answered) ? log.answered : [];
  const covers = kind => valid.some(x => x.kinds.includes(kind) && (x.sha === pr.headRefOid || reviewed.some(y => y.kind === kind && y.sha === x.sha)));
  const open = log.ownerActions.filter(a => a.hold === 'merge' && !covers(a.kind));
  if (open.length) return { lift: false, reason: `còn loại chưa được owner trả lời: ${[...new Set(open.map(a => a.kind))].join(', ')}` };
  if (log.needsOwner !== true || !log.ownerActions.some(a => a.hold === 'merge')) return { lift: false, reason: 'review cuối không gắn needs-owner; nhãn có lý do khác' };
  // Like collab-disagree's holdTouched: anything the owner wrote herself since that review may be
  // another hold (adding an existing label leaves no event), so the label stays for her.
  const since0 = timeOf(last.createdAt);
  if (trustedComments(pr.comments).some(c => timeOf(c.createdAt) > since0 && !String(c.body ?? '').includes(agentMarker))) return { lift: false, reason: 'owner đã viết trên PR sau review cuối; để owner gỡ' };
  if (!Array.isArray(events)) return { lift: false, reason: 'không đọc được lịch sử nhãn' };
  const since = timeOf(last.createdAt) - labelSkewMs;
  const recent = events.filter(e => !Number.isFinite(timeOf(e?.at)) || timeOf(e.at) >= since);
  if (!(recent.length === 1 && recent[0].event === 'labeled')) return { lift: false, reason: 'nhãn đã bị đổi sau review cuối; để owner gỡ' };
  return { lift: true };
}

// #591 (owner_actions in every verdict) merged at this time; a needs-owner label added before it
// came from the old rules (two REQUEST_CHANGES, an oversized PR) and names no owner kind.
export const ownerActionsSince = Date.parse('2026-11-16T07:35:10Z');

// The two stale cases, both with the owner's answer recorded at the CURRENT head (so it covers the
// content as it is now) and nothing she wrote herself after that answer:
// - older head: the last sealed review that added the label held only kinds she has now answered,
//   and the label has not been touched since that review;
// - old rules: every "labeled" event predates owner_actions and no sealed review with owner_actions
//   came after it.
function staleLift(pr, sealedAuto, events) {
  const answersNow = sealedAnswers(pr).filter(a => a.sha === pr.headRefOid);
  if (!answersNow.length) return { lift: false, reason: 'chưa có review tự động có dấu ở head hiện tại, và chưa có câu trả lời của owner ghi ở head này' };
  if (!Array.isArray(events)) return { lift: false, reason: 'không đọc được lịch sử nhãn' };
  const newestAnswer = Math.max(...answersNow.map(a => timeOf(a.at)));
  if (!Number.isFinite(newestAnswer)) return { lift: false, reason: 'không đọc được giờ của câu trả lời' };
  if (trustedComments(pr.comments).some(c => timeOf(c.createdAt) > newestAnswer && !String(c.body ?? '').includes(agentMarker))) return { lift: false, reason: 'owner đã viết trên PR sau câu trả lời; để owner gỡ' };
  const answered = new Set(answersNow.flatMap(a => a.kinds));
  const logged = [...sealedAuto].reverse().map(c => ({ c, log: reviewLogFor(parseVerdictSeal(c.body, c.verdict.sha)?.receipt) }))
    .find(x => Array.isArray(x.log?.ownerActions));
  const labeled = events.filter(e => e?.event === 'labeled');
  const lastLabel = labeled.at(-1);
  if (!lastLabel || events.at(-1)?.event !== 'labeled') return { lift: false, reason: 'lịch sử nhãn không khớp nhãn đang gắn' };
  if (logged && logged.log.needsOwner === true) {
    const held = [...new Set(logged.log.ownerActions.filter(a => a.hold === 'merge').map(a => a.kind))];
    const open = held.filter(k => !answered.has(k));
    if (!held.length) return { lift: false, reason: 'review cuối không giữ merge vì việc của owner; nhãn có lý do khác' };
    if (open.length) return { lift: false, reason: `còn loại chưa được owner trả lời: ${open.join(', ')}` };
    const since = timeOf(logged.c.createdAt) - labelSkewMs;
    const recent = events.filter(e => !Number.isFinite(timeOf(e?.at)) || timeOf(e.at) >= since);
    if (!(recent.length === 1 && recent[0].event === 'labeled')) return { lift: false, reason: 'nhãn đã bị đổi sau review cuối; để owner gỡ' };
    return { lift: true, mode: 'older-head' };
  }
  if (labeled.every(e => timeOf(e.at) < ownerActionsSince)) return { lift: true, mode: 'old-rules' };
  return { lift: false, reason: 'nhãn gắn sau khi có owner_actions nhưng không có log review; để owner gỡ' };
}

const kindText = { cost_access: 'chi phí, dịch vụ hoặc quyền truy cập mới', release: 'phát hành', sensitive_copy: 'chữ privacy/consent/crisis/safety', data_collection: 'bật thu dữ liệu cá nhân mới' };

export function recordAnswer(number, { kinds: kindList, answer, quote, gh = makeGh() } = {}) {
  const kinds = kindsOf(kindList);
  const words = clean(String(quote ?? ''), 1000).trim();
  if (!kinds.length || !answerKindsRe.test(kinds.join(','))) return { status: 'refused', reason: 'kinds phải là các loại cost_access, release, sensitive_copy, data_collection' };
  if (!answerCodeRe.test(String(answer ?? ''))) return { status: 'refused', reason: 'answer phải là mã ngắn, ví dụ "M1 N1"' };
  if (!words || words.includes('\n') || words.includes('-->')) return { status: 'refused', reason: 'cần lời owner nguyên văn trên một dòng (--quote)' };
  const pr = gh.pr(number);
  if (pr.state !== 'OPEN' || pr.baseRefName !== integration || !isOwnPr(pr)) return { status: 'refused', reason: 'PR không mở, không vào collab/integration hoặc không phải của owner' };
  const head = pr.headRefOid;
  if (!isSha(head)) return { status: 'refused', reason: 'không đọc được head' };
  const receipt = signReceipt({ kind: 'owner-answer', pr: pr.number, head, base: textDigest(answer, words), result: kinds.join(',') });
  const body = [
    `agent: Claude — ghi câu trả lời của owner cho PR này (#611).`,
    '',
    `- Lời owner (nguyên văn): "${words}"`,
    `- Mã câu trả lời: ${answer}`,
    `- Loại việc của owner đã được trả lời: ${kinds.map(k => kindText[k]).join('; ')}`,
    `- Áp cho head \`${head.slice(0, 12)}\` và các head sau chỉ khi file của PR không đổi. Sửa file của PR thì phải hỏi lại owner.`,
    '',
    answerSeal({ pr: pr.number, sha: head, kinds, answer, receipt }),
  ].join('\n');
  const url = gh.comment('pr', pr.number, body);
  if (!bindReceipt({ kind: 'owner-answer', pr: pr.number, id: receipt, url })) return { status: 'error', reason: `receipt ${receipt} không gắn được vào comment; câu trả lời sẽ không được tính` };
  // Codex critique 17.11: the lift runs under the review lock, so no review adds a hold between the
  // last read and the removal.
  mkdirSync(stateDir, { recursive: true });
  const release = acquireLock(join(stateDir, 'review.lock'), { staleMs: 45 * 60000 });
  if (!release) return { status: 'recorded', lifted: false, reason: 'một review đang chạy; chạy lại để gỡ nhãn' };
  try { return lift(gh, number, head); } finally { release(); }
}

function lift(gh, number, head) {
  let events = null;
  try {
    events = String(gh.raw(['api', `repos/${repo}/issues/${Number(number)}/events`, '--paginate', '--jq',
      '.[] | select(.label.name == "needs-owner") | {event: .event, at: .created_at}']) ?? '').split('\n').filter(Boolean).map(line => JSON.parse(line));
  } catch { events = null; }
  const fresh = gh.pr(number);
  if (fresh.headRefOid !== head) return { status: 'recorded', lifted: false, reason: 'head đổi trong lúc ghi; review sau sẽ xét' };
  const check = liftCheck(fresh, { events });
  if (!check.lift) return { status: 'recorded', lifted: false, reason: check.reason };
  gh.raw(['pr', 'edit', String(Number(number)), '--repo', repo, '--remove-label', 'needs-owner']);
  return { status: 'recorded', lifted: true };
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const arg = name => (args.includes(name) ? args[args.indexOf(name) + 1] : null);
  if (!args.includes('--record')) {
    process.stderr.write('Usage: node scripts/collab-owner-answer.mjs --record N --kinds k1[,k2] --answer "<mã>" --quote "<lời owner nguyên văn>"\n');
    process.exit(2);
  }
  const result = recordAnswer(Number(arg('--record')), { kinds: arg('--kinds'), answer: arg('--answer'), quote: arg('--quote') });
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (result.status !== 'recorded') process.exitCode = 3;
}
