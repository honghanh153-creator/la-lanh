import { readFileSync } from "node:fs";

import { expect, test } from "@playwright/test";

import { locate, runAcChecks, type AcCheck, type Selector } from "../verify/ac-check";
import { insightsReady, mockApi } from "../verify/fixtures";

// Lesson L04 (agreement 12.11 item B): a screen that reached its ready state but lost the content an
// acceptance criterion needs is recorded as "chưa đạt". The AC results come from this real browser
// page and are judged by the real judge() of scripts/verify/verify.mjs (no hand-made record).
// Synthetic data only (tests/verify/fixtures.ts).
type Feature = { id: string; states: Record<string, { ready: Selector; ac_checks?: AcCheck[] }> };
const map = JSON.parse(readFileSync(new URL("../../../../docs/operations/feature-map.json", import.meta.url), "utf8")) as { features: Feature[] };
const unlocked = map.features.find((feature) => feature.id === "insights")!.states.unlocked;
const verifyModule = new URL("../../../../scripts/verify/verify.mjs", import.meta.url).href;

async function record(page: import("@playwright/test").Page) {
  // Ready the way a run sees the page: the reading switch is on screen, so the state rendered.
  const ready = await locate(page, { role: "region", name: "Chọn hệ đọc" }).isVisible();
  const ac = await runAcChecks(page, unlocked.ac_checks ?? []);
  const { judge } = (await import(verifyModule)) as { judge: (r: unknown) => { status: string; failures: string[] } };
  return { ready, ac, verdict: judge({ ready, ready_selector: "region \"Chọn hệ đọc\"", ac }) };
}

test("a ready screen without the synthesis is recorded as not met for its AC", async ({ page }) => {
  await mockApi(page, "signed-in-deep");
  await page.goto("/insights");
  await expect(locate(page, unlocked.ready)).toBeVisible();
  const full = await record(page);
  expect(full.ready).toBe(true);
  expect(full.ac.filter((r) => r.result === "not-met"), "every configured check is met on the full screen").toEqual([]);
  expect(full.ac.find((r) => r.ac === "US-07 AC06")?.result, "a check with only a manual note is not called met").toBe("manual");
  expect(full.verdict.status).toBe("pass");

  // Same page, same green ready state, but the API answer lost its synthesis.
  await page.route("**/v1/insights/overview**", (route) => route.fulfill({ status: 200, json: { ...insightsReady, reading_projection: null } }));
  await page.goto("/insights");
  await expect(locate(page, { role: "region", name: "Chọn hệ đọc" })).toBeVisible();
  const dropped = await record(page);
  expect(dropped.ready, "the state still looks ready").toBe(true);
  expect(dropped.ac.find((r) => r.ac === "US-07 AC01")?.result).toBe("not-met");
  expect(dropped.verdict.status).toBe("fail");
  expect(dropped.verdict.failures.join("\n")).toMatch(/^AC US-07 AC01 chưa đạt: /m);
});
