import type { Locator, Page } from "@playwright/test";

// Acceptance criteria against the screen (lesson L04; agreement 12.11 item B: "test xanh nhưng
// mất phần tổng hợp vẫn bị ghi chưa đạt"). Each automated state of docs/operations/feature-map.json
// may list `ac_checks`; each check is judged on the real page (DOM) after the state is ready.
// Plan critiqued by Codex on 14.11 (SỬA), points taken:
// - a check proves only the part it names (`part`); what the screen cannot prove (for example
//   that the synthesis is built from the right chart facts) is written in `manual` and reported
//   as not automated, never as met;
// - results come from the browser per state and width, with the selector and the screenshot of the
//   run; a configured check whose content is missing is "not-met" and fails the run.
// Claude writes the checks, Codex reviews them (Codex 14.11).

export type Selector = { role: string; name?: string; exact?: boolean; within?: Selector; source?: string };
export type AcCheck = {
  ac: string;
  part: string;
  expect?: Selector;
  text?: string;
  count?: { selector: Selector; min?: number; max?: number };
  manual?: string;
};
export type AcResult = { ac: string; part: string; check: string; result: "met" | "not-met" | "manual" | "not-run"; detail?: string; manual?: string };

export function locateAll(page: Page, selector: Selector): Locator {
  const scope: Page | Locator = selector.within ? locate(page, selector.within) : page;
  const options = selector.name === undefined ? {} : { name: selector.name, exact: selector.exact ?? false };
  return scope.getByRole(selector.role as Parameters<Page["getByRole"]>[0], options);
}
export const locate = (page: Page, selector: Selector): Locator => locateAll(page, selector).first();

export const describeSelector = (s: Selector): string => `${s.within ? `${describeSelector(s.within)} > ` : ""}${s.role}${s.name ? ` "${s.name}"` : ""}`;
const describe = (c: AcCheck) => (c.count
  ? `count(${describeSelector(c.count.selector)}) in ${c.count.min ?? 0}..${c.count.max ?? "∞"}`
  : c.expect ? `${describeSelector(c.expect)}${c.text ? ` contains "${c.text}"` : ""}` : "manual");
const squash = (text: string) => text.normalize("NFC").replace(/\s+/g, " ").trim();

export async function runAcChecks(page: Page, checks: AcCheck[], { timeoutMs = 3_000 } = {}): Promise<AcResult[]> {
  const out: AcResult[] = [];
  for (const check of checks) {
    const base = { ac: check.ac, part: check.part, check: describe(check), ...(check.manual ? { manual: check.manual } : {}) };
    if (!check.expect && !check.count) { out.push({ ...base, result: "manual" }); continue; }
    try {
      if (check.count) {
        const n = await locateAll(page, check.count.selector).count();
        const ok = n >= (check.count.min ?? 0) && n <= (check.count.max ?? Number.POSITIVE_INFINITY);
        out.push({ ...base, result: ok ? "met" : "not-met", detail: `${n} found` });
        continue;
      }
      const target = locate(page, check.expect!);
      await target.waitFor({ state: "visible", timeout: timeoutMs });
      if (check.text !== undefined) {
        const seen = squash(await target.innerText());
        const ok = seen.includes(squash(check.text));
        out.push({ ...base, result: ok ? "met" : "not-met", ...(ok ? {} : { detail: "text not on screen" }) });
      } else out.push({ ...base, result: "met" });
    } catch {
      out.push({ ...base, result: "not-met", detail: "not visible" });
    }
  }
  return out;
}
