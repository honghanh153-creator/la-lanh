import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { MONTH_COPY } from "./monthCopy";

type Entry = { id: string; text: string; category: string };

describe("month copy mirrors the registry", () => {
  const registry = JSON.parse(
    readFileSync(join(process.cwd(), "../api/app/domains/content/copy_registry.json"), "utf8"),
  ) as { entries: Entry[] };
  const byId = new Map(registry.entries.map((entry) => [entry.id, entry]));

  it("every web label equals its registry sentence", () => {
    for (const [id, text] of Object.entries(MONTH_COPY)) {
      expect(byId.get(id)?.text, id).toBe(text);
      expect(byId.get(id)?.category, id).toBe("reading");
    }
  });

  it("every month.ui entry in the registry is used on the web", () => {
    const registered = registry.entries.filter((entry) => entry.id.startsWith("month.ui.")).map((entry) => entry.id);
    expect(registered.sort()).toEqual(Object.keys(MONTH_COPY).sort());
  });
});
