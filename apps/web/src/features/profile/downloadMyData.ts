import type { DataExport } from "../../shared/api/client";

// Same fixed, non-identifying name as the API's Content-Disposition: no date of birth, name or id.
export const DATA_EXPORT_FILE_NAME = "la-lanh-du-lieu-cua-toi.json";

export type SaveOutcome = "downloaded" | "shared" | "cancelled" | "unsupported";

function isNativeApp(): boolean {
  const capacitor = (window as Window & {
    Capacitor?: { isNativePlatform?: () => boolean };
  }).Capacitor;
  return capacitor?.isNativePlatform?.() === true;
}

function isShareCancel(error: unknown): boolean {
  // @capacitor/share rejects with "Share canceled" (iOS/Android) when the user closes the sheet.
  const message = error instanceof Error ? error.message : typeof error === "string" ? error : "";
  return /cancel/i.test(message) || (error instanceof DOMException && error.name === "AbortError");
}

/**
 * Native shell: WKWebView/Android WebView do not honour the download attribute, so the JSON is
 * written to the app cache directory with @capacitor/filesystem and handed to the system share
 * sheet with @capacitor/share ("Lưu vào Tệp"). The temp file is deleted right after the sheet
 * closes, whether the user saved, cancelled or the share failed. If the app is killed while the
 * sheet is open, or that deletion fails, removeOrphanedNativeExport() removes the file on the next
 * start and on every device/profile erase (Codex auto-3 on #117). Plugins are loaded lazily so the web bundle path is unchanged.
 */
async function saveNative(json: string): Promise<SaveOutcome> {
  let Filesystem: typeof import("@capacitor/filesystem").Filesystem;
  let Directory: typeof import("@capacitor/filesystem").Directory;
  let Encoding: typeof import("@capacitor/filesystem").Encoding;
  let Share: typeof import("@capacitor/share").Share;
  try {
    ({ Filesystem, Directory, Encoding } = await import("@capacitor/filesystem"));
    ({ Share } = await import("@capacitor/share"));
  } catch {
    return "unsupported";
  }
  let uri: string;
  try {
    ({ uri } = await Filesystem.writeFile({
      path: DATA_EXPORT_FILE_NAME,
      data: json,
      directory: Directory.Cache,
      encoding: Encoding.UTF8,
    }));
  } catch {
    return "unsupported";
  }
  try {
    await Share.share({ title: "Dữ liệu Lá Lành của tôi", files: [uri] });
    return "shared";
  } catch (error) {
    return isShareCancel(error) ? "cancelled" : "unsupported";
  } finally {
    try {
      await Filesystem.deleteFile({ path: DATA_EXPORT_FILE_NAME, directory: Directory.Cache });
    } catch {
      // Retried by removeOrphanedNativeExport() on next start and on device erase.
    }
  }
}

/**
 * Hands the owner's data file to the device without keeping a copy: on web the Blob URL is revoked
 * right after the click and nothing is written to localStorage, IndexedDB or the query cache.
 * In the native shell see saveNative; "unsupported" is returned only when the plugins or the share
 * sheet cannot take the file, and the anchor is never tried there (Codex auto-1 on #117).
 */
export async function saveDataExport(data: DataExport): Promise<SaveOutcome> {
  const json = JSON.stringify(data, null, 2);
  if (isNativeApp()) return saveNative(json);
  const file = new File([json], DATA_EXPORT_FILE_NAME, { type: "application/json" });
  const url = URL.createObjectURL(file);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = DATA_EXPORT_FILE_NAME;
    anchor.rel = "noopener";
    anchor.style.display = "none";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    // Let the click start the download before the URL goes away.
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  return "downloaded";
}

/**
 * Deletes a leftover native export file (app killed mid-share, or the post-share delete failed).
 * No-op on the web. Resolves when the file is gone or never existed; rejects only when the file is
 * still there afterwards, so device erase can report the failure instead of hiding it.
 */
export async function removeOrphanedNativeExport(): Promise<void> {
  if (!isNativeApp()) return;
  let Filesystem: typeof import("@capacitor/filesystem").Filesystem;
  let Directory: typeof import("@capacitor/filesystem").Directory;
  try {
    ({ Filesystem, Directory } = await import("@capacitor/filesystem"));
  } catch {
    return; // Without the plugin no export file can have been written.
  }
  const target = { path: DATA_EXPORT_FILE_NAME, directory: Directory.Cache };
  try {
    await Filesystem.deleteFile(target);
    return;
  } catch (deleteError) {
    // deleteFile also rejects when the file does not exist; only a file that survives is a failure.
    let stillThere = true;
    try {
      await Filesystem.stat(target);
    } catch {
      stillThere = false;
    }
    if (stillThere) {
      throw deleteError instanceof Error ? deleteError : new Error("Native export file could not be deleted");
    }
  }
}
