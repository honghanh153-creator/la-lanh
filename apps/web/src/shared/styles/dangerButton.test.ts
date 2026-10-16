import { describe, expect, it } from "vitest";

import ultravioletStyles from "./ultraviolet.css?raw";

function token(block: string, name: string): string {
  const match = new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})`).exec(block);
  if (!match) throw new Error(`missing ${name}`);
  return match[1];
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const light = ultravioletStyles.slice(0, ultravioletStyles.indexOf(':root[data-theme="dark"] {'));
const dark = ultravioletStyles.slice(ultravioletStyles.indexOf(':root[data-theme="dark"] {'));

describe("destructive confirm button", () => {
  it("is a filled danger pill, not danger text on the legacy red", () => {
    expect(ultravioletStyles).toMatch(
      /:root \.ultraviolet-app \.danger-button \{[^}]*color: #ffffff;[^}]*background: var\(--uv-danger\);/,
    );
    expect(ultravioletStyles).toMatch(/:root\[data-theme="dark"\] \.ultraviolet-app \.danger-button \{ color: #2a0f12; \}/);
    expect(ultravioletStyles).not.toMatch(/:is\(\.danger-button, \.danger-text\)/);
  });

  it("meets WCAG AA text contrast in both themes", () => {
    expect(contrast("#ffffff", token(light, "--uv-danger"))).toBeGreaterThanOrEqual(4.5);
    expect(contrast("#2a0f12", token(dark, "--uv-danger"))).toBeGreaterThanOrEqual(4.5);
  });
});
