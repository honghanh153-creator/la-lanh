// Reads public/_headers, index.html and the router source with Node APIs.
/// <reference types="node" />
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

const read = (path: string) => readFileSync(join(process.cwd(), path), "utf8");

// Every route whose URL carries a share or invite token (AGENTS.md: sensitive-by-capability).
function capabilityRoutePrefixes(): string[] {
  const router = read("src/app/router.tsx");
  const paths = [...router.matchAll(/path:\s*"([^"]*:token)"/g)].map((match) => match[1] ?? "");
  return paths.map((path) => `/${path.replace(/^\//, "").replace(/:token$/, "")}`);
}

function headerBlocks(): Map<string, string[]> {
  const blocks = new Map<string, string[]>();
  let current: string[] | undefined;
  for (const line of read("public/_headers").split("\n")) {
    if (line.trim() === "") continue;
    if (!/^\s/.test(line)) {
      current = [];
      blocks.set(line.trim(), current);
    } else {
      current?.push(line.trim());
    }
  }
  return blocks;
}

describe("public share and invite pages", () => {
  it("finds every token route in the router", () => {
    expect(capabilityRoutePrefixes().sort()).toEqual(["/la-chung/i/", "/radar/i/", "/share/"]);
  });

  it.each(capabilityRoutePrefixes())("static hosting never caches, indexes or leaks %s", (prefix) => {
    const block = headerBlocks().get(`${prefix}*`);

    expect(block).toBeDefined();
    expect(block).toContain("Cache-Control: no-store, max-age=0");
    expect(block).toContain("Referrer-Policy: no-referrer");
    expect(block).toContain("X-Robots-Tag: noindex, nofollow, noarchive");
  });

  it("asks crawlers not to index and browsers not to send a referrer from any page", () => {
    const html = read("index.html");

    expect(html).toContain('<meta name="robots" content="noindex, nofollow, noarchive" />');
    expect(html).toContain('<meta name="referrer" content="no-referrer" />');
  });
});
