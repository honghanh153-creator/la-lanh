// launchd entry for the collab safety net: one tick (plan, owner gate, merges, Codex reviews).
// Kept apart from collab-turn.mjs because codex-review.mjs imports collab-turn.mjs.
import { pathToFileURL } from 'node:url';
import { runReview } from './codex-review.mjs';
import { runMerge } from './collab-merge.mjs';
import { runCheckInClone } from './collab-check.mjs';
import { clean, makeGh } from './collab-trust.mjs';
import { opsAlert, tick } from './collab-turn.mjs';

export function runTick(gh = makeGh()) {
  return tick({ gh, check: n => runCheckInClone(n, { gh }), review: (n, o) => runReview(n, { ...o, gh }), merge: n => runMerge(n, { gh }), alert: text => opsAlert(gh, text) });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv.includes('--self-test')) {
    // Proves the entry loads all modules without hanging; touches nothing.
    process.stdout.write('collab-tick ok\n');
  } else {
    try { process.stdout.write(`${new Date().toISOString()} ${JSON.stringify(runTick())}\n`); }
    catch (error) { process.stderr.write(`collab-tick failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
  }
}
