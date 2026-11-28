// Owner 15.11.2026: at least 2 of the day's 3–5 items come from the 7-week plan; one list a day.
// Synthetic PR and issue numbers only.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { agentMarker } from './collab-trust.mjs';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { checkPrep, dayList, drainAt, drainState, mergedLimit, label7w, mergedItems, pickPlan, plannedEntry, prepRefs, quotaIssues, serious, startBlock, uiHold, workUnits } from './collab-quota.mjs';
import { writeJson } from './collab-trust.mjs';
import { renderProgress, workProgress } from './collab-work.mjs';

// Turns arrive priority-sorted (ops → content → privacy → feature); 7-week work is feature.
const turn = (number, { area = 'ops', turn = 'claude-check', item = null } = {}) => ({ number, title: `pr ${number}`, area, turn, item, source: 'AC', userSees: 'x' });
const prOf = (number, labels = []) => ({ number, labels: labels.map(name => ({ name })) });
const task = (number, labels = [label7w], criteria = true) => ({ number, title: `task ${number}`, labels: labels.map(name => ({ name })), body: criteria ? '## Tiêu chí đạt\n- AC1 làm được\n' : '## Việc\n- tổng hợp\n' });
const base = () => {
  const turns = [turn(1), turn(2), turn(3), turn(4, { area: 'content' }), turn(5, { area: 'content' }), turn(10, { area: 'feature', item: 100 }), turn(11, { area: 'feature', item: 100 }), turn(12, { area: 'feature' }), turn(13, { area: 'feature', turn: 'hold' })];
  const prs = [1, 2, 3, 4, 5, 10, 11, 13].map(n => prOf(n)).concat([prOf(12, [label7w])]);
  const issues = [task(100), task(101), task(102, [label7w, 'needs-owner']), task(512, [label7w], false)];
  return { turns, prs, issues };
};
const keys = list => list.items.map(u => u.key);

test('7-week: two seats are kept even when the old priority order puts the plan last', () => {
  const units = workUnits(base());
  const list = pickPlan(units);
  assert.equal(list.items.length, 5);
  assert.equal(list.items.filter(u => u.plan7w).length, 2, keys(list).join());
  assert.deepEqual(keys(list), ['pr:1', 'pr:2', 'pr:3', 'item:100', 'pr:12']);
  assert.equal(list.available7w, 3, 'item:100 (two PRs, one item), pr:12, issue 101 with no PR');
  // Two seats are a floor: with room, a third 7-week item stays in.
  const roomy = pickPlan(units.filter(u => !['pr:2', 'pr:3', 'pr:4', 'pr:5'].includes(u.key)));
  assert.equal(roomy.items.filter(u => u.plan7w).length, 3);
});

test('7-week: two PRs of one item take one seat; holds, needs-owner and trackers are not items', () => {
  const units = workUnits(base());
  const item = units.find(u => u.key === 'item:100');
  assert.deepEqual(item.prs, [10, 11]);
  assert.equal(item.plan7w, true, 'the label sits on the item issue');
  assert.equal(units.find(u => u.key === 'pr:13').ready, false, 'hold');
  assert.equal(units.some(u => u.item === 102), false, 'needs-owner');
  assert.equal(units.some(u => u.item === 512), false, 'a tracker has no criteria');
  const start = units.find(u => u.key === 'item:101');
  assert.deepEqual([start.start, start.prs.length, start.ready], [true, 0, true]);
});

test('7-week: fewer ready items than seats takes all of them; none leaves the old pick', () => {
  const one = workUnits({ turns: [turn(1), turn(2), turn(3), turn(4), turn(5), turn(6), turn(9, { area: 'feature' })], prs: [prOf(9, [label7w])], issues: [] });
  const list = pickPlan(one);
  assert.deepEqual([list.want, list.items.filter(u => u.plan7w).length, list.short7w], [1, 1, 1], 'one seat short of the target of 2');
  const none = pickPlan(workUnits({ turns: [1, 2, 3, 4, 5, 6].map(n => turn(n)), prs: [], issues: [] }));
  assert.deepEqual(keys(none), ['pr:1', 'pr:2', 'pr:3', 'pr:4', 'pr:5']);
});

test('7-week: a serious incident goes first, apart, and never takes a kept seat', () => {
  const b = base();
  b.issues.push(task(900, ['incident', 'severity:P1']));
  b.turns.unshift(turn(90, { item: 900 }));
  b.prs.push(prOf(90));
  const list = pickPlan(workUnits(b));
  assert.deepEqual(list.incidents.map(u => u.key), ['item:900']);
  assert.equal(list.items.some(u => u.incident), false);
  assert.equal(list.items.filter(u => u.plan7w).length, 2);
  // An ops-alert alone is not a serious incident.
  const alertOnly = workUnits({ turns: [turn(91)], prs: [prOf(91, ['ops-alert'])], issues: [] });
  assert.equal(alertOnly[0].incident, false);
});

// L60 (21.11.2026): hotfix #863 had `incident` alone and waited behind ordinary work while
// collab/integration was red.
test('L60: an incident PR without a severity goes first; only an explicit P2 or lower does not', () => {
  const units = workUnits({ turns: [turn(92), turn(93), turn(94)], prs: [prOf(92, ['incident']), prOf(93, ['incident', 'severity:P2']), prOf(94, ['incident', 'severity:P0'])], issues: [] });
  assert.deepEqual(units.map(u => [u.key, u.incident]), [['pr:92', true], ['pr:93', false], ['pr:94', true]]);
  assert.equal(serious([{ name: 'incident' }, { name: 'severity:P1' }]), true);
  assert.equal(serious([{ name: 'severity:P1' }]), false, 'a severity without incident is not an incident');
  assert.equal(pickPlan(units).incidents.some(u => u.key === 'pr:92'), true, 'planned first');
});

const prepComment = (body, date = '2026-11-16', who = 'OWNER') => ({ authorAssociation: who, createdAt: `${date}T00:00:00Z`, body: `${body}\n\n${agentMarker} morning-prep date=${date} -->` });
test('7-week: the morning list is used when it passes the same rules', () => {
  const units = workUnits(base());
  const list = dayList({ units, comments: [prepComment('items=pr:4,pr:10,item:101,pr:1')], date: '2026-11-16' });
  assert.equal(list.source, 'prep', list.note);
  assert.deepEqual(keys(list), ['pr:4', 'item:100', 'item:101', 'pr:1']);
  assert.match(list.note, /buổi sáng/);
});

test('7-week: a morning list short of seats, with bad refs, duplicates or no machine part is refused and re-picked', () => {
  const units = workUnits(base());
  const short = dayList({ units, comments: [prepComment('items=pr:1,pr:2,pr:3,pr:12')], date: '2026-11-16' });
  assert.equal(short.source, 'machine');
  assert.match(short.note, /chỉ có 1 việc kế hoạch 7 tuần, cần 2/);
  assert.equal(short.items.filter(u => u.plan7w).length, 2);
  // The class comes from labels read here; the list's own claim counts for nothing.
  assert.equal(checkPrep(['pr:1', 'pr:2', 'pr:3'], units).ok, false);
  assert.match(checkPrep(['pr:10', 'item:100', 'pr:12'], units).reasons.join(), /trùng việc item:100/);
  assert.match(checkPrep(['pr:13', 'pr:10', 'pr:12'], units).reasons.join(), /pr:13 đang giữ/);
  assert.match(checkPrep(['pr:999', 'pr:10', 'pr:12'], units).reasons.join(), /pr:999 không có/);
  assert.match(checkPrep(['pr:1', 'pr:2', 'pr:3', 'pr:4', 'pr:10', 'pr:12'], units).reasons.join(), /quá 5 việc/);
  assert.match(dayList({ units, comments: [prepComment('4 việc, không có dòng máy')], date: '2026-11-16' }).note, /items=/);
  // Untrusted, or another day's list: not a morning list at all.
  assert.equal(prepRefs([prepComment('items=pr:1', '2026-11-16', 'NONE')], '2026-11-16'), null);
  assert.equal(prepRefs([prepComment('items=pr:1', '2026-11-15')], '2026-11-16'), null);
  assert.match(dayList({ units, comments: [], date: '2026-11-16' }).note, /Chưa có danh sách buổi sáng/);
});

test('7-week: the record keeps the class at plan time and the progress line reports it', () => {
  const list = pickPlan(workUnits(base()));
  const planned = list.items.map(plannedEntry);
  assert.deepEqual(planned.filter(p => p.plan7w), [{ item: 100, plan7w: true }, { pr: 12, plan7w: true }]);
  const fetch = n => ({ body: '## Tiêu chí đạt\n- AC1 x\n', prs: n === 100 ? [{ number: 10, mergedAt: '2026-11-16T03:00:00Z', body: 'Việc: #100\nTiêu chí đạt: AC1' }] : [] });
  const p = workProgress({ date: '2026-11-16', planned, fetch, reviewed: () => true });
  assert.deepEqual(p.w7, { picked: 2, finished: 1 });
  assert.match(renderProgress(p), /\n- Việc kế hoạch 7 tuần: đã chọn 2 \(tối thiểu 2 khi có việc sẵn sàng\), đạt 1\./);
  // Days recorded before this change have no class: no 7-week line.
  assert.equal(workProgress({ date: 'x', planned: [{ pr: 1 }], fetch }).w7, null);
});

test('7-week: removing the kept seats makes the floor test fail (red check of the rule itself)', () => {
  const units = workUnits(base());
  const plain = pickPlan(units, { need: 0 });
  assert.ok(plain.items.filter(u => u.plan7w).length < 2, 'without the reservation the old order starves the plan');
});

test('7-week: a morning list shorter than 3 is refused when 3 are ready', () => {
  const units = workUnits(base());
  assert.match(checkPrep(['pr:10', 'pr:12'], units).reasons.join(), /chỉ có 2 việc, cần 3/);
  assert.equal(checkPrep(['pr:1', 'pr:10', 'pr:12'], units).ok, true);
});

// Three-agent dispatch 28.11.2026, part D. Synthetic numbers shaped like the real case: two 7-week
// feature issues stayed open after their PRs merged, and the planner kept starting them.
const fakeGh = ({ issues, merged, mergedFails = false }) => ({
  json: args => {
    if (args[0] === 'issue') { const label = args[args.indexOf('--label') + 1]; return issues.filter(i => i.labels.some(l => l.name === label)); }
    if (args[0] === 'pr' && args.includes('merged')) { if (mergedFails) throw new Error('gh: network'); return merged; }
    throw new Error(`unexpected ${args.join(' ')}`);
  },
});
const d7w = [task(714, [label7w, 'area:feature']), task(715, [label7w, 'area:feature']), task(713, [label7w, 'area:content']), task(935, [label7w]), task(711, [label7w, 'area:feature']), task(960, ['incident'])];
const mergedPrs = [{ number: 875, body: 'Việc: #714\nTiêu chí đạt: #714 AC1–AC5' }, { number: 876, body: 'Việc: #715' }, { number: 880, body: 'Việc: #714' }, { number: 881, body: 'không có việc' }];

test('planner: an item with a merged PR does not start again; the note says why (part D)', () => {
  assert.deepEqual([...mergedItems(mergedPrs)].map(([n, e]) => [n, e.pr, [...e.claimed].sort()]), [[714, 875, ['AC1', 'AC2', 'AC3', 'AC4', 'AC5']], [715, 876, []]]);
  const issues = quotaIssues(fakeGh({ issues: d7w, merged: mergedPrs }), { hold: false });
  const units = workUnits({ turns: [], prs: [], issues });
  const by = n => units.find(u => u.item === n);
  assert.equal(by(714).ready, false);
  assert.equal(by(714).skip, 'đã có PR #875 merge, đủ tiêu chí; cần đóng issue');
  assert.equal(by(715).skip, 'đã có PR #876 merge, còn AC1 chưa có PR nhận; cần mở việc tiếp');
  assert.equal(by(715).ready, false);
  for (const n of [713, 935, 711]) assert.equal(by(n).ready, true, `#${n} starts`);
  assert.equal(by(960).ready, true, 'an incident is never blocked');
  const picked = pickPlan(units).items.map(u => u.item);
  assert.ok(!picked.includes(714) && !picked.includes(715));
  const list = dayList({ units, comments: [], date: '2026-11-28' });
  assert.match(list.note, /Không mở việc mới: #714 \(đã có PR #875 merge, đủ tiêu chí; cần đóng issue\), #715/);
  assert.match(checkPrep(['item:714', 'item:713', 'item:711'], units).reasons.join(';'), /item:714 đang giữ \(đã có PR #875/);
});

test('planner: an item with an open PR is still worked; the merged rule only stops fresh starts', () => {
  const issues = quotaIssues(fakeGh({ issues: d7w, merged: mergedPrs }), { hold: true });
  const units = workUnits({ turns: [turn(990, { area: 'feature', item: 714 })], prs: [prOf(990)], issues });
  const u = units.find(x => x.key === 'item:714');
  assert.equal(u.ready, true);
  assert.equal(u.plan7w, true, 'the label still comes from the issue');
  assert.equal(units.filter(x => x.key === 'item:714').length, 1);
});

test('planner: while the UI hold stands, only ops, content, privacy and process issues start (part D)', () => {
  const issues = quotaIssues(fakeGh({ issues: d7w, merged: [] }), { hold: true });
  const units = workUnits({ turns: [], prs: [], issues });
  const ready = units.filter(u => u.ready).map(u => u.item).sort();
  assert.deepEqual(ready, [713, 960], 'content and the incident start; feature and unlabelled wait');
  assert.equal(units.find(u => u.item === 711).skip, 'đang giữ UI và tính năng mới');
  assert.equal(units.find(u => u.item === 935).skip, 'đang giữ UI và tính năng mới', 'unlabelled counts as held');
  const free = workUnits({ turns: [], prs: [], issues: quotaIssues(fakeGh({ issues: d7w, merged: [] }), { hold: false }) });
  assert.equal(free.filter(u => u.ready).length, d7w.length);
});

test('planner: a failed merged-PR read blocks fresh starts, never incidents; the hold file is read by status only', () => {
  const units = workUnits({ turns: [], prs: [], issues: quotaIssues(fakeGh({ issues: d7w, merged: [], mergedFails: true }), { hold: false }) });
  assert.deepEqual(units.filter(u => u.ready).map(u => u.item), [960]);
  assert.equal(units.find(u => u.item === 713).skip, 'chưa đọc được PR đã merge');
  assert.equal(startBlock(task(5, ['incident', 'severity:P1']), { mergedKnown: false, hold: true }), null);
  const dir = mkdtempSync(join(tmpdir(), 'uihold-'));
  const path = join(dir, 'ui.json');
  assert.equal(uiHold({ path }), false, 'no file: no hold on this host');
  writeJson(path, { status: 'awaiting_owner_master_ui_approval' });
  assert.equal(uiHold({ path }), true);
  writeJson(path, { status: 'approved' });
  assert.equal(uiHold({ path }), false);
});

test('planner: a merged-PR page that reaches the limit is unread, not complete (Codex r1 on #954)', () => {
  const asked = [];
  const gh = rows => ({ json: args => { if (args[0] === 'pr') asked.push(args[args.indexOf('--limit') + 1]); return fakeGh({ issues: d7w, merged: rows }).json(args); } });
  const full = Array.from({ length: 3 }, (_, i) => ({ number: 2000 + i, body: 'không có việc' }));
  const units = workUnits({ turns: [], prs: [], issues: quotaIssues(gh(full), { hold: false, limit: 3 }) });
  assert.equal(units.find(u => u.item === 713).skip, 'chưa đọc được PR đã merge', 'a full page may hide the PR that named #713');
  assert.deepEqual(units.filter(u => u.ready).map(u => u.item), [960], 'incidents still go');
  assert.equal(quotaIssues(gh(full.slice(0, 2)), { hold: false, limit: 3 }).find(i => i.number === 713).startBlock, null);
  quotaIssues(gh([]), { hold: false });
  assert.equal(asked.at(-1), String(mergedLimit));
  assert.ok(mergedLimit >= 1000, 'well above the 517 merged PRs of 28.11');
  // The tick's incident refresh skips the merged read; incidents are never blocked by it.
  const before = asked.length;
  const live = workUnits({ turns: [], prs: [], issues: quotaIssues(gh([]), { hold: false, readMerged: false }) });
  assert.equal(asked.length, before);
  assert.deepEqual(live.filter(u => u.ready && u.incident).map(u => u.item), [960]);
});

// BT1 step 0 (owner 28.11.2026): while 15 or more PRs are open the plan holds only work in progress,
// incidents and safety issues; no issue-only unit starts.
test('drain: at 15 open PRs no new issue-only item starts; in-progress PRs, incidents and safety still go', () => {
  assert.equal(drainAt, 15);
  const open = n => Array.from({ length: n }, (_, i) => prOf(300 + i));
  const turns = [turn(300, { area: 'feature' }), turn(301)];
  const issues = [task(101), task(960, ['incident']), task(961, [label7w, 'safety']), task(962, [label7w, 'incident', 'severity:P2'])];
  const busy = workUnits({ turns, prs: open(15), issues });
  assert.equal(busy.find(u => u.item === 101).skip, 'đang dọn PR mở (15 ≥ 15)');
  assert.equal(busy.find(u => u.item === 101).ready, false);
  assert.deepEqual(busy.filter(u => u.ready).map(u => u.key), ['pr:300', 'pr:301', 'item:960', 'item:961', 'item:962']);
  const list = dayList({ units: busy, comments: [], date: '2026-11-29', drain: drainState(open(15)) });
  assert.deepEqual(list.drain, { on: true, open: 15, at: 15 });
  assert.ok(!list.items.some(u => u.item === 101), 'no new item in the plan');
  assert.match(list.note, /#101 \(đang dọn PR mở/);
  // A morning list that names the new item does not pass.
  const prep = checkPrep(['pr:300', 'item:101'], busy);
  assert.equal(prep.ok, false);
  assert.match(prep.reasons.join(), /item:101 đang giữ \(đang dọn PR mở/);
  // Below 15 the item is ready again.
  const calm = workUnits({ turns, prs: open(14), issues });
  assert.equal(calm.find(u => u.item === 101).ready, true);
  assert.equal(drainState(open(14)).on, false);
  assert.equal(drainState(null).on, false);
});
