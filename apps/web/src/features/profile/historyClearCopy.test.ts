import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { HISTORY_CLEAR_FAILED, LOCAL_ERASE_FAILED, localEraseFailedText } from "./historyClearCopy";

type Entry = { id: string; text: string; status: string };
const registry = JSON.parse(
  readFileSync(resolve(__dirname, "../../../../api/app/domains/content/copy_registry.json"), "utf8"),
) as { entries: Entry[] };

describe("the device-erase error waits for the owner (Codex auto-2 on #734)", () => {
  it("is registered with the same text and is shown only once the registry approves it", () => {
    const entry = registry.entries.find((item) => item.id === LOCAL_ERASE_FAILED.id);
    expect(entry?.text).toBe(LOCAL_ERASE_FAILED.text);
    expect(LOCAL_ERASE_FAILED.approved).toBe(entry?.status === "approved");
    expect(localEraseFailedText()).toBe(entry?.status === "approved" ? LOCAL_ERASE_FAILED.text : HISTORY_CLEAR_FAILED);
  });
});
