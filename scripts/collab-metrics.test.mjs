import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { digest } from './codex-copy-review.mjs';
import { bundleMetric, collectMetrics, copyMetric, flowMetric, flowStages, leadTimeMetric, renderMetrics, servable } from './collab-metrics.mjs';

// Synthetic sentences only.
const ok = (id, text, approver = 'codex', category = 'reading') => ({ id, category, text, status: 'approved', approver, date: '2026-11-12', digest: digest(text) });
const pending = (id, text = 'Câu chờ.') => ({ id, category: 'reading', text, status: 'pending' });
const registry = { version: 'copy-registry/v1', entries: [
  ok('daily.bundle.a.01.headline', 'Tiêu đề 1.'), ok('daily.bundle.a.01.scene', 'Cảnh 1.'), ok('daily.bundle.a.01.action', 'Việc 1.', 'owner'),
  ok('daily.bundle.a.02.headline', 'Tiêu đề 2.'), ok('daily.bundle.a.02.scene', 'Cảnh 2.'), pending('daily.bundle.a.02.action'),
  ok('daily.bundle.b.01.headline', 'Tiêu đề 3.'), ok('daily.bundle.b.01.scene', 'Cảnh 3.'), { ...ok('daily.bundle.b.01.action', 'Việc 3.'), text: 'Việc 3 đã sửa.' },
  pending('daily.action.x.01'),
] };
const nowMs = Date.parse('2026-11-12T12:00:00Z');
const hoursAgo = h => new Date(nowMs - h * 3600000).toISOString();

test('a bundle is servable only when all three parts are approved and the digest matches the text', () => {
  assert.deepEqual(bundleMetric(registry), { ready: 1, total: 3 }, 'a pending part or an edited text without a new digest does not serve');
  assert.equal(servable({ ...ok('p', 'Câu.'), category: 'privacy' }), false, 'owner-only copy approved by Codex never serves');
  assert.equal(servable(ok('p', 'Câu.', 'owner', 'privacy')), true);
  assert.equal(servable({ ...ok('p', 'Câu.'), date: '' }), false);
});

test('approved copy is split by approver; pending is counted from the same registry', () => {
  assert.deepEqual(copyMetric(registry), { total: 10, codex: 6, owner: 1, pending: 2 });
});

test('lead time is the median of opened→merged hours over the last 7 days', () => {
  const pr = (opened, merged) => ({ createdAt: hoursAgo(opened), mergedAt: hoursAgo(merged), baseRefName: 'collab/integration' });
  assert.deepEqual(leadTimeMetric([pr(10, 8), pr(30, 20), pr(5, 1)], nowMs), { hours: 4, count: 3 });
  assert.deepEqual(leadTimeMetric([pr(10, 8), pr(30, 20)], nowMs), { hours: 6, count: 2 });
  assert.deepEqual(leadTimeMetric([pr(400, 200), { ...pr(3, 1), baseRefName: 'main' }], nowMs).error, 'không có PR nào merge vào integration trong 7 ngày qua');
});

test('every metric comes from its source and prints one plain line each', () => {
  const calls = [];
  const run = (cmd, args) => {
    calls.push(args.join(' '));
    if (args[0] === 'rev-list') return '42\n';
    if (args[0] === 'log') return `${Math.floor((nowMs - 3 * 86400000 - 60000) / 1000)}\n`;
    return '';
  };
  const gh = { json: args => { calls.push(args.join(' ')); return [{ createdAt: hoursAgo(10), mergedAt: hoursAgo(7), baseRefName: 'collab/integration' }]; } };
  const prs = [{ number: 1, author: { login: 'honghanh153-creator' }, isCrossRepository: false, baseRefName: 'collab/integration', headRefName: 'agent/claude/x', labels: [] }];
  const m = collectMetrics({ registry: () => registry, run, gh, prs, turns: [{ number: 1, turn: 'codex-review' }], nowMs,
    lessons: () => 'Lời hứa sửa quy trình: 1/3 đã chạy thật (đã merge, Codex duyệt), 2 đang làm, **1 quá hạn** (L02).' });
  assert.ok(calls.includes('rev-list --count origin/main..origin/collab/integration'));
  assert.ok(calls.some(c => c.startsWith('fetch --quiet origin main collab/integration')));
  assert.ok(calls.some(c => c.includes('--state merged') && c.includes('merged:>=2026-10-29') && c.includes('comments')), 'two weeks, with comments, in one read');
  const lines = renderMetrics(m);
  assert.deepEqual(lines, [
    'Bộ Daily phục vụ được: 1/3 bộ.',
    'Câu đã duyệt: 7/10 câu (Codex duyệt 6, owner duyệt 1, còn chờ 2).',
    'Khoảng cách tới người dùng: 42 commit ở integration chưa lên main; main cập nhật lần cuối 3 ngày trước.',
    'Thời gian từ mở PR tới merge vào integration (7 ngày qua): trung vị 3,0 giờ (1 PR).',
    'Tốc độ vòng (7 ngày qua; trong ngoặc là 7 ngày trước): mở tới merge trung vị 3,0 giờ (chưa có); chờ check chưa đo, chờ duyệt chưa đo, chờ merge chưa đo; 0,0 vòng duyệt/PR (chưa có); 100% được duyệt ngay lần đầu (chưa có); 1 PR.',
    'Việc đang làm: 0/3, đang chờ review: 1/3 (kế hoạch 7 tuần 0/1 và 0/1; Daily 0/1 và 0/1; quy trình 0/1 và 1/1).',
    'Lời hứa sửa quy trình: 1/3 đã chạy thật (đã merge, Codex duyệt), 2 đang làm, **1 quá hạn** (L02).',
  ]);
});

test('an unavailable source prints "chưa đo được (lý do)", never a number', () => {
  const m = collectMetrics({ registry: () => { throw new Error('ENOENT copy_registry.json'); }, run: () => { throw new Error('could not resolve host'); },
    gh: { json: () => { throw new Error('gh: HTTP 502'); } }, nowMs });
  const lines = renderMetrics(m);
  assert.match(lines[0], /^Bộ Daily phục vụ được: chưa đo được \(không đọc được kho câu chữ: ENOENT copy_registry\.json\)\.$/);
  assert.match(lines[1], /^Câu đã duyệt: chưa đo được \(/);
  assert.match(lines[2], /^Khoảng cách tới người dùng: chưa đo được \(không lấy được nhánh từ GitHub: could not resolve host\); ngày cập nhật main chưa đo được/);
  assert.match(lines[3], /chưa đo được \(gh: HTTP 502\)/);
  assert.ok(lines.slice(0, 4).every(l => !/\d+\/\d+|\d+ commit|trung vị/.test(l)), 'no number when the source failed');
  assert.deepEqual(renderMetrics(null), []);
});

// Fix-forward #615: with two lanes the board showed "2/1"; totals now read against both lane limits.
test('the WIP line counts against both lanes, with each lane after it', () => {
  const none = { error: 'x' };
  const rest = { bundles: none, copy: none, ahead: none, mainAge: none, leadTime: none };
  const base = renderMetrics({ ...rest, wip: { inProgress: 2, inReview: 1, lanes: { plan7w: { inProgress: 1, inReview: 1 }, process: { inProgress: 1, inReview: 0 } } } });
  assert.ok(base.includes('Việc đang làm: 2/2, đang chờ review: 1/2 (kế hoạch 7 tuần 1/1 và 1/1; quy trình 1/1 và 0/1).'), base.join(' | '));
  assert.ok(renderMetrics({ ...rest, wip: { inProgress: 0, inReview: 1 } }).includes('Việc đang làm: 0/1, đang chờ review: 1/1.'), 'a count without lanes reads as before');
});

// Research item 5 (owner 21.11.2026): is the loop getting faster or slower, and which stage waits.
test('item 5: each merged PR splits its lead time by stage; the board compares this week with the last', () => {
  const head = 'a'.repeat(40);
  const c = (at, body) => ({ authorAssociation: 'OWNER', createdAt: at, body });
  const auto = '<!-- la-lanh-agent codex-auto-review sha=' + head + ' p2=0 -->';
  const merged = (n, opened, mergedAt, comments) => ({ number: n, createdAt: opened, mergedAt, baseRefName: 'collab/integration', comments });
  const p1 = merged(1, '2026-11-20T00:00:00Z', '2026-11-20T10:00:00Z', [
    c('2026-11-20T02:00:00Z', `Author check: PASS @ ${head}`),
    c('2026-11-20T04:00:00Z', `Review verdict: REQUEST_CHANGES @ ${head}\nReviewer: Codex\n${auto}`),
    c('2026-11-20T06:00:00Z', `Review verdict: APPROVE @ ${head}\nReviewer: Codex\n${auto}`),
    c('2026-11-20T11:00:00Z', `Review verdict: REQUEST_CHANGES @ ${head}\nReviewer: Codex\n${auto}`),
    { ...c('2026-11-20T01:00:00Z', `Author check: PASS @ ${head}`), authorAssociation: 'NONE' },
  ]);
  assert.deepEqual(flowStages(p1), { lead: 10, toCheck: 2, toApprove: 4, toMerge: 4, rounds: 2, firstTime: false },
    'only trusted comments before the merge count');
  const p2 = merged(2, '2026-11-19T00:00:00Z', '2026-11-19T04:00:00Z', [c('2026-11-19T01:00:00Z', `Author check: PASS @ ${head}`), c('2026-11-19T03:00:00Z', `Review verdict: APPROVE @ ${head}\nReviewer: Codex\n${auto}`)]);
  const old = merged(3, '2026-11-10T00:00:00Z', '2026-11-11T00:00:00Z', []);
  const nowMs = Date.parse('2026-11-21T12:00:00Z');
  const f = flowMetric([p1, p2, old, { ...p2, number: 4, baseRefName: 'main' }], nowMs);
  assert.deepEqual([f.week.count, f.week.lead, f.week.toCheck, f.week.toApprove, f.week.toMerge, f.week.rounds, f.week.firstTimePct], [2, 7, 1.5, 3, 2.5, 1.5, 50]);
  assert.deepEqual([f.before.count, f.before.lead, f.before.toCheck], [1, 24, null], 'a stage without its comment is left out, never 0');
  const none = { error: 'x' };
  const line = renderMetrics({ bundles: none, copy: none, ahead: none, mainAge: none, leadTime: none, wip: none, flow: f }).find(l => l.startsWith('Tốc độ vòng'));
  assert.equal(line, 'Tốc độ vòng (7 ngày qua; trong ngoặc là 7 ngày trước): mở tới merge trung vị 7,0 giờ (24,0 giờ); chờ check 1,5 giờ, chờ duyệt 3,0 giờ, chờ merge 2,5 giờ; 1,5 vòng duyệt/PR (0,0 vòng duyệt/PR); 50% được duyệt ngay lần đầu (100% được duyệt ngay lần đầu); 2 PR.');
  assert.match(flowMetric([old], nowMs).error, /không có PR nào/);
});
