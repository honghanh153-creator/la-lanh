import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { auditReserve, collectFacts, keepDayM4, saveFacts } from './collab-audit.mjs';
import { auditMarker, auditWindow, baselineMarker, baselinePath, buildPrompt, datesIn, evidenceDigest, gatherEvidence, readRecord, runAuditCodex, runBaseline, runNightAudit, upsertAudit, validateJudgement } from './collab-audit-night.mjs';
import { agentMarker, codexDailyCap, dayStatePath, readJson, writeJson } from './collab-trust.mjs';
import { renderCheck } from './collab-check.mjs';
import { tick } from './collab-turn.mjs';

const head = 'e'.repeat(40);
// A full approving review output (the receipt check validates it, Codex r1 on #486).
const output = JSON.stringify({ verdict: 'APPROVE', sha: head, complete: true, summary: 'ok', findings: [] });
const digest = createHash('sha256').update(output).digest('hex');
const outputs = [{ pr: 7, head12: head.slice(0, 12), digest, out: JSON.parse(output) }];
const approve = { authorAssociation: 'OWNER', createdAt: '2026-11-14T03:00:00Z',
  body: `Review verdict: APPROVE @ ${head}\nReviewer: Codex (auto)\n\nOutput SHA-256: \`${digest}\`\n${agentMarker} codex-auto-review sha=${head} p2=0 -->` };
const rebuttal = { authorAssociation: 'OWNER', createdAt: '2026-11-14T03:30:00Z', body: 'agent: Claude — không sửa P2 vì đã có test khác' };
const merged = (n, extra = {}) => ({ number: n, title: `fix: ${n}`, body: 'thân PR', headRefOid: head, createdAt: '2026-11-14T01:00:00Z', mergedAt: '2026-11-14T04:00:00Z',
  comments: [approve, rebuttal], files: [{ path: 'scripts/x.mjs' }], ...extra });
const report = (id, at, body) => ({ id, author_association: 'OWNER', created_at: at, body });

// A GitHub stand-in: the plan issue's comments, merged PRs, open PRs, ops alerts, and comment edits.
function fakeGh({ reports = [report(1, '2026-11-14T07:00:00Z', 'agent: Claude — báo cáo\nĐã merge #7.')], prs = [merged(7)], alerts = [], fail = {} } = {}) {
  const state = { comments: [...reports], calls: [], nextId: 900 };
  const gh = {
    state,
    openPrs: () => [],
    json: args => {
      state.calls.push(args.join(' '));
      if (args[0] === 'api') { if (fail.list) throw new Error('gh: HTTP 502'); return [state.comments]; }
      if (args[0] === 'pr') { if (fail.merged) throw new Error('gh: HTTP 502'); return structuredClone(prs); }
      if (args[0] === 'issue') return structuredClone(alerts);
      throw new Error(`unexpected ${args.join(' ')}`);
    },
    raw: (args, input) => {
      state.calls.push(args.slice(0, 3).join(' '));
      const body = JSON.parse(input).body;
      if (args[2] === 'PATCH') {
        if (fail.patch) { fail.patch -= 1; throw new Error('gh: HTTP 502'); }
        const id = Number(args[3].split('/').at(-1));
        const c = state.comments.find(x => x.id === id);
        if (!c) throw new Error('gh: HTTP 404');
        c.body = body;
        return '{}';
      }
      const c = report(state.nextId++, '2026-11-14T16:05:00Z', body);
      state.comments.push(c);
      if (fail.postLost) { fail.postLost = false; throw new Error('gh: timeout'); }
      return JSON.stringify(c);
    },
  };
  return gh;
}

const good = { complete: true, notes: '', M1: { measured: true, missing: '', items: [] }, M3: { measured: true, missing: '', items: [] }, unrecorded: { measured: true, missing: '', items: [] } };
const fakeCodex = (out = good, status = 'ok') => { const calls = []; const run = prompt => { calls.push(prompt); return status === 'ok' ? { status, out } : { status, error: 'x' }; }; run.calls = calls; return run; };
const at = iso => new Date(iso);
let n = 0;
const fresh = () => mkdtempSync(join(tmpdir(), `night-${n++}-`));
const deps = (extra = {}) => ({ outputs: () => outputs, issue: 133, lock: () => () => {}, disagreements: () => [], clock: () => at('2026-11-14T16:05:00Z'), ...extra });

test('the audit runs 23:00–23:29 for today and before 10:00 for yesterday, nowhere else', () => {
  assert.deepEqual(auditWindow(at('2026-11-14T16:00:00Z')), { date: '2026-11-14', final: false }, '23:00 VN');
  assert.equal(auditWindow(at('2026-11-14T15:59:00Z')), null, '22:59 VN');
  assert.equal(auditWindow(at('2026-11-14T16:30:00Z')), null, '23:30 VN');
  assert.deepEqual(auditWindow(at('2026-11-14T17:10:00Z')), { date: '2026-11-14', final: true }, '00:10 VN next day');
  assert.equal(auditWindow(at('2026-11-15T03:00:00Z')), null, '10:00 VN');
  assert.equal(runNightAudit({ gh: fakeGh(), now: at('2026-11-14T08:00:00Z'), dir: fresh(), ...deps() }).status, 'idle');
});

test('23:00 judges once, counts the run, posts one comment; later ticks do nothing', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: 5 });
  const gh = fakeGh();
  const dir = fresh();
  const codex = fakeCodex();
  const run = minute => runNightAudit({ gh, now: at(`2026-11-14T16:${minute}:00Z`), dir, codex, ...deps() });
  assert.equal(run('05').status, 'judged');
  assert.equal(codex.calls.length, 1);
  assert.match(codex.calls[0], /DỮ LIỆU/, 'GitHub text is framed as data, not instructions');
  assert.deepEqual([readJson(dayStatePath(date), {}).codexRuns, readJson(dayStatePath(date), {}).auditRuns], [6, 1]);
  const record = readRecord(date, dir);
  assert.equal(record.final, false);
  assert.equal(record.metrics.M1.value, 0);
  assert.equal(gh.state.comments.filter(c => c.body.includes(auditMarker(date))).length, 1);
  assert.match(gh.state.comments.at(-1).body, /tạm tính/);
  assert.equal(run('15').status, 'done');
  assert.equal(codex.calls.length, 1, 'no second Codex run in the window');
});

test('cap spent: M1 is "chưa đo được" and Codex is not called', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: codexDailyCap });
  const dir = fresh();
  const codex = fakeCodex();
  runNightAudit({ gh: fakeGh(), now: at('2026-11-14T16:05:00Z'), dir, codex, ...deps() });
  assert.equal(codex.calls.length, 0);
  assert.equal(readJson(dayStatePath(date), {}).codexRuns, codexDailyCap);
  const M1 = readRecord(date, dir).metrics.M1;
  assert.equal(M1.value, null);
  assert.match(M1.missing, /hết lượt Codex \(32\/32\)/);
  assert.equal(readRecord(date, dir).judgement.retry, true, 'a cap stop is retried, it does not lock the record');
});

test('busy review lock or a usage limit: nothing counted, retried on the next tick', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: 3 });
  const dir = fresh();
  const codex = fakeCodex();
  assert.equal(runNightAudit({ gh: fakeGh(), now: at('2026-11-14T16:05:00Z'), dir, codex, ...deps({ lock: () => null }) }).status, 'busy');
  assert.equal(codex.calls.length, 0);
  const limited = fakeCodex(null, 'limit');
  assert.equal(runNightAudit({ gh: fakeGh(), now: at('2026-11-14T16:10:00Z'), dir, codex: limited, ...deps() }).status, 'limit');
  assert.equal(readJson(dayStatePath(date), {}).codexRuns, 3);
  assert.equal(readRecord(date, dir), null);
  assert.equal(runNightAudit({ gh: fakeGh(), now: at('2026-11-14T16:20:00Z'), dir, codex, ...deps() }).status, 'judged');
});

test('a Codex error still counts one run and leaves M1 unmeasured', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: 0 });
  const dir = fresh();
  runNightAudit({ gh: fakeGh(), now: at('2026-11-14T16:05:00Z'), dir, codex: fakeCodex(null, 'error'), ...deps() });
  assert.equal(readJson(dayStatePath(date), {}).codexRuns, 1);
  assert.match(readRecord(date, dir).metrics.M1.missing, /Codex lỗi/);
});

test('after midnight: same evidence reuses the 23:00 judgement, new evidence is judged again', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: 4 });
  writeJson(dayStatePath('2026-11-15'), { codexRuns: 0 });
  const dir = fresh();
  const gh = fakeGh();
  const codex = fakeCodex();
  runNightAudit({ gh, now: at('2026-11-14T16:05:00Z'), dir, codex, ...deps() });
  const later = { clock: () => at('2026-11-14T17:10:00Z') };
  assert.equal(runNightAudit({ gh, now: at('2026-11-14T17:10:00Z'), dir, codex, ...deps(later) }).status, 'updated');
  assert.equal(codex.calls.length, 1, 'M9 rose by the audit\'s own run, the comment was edited: still the same evidence');
  const record = readRecord(date, dir);
  assert.equal(record.final, true);
  assert.equal(record.judgement.final, true);
  assert.match(gh.state.comments.find(c => c.body.includes(auditMarker(date))).body, /đã chốt/);
  assert.equal(runNightAudit({ gh, now: at('2026-11-14T17:20:00Z'), dir, codex, ...deps(later) }).status, 'done');

  const dir2 = fresh();
  const gh2 = fakeGh();
  runNightAudit({ gh: gh2, now: at('2026-11-14T16:05:00Z'), dir: dir2, codex, ...deps() });
  gh2.state.comments.push(report(2, '2026-11-14T16:35:00Z', 'agent: Claude — retro 14.11\nKhông có lỗi nào.'));
  assert.equal(runNightAudit({ gh: gh2, now: at('2026-11-14T17:10:00Z'), dir: dir2, codex, ...deps(later) }).status, 'judged');
  assert.equal(codex.calls.length, 3);
  assert.equal(readJson(dayStatePath('2026-11-15'), {}).codexRuns, 1, 'the final run counts on the day it ran');
  assert.equal(readJson(dayStatePath('2026-11-15'), {}).auditRuns, undefined, 'and is not part of that day\'s M9 adjustment');
});

test('evidence digest ignores collection time and the audit\'s own Codex run', () => {
  const date = '2026-11-14';
  const gh = fakeGh();
  const facts = now => collectFacts({ date, gh, now, outputs: () => outputs, day: () => null });
  const one = gatherEvidence({ date, gh, facts: { ...facts(at('2026-11-14T16:05:00Z')), metrics: { ...facts(at('2026-11-14T16:05:00Z')).metrics, M9: { value: 10 } } }, issue: 133, outputs, disagreements: () => [], day: { auditRuns: 0 } });
  // After midnight the night audit keeps the M4 taken during the day (keepDayM4), as runNightAudit does.
  const later = keepDayM4(facts(at('2026-11-14T17:10:00Z')), facts(at('2026-11-14T16:05:00Z')));
  const two = gatherEvidence({ date, gh, facts: { ...later, metrics: { ...later.metrics, M9: { value: 11 } } }, issue: 133, outputs, disagreements: () => [], day: { auditRuns: 1 } });
  assert.equal(evidenceDigest(one), evidenceDigest(two));
  gh.state.comments[0].body += '\nThêm một câu.';
  const three = gatherEvidence({ date, gh, facts: facts(at('2026-11-14T16:05:00Z')), issue: 133, outputs, disagreements: () => [], day: null });
  assert.notEqual(evidenceDigest(one), evidenceDigest(three));
});

test('an item naming a source outside the evidence pack voids its section', () => {
  const date = '2026-11-14';
  const gh = fakeGh({ alerts: [{ number: 12, title: 'tick lỗi', body: 'x', createdAt: '2026-11-14T05:00:00Z', comments: [] }],
    prs: [merged(7), merged(9, { title: 'fix: unrelated', comments: [] })] });
  const ev = gatherEvidence({ date, gh, facts: collectFacts({ date, gh, now: at('2026-11-14T16:05:00Z'), outputs: () => outputs, day: () => null }), issue: 133, outputs, disagreements: () => [], day: null });
  assert.deepEqual(ev.approved.map(p => p.key), ['pr#7'], 'only PRs with a real review receipt can be linked');
  const ok = validateJudgement({ ...good,
    M1: { measured: true, missing: '', items: [{ report: 'r1', claim: 'Đã merge #7.', source: 'pr#7', why: 'x' }, { report: 'r1', claim: 'đã merge #7.', source: 'pr#7', why: 'trùng' }] },
    M3: { measured: true, missing: '', items: [{ candidate: 'alert#12', pr: 'pr#7', why: 'y' }] },
    unrecorded: { measured: true, missing: '', items: [{ pr: 'pr#7', evidence: 'c2', claude: 'không sửa', codex: 'P2' }] } }, ev);
  assert.deepEqual([ok.M1.value, ok.M3.value, ok.unrecorded.value], [1, 1, 1], 'duplicates count once');
  const forged = validateJudgement({ ...good, M1: { measured: true, missing: '', items: [{ report: 'r9', claim: 'x', source: 'pr#7', why: 'x' }] } }, ev);
  assert.equal(forged.M1.value, null);
  assert.equal(validateJudgement({ ...good, M1: { measured: true, missing: '', items: [{ report: 'r1', claim: 'x', source: 'theo trí nhớ', why: 'x' }] } }, ev).M1.value, null, 'a source with no key');
  assert.equal(validateJudgement({ ...good, M3: { measured: true, missing: '', items: [{ candidate: 'alert#12', pr: 'pr#9', why: 'cùng file' }] } }, ev).M3.value, null, 'a PR without a receipt');
  assert.equal(validateJudgement({ ...good, unrecorded: { measured: true, missing: '', items: [{ pr: 'pr#9', evidence: 'c1', claude: 'a', codex: 'b' }] } }, ev).unrecorded.value, null, 'evidence of another PR');
  const partial = validateJudgement({ ...good, complete: false, notes: 'gói quá dài' }, ev);
  assert.deepEqual([partial.M1.value, partial.M3.value, partial.unrecorded.value], [null, null, null]);
  const noLog = gatherEvidence({ date, gh, facts: ev.facts ? collectFacts({ date, gh, now: at('2026-11-14T16:05:00Z'), outputs: () => outputs, day: () => null }) : null, issue: 133, outputs, disagreements: null, day: null });
  assert.equal(validateJudgement(good, noLog).unrecorded.value, null, 'no disagreement log: never 0');
});

test('reports that do not fit are listed as omitted and cannot be judged', () => {
  const date = '2026-11-14';
  const long = 'x'.repeat(5900);
  const reports = Array.from({ length: 8 }, (_, i) => report(i + 1, `2026-11-14T0${i}:00:00Z`, long));
  reports.push(report(50, '2026-11-14T09:00:00Z', `${agentMarker} status-board -->`));
  const gh = fakeGh({ reports });
  const ev = gatherEvidence({ date, gh, facts: collectFacts({ date, gh, now: at('2026-11-14T16:05:00Z'), outputs: () => outputs, day: () => null }), issue: 133, outputs, disagreements: () => [], day: null });
  assert.equal(ev.reports.length, 8, 'the status board is not a report');
  assert.equal(ev.reports.filter(r => r.omitted).length, 2);
  const out = validateJudgement({ ...good, M1: { measured: true, missing: '', items: [{ report: 'r8', claim: 'x', source: 'day', why: 'x' }] } }, ev);
  assert.equal(out.M1.value, null);
  assert.match(validateJudgement(good, ev).M1.missing, /2 báo cáo/);
  assert.ok(buildPrompt(ev).length < 120000);
});

test('posting edits the day\'s comment; a failed edit or a lost response never makes a second one', () => {
  const date = '2026-11-14';
  const body = v => `bản ${v}\n${auditMarker(date)}`;
  const gh = fakeGh({ reports: [] });
  const id = upsertAudit(gh, 133, date, body(1), null);
  assert.equal(upsertAudit(gh, 133, date, body(2), { issue: 133, commentId: id }), id);
  assert.equal(gh.state.comments.length, 1);
  assert.equal(upsertAudit(gh, 133, date, body(3), null), id, 'cache lost: found by marker');
  const flaky = fakeGh({ reports: [], fail: { patch: 1 } });
  const first = upsertAudit(flaky, 133, date, body(1), null);
  assert.throws(() => upsertAudit(flaky, 133, date, body(2), { issue: 133, commentId: first }), /502/);
  assert.equal(flaky.state.comments.length, 1, 'PATCH 502 does not POST');
  const lost = fakeGh({ reports: [], fail: { postLost: true } });
  assert.throws(() => upsertAudit(lost, 133, date, body(1), null), /timeout/);
  upsertAudit(lost, 133, date, body(2), null);
  assert.equal(lost.state.comments.length, 1, 'a POST whose response was lost is found again');
  const gone = fakeGh({ reports: [] });
  assert.equal(upsertAudit(gone, 133, date, body(1), { issue: 133, commentId: 4242 }), 900, 'a deleted comment is created again');
});

test('a judgement stored before a failed post is posted again without Codex', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: 0 });
  const gh = fakeGh({ fail: { list: false } });
  const dir = fresh();
  const codex = fakeCodex();
  const realRaw = gh.raw;
  gh.raw = () => { throw new Error('gh: HTTP 502'); };
  assert.equal(runNightAudit({ gh, now: at('2026-11-14T16:05:00Z'), dir, codex, ...deps() }).status, 'error');
  assert.ok(readRecord(date, dir).judgement, 'judgement saved before posting');
  gh.raw = realRaw;
  assert.equal(runNightAudit({ gh, now: at('2026-11-14T16:15:00Z'), dir, codex, ...deps() }).status, 'updated');
  assert.equal(codex.calls.length, 1);
  assert.equal(gh.state.comments.filter(c => c.body.includes(auditMarker(date))).length, 1);
});

test('re-running the facts by hand keeps Codex\'s judgement', () => {
  const date = '2026-11-14';
  writeJson(dayStatePath(date), { codexRuns: 0 });
  const dir = fresh();
  const gh = fakeGh();
  runNightAudit({ gh, now: at('2026-11-14T16:05:00Z'), dir, codex: fakeCodex(), ...deps() });
  saveFacts(collectFacts({ date, gh, now: at('2026-11-14T16:20:00Z'), outputs: () => outputs, day: () => null }), dir);
  const record = readRecord(date, dir);
  assert.ok(record.judgement);
  assert.equal(record.metrics.M1.value, 0);
});

test('the Codex runner reads its own schema output and reports limits', () => {
  const ok = runAuditCodex('p', { run: (bin, args) => { writeFileSync(args[args.indexOf('-o') + 1], JSON.stringify(good)); return ''; } });
  assert.deepEqual(ok, { status: 'ok', out: good });
  const args = [];
  runAuditCodex('p', { run: (bin, a) => { args.push(...a); writeFileSync(a[a.indexOf('-o') + 1], '{}'); } });
  assert.ok(args.includes('read-only') && args.includes('--ephemeral'));
  assert.match(args[args.indexOf('--output-schema') + 1], /collab-audit-schema\.json$/);
  assert.equal(runAuditCodex('p', { run: () => { throw Object.assign(new Error('exit 1'), { stderr: 'You hit your usage limit' }); } }).status, 'limit');
  assert.equal(runAuditCodex('p', { run: (bin, a) => { writeFileSync(a[a.indexOf('-o') + 1], 'not json'); } }).status, 'error');
});

// The tick: the audit never breaks it, and reviews leave one Codex run for the audit.
const A = 'a'.repeat(40);
const goodBody = [
  '- Mức: M — script vòng tự động',
  ...['G1 Tài liệu: plan §3', 'G2 UI/UX: không áp dụng, không đụng giao diện', 'G3 Câu chữ: không có câu mới', 'G4 BE: không áp dụng', 'G5 FE: không áp dụng',
    'G6 QC: node --test', 'G7 Bảo mật: không đụng phiên, quyền, dữ liệu cá nhân hay log', 'G8 Data privacy: không thu dữ liệu', 'G9 Release: không áp dụng cho PR vào integration', 'G10 Chi phí / license: không'].map(l => `- ${l}`),
  'Người dùng thấy gì: không trực tiếp (vận hành)',
].join('\n');
const tickPr = () => ({ number: 7, title: 'ops: x', author: { login: 'honghanh153-creator' }, isCrossRepository: false, state: 'OPEN', isDraft: false, baseRefName: 'collab/integration',
  headRefName: 'agent/claude/x', headRefOid: A, mergeable: 'MERGEABLE', labels: [], createdAt: '2026-11-13T00:00:00Z', body: goodBody, files: [{ path: 'scripts/x.mjs' }],
  comments: [{ authorAssociation: 'OWNER', createdAt: '2026-11-13T01:00:00Z', body: renderCheck({ head: A, status: 'PASS', exitCode: 0, seconds: 1, date: 'x' }) }] });
const plannedGh = date => ({
  pr: () => tickPr(), openPrs: () => [tickPr()], raw: () => '',
  json: args => (args[0] === 'issue' && args[1] === 'list' ? [{ number: 50, title: 'Kế hoạch chạy tự động hằng ngày' }]
    : { comments: [{ authorAssociation: 'OWNER', createdAt: `${date}T01:50:00Z`, body: `${agentMarker} daily-plan date=${date} -->` }] }),
});

test('tick: a failing audit is logged and the tick still runs', () => {
  const date = '2026-12-02';
  const logs = [];
  const result = tick({ gh: plannedGh(date), now: { date, hour: 23, minute: 5 }, merge: () => ({}), review: () => ({ status: 'posted' }), log: l => logs.push(l), audit: () => { throw new Error('boom'); } });
  assert.equal(result.status, 'ran');
  assert.ok(logs.some(l => /night audit failed: boom/.test(l)));
});

test('tick: reviews stop one run short of the cap, which is kept for the night audit', () => {
  const date = '2026-12-03';
  writeJson(dayStatePath(date), { codexRuns: codexDailyCap - auditReserve });
  const started = [];
  tick({ gh: plannedGh(date), now: { date, hour: 12, minute: 0 }, merge: () => ({}), review: number => { started.push(number); return { status: 'posted' }; } });
  assert.deepEqual(started, []);
  writeJson(dayStatePath(date), { codexRuns: codexDailyCap - auditReserve - 1 });
  tick({ gh: plannedGh(date), now: { date, hour: 12, minute: 10 }, merge: () => ({}), review: number => { started.push(number); return { status: 'posted' }; } });
  assert.deepEqual(started, [7]);
  assert.ok(readFileSync(new URL('./codex-review.mjs', import.meta.url), 'utf8').includes('codexDailyCap - auditReserve'), 'direct automatic reviews keep the reserve too');
});

// L23: the 11–13.11 baseline with the same collector.
const baseReports = () => ['11', '12', '13'].map((d, i) => report(i + 1, `2026-11-${d}T07:00:00Z`, `agent: Claude — báo cáo ${d}.11`));

test('baseline: each day goes through the night collector once, one summary comment, re-runs cost nothing', () => {
  writeJson(dayStatePath('2026-11-14'), { codexRuns: 6 });
  const dir = fresh();
  const gh = fakeGh({ reports: baseReports() });
  const codex = fakeCodex();
  const seen = [];
  const audit = opts => { seen.push(opts.window); return runNightAudit(opts); };
  const result = runBaseline({ from: '2026-11-11', to: '2026-11-13', gh, dir, audit, codex, ...deps() });
  assert.deepEqual(datesIn('2026-11-11', '2026-11-13'), ['2026-11-11', '2026-11-12', '2026-11-13']);
  assert.deepEqual(seen, ['11', '12', '13'].map(d => ({ date: `2026-11-${d}`, final: true })));
  assert.equal(result.status, 'ok');
  assert.equal(codex.calls.length, 3);
  const day14 = readJson(dayStatePath('2026-11-14'), {});
  assert.deepEqual([day14.codexRuns, day14.baselineRuns, day14.auditRuns], [9, 3, undefined], 'counted on the day it ran, labelled as baseline');
  const posts = () => gh.state.comments.filter(c => c.body.includes(baselineMarker('2026-11-11', '2026-11-13')));
  assert.equal(posts().length, 1);
  assert.equal(gh.state.comments.filter(c => c.body.includes('experiment-audit')).length, 0, 'no comment per day');
  assert.match(posts()[0].body, /\| M8 bất đồng \| chưa đo được \| chưa đo được \| chưa đo được \|/);
  runBaseline({ from: '2026-11-11', to: '2026-11-13', gh, dir, codex, ...deps() });
  assert.equal(codex.calls.length, 3, 'final days are not judged again');
  assert.equal(posts().length, 1);
  assert.equal(readJson(dayStatePath('2026-11-14'), {}).codexRuns, 9);
  assert.ok(readJson(baselinePath('2026-11-11', '2026-11-13', dir), null).days.every(d => d.final));
  const ev = gatherEvidence({ date: '2026-11-14', gh, facts: collectFacts({ date: '2026-11-14', gh, now: at('2026-11-14T16:05:00Z'), outputs: () => outputs, day: () => null }), issue: 133, outputs, disagreements: () => [], day: null });
  assert.ok(ev.reports.every(r => !String(r.body).includes('experiment-baseline')), 'the baseline comment is not an owner report for M1');
});

test('baseline keeps the night audit\'s reserved run; a cap stop keeps finished days and retries later', () => {
  writeJson(dayStatePath('2026-11-14'), { codexRuns: codexDailyCap - auditReserve - 1 });
  const dir = fresh();
  const gh = fakeGh({ reports: baseReports() });
  const codex = fakeCodex();
  runNightAudit({ gh, dir, window: { date: '2026-11-13', final: true }, post: false, codex, ...deps({ clock: () => at('2026-11-13T10:00:00Z') }) });
  const before13 = readRecord('2026-11-13', dir).judgement.judgedAt;
  runBaseline({ from: '2026-11-11', to: '2026-11-13', gh, dir, codex, ...deps() });
  assert.equal(codex.calls.length, 2, 'day 11 judged with the last free run; day 12 stopped by the reserve; day 13 already final');
  assert.equal(readJson(dayStatePath('2026-11-14'), {}).codexRuns, codexDailyCap - auditReserve);
  assert.equal(readRecord('2026-11-12', dir).judgement.retry, true);
  assert.equal(typeof readRecord('2026-11-12', dir).metrics.M2.value, 'number', 'machine facts are kept without Codex');
  assert.equal(readRecord('2026-11-13', dir).judgement.judgedAt, before13);
  assert.equal(runNightAudit({ gh, now: at('2026-11-14T16:10:00Z'), dir, codex, ...deps() }).status, 'judged', 'the night audit still has its run');
  writeJson(dayStatePath('2026-11-15'), { codexRuns: 0 });
  runBaseline({ from: '2026-11-11', to: '2026-11-13', gh, dir, codex, ...deps({ clock: () => at('2026-11-15T03:00:00Z') }) });
  assert.equal(readRecord('2026-11-12', dir).judgement.retry, undefined, 'the stopped day is judged on a later run');
  const limited = fakeCodex(null, 'limit');
  const dir2 = fresh();
  const r = runBaseline({ from: '2026-11-11', to: '2026-11-13', gh, dir: dir2, codex: limited, post: false, ...deps({ clock: () => at('2026-11-15T03:00:00Z') }) });
  assert.deepEqual(r.days.map(d => d.status), ['limit', 'limit', 'limit']);
  assert.equal(limited.calls.length, 1, 'a usage limit stops the run');
});

test('baseline days: M4 and M8 stay unmeasured even when the logs exist today', () => {
  const gh = fakeGh();
  const log = () => [{ date: '2026-11-12', pr: 7, winner: 'codex' }];
  const facts = collectFacts({ date: '2026-11-12', gh, now: at('2026-11-14T16:00:00Z'), outputs: () => outputs, day: () => null, disagreements: log, lessons: () => ({ done: 1, open: 2, overdue: 0 }) });
  assert.equal(facts.metrics.M8.value, null);
  assert.equal(facts.metrics.M4.value, null);
  const ev = gatherEvidence({ date: '2026-11-12', gh, facts, issue: 133, outputs, disagreements: log, day: null });
  assert.equal(validateJudgement(good, ev).unrecorded.value, null);
  assert.equal(collectFacts({ date: '2026-11-14', gh, now: at('2026-11-14T16:00:00Z'), outputs: () => outputs, day: () => null }).metrics.M8.value, null, 'no log module: never 0');
});
