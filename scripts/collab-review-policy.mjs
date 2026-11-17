// The owner's review policy, shared by the review script that posts verdicts (codex-review.mjs)
// and the night audit that checks them (collab-audit.mjs): a receipt counts only if the Codex output
// it points to would itself give APPROVE under this policy (Codex r1 on #486).
import { blockingP2, clean } from './collab-trust.mjs';

const severities = ['P0', 'P1', 'P2', 'P3'];
const categories = ['privacy', 'security', 'user_copy', 'correctness', 'test', 'docs', 'other'];

// Owner 15–16.11.2026: only four kinds wait on the owner. Codex names them in owner_actions.
export const ownerKinds = ['cost_access', 'release', 'sensitive_copy', 'data_collection'];
const holds = ['merge', 'release'];

export const isBlocking = f => f.severity === 'P0' || f.severity === 'P1' || (f.severity === 'P2' && blockingP2.has(f.category));

// requireOwnerActions: the live review path (its schema makes the field required). The night audit
// re-checks outputs written before the field existed, so there a missing field means none.
export function validateOutput(out, head, { requireOwnerActions = false } = {}) {
  const bad = message => { throw new Error(`Codex output rejected: ${message}`); };
  if (!out || typeof out !== 'object') bad('not an object');
  if (!['APPROVE', 'REQUEST_CHANGES'].includes(out.verdict)) bad('verdict');
  if (out.sha !== head) bad(`sha ${clean(out.sha, 60)} is not head ${head}`);
  if (typeof out.complete !== 'boolean' || typeof out.summary !== 'string' || !Array.isArray(out.findings)) bad('shape');
  for (const f of out.findings) {
    if (!severities.includes(f?.severity) || !categories.includes(f?.category) || typeof f.file !== 'string' || typeof f.title !== 'string') bad('finding shape');
  }
  if (out.owner_actions === undefined && requireOwnerActions) bad('owner_actions missing');
  if (out.owner_actions !== undefined) {
    if (!Array.isArray(out.owner_actions)) bad('owner_actions shape');
    for (const a of out.owner_actions) {
      if (!ownerKinds.includes(a?.kind) || !holds.includes(a?.blocks) || typeof a.evidence !== 'string' || !a.evidence.trim()) bad('owner action shape');
    }
  }
  return out;
}

// What each owner action holds. The script may only make it stricter: only privacy/consent/crisis/
// safety copy may wait for release (it ships behind the pending flag); every other kind, or copy Codex
// says is served at once, holds the merge.
export function ownerHolds(out) {
  const actions = (out.owner_actions ?? []).map(a => ({ kind: a.kind, evidence: clean(a.evidence, 600), hold: a.kind === 'sensitive_copy' && a.blocks === 'release' ? 'release' : 'merge' }));
  return { actions, merge: actions.filter(a => a.hold === 'merge'), release: actions.filter(a => a.hold === 'release') };
}

// The script may only make a verdict stricter, never more lenient.
export function applyPolicy(out) {
  const blocking = out.findings.filter(isBlocking);
  const verdict = out.verdict === 'REQUEST_CHANGES' || blocking.length || !out.complete ? 'REQUEST_CHANGES' : 'APPROVE';
  const fixForward = verdict === 'APPROVE' ? out.findings.filter(f => f.severity === 'P2') : [];
  return { verdict, blocking, fixForward, escalated: verdict !== out.verdict };
}
