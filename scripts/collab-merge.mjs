// Merge one PR into collab/integration only when every condition in the auto-loop plan §4.2 holds.
// Usage: node scripts/collab-merge.mjs --pr N [--dry-run]
import { join } from 'node:path';
import { agentMarker, clean, dayStatePath, fixForwardIssue, integration, isOwnPr, isSha, keyCreatedMs, makeGh, readJson, repo, reviewState, sealValid, stateDir, trustedComments, vnNow, writeJson } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

// Merge-queue rules (P1-A/P1-B, 12.11.2026): the latest signed PASS must be for the live tip of
// collab/integration, and the latest signed APPROVE must be for the head and still valid for that tip
// (see approvalDrift). `baseFiles(from, to)` lists files changed on the base; without it any base
// move needs a new review.
export function mergeGate(pr, { baseFiles } = {}) {
  const reasons = [];
  const head = pr.headRefOid;
  const labels = (pr.labels ?? []).map(l => l.name ?? l);
  if (!isSha(head)) reasons.push('không đọc được head SHA');
  if (!isOwnPr(pr)) reasons.push('PR không phải của owner hoặc từ fork');
  if (pr.state && pr.state !== 'OPEN') reasons.push(`PR đang ${pr.state}`);
  if (pr.baseRefName !== integration) reasons.push(`base là ${pr.baseRefName}, chỉ merge vào ${integration}`);
  if (pr.isDraft) reasons.push('draft');
  if (labels.includes('needs-owner')) reasons.push('needs-owner');
  if (pr.mergeable !== 'MERGEABLE') reasons.push(`GitHub báo mergeable=${pr.mergeable}`);
  if (!isSha(pr.baseTipOid)) reasons.push(`không đọc được SHA hiện tại của ${integration}`);
  const { check, last, stale } = reviewState(pr, { baseFiles });
  if (!last?.seal || last.verdict.verdict !== 'APPROVE' || last.verdict.sha !== head) reasons.push('verdict mới nhất có biên nhận không phải APPROVE @ head');
  else if (stale) reasons.push(`APPROVE cần review lại: ${stale}`);
  // The newest author check for the head decides; an older PASS does not outvote a later FAIL.
  if (check?.status !== 'PASS') reasons.push(`Author check mới nhất @ head không phải PASS có biên nhận trên base hiện tại ${String(pr.baseTipOid ?? '?').slice(0, 7)}`);
  // Automatic approvals with non-blocking P2 must link their fix-forward issue; P2 comes from the signed seal.
  if (last?.seal && last.seal.p2 > 0 && !fixForwardIssue(last.body)) reasons.push('APPROVE có P2 nhưng thiếu issue fix-forward');
  return { ok: reasons.length === 0, head, base: pr.baseTipOid ?? null, reasons };
}

// Every merge, by the tick or by the direct command, lands in the day's list, so owner notes and
// the digest count it.
export function recordMerged(pr, date = vnNow().date) {
  const path = dayStatePath(date);
  const day = readJson(path, { codexRuns: 0, failures: 0 });
  writeJson(path, { ...day, mergedToday: [...(day.mergedToday ?? []).filter(m => m.number !== pr.number), { number: pr.number, title: pr.title }] });
}

export function runMerge(number, { gh = makeGh(), dryRun = false, date } = {}) {
  const pr = gh.pr(number);
  const gate = mergeGate(pr, { baseFiles: gh.compareFiles });
  if (!gate.ok) return { status: 'refused', reasons: gate.reasons };
  if (dryRun) return { status: 'would-merge', head: gate.head };
  // --match-head-commit fails the merge if the head moved after the check above.
  gh.raw(['pr', 'merge', String(pr.number), '--repo', repo, '--merge', '--match-head-commit', gate.head]);
  const retargeted = [];
  for (const child of gh.openPrs().filter(p => p.baseRefName === pr.headRefName)) {
    gh.raw(['pr', 'edit', String(child.number), '--repo', repo, '--base', integration]);
    // Informational only: the base change itself voids the old evidence (P1-A).
    gh.comment('pr', child.number, `PR cha #${pr.number} đã merge vào \`${integration}\`; base của PR này được đổi sang \`${integration}\`. Head không đổi; author check và verdict cũ không còn khớp base, PR cần check lại trên base mới.\n\n${agentMarker} retarget parent=${pr.number} -->`);
    retargeted.push(child.number);
  }
  try { recordMerged(pr, date); } catch {}
  writeJson(join(stateDir, 'logs', `merge-pr${pr.number}-${gate.head.slice(0, 12)}.json`), { pr: pr.number, head: gate.head, base: gate.base, retargeted, at: new Date().toISOString() });
  return { status: 'merged', head: gate.head, retargeted };
}

// Daily audit (P1-B): every PR merged into collab/integration in the last 24 hours must have had a
// signed APPROVE and a signed PASS for its final head before the merge. Anything else (a manual
// merge, a forged comment) is listed. Merges from before the key existed cannot have receipts.
export function auditMerges({ gh = makeGh(), nowMs = Date.now(), since = keyCreatedMs() } = {}) {
  if (since === null || since === undefined) return [];
  const from = Math.max(nowMs - 24 * 3600000, since);
  const day = new Date(from).toISOString().slice(0, 10);
  const merged = gh.json(['pr', 'list', '--repo', repo, '--base', integration, '--state', 'merged', '--limit', '100',
    '--search', `merged:>=${day}`, '--json', 'number,mergedAt,headRefOid,comments']);
  const found = [];
  for (const pr of merged ?? []) {
    const at = Date.parse(pr.mergedAt ?? '');
    if (!Number.isFinite(at) || at < from || at > nowMs) continue;
    const before = trustedComments(pr.comments).filter(c => Date.parse(c.createdAt ?? '') <= at);
    const verdict = before.filter(c => c.verdict).at(-1);
    const check = before.filter(c => c.check?.sha === pr.headRefOid).at(-1);
    const missing = [];
    if (!verdict || verdict.verdict.verdict !== 'APPROVE' || verdict.verdict.sha !== pr.headRefOid || !sealValid(verdict, pr.number)) missing.push('verdict');
    if (!check || check.check.status !== 'PASS' || !sealValid(check, pr.number)) missing.push('author check');
    if (missing.length) found.push({ pr: pr.number, head: pr.headRefOid, mergedAt: pr.mergedAt, missing });
  }
  return found;
}

// Once a day from the tick; findings go to the ops-alert issue. Returns the findings.
export function dailyReceiptAudit({ gh = makeGh(), alert, now, nowMs = Date.now(), since } = {}) {
  const path = join(stateDir, 'state', 'receipt-audit.json');
  if (readJson(path, {}).date === now.date) return [];
  const found = auditMerges({ gh, nowMs, ...(since === undefined ? {} : { since }) });
  if (found.length && alert) {
    alert(`Merge trong 24 giờ qua thiếu biên nhận cục bộ (verdict hoặc author check không do script ghi): ${found.map(f => `#${f.pr} @ ${String(f.head).slice(0, 7)} thiếu ${f.missing.join(' + ')}`).join('; ')}. Kiểm tra ai đã merge và comment nào đã cho qua.`);
  }
  writeJson(path, { date: now.date, at: new Date(nowMs).toISOString(), found: found.map(f => f.pr) });
  return found;
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const number = Number(args[args.indexOf('--pr') + 1]);
  if (!args.includes('--pr') || !Number.isInteger(number) || number <= 0) {
    process.stderr.write('Usage: node scripts/collab-merge.mjs --pr N [--dry-run]\n'); process.exit(2);
  }
  try {
    const result = runMerge(number, { dryRun: args.includes('--dry-run') });
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (!['merged', 'would-merge'].includes(result.status)) process.exitCode = 3;
  } catch (error) { process.stderr.write(`collab-merge failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
}
