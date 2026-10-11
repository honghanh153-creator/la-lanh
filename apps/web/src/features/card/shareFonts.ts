import latin600 from "@fontsource/be-vietnam-pro/files/be-vietnam-pro-latin-600-normal.woff2?url";
import latin800 from "@fontsource/be-vietnam-pro/files/be-vietnam-pro-latin-800-normal.woff2?url";
import vietnamese600 from "@fontsource/be-vietnam-pro/files/be-vietnam-pro-vietnamese-600-normal.woff2?url";
import vietnamese800 from "@fontsource/be-vietnam-pro/files/be-vietnam-pro-vietnamese-800-normal.woff2?url";

/**
 * An SVG rendered through <img>/canvas cannot see the page's web fonts, so the share image would
 * fall back to whatever system font the device has. We embed the already-bundled Be Vietnam Pro
 * subsets (same-origin, same hashed files the app CSS uses, so normally an HTTP-cache hit) once
 * per session and reuse the CSS for every render.
 */
const LATIN_RANGE = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";
const VIETNAMESE_RANGE = "U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB";

const faces = [
  { url: latin800, weight: 800, range: LATIN_RANGE },
  { url: vietnamese800, weight: 800, range: VIETNAMESE_RANGE },
  { url: latin600, weight: 600, range: LATIN_RANGE },
  { url: vietnamese600, weight: 600, range: VIETNAMESE_RANGE },
];

const FONT_TIMEOUT_MS = 2500;
let pending: Promise<string> | null = null;
let resolved: string | null = null;

function toBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
  }
  return btoa(binary);
}

async function fetchFace(face: (typeof faces)[number]): Promise<string> {
  const response = await fetch(face.url, { credentials: "same-origin" });
  if (!response.ok) throw new Error("Share font unavailable");
  const data = toBase64(await response.arrayBuffer());
  return `@font-face{font-family:'LL Share';font-style:normal;font-weight:${face.weight};src:url(data:font/woff2;base64,${data}) format('woff2');unicode-range:${face.range};}`;
}

/** Already-loaded font CSS, if any, so callers can render synchronously on later visits. */
export function cachedShareFontCss(): string | null {
  return resolved;
}

/**
 * Resolves with embedded @font-face CSS, or "" (system-font fallback, still full Vietnamese) when
 * the fonts cannot be fetched quickly. Failures are not cached so a later render can retry.
 */
export function loadShareFontCss(): Promise<string> {
  if (resolved !== null) return Promise.resolve(resolved);
  pending ??= Promise.all(faces.map(fetchFace))
    .then((parts) => {
      resolved = parts.join("");
      return resolved;
    })
    .finally(() => {
      pending = null;
    });
  const timeout = new Promise<string>((resolve) => setTimeout(() => resolve(""), FONT_TIMEOUT_MS));
  return Promise.race([pending, timeout]).catch(() => "");
}
