// The owner's review policy, shared by the review script that posts verdicts (codex-review.mjs)
// and the night audit that checks them (collab-audit.mjs): a receipt counts only if the Codex output
// it points to would itself give APPROVE under this policy (Codex r1 on #486).
import { blockingP2, clean } from './collab-trust.mjs';

const severities = ['P0', 'P1', 'P2', 'P3'];
const categories = ['privacy', 'security', 'user_copy', 'correctness', 'test', 'docs', 'other'];

export const isBlocking = f => f.severity === 'P0' || f.severity === 'P1' || (f.severity === 'P2' && blockingP2.has(f.category));

export function validateOutput(out, head) {
  const bad = message => { throw new Error(`Codex output rejected: ${message}`); };
  if (!out || typeof out !== 'object') bad('not an object');
  if (!['APPROVE', 'REQUEST_CHANGES'].includes(out.verdict)) bad('verdict');
  if (out.sha !== head) bad(`sha ${clean(out.sha, 60)} is not head ${head}`);
  if (typeof out.complete !== 'boolean' || typeof out.summary !== 'string' || !Array.isArray(out.findings)) bad('shape');
  for (const f of out.findings) {
    if (!severities.includes(f?.severity) || !categories.includes(f?.category) || typeof f.file !== 'string' || typeof f.title !== 'string') bad('finding shape');
  }
  return out;
}

// The script may only make a verdict stricter, never more lenient.
export function applyPolicy(out) {
  const blocking = out.findings.filter(isBlocking);
  const verdict = out.verdict === 'REQUEST_CHANGES' || blocking.length || !out.complete ? 'REQUEST_CHANGES' : 'APPROVE';
  const fixForward = verdict === 'APPROVE' ? out.findings.filter(f => f.severity === 'P2') : [];
  return { verdict, blocking, fixForward, escalated: verdict !== out.verdict };
}
