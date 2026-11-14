import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

import { runAcChecks, type AcCheck } from "./ac-check";
import { mockApi, type FixtureName } from "./fixtures";
import { layoutCheck, type LayoutFinding } from "./layout-check";

// Walks each feature in docs/operations/feature-map.json like a user and records evidence.
// Driven by scripts/verify/verify.mjs; findings never fail the Playwright test itself, they are
// written to <out>/raw/*.json and judged by the CLI. Fake data only (fixtures.ts).

type Selector = { role: string; name?: string; exact?: boolean; within?: Selector; source?: string };
type Step = { goto?: string; click?: Selector; fill?: Selector; value?: string; check?: Selector; press?: string; expect?: Selector };
type StateSpec = { fixture: FixtureName; walk: Step[]; ready: Selector; manual?: string; ac_checks?: AcCheck[] };
type Feature = { id: string; title: string; states: Record<string, StateSpec | { manual: string }> };

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../../../..");
const map = JSON.parse(readFileSync(resolve(repoRoot, "docs/operations/feature-map.json"), "utf8")) as { features: Feature[] };
const outDir = resolve(process.env.VERIFY_OUT ?? resolve(here, "../../test-results/verify"));
const wanted = (process.env.VERIFY_FEATURES ?? "all").split(",").map((id) => id.trim()).filter(Boolean);
const features = wanted.includes("all") ? map.features : map.features.filter((feature) => wanted.includes(feature.id));
mkdirSync(resolve(outDir, "raw"), { recursive: true });
mkdirSync(resolve(outDir, "screens"), { recursive: true });

function locate(page: Page, selector: Selector): Locator {
  const scope: Page | Locator = selector.within ? locate(page, selector.within) : page;
  const options = selector.name === undefined ? {} : { name: selector.name, exact: selector.exact ?? false };
  return scope.getByRole(selector.role as Parameters<Page["getByRole"]>[0], options).first();
}

async function runStep(page: Page, step: Step) {
  if (step.goto) await page.goto(step.goto);
  else if (step.click) await locate(page, step.click).click();
  else if (step.fill) await locate(page, step.fill).fill(step.value ?? "");
  else if (step.check) await locate(page, step.check).check();
  else if (step.press) await page.keyboard.press(step.press);
  else if (step.expect) await expect(locate(page, step.expect)).toBeVisible();
}

const describeSelector = (s: Selector): string => `${s.within ? `${describeSelector(s.within)} > ` : ""}${s.role}${s.name ? ` "${s.name}"` : ""}`;

for (const feature of features) {
  for (const [state, spec] of Object.entries(feature.states)) {
    if ("manual" in spec) continue;
    test(`${feature.id} › ${state}`, async ({ page }, testInfo) => {
      const width = testInfo.project.use.viewport?.width ?? 0;
      const base = `${feature.id}__${state}__w${width}`;
      const started = Date.now();
      const consoleErrors: string[] = [];
      const pageErrors: string[] = [];
      const failedRequests: string[] = [];
      const abortedRequests: string[] = [];
      const httpErrors: string[] = [];
      const externalRequests: string[] = [];
      const origin = new URL(testInfo.project.use.baseURL ?? "http://127.0.0.1").host;

      page.on("console", (message) => {
        if (message.type() !== "error") return;
        const text = message.text();
        // Network failures are judged from the response/request events below.
        if (text.startsWith("Failed to load resource")) return;
        consoleErrors.push(text.slice(0, 300));
      });
      page.on("pageerror", (error) => pageErrors.push(`${error.name}: ${error.message}`.slice(0, 300)));
      page.on("request", (request) => {
        const url = new URL(request.url());
        if (!["http:", "https:"].includes(url.protocol)) return;
        if (url.host !== origin) externalRequests.push(`${request.method()} ${url.origin}${url.pathname}`);
      });
      page.on("requestfailed", (request) => {
        const failure = request.failure()?.errorText ?? "failed";
        const url = new URL(request.url());
        const line = `${request.method()} ${url.pathname} ${failure}`;
        if (failure.includes("ERR_ABORTED")) abortedRequests.push(line);
        else failedRequests.push(line);
      });
      page.on("response", (response) => {
        const url = new URL(response.url());
        if (response.status() >= 400 && !url.pathname.startsWith("/v1/")) httpErrors.push(`${response.request().method()} ${url.pathname} ${response.status()}`);
      });

      const mockLog = await mockApi(page, spec.fixture);
      let walkError: string | null = null;
      let ready = false;
      try {
        for (const step of spec.walk) await runStep(page, step);
        await expect(locate(page, spec.ready)).toBeVisible({ timeout: 15_000 });
        ready = true;
      } catch (error) {
        walkError = (error instanceof Error ? error.message : String(error)).split("\n").slice(0, 3).join(" ").slice(0, 400);
      }
      await page.evaluate(() => document.fonts.ready).catch(() => undefined);
      await page.waitForLoadState("networkidle", { timeout: 3_000 }).catch(() => undefined);
      // L04: acceptance criteria judged on this page, this state and this width.
      const ac = ready ? await runAcChecks(page, spec.ac_checks ?? [])
        : (spec.ac_checks ?? []).map((c) => ({ ac: c.ac, part: c.part, check: "state not reached", result: "not-run" as const }));

      let layout: { findings: LayoutFinding[]; horizontalOverflow: number } = { findings: [], horizontalOverflow: 0 };
      let axe: Array<{ id: string; impact: string | null; help: string; nodes: number; targets: string[] }> = [];
      let toolError: string | null = null;
      try {
        await page.evaluate(() => window.scrollTo(0, 0));
        const top = await page.evaluate(layoutCheck, "top" as const);
        await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        await page.waitForTimeout(150);
        const bottom = await page.evaluate(layoutCheck, "bottom" as const);
        await page.evaluate(() => window.scrollTo(0, 0));
        layout = { findings: [...top.findings, ...bottom.findings], horizontalOverflow: top.horizontalOverflow };

        const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
        axe = results.violations.map((violation) => ({
          id: violation.id,
          impact: violation.impact ?? null,
          help: violation.help,
          nodes: violation.nodes.length,
          targets: violation.nodes.slice(0, 3).map((node) => node.target.join(" ")),
        }));
      } catch (error) {
        toolError = (error instanceof Error ? error.message : String(error)).slice(0, 300);
      }

      const screenshot = `screens/${base}.png`;
      await page.screenshot({ path: resolve(outDir, screenshot), fullPage: true, animations: "disabled" }).catch(() => undefined);

      const record = {
        feature: feature.id,
        title: feature.title,
        state,
        width,
        fixture: spec.fixture,
        ready_selector: describeSelector(spec.ready),
        url: new URL(page.url()).pathname,
        ready,
        walk_error: walkError,
        tool_error: toolError,
        screenshot,
        console_errors: consoleErrors,
        page_errors: pageErrors,
        failed_requests: failedRequests,
        aborted_requests: abortedRequests,
        http_errors: httpErrors,
        unmocked: Array.from(new Set(mockLog.unmocked)),
        external_requests: Array.from(new Set(externalRequests)),
        axe,
        layout,
        ac,
        duration_ms: Date.now() - started,
      };
      writeFileSync(resolve(outDir, "raw", `${base}.json`), `${JSON.stringify(record, null, 2)}\n`);
    });
  }
}
