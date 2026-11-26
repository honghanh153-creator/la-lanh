// launchd entry for the collab safety net: one tick (plan, owner gate, merges, Codex reviews).
// Kept apart from collab-turn.mjs because codex-review.mjs imports collab-turn.mjs.
import { execFileSync } from 'node:child_process';
import { runReview } from './codex-review.mjs';
import { dailyReceiptAudit, runMerge } from './collab-merge.mjs';
import { ciCheck, heavyJobFree, prepareAuthorClone, runCheckInClone, withCheckLock } from './collab-check.mjs';
import { healConflicts } from './collab-conflict-heal.mjs';
import { mayTouch, withPrLock } from './collab-pr-claim.mjs';
import { incidentPreflightAlert, incidentPreflightSubject, runPreflight } from './collab-preflight.mjs';
import { clean, lastStartAt, makeGh, vnNow } from './collab-trust.mjs';
import { opsAlert, planTurns, resolveOpsAlert, tick } from './collab-turn.mjs';
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
import { noteTickGap, tickGapSubject } from './collab-tick-gap.mjs';
import { areaWatch, areaWatchSubject } from './collab-area-label.mjs';
import { throughputTick } from './collab-throughput.mjs';
import { paceSubject, usageTick } from './collab-usage.mjs';
import { currentMode, fallbackStep } from './codex-fallback.mjs';
import { runAntigravity } from './collab-antigravity.mjs';
import { probeHolds } from './collab-merge-probe.mjs';
import { auditReceiptResult, readReceipts, receiptSummary, renderReceipts, tickReceiptResult, writeRunReceipt } from './collab-run-receipt.mjs';

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

// R9: no new loop work from 23:35. Tests inject their own runTick deps; a fake gh without openPrs is skipped.
const healTick = ({ gh, log, now = vnNow() }) => (now.hour * 60 + now.minute >= lastStartAt || typeof gh.openPrs !== 'function' ? [] : healConflicts({
  gh, log, prs: gh.openPrs(),
  prepare: (n, head) => prepareAuthorClone(n, head, execFileSync, { source: 'ci', deadlineMs: Date.now() + 10 * 60000 }),
  mayTouch: n => mayTouch(n), lock: fn => withCheckLock(fn), prLock: (n, fn) => withPrLock(n, fn, { waitMs: 0 }),
}));

export function runTick(gh = makeGh(), preflight = () => missingTools(), { run = tick, log = tickLog, gateWatch = agentGateWatch, rulesWatch = rulesHookWatch, gapNote = noteTickGap, areaNote = areaWatch, incidentAlert = incidentPreflightAlert, usageNote = usageTick, probe = probeHolds, conflictHeal = healTick, receipt = writeRunReceipt, receipts = () => renderReceipts(receiptSummary(readReceipts())) } = {}) {
  // L67: Claude usage is read once per tick, only when the board or the health block asks for it;
  // the pace alert goes out from the same read. A failed read leaves the board without the line.
  let usage;
  const usageNow = () => {
    if (usage === undefined) {
      try { usage = usageNote({ alert: text => opsAlert(gh, text, paceSubject) }); } catch (error) { usage = null; log(`usage read failed: ${clean(error.message, 200)}`); }
    }
    return usage;
  };
  const board = info => upsertBoard(gh, planIssue(gh), renderBoard({ ...info, usage: usageNow()?.line ?? null }));
  // L57: a gap since the last heartbeat is written with its cause before this tick writes its own.
  try { gapNote({ log, alert: text => opsAlert(gh, text, tickGapSubject) }); } catch (error) { log(`tick gap note failed: ${clean(error.message, 200)}`); }
  // L58: an open PR without an area label falls to the last group and is never worked; label or alert.
  try { areaNote({ gh, log, alert: text => opsAlert(gh, text, areaWatchSubject), resolve: text => resolveOpsAlert(gh, text, areaWatchSubject) }); } catch (error) { log(`area watch failed: ${clean(error.message, 200)}`); }
  // L74: a conflict only in a rule file (the lessons list) is merged by the machine before the queue
  // sends the PR to a Claude fix; Autofix in the app stays on as the fallback.
  try { conflictHeal({ gh, log }); } catch (error) { log(`conflict heal failed: ${clean(error.message, 200)}`); }
  const result = run({ gh, preflight, log, prPreflight: n => {
      const pr = gh.pr(n);
      const result = runPreflight(pr);
      try { incidentAlert(pr, result, text => opsAlert(gh, text, incidentPreflightSubject)); } catch {}
      return result;
    }, heavyFree: () => heavyJobFree(), board, check: (n, o) => runCheckInClone(n, { ...o, gh }), ciStatus: head => ciCheck(gh, head), review: (n, o) => runReview(n, { ...o, gh }), merge: n => runMerge(n, { gh, mode: usageNow()?.mode ?? currentMode() }), alert: text => opsAlert(gh, text),
    watchdog: () => {
      try { alertMissed({ beats: readBeats(), issues: ghIssues(gh.raw) }); } catch {}
      // P1-B: once a day, any merge of the last 24 hours without signed evidence opens an ops alert.
      try { dailyReceiptAudit({ gh, alert: text => opsAlert(gh, text, receiptSubject), now: vnNow() }); } catch {}
      // L06: the sub-agent gate hooks are still installed and on (one alert a day, closed when fixed).
      try { gateWatch({ alert: text => opsAlert(gh, text, gateAlertSubject), resolve: text => resolveOpsAlert(gh, text, gateAlertSubject), today: vnNow().date }); } catch {}
      // L37: the owner-rules hook (re-load of the rules sheet, R3 deny) is installed and passes its selftest.
      try { rulesWatch({ alert: text => opsAlert(gh, text, rulesHookAlertSubject), resolve: text => resolveOpsAlert(gh, text, rulesHookAlertSubject), today: vnNow().date }); } catch {}
      return watch({ alert: text => opsAlert(gh, text, watchdogSubject), resolve: text => resolveOpsAlert(gh, text, watchdogSubject) });
    }, health: () => [...healthLines(readBeats()), ...(() => { try { return [receipts()]; } catch { return []; } })(), ...hookHealth(), ...wrapperHealth(), ...skillRuleHealth(), ...rulesSheetHealth(), ...rulesHookHealth(), ...(usageNow()?.health ?? [])], copyPending: () => pendingCount(), copyBatch: () => runCopyBatch(), copySaved: () => Boolean(readSaved(savedPath, vnNow().date)),
    notify: (notes, comments) => postOwnerNotes(gh, planIssue(gh), notes, comments),
    // L72: throughput lines (Claude budget, merges, Gỡ Vướng, first-pass rates, triggers) join the outcome metrics.
    metrics: ({ prs, turns }) => [...renderMetrics(collectMetrics({ gh, prs, turns })), ...throughputTick({ gh, prs, usageNote: usageNow(), log })],
    // Research item 3: a night audit that read or judged anything leaves a receipt.
    audit: () => {
      const r = nightAudit(gh);
      const outcome = auditReceiptResult(r);
      if (outcome) {
        try { receipt({ kind: 'night-audit', result: outcome, counts: { final: r.final ? 1 : 0 } }); } catch {}
      }
      return r;
    },
    incidents: () => realSources(gh, vnNow().date).alerts(),
    mergeAudit: options => runMergeAudit(options),
    // L70: Antigravity reviews PRs Codex fixed (any mode: it costs no Claude); then the Codex fix step.
    fallback: ({ turns, prs }) => {
      let second = null;
      try { second = runAntigravity({ gh, prs, turns, log }); } catch (error) { log(`antigravity failed: ${clean(error.message, 200)}`); }
      const fix = fallbackStep({ gh, mode: usageNow()?.mode ?? currentMode(), turns, prs, log });
      return second || fix ? { second, fix } : null;
    } });
  // Research item 2 (owner 21.11): once an hour, a trial merge of every pair held only for a shared
  // file, recorded next to the hold. Observe only; it never changes a turn.
  try { probe({ list: () => planTurns(gh, vnNow()), log }); } catch (error) { log(`merge probe failed: ${clean(error.message, 200)}`); }
  // Research item 3 (owner 21.11): the tick's own receipt, with the commit of the code that ran.
  try {
    receipt({ kind: 'tick', result: tickReceiptResult(result?.status), counts: { done: Array.isArray(result?.done) ? result.done.length : 0 } });
  } catch (error) { log(`run receipt failed: ${clean(error.message, 200)}`); }
  return result;
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
