import { useCallback, useEffect, useMemo, useState } from "react";

import type { ShareFormat } from "../../shared/api/client";
import { buildShareArtSvg, shareCanvasSize, type ShareArtSpec } from "./shareArt";
import { cachedShareFontCss, loadShareFontCss } from "./shareFonts";
import { rasterizeSvg, svgToPngFile } from "./shareRaster";

type IdleWindow = Window & {
  requestIdleCallback?: (callback: () => void, options?: { timeout: number }) => number;
  cancelIdleCallback?: (handle: number) => void;
};

/**
 * Builds the share SVG once fonts are ready (instant after the first card in a session), then
 * pre-renders the PNG in idle time so Chia sẻ / Tải PNG respond immediately and keep the
 * user-activation window that navigator.share needs.
 */
export function useShareArt(spec: ShareArtSpec | null, format: ShareFormat) {
  const [fontCss, setFontCss] = useState<string | null>(cachedShareFontCss);
  const specKey = spec ? JSON.stringify(spec) : null;
  const { width, height } = shareCanvasSize[format];

  useEffect(() => {
    if (fontCss !== null) return;
    let active = true;
    void loadShareFontCss().then((css) => {
      if (active) setFontCss(css);
    });
    return () => {
      active = false;
    };
  }, [fontCss]);

  const svg = useMemo(
    () => (specKey && fontCss !== null ? buildShareArtSvg(JSON.parse(specKey) as ShareArtSpec, format, fontCss) : null),
    [specKey, format, fontCss],
  );

  useEffect(() => {
    if (!svg) return;
    const idle = window as IdleWindow;
    const warm = () => {
      void rasterizeSvg(svg, width, height).catch(() => undefined);
    };
    if (idle.requestIdleCallback) {
      const handle = idle.requestIdleCallback(warm, { timeout: 1200 });
      return () => idle.cancelIdleCallback?.(handle);
    }
    const handle = window.setTimeout(warm, 200);
    return () => window.clearTimeout(handle);
  }, [svg, width, height]);

  const pngFile = useCallback(
    (name: string) => {
      if (!svg) return Promise.reject(new Error("Share art is not ready"));
      return svgToPngFile(svg, width, height, name);
    },
    [svg, width, height],
  );

  return { svg, pngFile, ready: svg !== null };
}
