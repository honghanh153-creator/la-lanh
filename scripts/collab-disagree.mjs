// Disagreement log for the 3+3 day workflow experiment (docs/operations/workflow-experiment-2026-11.md).
// Arm 1 (Claude's way, 14–16.11): Claude records each disagreement with Codex itself. The nightly
// audit reads this file and checks it against the PR comments, so an unrecorded disagreement shows
// up as a gap (metric M8). Arm 2 replaces Claude's own entry with a record made by the program.
// Usage: node scripts/collab-disagree.mjs --add (--pr N | --task ID) --claude "…" --codex "…" --winner codex|claude|owner [--note "…"]
//        node scripts/collab-disagree.mjs --override --of <at of the entry> --winner owner|claude|codex --note "…"   (owner reverses later)
//        node scripts/collab-disagree.mjs --list [--date YYYY-MM-DD]
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { clean, stateDir, vnNow } from './collab-trust.mjs';
import { isMain } from './is-main.mjs';

export const logPath = join(stateDir, 'disagreements.jsonl');
export const winners = ['codex', 'claude', 'owner'];

// Codex 13.11: a disagreement can come before any PR exists (a plan), so a task id is accepted too.
export function entry({ pr, task, claude, codex, winner, note = '', at = new Date(), date = vnNow(at).date }) {
  const n = Number(pr);
  const ref = pr !== undefined ? (Number.isInteger(n) && n > 0 ? { pr: n } : null) : (/^[A-Za-z][\w.-]{0,40}$/.test(task ?? '') ? { task } : null);
  if (!ref) throw new Error('--pr must be a PR number, or --task an id such as L21');
  if (!String(claude ?? '').trim() || !String(codex ?? '').trim()) throw new Error('both positions are required');
  if (!winners.includes(winner)) throw new Error(`--winner must be one of ${winners.join(', ')}`);
  return { at: at.toISOString(), date, ...ref, claude: clean(claude, 600), codex: clean(codex, 600), winner, ...(note ? { note: clean(note, 300) } : {}) };
}

// The owner reversing a decision later is its own record, so the original line is never edited.
export function override({ of, winner, note, at = new Date() }) {
  if (!/^\d{4}-\d{2}-\d{2}T/.test(of ?? '')) throw new Error('--of must be the at of the original entry');
  if (!winners.includes(winner)) throw new Error(`--winner must be one of ${winners.join(', ')}`);
  if (!String(note ?? '').trim()) throw new Error('--note is required for an override');
  return { at: at.toISOString(), date: vnNow(at).date, type: 'override', of, winner, note: clean(note, 300) };
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

if (isMain(import.meta.url)) {
  const args = process.argv.slice(2);
  try {
    if (args.includes('--add')) {
      const e = append(entry({ pr: flag(args, '--pr'), task: flag(args, '--task'), claude: flag(args, '--claude'), codex: flag(args, '--codex'), winner: flag(args, '--winner'), note: flag(args, '--note') }));
      process.stdout.write(`${JSON.stringify(e)}\n`);
    } else if (args.includes('--override')) {
      process.stdout.write(`${JSON.stringify(append(override({ of: flag(args, '--of'), winner: flag(args, '--winner'), note: flag(args, '--note') })))}\n`);
    } else if (args.includes('--list')) {
      const date = flag(args, '--date');
      for (const e of read().filter(e => !date || e.date === date)) process.stdout.write(`${JSON.stringify(e)}\n`);
    } else { process.stderr.write('Usage: collab-disagree.mjs --add --pr N --claude … --codex … --winner codex|claude|owner | --list [--date D]\n'); process.exitCode = 2; }
  } catch (error) { process.stderr.write(`collab-disagree: ${error.message}\n`); process.exitCode = 1; }
}
