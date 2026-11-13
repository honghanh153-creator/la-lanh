// Disagreement log for the 3+3 day workflow experiment (docs/operations/workflow-experiment-2026-11.md).
// Arm 1 (Claude's way, 14–16.11): Claude records each disagreement with Codex itself. The nightly
// audit reads this file and checks it against the PR comments, so an unrecorded disagreement shows
// up as a gap (metric M8). Arm 2 replaces Claude's own entry with a record made by the program.
// Usage: node scripts/collab-disagree.mjs --add --pr N --claude "…" --codex "…" --winner codex|claude|owner [--note "…"]
//        node scripts/collab-disagree.mjs --list [--date YYYY-MM-DD]
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { clean, stateDir, vnNow } from './collab-trust.mjs';

export const logPath = join(stateDir, 'disagreements.jsonl');
export const winners = ['codex', 'claude', 'owner'];

export function entry({ pr, claude, codex, winner, note = '', at = new Date(), date = vnNow(at).date }) {
  const n = Number(pr);
  if (!Number.isInteger(n) || n <= 0) throw new Error('--pr must be a PR number');
  if (!String(claude ?? '').trim() || !String(codex ?? '').trim()) throw new Error('both positions are required');
  if (!winners.includes(winner)) throw new Error(`--winner must be one of ${winners.join(', ')}`);
  return { at: at.toISOString(), date, pr: n, claude: clean(claude, 600), codex: clean(codex, 600), winner, ...(note ? { note: clean(note, 300) } : {}) };
}

export function append(e, path = logPath) {
  mkdirSync(dirname(path), { recursive: true });
  appendFileSync(path, `${JSON.stringify(e)}\n`);
  return e;
}

export function read(path = logPath) {
  if (!existsSync(path)) return [];
  return readFileSync(path, 'utf8').split('\n').filter(Boolean).map(line => { try { return JSON.parse(line); } catch { return null; } }).filter(Boolean);
}

const flag = (args, name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  try {
    if (args.includes('--add')) {
      const e = append(entry({ pr: flag(args, '--pr'), claude: flag(args, '--claude'), codex: flag(args, '--codex'), winner: flag(args, '--winner'), note: flag(args, '--note') }));
      process.stdout.write(`${JSON.stringify(e)}\n`);
    } else if (args.includes('--list')) {
      const date = flag(args, '--date');
      for (const e of read().filter(e => !date || e.date === date)) process.stdout.write(`${JSON.stringify(e)}\n`);
    } else { process.stderr.write('Usage: collab-disagree.mjs --add --pr N --claude … --codex … --winner codex|claude|owner | --list [--date D]\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-disagree: ${error.message}\n`); process.exitCode = 1; }
}
