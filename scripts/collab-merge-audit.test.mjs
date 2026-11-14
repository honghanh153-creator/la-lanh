import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { auditMarker, auditMerges, runMergeAudit, settleMs } from './collab-merge-audit.mjs';
import { tick } from './collab-turn.mjs';
import { planTitle } from './collab-plan.mjs';

// Synthetic PRs only. Each PR has its own head and, when "good", a real-looking automatic APPROVE
// whose digest matches a local Codex output that gives APPROVE for that head.
const headOf = n => `${String(n).padStart(6, '0')}${'b'.repeat(34)}`;
const outputOf = (n, sha = headOf(n)) => JSON.stringify({ verdict: 'APPROVE', sha, complete: true, summary: 'ok', findings: [] });
const digestOf = text => createHash('sha256').update(text).digest('hex');
const owner = (body, at) => ({ authorAssociation: 'OWNER', createdAt: at, body });
const approve = (sha, digest, at) => owner(`Review verdict: APPROVE @ ${sha}\nReviewer: Codex (auto, scripts/codex-review.mjs)\n\nok\n\nOutput SHA-256: \`${digest}\`\n<!-- la-lanh-agent codex-auto-review sha=${sha} p2=0 -->`, at);
const base = Date.parse('2026-11-16T03:00:00Z');
const iso = ms => new Date(ms).toISOString().replace('.000Z', 'Z');
const at = minutes => iso(base + minutes * 60000);

function world() {
  const prs = [];
  const comments = {};
  const outputs = [];
  const add = (n, { mergedMin = n, kind = 'good' } = {}) => {
    const mergedAt = at(mergedMin);
    const before = iso(Date.parse(mergedAt) - 60000);
    prs.push({ number: n, mergedAt, headRefOid: headOf(n), createdAt: iso(Date.parse(mergedAt) - 3600000) });
    const out = outputOf(n);
    if (kind === 'good' || kind === 'fake') outputs.push({ pr: n, head12: headOf(n).slice(0, 12), digest: digestOf(out), out: JSON.parse(out) });
    comments[n] = kind === 'none' ? []
      : kind === 'wrong-head' ? [approve(headOf(n + 1000), digestOf(outputOf(n, headOf(n + 1000))), before)]
        : kind === 'fake' ? [approve(headOf(n), '0'.repeat(64), before)]
          : [approve(headOf(n), digestOf(out), before)];
  };
  return { prs, comments, outputs, add };
}

// A fake gh that answers the three GraphQL connections 100 nodes a page, plus opsAlert's calls.
function fakeGh(w, { failOn = () => false, onCall = () => {} } = {}) {
  const issues = [];
  const calls = [];
  const vars = args => Object.fromEntries(args.flatMap((a, i) => (args[i - 1] === '-f' || args[i - 1] === '-F' ? [a.split(/=(.*)/s).slice(0, 2)] : [])));
  const page = (list, after) => {
    const from = after ? Number(after) : 0;
    const next = from + 100;
    return { pageInfo: { hasNextPage: next < list.length, endCursor: String(next) }, nodes: list.slice(from, next) };
  };
  return {
    issues, calls,
    json: args => {
      calls.push(args);
      onCall(args);
      if (failOn(args)) throw new Error('gh: connect ETIMEDOUT api.github.com');
      if (args[0] === 'api' && args[1] === 'graphql') {
        const v = vars(args);
        if (v.query.includes('pullRequests(')) return { data: { repository: { pullRequests: page(w.prs, v.after) } } };
        if (v.query.includes('pullRequest(number')) return { data: { repository: { pullRequest: { comments: page(w.comments[Number(v.number)] ?? [], v.after) } } } };
        if (v.query.includes('issues(')) return { data: { repository: { issues: page(issues, v.after) } } };
      }
      if (args[0] === 'issue' && args[1] === 'list') return [];
      throw new Error(`unexpected ${args.join(' ')}`);
    },
    raw: (args, input) => {
      calls.push(args);
      if (failOn(args)) throw new Error('gh: connect ETIMEDOUT api.github.com');
      if (args[0] === 'issue' && args[1] === 'create') {
        issues.push({ number: 900 + issues.length, body: input, title: args[args.indexOf('--title') + 1] });
        if (onCall(args) === 'crash') throw new Error('gh: stream error after the issue was created');
        return `https://github.com/x/y/issues/${900 + issues.length - 1}\n`;
      }
      return '';
    },
  };
}

const home = () => { const dir = mkdtempSync(join(tmpdir(), 'merge-audit-')); return { statePath: join(dir, 'merge-audit.json'), logPath: join(dir, 'merge-audit.jsonl') }; };
const after = minutes => new Date(base + minutes * 60000 + settleMs + 1000);
const created = gh => gh.calls.filter(a => a[0] === 'issue' && a[1] === 'create');
const logLines = path => (existsSync(path) ? readFileSync(path, 'utf8').trim().split('\n').filter(Boolean).map(l => JSON.parse(l)) : []);
const state = path => JSON.parse(readFileSync(path, 'utf8'));

test('a merge into integration without an automatic APPROVE receipt at the merged head raises one ops-alert', () => {
  const w = world();
  w.add(1); w.add(2, { kind: 'wrong-head' }); w.add(3, { kind: 'none' }); w.add(4, { kind: 'fake' });
  const gh = fakeGh(w);
  const paths = home();
  const result = auditMerges({ gh, now: after(10), outputs: () => w.outputs, ...paths });
  assert.equal(result.status, 'ok');
  assert.equal(result.processed, 4);
  assert.deepEqual(result.missing.map(m => m.pr), [2, 3, 4]);
  assert.match(result.missing[0].why, /APPROVE không phải của head đã merge/, 'wrong head');
  assert.match(result.missing[1].why, /không có verdict/, 'no verdict at all');
  assert.match(result.missing[2].why, /không có file output Codex khớp/, 'an APPROVE comment with no matching Codex output');
  assert.equal(created(gh).length, 3, 'one alert per PR, none for the good merge');
  for (const n of [2, 3, 4]) {
    const issue = gh.issues.find(i => i.body.includes(auditMarker(n)));
    assert.ok(issue, `#${n} has its marker`);
    assert.match(issue.title, new RegExp(`merge #${n} `));
    assert.match(issue.body, /không chứng minh Codex đã review độc lập/, 'the alert states the limit');
  }
  assert.ok(created(gh).every(a => a.includes('ops-alert')), 'raised as ops-alert issues');
  assert.deepEqual(logLines(paths.logPath).map(l => [l.pr, l.head]), [[2, headOf(2)], [3, headOf(3)], [4, headOf(4)]]);
  assert.deepEqual(state(paths.statePath).cursor, { mergedAt: at(4), number: 4 });
});

test('a good merge raises no alert and writes no audit line', () => {
  const w = world();
  w.add(1); w.add(2);
  const gh = fakeGh(w);
  const paths = home();
  const result = auditMerges({ gh, now: after(10), outputs: () => w.outputs, ...paths });
  assert.deepEqual([result.status, result.processed, result.missing], ['ok', 2, []]);
  assert.equal(created(gh).length, 0);
  assert.equal(existsSync(paths.logPath), false);
  assert.ok(!gh.calls.some(a => a.some(x => String(x).includes('issues('))), 'ops-alert issues are not read without a gap');
});

test('a verdict on the second comment page is seen', () => {
  const w = world();
  w.add(5);
  const real = w.comments[5][0];
  const chatter = Array.from({ length: 130 }, (_, i) => owner(`ghi chú ${i}`, iso(base - 7200000 + i * 1000)));
  w.comments[5] = [...chatter.slice(0, 110), real, ...chatter.slice(110)];
  const gh = fakeGh(w);
  const result = auditMerges({ gh, now: after(10), outputs: () => w.outputs, ...home() });
  assert.deepEqual(result.missing, [], 'the APPROVE at position 111 counts');
  assert.equal(gh.calls.filter(a => a.some(x => String(x).includes('pullRequest(number'))).length, 2, 'two comment pages read');
});

test('re-running does not alert again, and the hourly entry skips inside the hour', () => {
  const w = world();
  w.add(1, { kind: 'none' });
  const gh = fakeGh(w);
  const paths = home();
  const first = runMergeAudit({ gh, now: after(10), outputs: () => w.outputs, ...paths });
  assert.equal(first.missing.length, 1);
  assert.equal(runMergeAudit({ gh, now: after(40), outputs: () => w.outputs, ...paths }).status, 'skipped');
  const again = runMergeAudit({ gh, now: after(75), outputs: () => w.outputs, ...paths });
  assert.deepEqual([again.status, again.processed], ['ok', 0], 'the cursor is past #1');
  // Even with the cursor lost, the marker on GitHub and the de-duplicated log hold.
  const lost = auditMerges({ gh, now: after(80), outputs: () => w.outputs, ...paths, statePath: join(mkdtempSync(join(tmpdir(), 'merge-audit-lost-')), 's.json') });
  assert.deepEqual(lost.missing.map(m => m.alerted), [false]);
  assert.equal(created(gh).length, 1);
  assert.equal(logLines(paths.logPath).length, 1);
});

test('a crash after the issue was created but before the state was saved does not alert again', () => {
  const w = world();
  w.add(1, { kind: 'none' }); w.add(2);
  let crash = true;
  const gh = fakeGh(w, { onCall: args => (args[1] === 'create' && crash ? 'crash' : undefined) });
  const paths = home();
  const first = auditMerges({ gh, now: after(10), outputs: () => w.outputs, ...paths });
  assert.equal(first.status, 'error');
  assert.equal(gh.issues.length, 1, 'GitHub created the issue');
  assert.deepEqual(state(paths.statePath).cursor ?? null, null, 'the cursor did not move past #1');
  crash = false;
  const second = auditMerges({ gh, now: after(70), outputs: () => w.outputs, ...paths });
  assert.deepEqual([second.status, second.processed], ['ok', 2]);
  assert.deepEqual(second.missing, [{ pr: 1, why: 'không có verdict', alerted: false }], 'the marker is found on GitHub');
  assert.equal(created(gh).length, 1, 'still exactly one issue');
});

test('a network error mid-way keeps the cursor and is not read as a missing receipt', () => {
  const w = world();
  for (const n of [1, 2, 3, 4, 5]) w.add(n);
  let down = true;
  const gh = fakeGh(w, { failOn: args => down && args.some(x => x === 'number=3') });
  const paths = home();
  const first = auditMerges({ gh, now: after(10), outputs: () => w.outputs, ...paths });
  assert.equal(first.status, 'error');
  assert.match(first.error, /ETIMEDOUT/);
  assert.deepEqual(first.missing, []);
  assert.equal(created(gh).length, 0, 'no alert for an unread PR');
  assert.deepEqual(state(paths.statePath).cursor, { mergedAt: at(2), number: 2 });
  down = false;
  const second = auditMerges({ gh, now: after(70), outputs: () => w.outputs, ...paths });
  assert.deepEqual([second.status, second.processed, second.missing], ['ok', 3, []], 'resumes at #3');
  // An unreadable output folder stops the pass the same way.
  w.add(6, { mergedMin: 30 });
  const broken = auditMerges({ gh, now: after(80), outputs: () => { throw new Error('EACCES logs'); }, ...paths });
  assert.equal(broken.status, 'error');
  assert.deepEqual(state(paths.statePath).cursor, { mergedAt: at(5), number: 5 });
});

test('more than 100 merged PRs paginate fully', () => {
  const w = world();
  for (let n = 1; n <= 230; n += 1) w.add(n, { kind: n === 205 ? 'none' : 'good' });
  const gh = fakeGh(w);
  const paths = home();
  const result = auditMerges({ gh, now: after(300), outputs: () => w.outputs, ...paths });
  assert.deepEqual([result.status, result.processed], ['ok', 230]);
  assert.deepEqual(result.missing.map(m => m.pr), [205], 'a gap on the third page is found');
  assert.equal(gh.calls.filter(a => a.some(x => String(x).includes('pullRequests('))).length, 3);
  assert.deepEqual(state(paths.statePath).cursor, { mergedAt: at(230), number: 230 });
});

test('several PRs with the same mergedAt are all processed, in number order', () => {
  const w = world();
  w.add(9, { mergedMin: 5, kind: 'none' }); w.add(3, { mergedMin: 5 }); w.add(5, { mergedMin: 5, kind: 'none' }); w.add(1, { mergedMin: 2 });
  let down = true;
  const gh = fakeGh(w, { failOn: args => down && args.some(x => x === 'number=9') });
  const paths = home();
  const first = auditMerges({ gh, now: after(10), outputs: () => w.outputs, ...paths });
  assert.deepEqual([first.status, first.processed], ['error', 3]);
  assert.deepEqual(state(paths.statePath).cursor, { mergedAt: at(5), number: 5 });
  down = false;
  const second = auditMerges({ gh, now: after(70), outputs: () => w.outputs, ...paths });
  assert.deepEqual([second.processed, second.missing.map(m => m.pr)], [1, [9]], '#9 shares #5\'s mergedAt and is not skipped');
  assert.equal(created(gh).length, 2);
});

test('a merge landing during the scan is left for the next pass', () => {
  const w = world();
  for (let n = 1; n <= 120; n += 1) w.add(n, { mergedMin: 1 });
  const now = after(10);
  let landed = false;
  const gh = fakeGh(w, { onCall: args => {
    if (!landed && args.some(x => x === 'after=100')) {
      landed = true;
      w.add(121, { mergedMin: 0, kind: 'none' });
      w.prs.at(-1).mergedAt = iso(now.getTime() + 5000);
    }
  } });
  const paths = home();
  const first = auditMerges({ gh, now, outputs: () => w.outputs, ...paths });
  assert.deepEqual([first.status, first.processed, first.missing], ['ok', 120, []]);
  assert.deepEqual(state(paths.statePath).cursor, { mergedAt: at(1), number: 120 });
  const next = auditMerges({ gh, now: new Date(now.getTime() + 3600000), outputs: () => w.outputs, ...paths });
  assert.deepEqual(next.missing.map(m => m.pr), [121], 'the next pass audits it');
});

test('the audit runs from the tick while the plan is closed, at most once an hour', () => {
  const w = world();
  w.add(1, { kind: 'none' });
  const gh = fakeGh(w);
  const base0 = gh.json;
  gh.json = args => (args[0] === 'issue' && args[1] === 'list' && args.includes('daily-plan') ? [{ number: 50, title: planTitle }]
    : args[0] === 'issue' && args[1] === 'view' ? { comments: [] } : base0(args));
  gh.openPrs = () => [];
  const paths = home();
  const runs = [];
  const mergeAudit = options => { runs.push(options.now.toISOString()); return runMergeAudit({ ...options, outputs: () => w.outputs, ...paths }); };
  const date = '2026-11-16';
  let ms = after(10).getTime();
  const r = tick({ gh, now: { date, hour: 2, minute: 0 }, nowMs: () => ms, mergeAudit, merge: () => ({}), review: () => ({}) });
  assert.equal(r.status, 'closed');
  assert.equal(runs.length, 1);
  assert.equal(created(gh).length, 1, 'the closed plan does not stop the audit');
  ms += 10 * 60000;
  tick({ gh, now: { date, hour: 2, minute: 10 }, nowMs: () => ms, mergeAudit, merge: () => ({}), review: () => ({}) });
  assert.equal(created(gh).length, 1);
  assert.equal(state(paths.statePath).lastRunAt, after(10).toISOString(), 'the second tick inside the hour did not run a pass');
  const logs = [];
  tick({ gh, now: { date, hour: 2, minute: 20 }, nowMs: () => ms, mergeAudit: () => { throw new Error('boom'); }, log: l => logs.push(l), merge: () => ({}), review: () => ({}) });
  assert.match(logs.join('\n'), /merge audit failed, retry next run: boom/, 'an audit failure never breaks the tick');
});
