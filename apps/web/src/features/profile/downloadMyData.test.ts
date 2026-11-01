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

const fs = vi.hoisted(() => ({
  writeFile: vi.fn<(options: { path: string; data: string; directory: string; encoding: string }) => Promise<{ uri: string }>>(),
  deleteFile: vi.fn<(options: { path: string; directory: string }) => Promise<void>>(),
}));
const share = vi.hoisted(() => ({ share: vi.fn<(options: { title?: string; files?: string[] }) => Promise<unknown>>() }));

vi.mock("@capacitor/filesystem", () => ({
  Filesystem: fs,
  Directory: { Cache: "CACHE" },
  Encoding: { UTF8: "utf8" },
}));
vi.mock("@capacitor/share", () => ({ Share: share }));

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
    fs.writeFile.mockReset().mockResolvedValue({ uri: "file:///cache/export.json" });
    fs.deleteFile.mockReset().mockResolvedValue(undefined);
    share.share.mockReset().mockResolvedValue({});
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

  it("writes a cache file, opens the share sheet and deletes the file in the native shell", async () => {
    (window as CapacitorWindow).Capacitor = { isNativePlatform: () => true };
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click");

    await expect(saveDataExport(data)).resolves.toBe("shared");

    expect(fs.writeFile).toHaveBeenCalledTimes(1);
    const written = fs.writeFile.mock.calls[0][0];
    expect(written).toMatchObject({ path: DATA_EXPORT_FILE_NAME, directory: "CACHE", encoding: "utf8" });
    expect(JSON.parse(written.data)).toEqual(data);
    expect(share.share).toHaveBeenCalledWith(expect.objectContaining({ files: ["file:///cache/export.json"] }));
    expect(fs.deleteFile).toHaveBeenCalledWith({ path: DATA_EXPORT_FILE_NAME, directory: "CACHE" });
    expect(click).not.toHaveBeenCalled();
    expect(createObjectURL).not.toHaveBeenCalled();
  });

  it("treats closing the share sheet as a cancel, not an error, and still deletes the file", async () => {
    (window as CapacitorWindow).Capacitor = { isNativePlatform: () => true };
    share.share.mockRejectedValueOnce(new Error("Share canceled"));
    await expect(saveDataExport(data)).resolves.toBe("cancelled");
    expect(fs.deleteFile).toHaveBeenCalledTimes(1);
  });

  it("never reports a save in the native shell when the plugins fail", async () => {
    (window as CapacitorWindow).Capacitor = { isNativePlatform: () => true };
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click");
    share.share.mockRejectedValueOnce(new Error("No activity found"));
    await expect(saveDataExport(data)).resolves.toBe("unsupported");
    expect(fs.deleteFile).toHaveBeenCalledTimes(1);

    fs.writeFile.mockRejectedValueOnce(new Error("disk full"));
    await expect(saveDataExport(data)).resolves.toBe("unsupported");
    expect(share.share).toHaveBeenCalledTimes(1);
    expect(click).not.toHaveBeenCalled();
    expect(createObjectURL).not.toHaveBeenCalled();
  });
});
