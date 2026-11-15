#!/usr/bin/env node
// Verification run: walks features of the web app like a user, on fake data, and reports.
//
//   node scripts/verify/verify.mjs --features <ids|all> [--widths 360,390] [--out dir]
//   node scripts/verify/verify.mjs --changed [base]     # features touched by the diff vs base
//   node scripts/verify/verify.mjs --list               # feature ids from the map
//
// Fixed steps live here and in apps/web/tests/verify; only judging the screenshots is left to the
// agent (skill: .claude/skills/verify-la-lanh). Per feature/state/width it captures a full-page
// PNG, console errors, failed requests, an axe-core scan and an overlap/clipped-text check, then
// writes report.json + summary.md. Exit 0 = pass, 1 = findings, 2 = usage or setup problem,
// 3 = another heavy check is running.
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { isMain } from "../is-main.mjs";

import { automatedStates, featuresForChangedFiles, loadMap, REPO_ROOT } from "./feature-map.mjs";

const WEB_ROOT = join(REPO_ROOT, "apps/web");
const SERIOUS = new Set(["critical", "serious"]);

export const USAGE = `Usage: node scripts/verify/verify.mjs [--features <ids|all>] [--changed [base]] [--widths 360,390] [--out dir]
                                   [--reuse-build] [--allow-concurrent] [--list]
  --features        comma-separated feature ids from docs/operations/feature-map.json, or "all" (default)
  --changed [base]  pick features from files changed vs base (default origin/collab/integration) + working tree
  --widths          viewport widths in px (default 360,390); height is 844
  --out             output folder (default apps/web/test-results/verify/<timestamp>)
  --reuse-build     serve the existing apps/web/dist instead of building again
  --allow-concurrent  skip the "another playwright/vitest/pnpm check is running" guard
  --list            print feature ids and exit`;

export function parseArgs(argv) {
  const options = { features: null, changed: null, widths: [360, 390], out: null, reuseBuild: false, allowConcurrent: false, list: false, help: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      const value = argv[i + 1];
      if (value === undefined || value.startsWith("--")) throw new Error(`${arg} needs a value`);
      i += 1;
      return value;
    };
    if (arg === "--features") options.features = next().split(",").map((id) => id.trim()).filter(Boolean);
    else if (arg === "--changed") {
      const value = argv[i + 1];
      options.changed = value && !value.startsWith("--") ? (i += 1, value) : "origin/collab/integration";
    } else if (arg === "--widths") {
      options.widths = next().split(",").map((value) => Number(value.trim()));
      if (!options.widths.length || options.widths.some((width) => !Number.isInteger(width) || width < 240 || width > 2000)) {
        throw new Error("--widths must be whole pixel widths between 240 and 2000");
      }
    } else if (arg === "--out") options.out = next();
    else if (arg === "--reuse-build") options.reuseBuild = true;
    else if (arg === "--allow-concurrent") options.allowConcurrent = true;
    else if (arg === "--list") options.list = true;
    else if (arg === "--help" || arg === "-h") options.help = true;
    else throw new Error(`unknown argument ${arg}`);
  }
  if (options.features && options.changed) throw new Error("use --features or --changed, not both");
  return options;
}

export function resolveFeatureIds(map, requested) {
  const known = map.features.map((feature) => feature.id);
  if (!requested || requested.includes("all")) return known;
  const unknown = requested.filter((id) => !known.includes(id));
  if (unknown.length) throw new Error(`unknown feature id(s): ${unknown.join(", ")}. Known: ${known.join(", ")}`);
  return requested;
}

/** Judge one raw record from verify.spec.ts: failures block, warnings are for the reader. */
export function judge(record) {
  const failures = [];
  const warnings = [];
  if (!record.ready) failures.push(`did not reach ${record.ready_selector}: ${record.walk_error ?? "unknown error"}`);
  if (record.tool_error) failures.push(`check tool error: ${record.tool_error}`);
  for (const error of record.page_errors ?? []) failures.push(`page error: ${error}`);
  for (const error of record.console_errors ?? []) failures.push(`console error: ${error}`);
  for (const request of record.failed_requests ?? []) failures.push(`failed request: ${request}`);
  for (const request of record.http_errors ?? []) failures.push(`http error: ${request}`);
  for (const violation of record.axe ?? []) {
    const line = `a11y ${violation.impact ?? "unknown"} ${violation.id}: ${violation.help} (${violation.nodes} node${violation.nodes === 1 ? "" : "s"}: ${violation.targets.join(" | ")})`;
    (SERIOUS.has(violation.impact) ? failures : warnings).push(line);
  }
  for (const finding of record.layout?.findings ?? []) {
    if (finding.kind === "overlap") failures.push(`overlap: ${finding.control} covers text "${finding.text}" (${finding.detail})`);
    else failures.push(`${finding.kind} text: "${finding.text}" (${finding.detail})`);
  }
  if (record.layout?.horizontalOverflow > 0) failures.push(`page scrolls sideways by ${record.layout.horizontalOverflow}px`);
  for (const call of record.unmocked ?? []) warnings.push(`no fake answer for ${call} (got 503)`);
  for (const call of record.external_requests ?? []) warnings.push(`request to another host: ${call}`);
  return { status: failures.length ? "fail" : "pass", failures, warnings };
}

function mergeByText(entries) {
  const merged = new Map();
  for (const { text, tag } of entries) {
    if (!merged.has(text)) merged.set(text, new Set());
    merged.get(text).add(tag);
  }
  return [...merged].map(([text, tags]) => `[${[...tags].join(", ")}] ${text}`);
}

export function buildReport(map, featureIds, records, meta) {
  const features = featureIds.map((id) => {
    const feature = map.features.find((entry) => entry.id === id);
    const expected = automatedStates(feature).flatMap(([state]) => meta.widths.map((width) => ({ state, width })));
    const runs = expected.map(({ state, width }) => {
      const record = records.find((entry) => entry.feature === id && entry.state === state && entry.width === width);
      if (!record) return { state, width, status: "fail", failures: ["no result recorded (the test crashed or was skipped)"], warnings: [], screenshot: null };
      return { state, width, url: record.url, fixture: record.fixture, screenshot: record.screenshot, ...judge(record) };
    });
    const tag = (run) => `${run.state} @${run.width}`;
    return {
      id,
      title: feature.title,
      us: feature.us,
      owner_only: feature.owner_only,
      status: runs.some((run) => run.status === "fail") ? "fail" : "pass",
      reasons: mergeByText(runs.flatMap((run) => run.failures.map((text) => ({ text, tag: tag(run) })))),
      warnings: mergeByText(runs.flatMap((run) => run.warnings.map((text) => ({ text, tag: tag(run) })))),
      manual_states: Object.entries(feature.states).filter(([, spec]) => spec.manual).map(([state, spec]) => ({ state, check: spec.manual })),
      runs,
    };
  });
  const failed = features.filter((feature) => feature.status === "fail").length;
  return {
    generated_at: meta.generatedAt,
    commit: meta.commit,
    widths: meta.widths,
    status: failed ? "fail" : "pass",
    totals: { features: features.length, passed: features.length - failed, failed, runs: features.reduce((sum, feature) => sum + feature.runs.length, 0) },
    features,
  };
}

export function renderMarkdown(report) {
  const lines = [
    `# Verification run — ${report.status === "pass" ? "PASS" : "FAIL"}`,
    "",
    `Commit \`${report.commit}\` · widths ${report.widths.join(", ")}px · ${report.totals.passed}/${report.totals.features} features pass · ${report.totals.runs} runs · fake data only`,
    "",
    "| Feature | Result | Failures | Warnings |",
    "| --- | --- | --- | --- |",
    ...report.features.map((feature) => `| \`${feature.id}\`${feature.owner_only ? " (owner-only copy)" : ""} | ${feature.status === "pass" ? "pass" : "**fail**"} | ${feature.reasons.length} | ${feature.warnings.length} |`),
    "",
  ];
  for (const feature of report.features) {
    if (!feature.reasons.length && !feature.warnings.length) continue;
    lines.push(`## ${feature.id} — ${feature.title}`, "");
    for (const reason of feature.reasons) lines.push(`- FAIL ${reason}`);
    for (const warning of feature.warnings) lines.push(`- warn ${warning}`);
    const shots = feature.runs.filter((run) => run.screenshot).map((run) => `[${run.state} @${run.width}](${run.screenshot})`);
    if (shots.length) lines.push(`- screenshots: ${shots.join(" · ")}`);
    lines.push("");
  }
  const manual = report.features.flatMap((feature) => feature.manual_states.map((entry) => `- \`${feature.id}\` ${entry.state}: ${entry.check}`));
  if (manual.length) lines.push("## Not automated (check by hand when the diff touches them)", "", ...manual, "");
  return `${lines.join("\n")}\n`;
}

function ancestorPids() {
  const pids = new Set([String(process.pid)]);
  let pid = String(process.ppid);
  for (let depth = 0; pid && pid !== "0" && pid !== "1" && depth < 32; depth += 1) {
    pids.add(pid);
    try {
      pid = execFileSync("ps", ["-o", "ppid=", "-p", pid], { encoding: "utf8" }).trim();
    } catch {
      break;
    }
  }
  return pids;
}

function otherHeavyJobs() {
  try {
    const out = execFileSync("pgrep", ["-fl", "playwright|vitest|pnpm check"], { encoding: "utf8" });
    const mine = ancestorPids();
    return out.split("\n").map((line) => line.trim()).filter(Boolean).filter((line) => !mine.has(line.split(/\s+/)[0]));
  } catch {
    return [];
  }
}

function changedFiles(base) {
  const git = (...args) => execFileSync("git", args, { cwd: REPO_ROOT, encoding: "utf8" }).split("\n").filter(Boolean);
  return [...new Set([
    ...git("diff", "--name-only", `${base}...HEAD`),
    ...git("diff", "--name-only", "HEAD"),
    ...git("ls-files", "--others", "--exclude-standard"),
  ])];
}

function main(argv) {
  let options;
  try {
    options = parseArgs(argv);
  } catch (error) {
    console.error(`verify: ${error.message}\n${USAGE}`);
    return 2;
  }
  if (options.help) {
    console.log(USAGE);
    return 0;
  }
  const map = loadMap();
  if (options.list) {
    for (const feature of map.features) console.log(`${feature.id.padEnd(26)} ${feature.routes.join(" ") || "(no route)"}  ${feature.title}`);
    return 0;
  }

  let featureIds;
  try {
    if (options.changed) {
      const picked = featuresForChangedFiles(map, changedFiles(options.changed));
      if (picked.all) console.log(`verify: shared files changed (${picked.shared.slice(0, 5).join(", ")}${picked.shared.length > 5 ? ", …" : ""}); running all features`);
      if (!picked.ids.length) {
        console.log(`verify: no web feature touched vs ${options.changed}; nothing to run`);
        return 0;
      }
      featureIds = picked.ids;
    } else {
      featureIds = resolveFeatureIds(map, options.features);
    }
  } catch (error) {
    console.error(`verify: ${error.message}`);
    return 2;
  }

  if (!options.allowConcurrent) {
    const busy = otherHeavyJobs();
    if (busy.length) {
      console.error("verify: another heavy check is running; wait for it or pass --allow-concurrent:");
      for (const line of busy.slice(0, 5)) console.error(`  ${line.slice(0, 160)}`);
      return 3;
    }
  }

  const cli = join(WEB_ROOT, "node_modules/@playwright/test/cli.js");
  if (!existsSync(cli)) {
    console.error("verify: Playwright is not installed; run pnpm install --frozen-lockfile first");
    return 2;
  }
  if (options.reuseBuild && !existsSync(join(WEB_ROOT, "dist/index.html"))) {
    console.error("verify: --reuse-build needs apps/web/dist; run once without it");
    return 2;
  }

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const outDir = resolve(options.out ?? join(WEB_ROOT, "test-results/verify", stamp));
  mkdirSync(outDir, { recursive: true });
  rmSync(join(outDir, "raw"), { recursive: true, force: true });
  console.log(`verify: ${featureIds.length} feature(s) at ${options.widths.join(", ")}px → ${relative(REPO_ROOT, outDir)}`);

  const run = spawnSync(process.execPath, [cli, "test", "-c", "tests/verify/verify.config.ts"], {
    cwd: WEB_ROOT,
    stdio: "inherit",
    env: {
      ...process.env,
      VERIFY_FEATURES: featureIds.join(","),
      VERIFY_WIDTHS: options.widths.join(","),
      VERIFY_OUT: outDir,
      VERIFY_REUSE_SERVER: options.reuseBuild ? "1" : "0",
    },
  });

  const rawDir = join(outDir, "raw");
  const records = existsSync(rawDir)
    ? readdirSync(rawDir).filter((name) => name.endsWith(".json")).map((name) => JSON.parse(readFileSync(join(rawDir, name), "utf8")))
    : [];
  let commit = "unknown";
  try {
    commit = execFileSync("git", ["rev-parse", "--short", "HEAD"], { cwd: REPO_ROOT, encoding: "utf8" }).trim();
  } catch { /* not a git checkout */ }
  const report = buildReport(map, featureIds, records, { generatedAt: new Date().toISOString(), commit, widths: options.widths });
  if (run.status !== 0 && !records.length) {
    console.error("verify: the Playwright run failed before any feature was recorded (build or server problem?)");
    return 2;
  }
  writeFileSync(join(outDir, "report.json"), `${JSON.stringify(report, null, 2)}\n`);
  writeFileSync(join(outDir, "summary.md"), renderMarkdown(report));
  console.log(`verify: ${report.status.toUpperCase()} — ${report.totals.passed}/${report.totals.features} features pass`);
  for (const feature of report.features.filter((entry) => entry.status === "fail")) {
    console.log(`  ✗ ${feature.id}: ${feature.reasons[0]}${feature.reasons.length > 1 ? ` (+${feature.reasons.length - 1} more)` : ""}`);
  }
  console.log(`verify: report ${relative(REPO_ROOT, join(outDir, "report.json"))}, summary ${relative(REPO_ROOT, join(outDir, "summary.md"))}`);
  return report.status === "pass" ? 0 : 1;
}

if (isMain(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
