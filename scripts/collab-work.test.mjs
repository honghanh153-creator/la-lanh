import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
process.env.LA_LANH_COLLAB_HOME = mkdtempSync(join(tmpdir(), 'collab-work-'));
const assert = (await import('node:assert/strict')).default;
const test = (await import('node:test')).default;
const { claimedCriteria, issueCriteria, itemStatus, plannedWork, renderProgress, workProgress, workRef } = await import('./collab-work.mjs');
const { ownerNotes } = await import('./collab-status.mjs');

// Synthetic issue and PRs only.
const sha = n => String(n).repeat(40).slice(0, 40);
const approved = n => ({ authorAssociation: 'OWNER', createdAt: '2026-11-14T01:00:00Z', body: `Review verdict: APPROVE @ ${sha(n)}\nReviewer: Codex\n<!-- la-lanh-agent codex-auto-review sha=${sha(n)} -->` });
const merged = (number, body, mergedAt, { reviewed = true } = {}) => ({ number, body, mergedAt, state: 'MERGED', baseRefName: 'collab/integration', headRefOid: sha(number), comments: reviewed ? [approved(number)] : [] });
const issue = '## Mục tiêu cho người dùng\n\nx\n\n## Tiêu chí đạt\n\n- [ ] Người dùng thấy tóm tắt\n- [x] AC07 mở được căn cứ\n- [ ]\n\n## Phối hợp hiện tại\n\n- Trạng thái: đang làm\n';

test('a PR names its item and the criteria it meets; the issue lists its criteria', () => {
  assert.equal(workRef('Related: #5\nViệc: #12\n'), 12);
  assert.equal(workRef('Việc: #ISSUE_NUMBER'), null, 'the template line is not an item');
  assert.deepEqual([...claimedCriteria('Tiêu chí đạt: TC1, ac07')], ['TC1', 'AC07']);
  assert.deepEqual([...claimedCriteria('Tiêu chí đạt: <mã tiêu chí trong mục "Tiêu chí đạt" của issue mà PR này làm xong, cách nhau dấu phẩy; để trống nếu chưa xong>')], [], 'the template placeholder claims nothing');
  assert.deepEqual(issueCriteria(issue), ['TC1', 'AC07'], 'an empty template line is not a criterion; a ticked box proves nothing either');
  assert.deepEqual(issueCriteria('## Tiêu chí đạt\n\n- [ ]\n'), []);
});

test('two PRs for one item count once; a merge without all criteria is not a finished item', () => {
  const prs = [merged(1, 'Việc: #12\nTiêu chí đạt: TC1', '2026-11-14T03:00:00Z'), merged(2, 'Việc: #12\nTiêu chí đạt: AC07', '2026-11-14T05:00:00Z')];
  const s = itemStatus(issue, prs);
  assert.equal(s.metAt, '2026-11-14T05:00:00Z');
  assert.deepEqual(s.prs, [1, 2]);
  const half = itemStatus(issue, prs.slice(0, 1));
  assert.equal(half.metAt, null);
  assert.deepEqual(half.missing, ['AC07']);
  const unreviewed = itemStatus(issue, [prs[0], merged(2, 'Việc: #12\nTiêu chí đạt: AC07', '2026-11-14T05:00:00Z', { reviewed: false })]);
  assert.equal(unreviewed.metAt, null, 'a merge without Codex APPROVE of its head is not evidence');
  assert.equal(itemStatus('## Tiêu chí đạt\n\n- [ ]\n', [merged(3, 'Việc: #12\nTiêu chí đạt: TC1', '2026-11-14T03:00:00Z')]).metAt, null, 'no criteria: never met');
  const fetch = () => ({ body: issue, prs });
  const p = workProgress({ date: '2026-11-14', planned: [{ item: 12 }, { pr: 40 }], fetch });
  assert.deepEqual({ picked: p.picked, finished: p.finished, unlinked: p.unlinked }, { picked: 1, finished: [12], unlinked: [40] });
  assert.equal(renderProgress(p), 'Việc đạt tiêu chí: 1/1 việc đã chọn đạt đủ tiêu chí; 1 PR chưa gắn việc (#40), không tính.');
});

test('an item met on an earlier day is not counted again for a follow-up PR today', () => {
  const prs = [merged(1, 'Việc: #12\nTiêu chí đạt: TC1, AC07', '2026-11-13T09:00:00Z'), merged(2, 'Việc: #12\nTiêu chí đạt: TC1', '2026-11-14T03:00:00Z')];
  const p = workProgress({ date: '2026-11-14', planned: [{ item: 12 }], fetch: () => ({ body: issue, prs }) });
  assert.deepEqual(p.finished, []);
  assert.deepEqual(p.open, [], 'met yesterday: not open either');
  // The day is the Vietnam day: 18:30Z on the 13th is 01:30 on the 14th in Vietnam.
  const late = workProgress({ date: '2026-11-14', planned: [{ item: 12 }], fetch: () => ({ body: issue, prs: [merged(1, 'Việc: #12\nTiêu chí đạt: TC1, AC07', '2026-11-13T18:30:00Z')] }) });
  assert.deepEqual(late.finished, [12]);
});

test('the items of the day are fixed at plan time and a failed read is unmeasured, not zero', () => {
  const turns = [{ number: 1, item: 12 }, { number: 2, item: 12 }, { number: 3, item: null }];
  assert.deepEqual(plannedWork(turns), [{ item: 12 }, { pr: 3 }], 'two PRs of one item are one planned item');
  const broken = workProgress({ date: '2026-11-14', planned: [{ item: 12 }], fetch: () => { throw new Error('gh: timeout'); } });
  assert.match(renderProgress(broken), /^Việc đạt tiêu chí: chưa đo được \(gh: timeout\)\.$/);
  const notes = ownerNotes({ now: { date: '2026-11-14', hour: 14, minute: 5 }, merged: [{ number: 1, title: 'x' }, { number: 2, title: 'y' }], planned: [1, 2], work: () => renderProgress(workProgress({ date: '2026-11-14', planned: [{ item: 12 }], fetch: () => ({ body: issue, prs: [] }) })) });
  const digest = notes.find(n => n.key.startsWith('digest-')).lines.join('\n');
  assert.match(digest, /Việc đạt tiêu chí: 0\/1 việc đã chọn đạt đủ tiêu chí\./);
  assert.match(digest, /Đã gộp 2 PR hôm nay \(số PR, không phải số việc\)\./);
  assert.doesNotMatch(digest, /Xong: 2\/2/, 'two merges are not two finished items');
});
