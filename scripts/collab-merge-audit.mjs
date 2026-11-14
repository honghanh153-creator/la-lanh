// L26, "cách 2-nhẹ" (docs/operations/workflow-experiment-2026-11.md §0): an audit after each merge.
// The owner declined an independent gatekeeper on 14.11, so this is arm 2's only merge control.
// Once an hour the tick reads the PRs merged into collab/integration since the last pass and checks
// the same receipt as the night audit's M2 (collab-audit.mjs `receipt`): the last trusted verdict
// before the merge is Codex's automatic APPROVE of the merged head, and a local Codex output for that
// head is valid and gives APPROVE under the review policy. A merge without one raises one ops-alert.
// LIMIT (Codex P1, still open): with the same machine rights Claude could edit the outputs, the
// comments or this program. The audit checks consistency; it does not prove that Codex reviewed
// independently. It finds a gap after the merge and never blocks one.
// Usage: node scripts/collab-merge-audit.mjs [--force]   (one pass; prints JSON)
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { readOutputs, receipt } from './collab-audit.mjs';
import { clean, integration, makeGh, readJson, repo, stateDir, vnNow, writeJson } from './collab-trust.mjs';
import { opsAlert } from './collab-turn.mjs';
import { isMain } from './is-main.mjs';

export const auditStatePath = join(stateDir, 'merge-audit.json');
// Cross-check only: M2 stays measured by the night audit from GitHub and the outputs, not from here.
export const auditLogPath = join(stateDir, 'merge-audit.jsonl');
export const auditEveryMs = 60 * 60000;
// The first pass starts here (15.11 00:00 in Vietnam). Older merges are measured by the night
// audit's M2; alerting on them would open one issue per historical PR.
export const auditFrom = '2026-11-14T17:00:00Z';
// A merge this close to the scan start waits for the next pass: GitHub may list a merge shortly
// after its mergedAt, and the Mac clock may run ahead. Otherwise the cursor could pass it unseen.
export const settleMs = 2 * 60000;
const maxPages = 500;
const [owner, name] = repo.split('/');
export const auditMarker = number => `<!-- la-lanh-agent merge-audit pr=${Number(number)} -->`;
export const auditSubject = number => `merge #${Number(number)} vào integration thiếu biên nhận review`;
const reason = error => clean(String(error?.message ?? error).split('\n')[0], 200);

// Created order is stable while new PRs are added, so a full walk sees every merged PR once.
const listQuery = `query($owner:String!,$name:String!,$base:String!,$after:String){repository(owner:$owner,name:$name){
pullRequests(baseRefName:$base,states:MERGED,first:100,after:$after,orderBy:{field:CREATED_AT,direction:ASC}){
pageInfo{hasNextPage endCursor} nodes{number mergedAt headRefOid}}}}`;
const commentsQuery = `query($owner:String!,$name:String!,$number:Int!,$after:String){repository(owner:$owner,name:$name){
pullRequest(number:$number){comments(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{authorAssociation createdAt body}}}}}`;
const alertsQuery = `query($owner:String!,$name:String!,$after:String){repository(owner:$owner,name:$name){
issues(labels:["ops-alert"],states:[OPEN,CLOSED],first:100,after:$after,orderBy:{field:CREATED_AT,direction:ASC}){
pageInfo{hasNextPage endCursor} nodes{number body}}}}`;

// Every page of a GraphQL connection. Any failure throws: an unread page is never "no data".
export function allPages(gh, query, vars, pick) {
  const nodes = [];
  let after = null;
  for (let page = 0; page < maxPages; page += 1) {
    const args = ['api', 'graphql', '-f', `query=${query}`];
    for (const [k, v] of Object.entries(vars)) args.push(typeof v === 'number' ? '-F' : '-f', `${k}=${v}`);
    if (after) args.push('-f', `after=${after}`);
    const conn = pick(gh.json(args)?.data);
    if (!Array.isArray(conn?.nodes)) throw new Error('GitHub trả dữ liệu không đúng dạng');
    nodes.push(...conn.nodes);
    if (!conn.pageInfo?.hasNextPage) return nodes;
    if (!conn.pageInfo.endCursor || conn.pageInfo.endCursor === after) throw new Error('GitHub phân trang không tiến');
    after = conn.pageInfo.endCursor;
  }
  throw new Error(`quá ${maxPages} trang`);
}

// PRs are ordered by (mergedAt, number); the cursor is the last PR fully processed.
const key = pr => [Date.parse(pr.mergedAt), Number(pr.number)];
const later = (a, b) => a[0] > b[0] || (a[0] === b[0] && a[1] > b[1]);

function logOnce(path, entry) {
  const seen = existsSync(path) ? readFileSync(path, 'utf8').split('\n').some(line => {
    try { return JSON.parse(line).pr === entry.pr; } catch { return false; }
  }) : false;
  if (seen) return false;
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, `${JSON.stringify(entry)}\n`);
  return true;
}

export function alertText(pr, why) {
  return [
    `Merge #${pr.number} vào ${integration} lúc ${pr.mergedAt} (head ${String(pr.headRefOid).slice(0, 12)}) thiếu biên nhận review tự động: ${why}.`,
    'Cần xem PR này: merge không có Codex APPROVE tự động đúng head, kèm file output Codex hợp lệ cho head đó.',
    'Giới hạn: kiểm toán này chỉ đối chiếu sự nhất quán. Cùng quyền trên máy, Claude có thể sửa file output, comment hoặc chính chương trình này, nên nó không chứng minh Codex đã review độc lập.',
    auditMarker(pr.number),
  ].join('\n');
}

// One pass. A GitHub or file error stops the pass with the cursor where it was, so the next run
// retries from the first PR not fully processed; an error is never read as a missing receipt.
export function auditMerges({ gh = makeGh(), now = new Date(), outputs = () => readOutputs(), alert = null,
  statePath = auditStatePath, logPath = auditLogPath } = {}) {
  const raise = alert ?? ((text, subject) => opsAlert(gh, text, subject, vnNow(now)));
  const until = new Date(now.getTime() - settleMs).toISOString();
  let cursor = readJson(statePath, {}).cursor ?? { mergedAt: auditFrom, number: 0 };
  const save = patch => writeJson(statePath, { ...readJson(statePath, {}), ...patch });
  const result = { status: 'ok', until, processed: 0, missing: [] };
  try {
    const outs = outputs();
    const seen = new Set();
    const merged = allPages(gh, listQuery, { owner, name, base: integration }, d => d?.repository?.pullRequests)
      .filter(p => p?.mergedAt && Number.isInteger(p.number) && !seen.has(p.number) && seen.add(p.number))
      .filter(p => later(key(p), key(cursor)) && Date.parse(p.mergedAt) <= Date.parse(until))
      .sort((a, b) => key(a)[0] - key(b)[0] || a.number - b.number);
    let bodies = null; // ops-alert issues, open and closed, read once when the first gap appears
    for (const pr of merged) {
      const comments = allPages(gh, commentsQuery, { owner, name, number: pr.number }, d => d?.repository?.pullRequest?.comments);
      const check = receipt({ ...pr, comments }, outs);
      if (!check.ok) {
        // The marker on GitHub, not local state, decides: a crash after the issue was created and
        // before the state was saved must not alert twice.
        bodies ??= allPages(gh, alertsQuery, { owner, name }, d => d?.repository?.issues).map(i => String(i?.body ?? ''));
        const known = bodies.some(b => b.includes(auditMarker(pr.number)));
        if (!known) { raise(alertText(pr, check.why), auditSubject(pr.number)); bodies.push(auditMarker(pr.number)); }
        logOnce(logPath, { at: now.toISOString(), pr: pr.number, head: pr.headRefOid, reason: check.why });
        result.missing.push({ pr: pr.number, why: check.why, alerted: !known });
      }
      cursor = { mergedAt: pr.mergedAt, number: pr.number };
      save({ cursor });
      result.processed += 1;
    }
  } catch (error) {
    result.status = 'error';
    result.error = reason(error);
  }
  result.cursor = cursor;
  save({ lastPass: { at: now.toISOString(), until, status: result.status, processed: result.processed, missing: result.missing.length, ...(result.error ? { error: result.error } : {}) } });
  return result;
}

// The tick's entry: at most one pass an hour. The run time is stored first, so a failing GitHub
// is retried on the next hourly run, not on every 10-minute tick.
export function runMergeAudit({ now = new Date(), statePath = auditStatePath, force = false, ...rest } = {}) {
  const last = Date.parse(readJson(statePath, {}).lastRunAt ?? '');
  const age = now.getTime() - last;
  if (!force && Number.isFinite(last) && age >= 0 && age < auditEveryMs) return { status: 'skipped' };
  writeJson(statePath, { ...readJson(statePath, {}), lastRunAt: now.toISOString() });
  return auditMerges({ now, statePath, ...rest });
}

if (isMain(import.meta.url)) {
  try {
    const result = runMergeAudit({ force: process.argv.includes('--force') });
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (result.status === 'error') process.exitCode = 1;
  } catch (error) { process.stderr.write(`collab-merge-audit failed: ${reason(error)}\n`); process.exitCode = 1; }
}
