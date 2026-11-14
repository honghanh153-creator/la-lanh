import assert from "node:assert/strict";
import { test } from "node:test";

import { buildReport, judge, parseArgs, renderMarkdown, resolveFeatureIds } from "./verify.mjs";

const clean = {
  feature: "home", state: "default", width: 390, fixture: "signed-in", url: "/home", ready: true, ready_selector: 'button "Chọn mood hôm nay"',
  walk_error: null, tool_error: null, screenshot: "screens/home__default__w390.png", console_errors: [], page_errors: [],
  failed_requests: [], aborted_requests: [], http_errors: [], unmocked: [], external_requests: [], axe: [],
  layout: { findings: [], horizontalOverflow: 0 },
};

test("parseArgs: defaults, lists and errors", () => {
  assert.deepEqual(parseArgs([]).widths, [360, 390]);
  const options = parseArgs(["--features", "home, mood", "--widths", "360,412", "--out", "x", "--reuse-build"]);
  assert.deepEqual(options.features, ["home", "mood"]);
  assert.deepEqual(options.widths, [360, 412]);
  assert.equal(options.out, "x");
  assert.equal(options.reuseBuild, true);
  assert.equal(parseArgs(["--changed"]).changed, "origin/collab/integration");
  assert.equal(parseArgs(["--changed", "origin/main"]).changed, "origin/main");
  assert.throws(() => parseArgs(["--widths", "abc"]), /whole pixel widths/);
  assert.throws(() => parseArgs(["--bogus"]), /unknown argument/);
  assert.throws(() => parseArgs(["--features", "home", "--changed"]), /not both/);
  assert.throws(() => parseArgs(["--out"]), /needs a value/);
});

test("resolveFeatureIds rejects unknown ids", () => {
  const map = { features: [{ id: "home" }, { id: "mood" }] };
  assert.deepEqual(resolveFeatureIds(map, null), ["home", "mood"]);
  assert.deepEqual(resolveFeatureIds(map, ["all"]), ["home", "mood"]);
  assert.throws(() => resolveFeatureIds(map, ["home", "nope"]), /unknown feature id\(s\): nope/);
});

test("judge: a clean run passes", () => {
  assert.deepEqual(judge(clean), { status: "pass", failures: [], warnings: [] });
});

test("judge: overlaps, console errors, serious a11y and sideways scroll fail; minor a11y and unmocked calls warn", () => {
  const verdict = judge({
    ...clean,
    console_errors: ["TypeError: x is undefined"],
    axe: [
      { id: "color-contrast", impact: "serious", help: "Contrast", nodes: 2, targets: [".a", ".b"] },
      { id: "region", impact: "moderate", help: "Landmarks", nodes: 1, targets: [".c"] },
    ],
    layout: { findings: [{ kind: "overlap", control: 'button "Đóng"', text: "Một dòng chữ", detail: "5x6px" }], horizontalOverflow: 12 },
    unmocked: ["GET /v1/new"],
  });
  assert.equal(verdict.status, "fail");
  assert.equal(verdict.failures.length, 4);
  assert.ok(verdict.failures.some((line) => line.startsWith('overlap: button "Đóng" covers text "Một dòng chữ"')));
  assert.ok(verdict.failures.some((line) => line.includes("sideways by 12px")));
  assert.deepEqual(verdict.warnings.map((line) => line.split(":")[0]), ["a11y moderate region", "no fake answer for GET /v1/new (got 503)"]);
});

test("judge: not reaching the ready selector fails with the walk error", () => {
  const verdict = judge({ ...clean, ready: false, walk_error: "Timeout 15000ms" });
  assert.deepEqual(verdict.failures, ['did not reach button "Chọn mood hôm nay": Timeout 15000ms']);
});

test("buildReport merges the same finding across widths and flags missing runs", () => {
  const map = { features: [{ id: "home", title: "Home", us: ["US-03"], owner_only: false, states: {
    default: { fixture: "signed-in", walk: [{ goto: "/home" }], ready: { role: "button" } },
    offline: { manual: "Tắt mạng." },
  } }] };
  const overlap = { ...clean, layout: { findings: [{ kind: "overlap", control: "x", text: "t", detail: "d" }], horizontalOverflow: 0 } };
  const report = buildReport(map, ["home"], [overlap, { ...overlap, width: 360 }], { generatedAt: "now", commit: "abc", widths: [360, 390] });
  assert.equal(report.status, "fail");
  assert.deepEqual(report.features[0].reasons, ['[default @360, default @390] overlap: x covers text "t" (d)']);
  assert.deepEqual(report.features[0].manual_states, [{ state: "offline", check: "Tắt mạng." }]);

  const missing = buildReport(map, ["home"], [clean], { generatedAt: "now", commit: "abc", widths: [360, 390] });
  assert.equal(missing.status, "fail");
  assert.match(missing.features[0].reasons[0], /^\[default @360\] no result recorded/);

  const passing = buildReport(map, ["home"], [clean, { ...clean, width: 360 }], { generatedAt: "now", commit: "abc", widths: [360, 390] });
  assert.equal(passing.status, "pass");
  const markdown = renderMarkdown(passing);
  assert.match(markdown, /^# Verification run — PASS/);
  assert.match(markdown, /\| `home` \| pass \| 0 \| 0 \|/);
  assert.match(markdown, /`home` offline: Tắt mạng\./);
});
