// Owner 15.11.2026: at least 2 of the day's 3–5 items come from the 7-week plan; one list a day.
// Synthetic PR and issue numbers only.
import './collab-test-home.mjs';
import assert from 'node:assert/strict';
import test from 'node:test';
import { agentMarker } from './collab-trust.mjs';
import { checkPrep, dayList, label7w, pickPlan, plannedEntry, prepRefs, workUnits } from './collab-quota.mjs';
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
  assert.deepEqual([list.want, list.items.filter(u => u.plan7w).length, list.short7w], [1, 1, 0]);
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
