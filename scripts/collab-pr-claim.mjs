// One session per PR (owner 16.11.2026, 5-fix package item 3a). Several Claude sessions (the
// hourly autopilot, the workflow lane, product lanes) could fix the same PR at once. The authoritative
// claim is a local file on the owner's machine, created atomically (O_EXCL), keyed by PR number and
// holding an opaque session id. A comment or label on the public PR is not a claim: it cannot be
// authenticated or taken atomically (Codex 16.11). Missing commits never prove a session is gone,
// so a claim is never taken over by age; it ends when its session releases it, when the PR is merged
// or closed, or by an explicit forced release that is logged with its reason.
// Usage:
//   node scripts/collab-pr-claim.mjs --claim N [--branch B]   (session id from LA_LANH_SESSION)
//   node scripts/collab-pr-claim.mjs --release N
//   node scripts/collab-pr-claim.mjs --force-release N --reason "<why>"
//   node scripts/collab-pr-claim.mjs --status [N]
import { appendFileSync, mkdirSync, readdirSync, readFileSync, unlinkSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { clean, stateDir } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const claimDir = () => join(stateDir, 'pr-claims');
const pathOf = n => join(claimDir(), `pr-${Number(n)}.json`);
const sessionPattern = /^[A-Za-z0-9._-]{4,64}$/;
export const sessionId = (env = process.env) => (sessionPattern.test(String(env.LA_LANH_SESSION ?? '')) ? env.LA_LANH_SESSION : null);

export function readClaim(n) {
  try { return JSON.parse(readFileSync(pathOf(n), 'utf8')); }
  catch (error) { return error?.code === 'ENOENT' ? null : { unreadable: true }; }
}

export function claimPr(n, { session, branch = null, now = new Date() } = {}) {
  if (!Number.isInteger(Number(n)) || Number(n) <= 0) return { ok: false, reason: 'pr-number' };
  if (!sessionPattern.test(String(session ?? ''))) return { ok: false, reason: 'session-id' };
  mkdirSync(claimDir(), { recursive: true });
  try {
    writeFileSync(pathOf(n), `${JSON.stringify({ pr: Number(n), session, branch, at: now.toISOString() })}\n`, { flag: 'wx', mode: 0o600 });
    return { ok: true, created: true };
  } catch (error) { if (error?.code !== 'EEXIST') throw error; }
  const held = readClaim(n);
  if (held?.session === session) return { ok: true, created: false };
  return { ok: false, reason: held?.unreadable ? 'claim-unreadable' : 'claimed', holder: held?.session ?? null, since: held?.at ?? null };
}

// Who may write to PR n (push, sync with integration, fix): nobody else while a session holds it.
// The machine (no session) never holds a claim, so it leaves a claimed PR to its session.
export function mayTouch(n, session = null) {
  const held = readClaim(n);
  if (!held) return { ok: true };
  if (held.unreadable) return { ok: false, reason: 'claim-unreadable' };
  return held.session === session ? { ok: true } : { ok: false, reason: 'claimed', holder: held.session };
}

const releaseLog = () => join(claimDir(), 'releases.jsonl');
export function releasePr(n, { session = null, force = null, now = new Date() } = {}) {
  const held = readClaim(n);
  if (!held) return { ok: true, released: false };
  const reason = clean(String(force ?? ''), 300).trim();
  if (held.session !== session && !reason) return { ok: false, reason: 'not-holder', holder: held.session ?? null };
  if (held.session !== session) appendFileSync(releaseLog(), `${JSON.stringify({ pr: Number(n), holder: held.session ?? null, by: session, reason, at: now.toISOString() })}\n`);
  unlinkSync(pathOf(n));
  return { ok: true, released: true };
}

export function claimsByPr() {
  let names = [];
  try { names = readdirSync(claimDir()).filter(f => /^pr-\d+\.json$/.test(f)); } catch { return {}; }
  return Object.fromEntries(names.map(f => { const n = Number(/\d+/.exec(f)[0]); return [n, readClaim(n)]; }));
}

// A merged or closed PR needs no claim: the tick drops claims of PRs that are no longer open. It is
// given the complete open list only; a failed or partial read prunes nothing.
export function pruneClaims(openNumbers, { now = new Date() } = {}) {
  const open = new Set(openNumbers.map(Number));
  const dropped = [];
  for (const [n, held] of Object.entries(claimsByPr())) {
    if (open.has(Number(n))) continue;
    unlinkSync(pathOf(n));
    appendFileSync(releaseLog(), `${JSON.stringify({ pr: Number(n), holder: held?.session ?? null, by: 'tick', reason: 'PR không còn mở', at: now.toISOString() })}\n`);
    dropped.push(Number(n));
  }
  return dropped;
}

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  const arg = name => (args.includes(name) ? args[args.indexOf(name) + 1] : null);
  const session = sessionId();
  let result;
  if (args.includes('--claim')) result = claimPr(Number(arg('--claim')), { session, branch: arg('--branch') });
  else if (args.includes('--release')) result = releasePr(Number(arg('--release')), { session });
  else if (args.includes('--force-release')) result = releasePr(Number(arg('--force-release')), { session, force: arg('--reason') || null });
  else if (args.includes('--status')) result = arg('--status') ? { claim: readClaim(Number(arg('--status'))) } : { claims: claimsByPr() };
  else { process.stderr.write('Usage: node scripts/collab-pr-claim.mjs --claim N [--branch B] | --release N | --force-release N --reason "<why>" | --status [N]\n'); process.exit(2); }
  process.stdout.write(`${JSON.stringify(result)}\n`);
  if (result.ok === false) process.exitCode = 3;
}
