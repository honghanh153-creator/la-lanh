/**
 * SVG → PNG with a tiny in-memory cache keyed by the exact SVG markup. The preview pre-warms the
 * cache while the user looks at the card, so "Chia sẻ" / "Tải PNG" reuse the same bitmap instead of
 * decoding and encoding again (and the share → download fallback no longer rasterizes twice).
 * Nothing is persisted; the cache lives only for the tab session.
 */
const MAX_ENTRIES = 4;
const cache = new Map<string, Promise<Blob>>();

export function svgDataUrl(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

async function rasterize(svg: string, width: number, height: number): Promise<Blob> {
  const image = new Image();
  image.decoding = "async";
  image.src = svgDataUrl(svg);
  await image.decode();
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Canvas is not available");
  context.drawImage(image, 0, 0, width, height);
  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((value) => (value ? resolve(value) : reject(new Error("PNG render failed"))), "image/png");
  });
}

export function rasterizeSvg(svg: string, width: number, height: number): Promise<Blob> {
  const hit = cache.get(svg);
  if (hit) return hit;
  const job = rasterize(svg, width, height);
  cache.set(svg, job);
  job.catch(() => cache.delete(svg));
  while (cache.size > MAX_ENTRIES) cache.delete(cache.keys().next().value as string);
  return job;
}

export async function svgToPngFile(svg: string, width: number, height: number, name: string): Promise<File> {
  const blob = await rasterizeSvg(svg, width, height);
  return new File([blob], name, { type: "image/png" });
}

export function clearShareRasterCache() {
  cache.clear();
}
