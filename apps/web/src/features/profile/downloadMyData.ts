import type { DataExport } from "../../shared/api/client";

// Same fixed, non-identifying name as the API's Content-Disposition: no date of birth, name or id.
export const DATA_EXPORT_FILE_NAME = "la-lanh-du-lieu-cua-toi.json";

export type SaveOutcome = "downloaded" | "shared" | "cancelled";

function isNativeApp(): boolean {
  const capacitor = (window as Window & {
    Capacitor?: { isNativePlatform?: () => boolean };
  }).Capacitor;
  return capacitor?.isNativePlatform?.() === true;
}

/**
 * Hands the owner's data file to the device without keeping a copy: the Blob URL is revoked right
 * after the click and nothing is written to localStorage, IndexedDB or the query cache.
 *
 * Web: a Blob + anchor download. Native shell: WKWebView/Android WebView do not reliably honour
 * the download attribute, so the system share sheet ("Lưu vào Tệp") is used when it accepts files;
 * otherwise the anchor is tried as a fallback.
 */
export async function saveDataExport(data: DataExport): Promise<SaveOutcome> {
  const json = JSON.stringify(data, null, 2);
  const file = new File([json], DATA_EXPORT_FILE_NAME, { type: "application/json" });
  if (isNativeApp() && typeof navigator.canShare === "function" && navigator.canShare({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: "Dữ liệu Lá Lành của tôi" });
      return "shared";
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return "cancelled";
      throw error;
    }
  }
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
