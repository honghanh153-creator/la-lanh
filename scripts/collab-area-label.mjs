// PRs without an area label (L58, 21.11.2026). The machine works the earliest area group that has work
// (activeArea, collab-turn.mjs); a PR with no `area:` label falls to `feature`, the last group, and
// ops and content always had work. Eight process PRs (#743 … #820) sat for up to three days without
// a single check or review. Each tick now looks at own open PRs into collab/integration:
// - a PR that changes only workflow files (loop scripts, docs/operations, docs/reviews, .github,
//   AGENTS.md, CLAUDE.md) is labelled `area:ops`, as classifyArea already does for `ops(` titles;
// - any other unlabelled PR that classifyArea can only put in the last group (`feature`), seen on two
//   ticks in a row, opens one ops alert naming them. A title such as `content(radar): …` already
//   places a PR without a label, so those are left alone. The alert is raised again only when the set
//   changes, and closed when none is left.
// Drafts are skipped: they are on hold anyway.
import { join } from 'node:path';
import { classifyArea, integration, isOwnPr, readJson, repo, stateDir, writeJson } from './collab-trust.mjs';

export const areaLabels = ['area:ops', 'area:content', 'area:privacy', 'area:feature'];
export const areaWatchSubject = 'PR chưa có nhãn area';
export const areaStatePath = () => join(stateDir, 'state', 'area-watch.json');
export const workflowPath = path => /^scripts\/(collab-|codex-|collaboration-)/.test(path) || /^docs\/(operations|reviews)\//.test(path)
  || /^\.github\//.test(path) || ['AGENTS.md', 'CLAUDE.md'].includes(path);
const names = pr => (pr.labels ?? []).map(l => l.name ?? l);
const paths = pr => (pr.files ?? []).map(f => f?.path ?? f).filter(p => typeof p === 'string' && p);
export const unlabelled = prs => (prs ?? []).filter(pr => isOwnPr(pr) && !pr.isDraft && pr.baseRefName === integration && !names(pr).some(n => areaLabels.includes(n)));

const listOpen = gh => gh.json(['pr', 'list', '--repo', repo, '--state', 'open', '--base', integration, '--limit', '100',
  '--json', 'number,title,labels,files,isDraft,baseRefName,author,isCrossRepository']);

export function areaWatch({ gh, log = () => {}, alert = () => {}, resolve = () => {}, list = () => listOpen(gh), statePath = areaStatePath(), nowIso = new Date().toISOString() }) {
  const state = readJson(statePath, { seen: {}, alerted: [] });
  const labelled = [];
  const left = [];
  for (const pr of unlabelled(list())) {
    const files = paths(pr);
    if (files.length && files.every(workflowPath)) {
      gh.raw(['pr', 'edit', String(pr.number), '--repo', repo, '--add-label', 'area:ops']);
      log(`#${pr.number} không có nhãn area và chỉ đổi file quy trình: đã gắn area:ops`);
      labelled.push(pr.number);
    } else if (classifyArea(pr) === 'feature') left.push(pr.number);
  }
  const seen = Object.fromEntries(left.map(n => [n, state.seen?.[n] ?? nowIso]));
  const stale = left.filter(n => state.seen?.[n]).sort((a, b) => a - b);
  let alerted = state.alerted ?? [];
  if (stale.length && stale.join(',') !== alerted.join(',')) {
    alert(`${stale.length} PR vào collab/integration chưa có nhãn area, tiêu đề cũng không cho biết nhóm, nên vòng xếp vào nhóm cuối và có thể không bao giờ tới lượt: ${stale.map(n => `#${n}`).join(', ')}. Gắn một trong ${areaLabels.join(', ')}.`);
    alerted = stale;
  } else if (!stale.length && alerted.length) {
    resolve(`Không còn PR nào thiếu nhãn area mà bị xếp vào nhóm cuối.`);
    alerted = [];
  }
  writeJson(statePath, { seen, alerted });
  return { labelled, unlabelled: left, alerted };
}
