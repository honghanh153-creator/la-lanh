// launchd entry for the collab safety net: one tick (plan, owner gate, merges, Codex reviews).
// Kept apart from collab-turn.mjs because codex-review.mjs imports collab-turn.mjs.
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { runReview } from './codex-review.mjs';
import { runMerge } from './collab-merge.mjs';
import { runCheckInClone } from './collab-check.mjs';
import { clean, makeGh } from './collab-trust.mjs';
import { opsAlert, tick } from './collab-turn.mjs';

// Tools the loop and pnpm check need. A missing one used to surface as a false FAIL receipt
// (31.10.2026: sha256sum, pnpm); now the tick stops with an error and alerts instead.
export const requiredTools = ['pnpm', 'node', 'uv', 'make', 'sha256sum', 'gh'];
export function missingTools(path = process.env.PATH, run = execFileSync) {
  return requiredTools.filter(tool => {
    try { run('/bin/sh', ['-c', `command -v ${tool}`], { env: { PATH: path }, stdio: 'ignore' }); return false; } catch { return true; }
  });
}

export function runTick(gh = makeGh(), preflight = () => missingTools()) {
  return tick({ gh, preflight, check: (n, o) => runCheckInClone(n, { ...o, gh }), review: (n, o) => runReview(n, { ...o, gh }), merge: n => runMerge(n, { gh }), alert: text => opsAlert(gh, text) });
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
