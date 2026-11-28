import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { agentMarker, stateDir, trustedComments } from './collab-trust.mjs';

const fixedMark = `${agentMarker} fallback pr=`;
// Codex r1 on #894 (P1): the comment alone was the provenance, posted after the push; a failed comment
// left a Codex-fixed head that needed no second critic. The local record is written before the push
// (no record, no push) and counts on its own. An unreadable record throws: the gate fails closed.
export const fallbackRunsPath = (home = stateDir) => join(home, 'fallback-runs.jsonl');
export function fallbackRuns(home = stateDir) {
  let text;
  try { text = readFileSync(fallbackRunsPath(home), 'utf8'); }
  catch (error) { if (error?.code === 'ENOENT') return []; throw new Error('fallback-runs.jsonl không đọc được: coi như PR nào cũng có thể do Codex sửa'); }
  return text.split('\n').filter(Boolean).map(line => { try { return JSON.parse(line); } catch { return null; } }).filter(Boolean);
}
export const codexFixed = (pr, runs = fallbackRuns()) => trustedComments(pr.comments).some(c => String(c.body ?? '').includes(fixedMark))
  || runs.some(r => Number(r.pr) === Number(pr.number));
