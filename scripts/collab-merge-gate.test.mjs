// Merge-queue rules for the auto-loop merge gate (Codex P1-A and P1-B, 12.11.2026).
// P1-A: author-check evidence is bound to the base it was tested on, and an APPROVE stops counting
//       when the base moved over the PR's files. P1-B: verdicts and check receipts count only with a
//       local HMAC receipt written by the scripted review/check path; a comment alone is refused.
// Synthetic SHAs and PR numbers only.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { readFileSync, statSync, writeFileSync, readdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';

const trust = await import('./collab-trust.mjs');
const { asPosted, freshUrl } = await import('./collab-test-post.mjs');
const { auditMerges, dailyReceiptAudit, mergeGate, runMerge } = await import('./collab-merge.mjs');
const { prTurn } = await import('./collab-turn.mjs');
const { ciCheck, renderCheck, runCheck, runCheckInClone } = await import('./collab-check.mjs');
const preflightMod = await import('./collab-preflight.mjs');

const H = 'a'.repeat(40);
const H2 = 'c'.repeat(40);
const B1 = '1'.repeat(40);
const B2 = '2'.repeat(40);
const N = 7;
const goodBody = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10'].map(g => `- ${g}: ${g === 'G7' ? 'không đụng phiên, quyền, dữ liệu, log' : 'ok'}`).join('\n') + '\nMức: S\nNgười dùng thấy gì: không trực tiếp (vận hành)\n';

let tick = 0;
const stamp = () => `2026-11-12T0${Math.floor(tick / 60)}:${String(tick++ % 60).padStart(2, '0')}:00Z`;
const owner = body => asPosted(trust, { authorAssociation: 'OWNER', createdAt: stamp(), body });
// What `gh pr comment` prints for a fake post: the new comment's URL.
const postUrl = () => freshUrl();
const checkBody = ({ head = H, base = B1, status = 'PASS', receipt }) => renderCheck({ head, base, receipt, status, exitCode: status === 'PASS' ? 0 : 1, seconds: 1, date: 'x' });
const verdictBody = ({ head = H, base = B1, verdict = 'APPROVE', p2 = 0, receipt, fix = null }) =>
  [`Review verdict: ${verdict} @ ${head}`, 'Reviewer: Codex (auto, scripts/codex-review.mjs)', '', 'ok', '', ...(fix ? [`Fix-forward: #${fix}`, ''] : []), trust.verdictSeal({ head, p2, base, receipt })].join('\n');
// What the scripted paths post: a comment plus a receipt in the local state dir.
const sealedCheck = (o = {}) => { const c = { head: H, base: B1, status: 'PASS', pr: N, ...o }; return owner(checkBody({ ...c, receipt: trust.signReceipt({ kind: 'check', pr: c.pr, head: c.head, base: c.base, result: c.status }) })); };
const sealedVerdict = (o = {}) => { const v = { head: H, base: B1, verdict: 'APPROVE', p2: 0, pr: N, ...o }; return owner(verdictBody({ ...v, receipt: trust.signReceipt({ kind: 'verdict', pr: v.pr, head: v.head, base: v.base, result: v.verdict, p2: v.p2 }) })); };
const pr = (extra = {}) => ({ number: N, title: 'ops(collab): x', author: { login: trust.ownerLogin }, isCrossRepository: false, state: 'OPEN', isDraft: false, baseRefName: trust.integration, headRefName: 'agent/claude/x', headRefOid: H, baseTipOid: B1, mergeable: 'MERGEABLE', labels: [], createdAt: '2026-11-12T00:00:00Z', files: [{ path: 'scripts/a.mjs' }], body: goodBody, comments: [], ...extra });
const noFiles = () => [];

test('P1-A: the evidence of base B1 does not merge onto B2 (no retarget marker needed)', () => {
  const p = pr({ comments: [sealedCheck(), sealedVerdict()] });
  assert.deepEqual(mergeGate(p, { baseFiles: noFiles }).reasons, [], 'B1 evidence merges onto B1');
  const moved = { ...p, baseTipOid: B2 };
  const gate = mergeGate(moved, { baseFiles: noFiles });
  assert.equal(gate.ok, false);
  assert.ok(gate.reasons.some(r => /Author check/.test(r) && /base/.test(r)), gate.reasons.join(' | '));
  assert.equal(prTurn(moved, { baseFiles: noFiles }).turn, 'claude-check', 'the tick sends it back for a check on the new base');
});

test('P1-A: a fresh PASS on B2 without file overlap keeps the APPROVE', () => {
  const p = pr({ baseTipOid: B2, comments: [sealedCheck(), sealedVerdict(), sealedCheck({ base: B2 })] });
  const asked = [];
  const baseFiles = (from, to) => { asked.push([from, to]); return ['docs/other.md', 'apps/web/x.ts']; };
  assert.deepEqual(mergeGate(p, { baseFiles }).reasons, []);
  assert.deepEqual(asked[0], [B1, B2], 'files changed on the base since the reviewed base');
  assert.equal(prTurn(p, { baseFiles }).turn, 'merge');
});

test('P1-A: base changes over the PR files need a new APPROVE', () => {
  const p = pr({ baseTipOid: B2, files: [{ path: 'scripts/a.mjs' }, { path: 'docs/b.md' }], comments: [sealedCheck(), sealedVerdict(), sealedCheck({ base: B2 })] });
  const baseFiles = () => ['scripts/a.mjs'];
  const gate = mergeGate(p, { baseFiles });
  assert.equal(gate.ok, false);
  assert.ok(gate.reasons.some(r => /review lại/.test(r) && /scripts\/a\.mjs/.test(r)), gate.reasons.join(' | '));
  assert.equal(prTurn(p, { baseFiles }).turn, 'codex-review');
  p.comments.push(sealedVerdict({ base: B2 }));
  assert.deepEqual(mergeGate(p, { baseFiles }).reasons, [], 'a new APPROVE on B2 merges');
  // Unknown base files (API error, more than 300 files, diverged base) count as overlap.
  const unknown = pr({ baseTipOid: B2, comments: [sealedCheck({ base: B2 }), sealedVerdict()] });
  assert.equal(mergeGate(unknown, { baseFiles: () => null }).ok, false);
  assert.equal(mergeGate(unknown).ok, false, 'no base-file lookup: re-review');
});

test('P1-A: a missing base anywhere in the tuple is refused', () => {
  const ok = pr({ comments: [sealedCheck(), sealedVerdict()] });
  assert.equal(mergeGate({ ...ok, baseTipOid: undefined }, { baseFiles: noFiles }).ok, false, 'current base unknown');
  assert.equal(mergeGate(pr({ comments: [sealedCheck({ base: 'none' }), sealedVerdict()] }), { baseFiles: noFiles }).ok, false, 'check without a tested base');
  const unknownReviewBase = pr({ baseTipOid: B2, comments: [sealedCheck({ base: B2 }), sealedVerdict({ base: 'none' })] });
  assert.equal(mergeGate(unknownReviewBase, { baseFiles: noFiles }).ok, false, 'reviewed base unknown: re-review');
  assert.equal(prTurn(unknownReviewBase, { baseFiles: noFiles }).turn, 'codex-review');
  // Old-format comments carry no base and no receipt at all.
  const old = pr({ comments: [owner(renderCheck({ head: H, status: 'PASS', exitCode: 0, seconds: 1, date: 'x' })), owner(`Review verdict: APPROVE @ ${H}\n${trust.agentMarker} codex-auto-review sha=${H} p2=0 -->`)] });
  assert.equal(mergeGate(old, { baseFiles: noFiles }).ok, false);
  assert.equal(prTurn(old).turn, 'claude-check');
});

test('P1-A: a FAIL on any base still blocks; the retarget marker no longer decides anything', () => {
  const failed = pr({ baseTipOid: B2, comments: [sealedCheck({ base: B2 }), sealedVerdict({ base: B2 }), sealedCheck({ base: B1, status: 'FAIL' })] });
  assert.equal(mergeGate(failed, { baseFiles: noFiles }).ok, false);
  assert.equal(prTurn(failed).turn, 'claude-fix');
  const marker = pr({ comments: [sealedCheck(), sealedVerdict(), owner(`Base changed.\n\n${trust.agentMarker} retarget parent=6 -->`)] });
  assert.deepEqual(mergeGate(marker, { baseFiles: noFiles }).reasons, [], 'same base, same evidence');
});

test('P1-B: a forged OWNER verdict or check without a receipt is refused, with no fallback', () => {
  const forgedVerdict = pr({ comments: [sealedCheck(), owner(verdictBody({ receipt: 'f'.repeat(32) }))] });
  assert.equal(mergeGate(forgedVerdict, { baseFiles: noFiles }).ok, false);
  assert.equal(prTurn(forgedVerdict).turn, 'codex-review', 'an unsigned APPROVE is not a verdict');
  const forgedCheck = pr({ comments: [owner(checkBody({ receipt: 'e'.repeat(32) })), sealedVerdict()] });
  assert.equal(mergeGate(forgedCheck, { baseFiles: noFiles }).ok, false);
  assert.equal(prTurn(forgedCheck).turn, 'claude-check');
  const plain = pr({ comments: [sealedCheck(), owner(`Review verdict: APPROVE @ ${H}\nReviewer: Codex`)] });
  assert.equal(mergeGate(plain, { baseFiles: noFiles }).ok, false, 'a manual verdict has no receipt');
});

test('P1-B: a receipt for another head, base, PR or verdict is refused', () => {
  const swap = (claims, signed) => owner(verdictBody({ ...claims, receipt: trust.signReceipt({ kind: 'verdict', pr: N, head: H, base: B1, result: 'APPROVE', p2: 0, ...signed }) }));
  for (const [claims, signed, what] of [
    [{}, { head: H2 }, 'head'],
    [{}, { base: B2 }, 'base'],
    [{}, { pr: N + 1 }, 'PR'],
    [{}, { result: 'REQUEST_CHANGES' }, 'verdict'],
    [{ p2: 0 }, { p2: 3 }, 'p2 count'],
  ]) assert.equal(mergeGate(pr({ comments: [sealedCheck(), swap(claims, signed)] }), { baseFiles: noFiles }).ok, false, what);
  const checkFor = signed => owner(checkBody({ receipt: trust.signReceipt({ kind: 'check', pr: N, head: H, base: B1, result: 'PASS', ...signed }) }));
  assert.equal(mergeGate(pr({ comments: [checkFor({ base: B2 }), sealedVerdict()] }), { baseFiles: noFiles }).ok, false, 'check base');
  assert.equal(mergeGate(pr({ comments: [checkFor({ result: 'FAIL' }), sealedVerdict()] }), { baseFiles: noFiles }).ok, false, 'check status');
  assert.equal(mergeGate(pr({ comments: [checkFor({ kind: 'verdict', result: 'APPROVE' }), sealedVerdict()] }), { baseFiles: noFiles }).ok, false, 'kind');
});

test('P1-B: a tampered receipt is refused; a valid one is allowed', () => {
  const check = sealedCheck();
  const verdict = sealedVerdict();
  const ok = pr({ comments: [check, verdict] });
  assert.deepEqual(mergeGate(ok, { baseFiles: noFiles }).reasons, []);
  const id = /receipt=([0-9a-f]{32})/.exec(verdict.body)[1];
  const file = join(trust.receiptDir(), readdirSync(trust.receiptDir()).find(f => f.endsWith(`-${id}.json`)));
  const original = readFileSync(file, 'utf8');
  const receipt = JSON.parse(original);
  writeFileSync(file, JSON.stringify({ ...receipt, mac: `${receipt.mac.slice(0, -1)}${receipt.mac.endsWith('0') ? '1' : '0'}` }));
  assert.equal(mergeGate(ok, { baseFiles: noFiles }).ok, false, 'MAC changed');
  writeFileSync(file, JSON.stringify({ ...receipt, head: H2 }));
  assert.equal(mergeGate(ok, { baseFiles: noFiles }).ok, false, 'fields changed');
  rmSync(file);
  assert.equal(mergeGate(ok, { baseFiles: noFiles }).ok, false, 'receipt gone');
  writeFileSync(file, original);
  assert.deepEqual(mergeGate(ok, { baseFiles: noFiles }).reasons, []);
});

test('replay (#456 auto-1): copies of a signed PASS and APPROVE posted after a newer FAIL and REQUEST_CHANGES never count', () => {
  const pass = sealedCheck();
  const approve = sealedVerdict();
  const fail = sealedCheck({ status: 'FAIL' });
  const changes = sealedVerdict({ verdict: 'REQUEST_CHANGES' });
  // Same public bodies, receipt ids included, but new comments: new ids, later times.
  const copy = c => ({ ...c, url: freshUrl(), createdAt: stamp() });
  const replayed = pr({ comments: [pass, approve, fail, changes, copy(pass), copy(approve)] });
  const gate = mergeGate(replayed, { baseFiles: noFiles });
  assert.equal(gate.ok, false, gate.reasons.join(' | '));
  assert.equal(prTurn(replayed, { baseFiles: noFiles }).turn, 'claude-fix');
  assert.equal(trust.sealValid(trust.trustedComments([copy(approve)])[0], N), false, 'a copied verdict has no valid receipt');
  assert.equal(trust.sealValid(trust.trustedComments([approve])[0], N), true, 'the original still verifies');
  // A newer comment edited to the original body keeps its own id: refused too.
  const edited = { ...fail, body: pass.body, createdAt: stamp() };
  assert.equal(mergeGate(pr({ comments: [approve, fail, edited] }), { baseFiles: noFiles }).ok, false);
  // A receipt binds once; rebinding it to another comment is refused.
  const id = /receipt=([0-9a-f]{32})/.exec(pass.body)[1];
  assert.equal(trust.bindReceipt({ kind: 'check', pr: N, id, url: freshUrl() }), false);
  assert.equal(trust.bindReceipt({ kind: 'check', pr: N, id: 'd'.repeat(32), url: freshUrl() }), false, 'no receipt, no binding');
  // No URL at all (an old fixture or an API without ids): refused.
  assert.equal(trust.sealValid({ ...trust.trustedComments([pass])[0], url: undefined }, N), false);
  // The daily audit sees the replayed merge as missing receipts.
  const nowMs = Date.parse('2026-11-12T12:00:00Z');
  const merged = { number: N, headRefOid: H, mergedAt: '2026-11-12T11:00:00Z', comments: replayed.comments };
  const found = auditMerges({ gh: { json: () => [merged] }, nowMs, since: 0 });
  assert.deepEqual(found.map(f => [f.pr, f.missing]), [[N, ['verdict', 'author check']]]);
  // Without the replay the same PR is clean: original PASS then APPROVE.
  assert.deepEqual(mergeGate(pr({ comments: [pass, approve] }), { baseFiles: noFiles }).reasons, []);
});

test('P1-B: the key lives outside any checkout with mode 600; no key means no valid receipt', () => {
  sealedCheck();
  assert.equal(trust.verdictKeyPath(), join(trust.stateDir, 'keys', 'verdict.key'));
  assert.equal(statSync(trust.verdictKeyPath()).mode & 0o777, 0o600);
  assert.equal(statSync(join(trust.stateDir, 'keys')).mode & 0o077, 0);
  assert.equal(trust.receiptDir(), join(trust.stateDir, 'state', 'receipts'));
  const ok = pr({ comments: [sealedCheck(), sealedVerdict()] });
  const key = readFileSync(trust.verdictKeyPath());
  rmSync(trust.verdictKeyPath());
  try { assert.equal(mergeGate(ok, { baseFiles: noFiles }).ok, false); }
  finally { writeFileSync(trust.verdictKeyPath(), key, { mode: 0o600 }); }
  assert.ok(mergeGate(ok, { baseFiles: noFiles }).ok);
});

test('P1-B: an unsigned REQUEST_CHANGES still blocks (stricter only), an unsigned APPROVE never passes', () => {
  const p = pr({ comments: [sealedCheck(), sealedVerdict(), owner(`Review verdict: REQUEST_CHANGES @ ${H}\nReviewer: Codex`)] });
  assert.equal(mergeGate(p, { baseFiles: noFiles }).ok, false);
  assert.equal(prTurn(p).turn, 'claude-fix');
});

test('P1-B: the P2 count that needs a fix-forward link comes from the signed marker', () => {
  assert.equal(mergeGate(pr({ comments: [sealedCheck(), sealedVerdict({ p2: 2 })] }), { baseFiles: noFiles }).ok, false);
  const linked = pr({ comments: [sealedCheck(), owner(verdictBody({ p2: 2, fix: 901, receipt: trust.signReceipt({ kind: 'verdict', pr: N, head: H, base: B1, result: 'APPROVE', p2: 2 }) }))] });
  assert.deepEqual(mergeGate(linked, { baseFiles: noFiles }).reasons, []);
});

test('runMerge reads the live integration tip and the base-file diff through gh', () => {
  const merged = [];
  const state = pr({ baseTipOid: B2, comments: [sealedCheck({ base: B2 }), sealedVerdict()] });
  const gh = {
    pr: () => structuredClone(state),
    openPrs: () => [],
    compareFiles: (from, to) => { merged.push(['compare', from, to]); return ['docs/z.md']; },
    raw: args => { merged.push(args); return ''; },
    comment: () => {},
  };
  assert.equal(runMerge(N, { gh }).status, 'merged');
  assert.deepEqual(merged[0], ['compare', B1, B2]);
});

test('makeGh attaches the live tip of collab/integration, not the stale baseRefOid', () => {
  const calls = [];
  const gh = trust.makeGh((cmd, args) => {
    calls.push(args);
    if (args[0] === 'api' && String(args[1]).includes('git/ref/heads/collab/integration')) return `${B2}\n`;
    if (args[0] === 'api' && String(args[1]).includes('/compare/')) return JSON.stringify({ status: 'ahead', n: 2, files: ['a.md', 'old.md'] });
    if (args[1] === 'view') return JSON.stringify({ number: N, baseRefName: trust.integration, baseRefOid: B1 });
    return JSON.stringify([{ number: 8, baseRefName: trust.integration, baseRefOid: B1 }, { number: 9, baseRefName: 'feat/x' }]);
  });
  assert.equal(gh.pr(N).baseTipOid, B2);
  const list = gh.openPrs();
  assert.equal(list[0].baseTipOid, B2);
  assert.equal(list[1].baseTipOid, null, 'a stacked PR has no integration tip');
  assert.deepEqual(gh.compareFiles(B1, B2), ['a.md', 'old.md']);
  const bad = trust.makeGh((cmd, args) => (String(args[1]).includes('/compare/') ? JSON.stringify({ status: 'diverged', n: 1, files: ['a'] }) : ''));
  assert.equal(bad.compareFiles(B1, B2), null, 'a diverged base is unknown');
  const many = trust.makeGh(() => JSON.stringify({ status: 'ahead', n: 300, files: [] }));
  assert.equal(many.compareFiles(B1, B2), null, '300 files may be truncated');
  assert.equal(trust.makeGh(() => { throw new Error('api down'); }).compareFiles(B1, B2), null);
});

test('author check records the base it tested; a branch behind integration is not checked', () => {
  const posted = [];
  const gh = { pr: () => pr(), comment: (kind, n, body) => { posted.push(body); return `${postUrl()}\n`; }, withDeadline: () => gh };
  const behind = args => {
    if (args[0] === 'rev-parse') return args[1] === 'HEAD' ? H : B2;
    if (args[0] === 'merge-base') throw new Error('not ancestor');
    return '';
  };
  const never = () => { throw new Error('pnpm must not run on a stale base'); };
  const stale = runCheck(N, { gh, git: behind, busy: () => null, spawn: never, terms: () => [] });
  assert.equal(stale.status, 'preflight');
  assert.match(stale.reasons[0], /collab\/integration/);
  assert.deepEqual(posted, []);
  const upToDate = args => (args[0] === 'rev-parse' ? (args[1] === 'HEAD' ? H : B1) : '');
  assert.equal(runCheck(N, { gh, git: upToDate, busy: () => null, spawn: () => ({ status: 0 }), terms: () => [] }).status, 'PASS');
  const check = trust.parseAuthorCheck(posted[0]);
  assert.deepEqual([check.status, check.sha, check.base], ['PASS', H, B1]);
  assert.ok(mergeGate(pr({ comments: [owner(posted[0]), sealedVerdict()] }), { baseFiles: noFiles }).ok, 'the posted receipt is signed');
  preflightMod.recordPreflight(N, H, { status: 'PASS' });
});

test('CI mode: the PASS counts only for the base the pr-check run actually merged', () => {
  const posted = [];
  const gh = { pr: () => pr({ baseTipOid: B2 }), comment: (kind, n, body) => { posted.push(body); return postUrl(); } };
  const run = (cmd, args) => (args[0] === 'rev-parse' ? H : '');
  const never = () => { throw new Error('nothing runs on the Mac in CI mode'); };
  const opts = ci => ({ gh, run, group: never, spawn: never, busy: never, terms: () => [], preflight: () => null, source: 'ci', ci });
  const old = runCheckInClone(N, opts(() => ({ state: 'PASS', conclusion: 'success', url: 'u', base: B1 })));
  assert.equal(old.status, 'ci-pending', 'CI tested B1, the tip is B2: wait, post nothing');
  const missing = runCheckInClone(N, opts(() => ({ state: 'PASS', conclusion: 'success', url: 'u', base: null })));
  assert.equal(missing.status, 'ci-pending', 'no tested base: no evidence');
  assert.deepEqual(posted, []);
  assert.equal(runCheckInClone(N, opts(() => ({ state: 'PASS', conclusion: 'success', url: 'u', base: B2 }))).status, 'PASS');
  assert.equal(trust.parseAuthorCheck(posted[0]).base, B2);
  assert.equal(runCheckInClone(N, opts(() => ({ state: 'FAIL', conclusion: 'failure', url: 'u', base: null }))).status, 'FAIL', 'a FAIL is posted even without a base');
  assert.equal(trust.parseAuthorCheck(posted[1]).status, 'FAIL');
});

test('ciCheck reads the tested base from the check job annotation', () => {
  const runs = [{ id: 1, path: '.github/workflows/pr-check.yml', head_sha: H, status: 'completed', created_at: '2026-11-12T01:00:00Z' }];
  const job = { name: 'check', run_id: 1, head_sha: H, status: 'completed', conclusion: 'success', check_run_url: 'https://api.github.com/repos/x/y/check-runs/55' };
  const at = notes => ({ json: args => {
    if (args[1].includes('/actions/workflows/')) return { workflow_runs: runs };
    if (args[1].includes('/jobs')) return { jobs: [job] };
    if (/check-runs\/55\/annotations/.test(args[1])) return notes;
    throw new Error(`unexpected ${args[1]}`);
  } });
  const note = (base, head = H) => ({ title: 'pr-check-tested-base', annotation_level: 'notice', message: `base=${base} head=${head}` });
  assert.equal(ciCheck(at([note(B2)]), H).base, B2);
  assert.equal(ciCheck(at([]), H).base, null);
  assert.equal(ciCheck(at([note(B2, H2)]), H).base, null, 'another head');
  assert.equal(ciCheck(at([note(B1), note(B2)]), H).base, null, 'two different bases: unknown');
  assert.equal(ciCheck(at([{ ...note(B2), title: 'other' }]), H).base, null);
  const down = at([]);
  const json = down.json;
  down.json = args => { if (args[1].includes('annotations')) throw new Error('down'); return json(args); };
  assert.deepEqual([ciCheck(down, H).state, ciCheck(down, H).base], ['PASS', null], 'an API error leaves the base unknown');
});

test('audit: a merge in the last 24h whose verdict or check lacks a receipt is listed and alerted once a day', () => {
  const nowMs = Date.parse('2026-11-12T12:00:00Z');
  const good = { number: 21, headRefOid: H, mergedAt: '2026-11-12T10:00:00Z', comments: [sealedCheck({ pr: 21 }), sealedVerdict({ pr: 21 })] };
  const forged = { number: 22, headRefOid: H, mergedAt: '2026-11-12T11:00:00Z', comments: [sealedCheck({ pr: 22 }), owner(verdictBody({ receipt: '9'.repeat(32) }))] };
  const old = { number: 23, headRefOid: H, mergedAt: '2026-11-10T11:00:00Z', comments: [] };
  const afterMerge = { number: 24, headRefOid: H, mergedAt: '2026-11-12T09:00:00Z', comments: [sealedCheck({ pr: 24 }), { ...sealedVerdict({ pr: 24 }), createdAt: '2026-11-12T09:30:00Z' }] };
  const asked = [];
  const gh = { json: args => { asked.push(args); return [good, forged, old, afterMerge]; } };
  const found = auditMerges({ gh, nowMs, since: 0 });
  assert.deepEqual(found.map(f => f.pr), [22, 24]);
  assert.ok(asked[0].includes('merged') && asked[0].includes(trust.integration));
  assert.deepEqual(auditMerges({ gh, nowMs, since: Date.parse('2026-11-12T11:30:00Z') }), [], 'merges before the key existed are not audited');
  const alerts = [];
  const day = { date: '2026-11-12', hour: 9, minute: 0 };
  assert.equal(dailyReceiptAudit({ gh, alert: text => alerts.push(text), now: day, nowMs, since: 0 }).length, 2);
  assert.equal(alerts.length, 1);
  assert.match(alerts[0], /#22/);
  dailyReceiptAudit({ gh, alert: text => alerts.push(text), now: day, nowMs, since: 0 });
  assert.equal(alerts.length, 1, 'once a day');
});
