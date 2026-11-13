// Merge one PR into collab/integration only when every condition in the auto-loop plan §4.2 holds.
// Usage: node scripts/collab-merge.mjs --pr N [--dry-run]
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { agentMarker, clean, fixForwardIssue, integration, isOwnPr, isSha, makeGh, repo, reviewState, stateDir, writeJson } from './collab-trust.mjs';

export function mergeGate(pr) {
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
  const { check, last } = reviewState(pr);
  if (!last || last.verdict.verdict !== 'APPROVE' || last.verdict.sha !== head) reasons.push('verdict mới nhất (sau lần đổi base gần nhất) không phải APPROVE @ head');
  // The newest author check for the head decides; an older PASS does not outvote a later FAIL.
  if (check?.status !== 'PASS') reasons.push('Author check mới nhất @ head không phải PASS');
  // Automatic approvals with non-blocking P2 must link their fix-forward issue.
  const p2 = Number(/codex-auto-review sha=[0-9a-f]{40} p2=(\d+)/.exec(last?.body ?? '')?.[1] ?? 0);
  if (last?.auto && p2 > 0 && !fixForwardIssue(last.body)) reasons.push('APPROVE có P2 nhưng thiếu issue fix-forward');
  return { ok: reasons.length === 0, head, reasons };
}

export function runMerge(number, { gh = makeGh(), dryRun = false } = {}) {
  const pr = gh.pr(number);
  const gate = mergeGate(pr);
  if (!gate.ok) return { status: 'refused', reasons: gate.reasons };
  if (dryRun) return { status: 'would-merge', head: gate.head };
  // --match-head-commit fails the merge if the head moved after the check above.
  gh.raw(['pr', 'merge', String(pr.number), '--repo', repo, '--merge', '--match-head-commit', gate.head]);
  const retargeted = [];
  for (const child of gh.openPrs().filter(p => p.baseRefName === pr.headRefName)) {
    gh.raw(['pr', 'edit', String(child.number), '--repo', repo, '--base', integration]);
    gh.comment('pr', child.number, `PR cha #${pr.number} đã merge vào \`${integration}\`; base của PR này được đổi sang \`${integration}\`. Head không đổi; verdict trước đây hết hiệu lực, PR cần review lại.\n\n${agentMarker} retarget parent=${pr.number} -->`);
    retargeted.push(child.number);
  }
  writeJson(join(stateDir, 'logs', `merge-pr${pr.number}-${gate.head.slice(0, 12)}.json`), { pr: pr.number, head: gate.head, retargeted, at: new Date().toISOString() });
  return { status: 'merged', head: gate.head, retargeted };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
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
