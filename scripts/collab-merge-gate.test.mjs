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

// L13 closure (Codex auto-1 on #543): the production entry runMerge itself refuses every unsafe
// case the pre-#456 gate accepted, and issues no merge call for any of them.
test('L13: runMerge issues no merge for stale-base, base-drift, unsigned or replayed evidence; valid evidence merges', () => {
  const attempt = (state, changed = []) => {
    const calls = [];
    const gh = { pr: () => structuredClone(state), openPrs: () => [], compareFiles: () => changed, raw: args => { calls.push(args); return ''; }, comment: () => {} };
    const r = runMerge(N, { gh });
    return { status: r.status, merges: calls.filter(a => a[0] === 'pr' && a[1] === 'merge').length };
  };
  const refused = { status: 'refused', merges: 0 };
  // Stale base: PASS and APPROVE signed for B1 while integration is at B2.
  assert.deepEqual(attempt(pr({ baseTipOid: B2, comments: [sealedCheck(), sealedVerdict()] })), refused, 'stale base');
  // Base drift over the PR's own files: a fresh PASS on B2, but the APPROVE was for B1.
  assert.deepEqual(attempt(pr({ baseTipOid: B2, comments: [sealedCheck({ base: B2 }), sealedVerdict()] }), ['scripts/a.mjs']), refused, 'base drift');
  // Unsigned: an OWNER APPROVE or PASS whose receipt does not exist.
  assert.deepEqual(attempt(pr({ comments: [sealedCheck(), owner(verdictBody({ receipt: 'f'.repeat(32) }))] })), refused, 'unsigned APPROVE');
  assert.deepEqual(attempt(pr({ comments: [owner(checkBody({ receipt: 'e'.repeat(32) })), sealedVerdict()] })), refused, 'unsigned PASS');
  assert.deepEqual(attempt(pr({ comments: [sealedCheck(), owner(`Review verdict: APPROVE @ ${H}\nReviewer: Codex`)] })), refused, 'manual verdict');
  // Replay: copies of a signed PASS and APPROVE posted after a newer FAIL and REQUEST_CHANGES.
  const pass = sealedCheck();
  const approve = sealedVerdict();
  const copy = c => ({ ...c, url: freshUrl(), createdAt: stamp() });
  assert.deepEqual(attempt(pr({ comments: [pass, approve, sealedCheck({ status: 'FAIL' }), sealedVerdict({ verdict: 'REQUEST_CHANGES' }), copy(pass), copy(approve)] })), refused, 'replay');
  // The same gate merges valid evidence, so the refusals above are not a gate that refuses everything.
  assert.deepEqual(attempt(pr({ comments: [sealedCheck(), sealedVerdict()] })), { status: 'merged', merges: 1 });
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

// Incident 18.11.2026 (Codex run 23): every merge entry point respects the merge reservation. While
// integration is reserved for one PR, another PR with valid evidence gets no merge call; the
// reserved PR merges and its reservation ends.
test('reservation: runMerge refuses any other PR while integration is reserved, and the reserved PR releases it on merge', async () => {
  const reservation = await import('./collab-reservation.mjs');
  reservation._resetReservation();
  const calls = [];
  const state = pr({ baseTipOid: B2, comments: [sealedCheck({ base: B2 }), sealedVerdict()] });
  const gh = {
    pr: () => structuredClone(state),
    openPrs: () => [],
    compareFiles: () => ['docs/z.md'],
    raw: args => { calls.push(args); return ''; },
    comment: () => {},
  };
  const other = N + 1;
  assert.ok(reservation.reserve(other, 'c'.repeat(40)).reservation);
  const refused = runMerge(N, { gh });
  assert.equal(refused.status, 'refused');
  assert.match(refused.reasons.join(), new RegExp(`đang giữ cho #${other}`));
  assert.equal(calls.length, 0, 'no merge call while another PR holds integration');
  // The holder's reservation ends: now N may merge, and its own reservation is released after.
  assert.equal(reservation.releaseReservation(other, 'test'), true);
  assert.ok(reservation.reserve(N, H).reservation);
  assert.equal(runMerge(N, { gh }).status, 'merged');
  assert.equal(reservation.activeReservation(), null, 'the reserved PR merged: integration is free');
  // An expired reservation does not block anyone.
  reservation.reserve(other, 'd'.repeat(40), { nowMs: Date.now() - 2 * 3600000 });
  assert.equal(runMerge(N, { gh }).status, 'merged');
  reservation._resetReservation();
});

// ---- Merge reservation module (incident 18.11.2026; Codex run 23) ----
const r = await import('./collab-reservation.mjs');
const RH1 = '1'.repeat(40);
const RH2 = '2'.repeat(40);
const T0 = Date.parse('2026-11-18T05:00:00Z');
const min = m => T0 + m * 60000;

test('reservation rules: one holder, expiry, no renewal at the same head, head follow and release', () => {
  r._resetReservation();
  assert.equal(r.activeReservation(T0), null);
  assert.equal(r.reserve(684, RH1, { nowMs: T0 }).reservation.pr, 684);
  // Another PR cannot take it while it stands; the same PR keeps it.
  const other = r.reserve(411, RH2, { nowMs: min(5) });
  assert.equal(other.other, true);
  assert.equal(other.reservation.pr, 684);
  assert.equal(r.mergeAllowed(411, min(5)).ok, false);
  assert.match(r.mergeAllowed(411, min(5)).reason, /#684/);
  assert.equal(r.mergeAllowed(684, min(5)).ok, true);
  // The tick's own sync moves the holder to its new head.
  assert.equal(r.followHead(684, RH2, { nowMs: min(6) }).head, RH2);
  // Expiry frees integration; the same PR at the same head does not get a second window.
  assert.equal(r.activeReservation(min(r.reservationMinutes + 1)), null);
  assert.equal(r.mergeAllowed(411, min(r.reservationMinutes + 1)).ok, true);
  assert.match(r.reserve(684, RH2, { nowMs: min(r.reservationMinutes + 2) }).refused, /hết lượt/);
  // Another PR may reserve now; a new head of the stuck PR may reserve later.
  assert.equal(r.reserve(411, RH1, { nowMs: min(r.reservationMinutes + 3) }).reservation.pr, 411);
  assert.equal(r.releaseReservation(684, 'not the holder'), false);
  assert.equal(r.releaseReservation(411, 'merged'), true);
  assert.equal(r.reserve(684, '3'.repeat(40), { nowMs: min(r.reservationMinutes + 4) }).reservation.pr, 684);
  // Bad input never reserves.
  assert.ok(r.reserve(0, RH1).refused);
  assert.ok(r.reserve(5, 'nope').refused);
  r._resetReservation();
});

// The incident, replayed: a full-check PR needs 35 minutes of an unchanged integration tip (CI,
// check, review); fast PRs are ready to merge every 20 minutes. Without the reservation it never
// merges; with it, it merges in its first window and the fast PRs follow.
function replay({ reservations }) {
  r._resetReservation();
  let tip = 0;
  let synced = null;
  let mergedAt = null;
  const fast = [];
  for (let m = 0; m <= 240; m += 1) {
    const now = min(m);
    if (mergedAt === null) {
      // The tick: the full PR is the front; it reserves, then syncs when it is behind.
      if (reservations && !r.activeReservation(now)) r.reserve(684, `${String(tip).padStart(2, '0')}${'f'.repeat(38)}`, { nowMs: now });
      if (!synced || synced.tip !== tip) synced = { tip, at: m };
      if (synced.tip === tip && m - synced.at >= 35 && (!reservations || r.mergeAllowed(684, now).ok)) {
        mergedAt = m;
        tip += 1;
        if (reservations) r.releaseReservation(684, 'merged', { nowMs: now });
      }
    }
    if (m % 20 === 10 && (!reservations || r.mergeAllowed(900 + m, now).ok)) { fast.push(m); tip += 1; }
  }
  r._resetReservation();
  return { mergedAt, fast };
}

test('incident replay: with fast merges every 20 minutes the full-check PR merges only with the reservation', () => {
  const without = replay({ reservations: false });
  assert.equal(without.mergedAt, null, 'today: the full-check PR never gets 35 quiet minutes');
  const withIt = replay({ reservations: true });
  assert.ok(withIt.mergedAt !== null && withIt.mergedAt <= 40, `merged at ${withIt.mergedAt}`);
  assert.ok(withIt.fast.length >= 9, 'the fast PRs still merge after the window');
  assert.ok(withIt.fast.every(m => m > withIt.mergedAt), 'no fast merge inside the reserved window');
});

// Codex P2 on #736: a reservation is never made while a merge holds the merge lock, so a merge
// admitted before it cannot land inside the reserved window.
test('reservation changes wait for the merge lock', async () => {
  const lock = await import('./collab-lock.mjs');
  r._resetReservation();
  const release = lock.acquireLock(r.mergeLockPath(), { staleMs: 600000 });
  assert.ok(release, 'a merge holds the lock');
  assert.match(r.reserve(684, RH1, { nowMs: T0, lockWaitMs: 0 }).refused, /merge khác đang chạy/);
  assert.equal(r.activeReservation(T0), null);
  release();
  assert.equal(r.reserve(684, RH1, { nowMs: T0, lockWaitMs: 0 }).reservation.pr, 684);
  r._resetReservation();
});


// Fix-forward #737: an expired holder is not stuck forever. Its spent window is bound to the
// integration tip; after another PR merges (the tip moves), it needs a sync and may reserve again.
test('#737: an expired holder may reserve again at the same head once integration has moved', () => {
  r._resetReservation();
  const tip1 = 'a'.repeat(40);
  const tip2 = 'b'.repeat(40);
  assert.equal(r.reserve(61, RH1, { nowMs: T0, tip: tip1, lockWaitMs: 0 }).reservation.tip, tip1);
  const later = min(r.reservationMinutes + 1);
  assert.match(r.reserve(61, RH1, { nowMs: later, tip: tip1, lockWaitMs: 0 }).refused, /hết lượt/, 'same head, same tip: no second window');
  assert.match(r.reserve(61, RH1, { nowMs: later, lockWaitMs: 0 }).refused, /hết lượt/, 'unknown tip: still refused');
  assert.equal(r.reserve(61, RH1, { nowMs: later + 60000, tip: tip2, lockWaitMs: 0 }).reservation.pr, 61, 'integration moved: it may reserve again');
  r._resetReservation();
});

// L61 (21.11.2026): hotfix #863 waited silently in claude-fix because its body grouped several gates
// on one line, while collab/integration stayed red.
test('L61: a preflight failure on an incident PR raises an ops alert at once; other PRs stay quiet', async () => {
  const { incidentPreflightAlert } = await import('./collab-preflight.mjs');
  const { runTick } = await import('./collab-tick.mjs');
  const fail = { status: 'FAIL', reasons: ['PR body thiếu cổng G3, G4'] };
  const alerts = [];
  assert.equal(incidentPreflightAlert({ number: 863, labels: [{ name: 'incident' }] }, fail, t => alerts.push(t)), true);
  assert.match(alerts[0], /^PR sự cố #863 bị chặn ở kiểm đầu vào: PR body thiếu cổng G3, G4\./);
  assert.equal(incidentPreflightAlert({ number: 5, labels: [{ name: 'area:ops' }] }, fail, t => alerts.push(t)), false, 'not an incident');
  assert.equal(incidentPreflightAlert({ number: 863, labels: ['incident'] }, { status: 'PASS', reasons: [] }, t => alerts.push(t)), false, 'passed');
  assert.equal(alerts.length, 1);
  // The tick's preflight goes through it, and a failing alert never changes the preflight result.
  const seen = [];
  const gh = { raw: () => '', json: () => [], pr: n => ({ number: n, labels: [{ name: 'incident' }], body: 'trống', files: [] }) };
  const given = runTick(gh, () => [], { run: g => g, gapNote: () => null, areaNote: () => null, probe: () => [], receipt: () => {}, proofs: () => null,
    incidentAlert: (pr, result) => { seen.push([pr.number, result.status]); throw new Error('gh down'); } });
  assert.equal(given.prPreflight(863).status, 'FAIL');
  assert.deepEqual(seen, [[863, 'FAIL']]);
});
