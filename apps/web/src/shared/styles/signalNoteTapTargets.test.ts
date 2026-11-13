import { describe, expect, it } from "vitest";

import signalNoteStyles from "./signal-note.css?raw";

// US-01 AC26 / AC12: product tap targets are at least 44×44 CSS px (2.75rem at 16px root).
const MIN_REM = 2.75;
const css = signalNoteStyles.replace(/\/\*[\s\S]*?\*\//g, "");

function declarations(selector: string): string {
  const rules = [...css.matchAll(/([^{}@]+)\{([^{}]*)\}/g)];
  const rule = rules.find(([, sel]) => sel.trim().replace(/\s+/g, " ") === selector);
  if (!rule) throw new Error(`missing rule ${selector}`);
  return rule[2];
}

function rem(block: string, property: string): number {
  const match = new RegExp(`(?:^|[;\\s])${property}:\\s*([\\d.]+)rem`).exec(block);
  if (!match) throw new Error(`missing ${property}`);
  return Number(match[1]);
}

describe("signal-note tap targets", () => {
  it("gives the thumbs and share buttons a 44px hit area", () => {
    const block = declarations(".note-quick-actions button, .note-quick-actions a");
    expect(rem(block, "width")).toBeGreaterThanOrEqual(MIN_REM);
    expect(rem(block, "height")).toBeGreaterThanOrEqual(MIN_REM);
  });

  it("gives the mood trigger a 44px hit area", () => {
    expect(rem(declarations(".mood-quick-trigger"), "min-height")).toBeGreaterThanOrEqual(MIN_REM);
  });

  it("keeps the footer detail link and daily utility link at 44px", () => {
    expect(rem(declarations(".signal-note-paper__footer .signal-note-paper__detail"), "min-height")).toBeGreaterThanOrEqual(MIN_REM);
    expect(rem(declarations(".home-daily-signal__utility > a"), "min-height")).toBeGreaterThanOrEqual(MIN_REM);
  });

  it("reserves room for the wider quick-action toolbar so the mode label does not run under it", () => {
    const toolbar = 3 * MIN_REM + 2 * rem(declarations(".note-quick-actions"), "gap");
    for (const selector of [
      ".signal-note-paper .reading-content__toolbar + .reading-mode",
      ".signal-note-paper--legacy > .reading-mode",
    ]) {
      const reserved = /max-width:\s*calc\(100% - ([\d.]+)rem\)/.exec(declarations(selector));
      expect(reserved, selector).not.toBeNull();
      expect(Number(reserved![1])).toBeGreaterThanOrEqual(toolbar);
    }
  });
});
