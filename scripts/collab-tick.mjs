// launchd entry for the collab safety net: one tick (plan, owner gate, merges, Codex reviews).
// Kept apart from collab-turn.mjs because codex-review.mjs imports collab-turn.mjs.
import { execFileSync } from 'node:child_process';
import { runReview } from './codex-review.mjs';
import { dailyReceiptAudit, runMerge } from './collab-merge.mjs';
import { ciCheck, heavyJobFree, runCheckInClone } from './collab-check.mjs';
import { incidentPreflightAlert, incidentPreflightSubject, runPreflight } from './collab-preflight.mjs';
import { clean, makeGh, vnNow } from './collab-trust.mjs';
import { opsAlert, resolveOpsAlert, tick } from './collab-turn.mjs';
import { postOwnerNotes, renderBoard, upsertBoard } from './collab-status.mjs';
import { collectMetrics, renderMetrics } from './collab-metrics.mjs';
import { realSources } from './collab-snapshot.mjs';
import { planIssue } from './collab-plan.mjs';
import { healthLines, readBeats, watch } from './collab-watchdog.mjs';
import { alertMissed, ghIssues } from './collab-missed-run.mjs';
import { pendingCount, readSaved, runCopyBatch, savedPath } from './codex-copy-review.mjs';
import { hookHealth } from './collab-hooks.mjs';
import { agentGateWatch, gateAlertSubject, rulesHookAlertSubject, rulesHookHealth, rulesHookWatch, rulesSheetHealth, skillRuleHealth, wrapperHealth } from './collab-ops-wrapper.mjs';
import { runMergeAudit } from './collab-merge-audit.mjs';
import { isMain } from './is-main.mjs';
import { loadAuditDeps } from './collab-audit.mjs';
import { runNightAudit } from './collab-audit-night.mjs';

const auditDeps = await loadAuditDeps();
// The tick's night audit, with the promise register and the disagreement log (L22) wired in.
export const nightAudit = (gh, opts = {}) => runNightAudit({ gh, issue: () => planIssue(gh), ...auditDeps, ...opts });

// Tools the loop and pnpm check need. A missing one used to surface as a false FAIL receipt
// (31.10.2026: sha256sum, pnpm); now the tick stops with an error and alerts instead.
export const requiredTools = ['pnpm', 'node', 'uv', 'make', 'sha256sum', 'gh'];
export function missingTools(path = process.env.PATH, run = execFileSync) {
  return requiredTools.filter(tool => {
    try { run('/bin/sh', ['-c', `command -v ${tool}`], { env: { PATH: path }, stdio: 'ignore' }); return false; } catch { return true; }
  });
}

// #292: tick() logs failed deliveries (idle alert) through log(); without one they vanished.
// stderr lands in the launchd error log next to the stdout result line.
export function tickLog(line, write = text => process.stderr.write(text)) {
  write(`${new Date().toISOString()} collab-tick: ${clean(String(line), 2000)}\n`);
}

const watchdogSubject = 'tác vụ hẹn giờ bị treo';
const receiptSubject = 'merge thiếu biên nhận';

export function runTick(gh = makeGh(), preflight = () => missingTools(), { run = tick, log = tickLog, gateWatch = agentGateWatch, rulesWatch = rulesHookWatch, incidentAlert = incidentPreflightAlert } = {}) {
  const board = info => upsertBoard(gh, planIssue(gh), renderBoard(info));
  return run({ gh, preflight, log, prPreflight: n => {
      const pr = gh.pr(n);
      const result = runPreflight(pr);
      try { incidentAlert(pr, result, text => opsAlert(gh, text, incidentPreflightSubject)); } catch {}
      return result;
    }, heavyFree: () => heavyJobFree(), board, check: (n, o) => runCheckInClone(n, { ...o, gh }), ciStatus: head => ciCheck(gh, head), review: (n, o) => runReview(n, { ...o, gh }), merge: n => runMerge(n, { gh }), alert: text => opsAlert(gh, text),
    watchdog: () => {
      try { alertMissed({ beats: readBeats(), issues: ghIssues(gh.raw) }); } catch {}
      // P1-B: once a day, any merge of the last 24 hours without signed evidence opens an ops alert.
      try { dailyReceiptAudit({ gh, alert: text => opsAlert(gh, text, receiptSubject), now: vnNow() }); } catch {}
      // L06: the sub-agent gate hooks are still installed and on (one alert a day, closed when fixed).
      try { gateWatch({ alert: text => opsAlert(gh, text, gateAlertSubject), resolve: text => resolveOpsAlert(gh, text, gateAlertSubject), today: vnNow().date }); } catch {}
      // L37: the owner-rules hook (re-load of the rules sheet, R3 deny) is installed and passes its selftest.
      try { rulesWatch({ alert: text => opsAlert(gh, text, rulesHookAlertSubject), resolve: text => resolveOpsAlert(gh, text, rulesHookAlertSubject), today: vnNow().date }); } catch {}
      return watch({ alert: text => opsAlert(gh, text, watchdogSubject), resolve: text => resolveOpsAlert(gh, text, watchdogSubject) });
    }, health: () => [...healthLines(readBeats()), ...hookHealth(), ...wrapperHealth(), ...skillRuleHealth(), ...rulesSheetHealth(), ...rulesHookHealth()], copyPending: () => pendingCount(), copyBatch: () => runCopyBatch(), copySaved: () => Boolean(readSaved(savedPath, vnNow().date)),
    notify: (notes, comments) => postOwnerNotes(gh, planIssue(gh), notes, comments),
    metrics: ({ prs, turns }) => renderMetrics(collectMetrics({ gh, prs, turns })),
    audit: () => nightAudit(gh),
    incidents: () => realSources(gh, vnNow().date).alerts(),
    mergeAudit: options => runMergeAudit(options) });
}

if (isMain(import.meta.url)) {
  if (process.argv.includes('--self-test')) {
    // Proves the entry loads all modules without hanging; touches nothing.
    process.stdout.write('collab-tick ok\n');
  } else {
    try { process.stdout.write(`${new Date().toISOString()} ${JSON.stringify(runTick())}\n`); }
    catch (error) { process.stderr.write(`collab-tick failed: ${clean(error.message, 500)}\n`); process.exitCode = 1; }
  }
}
