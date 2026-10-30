import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DataExport } from "../../shared/api/client";
import { DATA_EXPORT_FILE_NAME, saveDataExport } from "./downloadMyData";

const data = { format: "la-lanh-data-export-v1", notice: "riêng tư" } as DataExport;

function readText(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(typeof reader.result === "string" ? reader.result : "");
    reader.onerror = () => reject(reader.error ?? new Error("read failed"));
    reader.readAsText(blob);
  });
}

type CapacitorWindow = Window & { Capacitor?: { isNativePlatform?: () => boolean } };

describe("saveDataExport", () => {
  let created: Blob[];
  let revoked: string[];
  let createObjectURL: ReturnType<typeof vi.fn<(blob: Blob) => string>>;

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout"] });
    created = [];
    revoked = [];
    createObjectURL = vi.fn((blob: Blob) => {
      created.push(blob);
      return "blob:la-lanh/export";
    });
    URL.createObjectURL = createObjectURL;
    URL.revokeObjectURL = vi.fn((url: string) => { revoked.push(url); });
  });

  afterEach(() => {
    vi.useRealTimers();
    delete (window as CapacitorWindow).Capacitor;
    vi.restoreAllMocks();
  });

  it("downloads a JSON file with a fixed, non-identifying name and drops the Blob URL", async () => {
    const clicked: HTMLAnchorElement[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      clicked.push(this);
    });

    await expect(saveDataExport(data)).resolves.toBe("downloaded");

    expect(clicked).toHaveLength(1);
    expect(clicked[0].download).toBe(DATA_EXPORT_FILE_NAME);
    expect(DATA_EXPORT_FILE_NAME).toBe("la-lanh-du-lieu-cua-toi.json");
    expect(clicked[0].href).toBe("blob:la-lanh/export");
    expect(document.querySelector("a[download]")).toBeNull();
    expect(created[0].type).toBe("application/json");
    expect(JSON.parse(await readText(created[0]))).toEqual(data);
    vi.runAllTimers();
    expect(revoked).toEqual(["blob:la-lanh/export"]);
  });

  it("uses the system share sheet in the native shell and reports a cancelled save", async () => {
    (window as CapacitorWindow).Capacitor = { isNativePlatform: () => true };
    const share = vi.fn<(input: ShareData) => Promise<void>>().mockResolvedValueOnce(undefined)
      .mockRejectedValueOnce(new DOMException("closed", "AbortError"));
    Object.assign(navigator, { canShare: () => true, share });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click");

    await expect(saveDataExport(data)).resolves.toBe("shared");
    const shared = share.mock.calls[0][0].files?.[0];
    expect(shared?.name).toBe(DATA_EXPORT_FILE_NAME);
    await expect(saveDataExport(data)).resolves.toBe("cancelled");
    expect(click).not.toHaveBeenCalled();
    expect(createObjectURL).not.toHaveBeenCalled();
  });
});
