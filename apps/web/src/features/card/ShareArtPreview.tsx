import { useState } from "react";

import type { ShareFormat } from "../../shared/api/client";
import { svgDataUrl } from "./shareRaster";
import "./shareArt.css";

type Props = {
  format: ShareFormat;
  /** Final SVG; null while data/fonts are still loading. */
  svg: string | null;
  alt: string;
  /** Page heading text (visually hidden; the image carries the visual hierarchy). */
  heading?: string | null;
  loadingText?: string;
};

export function ShareArtSkeleton({ format, loadingText = "Lá đang vẽ thẻ của bạn…" }: { format: ShareFormat; loadingText?: string }) {
  return (
    <div className={`share-art__skeleton share-art__skeleton--${format === "square_1_1" ? "square" : "story"}`}>
      <div aria-hidden="true" className="share-art__bones">
        <span className="share-art__bone share-art__bone--brand" />
        <span className="share-art__bone share-art__bone--disc" />
        <span className="share-art__bone share-art__bone--badge" />
        <span className="share-art__bone share-art__bone--line" />
        <span className="share-art__bone share-art__bone--line share-art__bone--short" />
        <span className="share-art__bone share-art__bone--note" />
      </div>
      <p className="share-art__loading" role="status">{loadingText}</p>
    </div>
  );
}

export function ShareArtPreview({ format, svg, alt, heading, loadingText }: Props) {
  const src = svg ? svgDataUrl(svg) : null;
  const [loadedSrc, setLoadedSrc] = useState<string | null>(null);
  const loaded = src !== null && loadedSrc === src;
  const variant = format === "square_1_1" ? "square" : "story";

  return (
    <figure aria-busy={!loaded} className={`share-art share-art--${variant}`}>
      {heading ? <h1 className="sr-only">{heading}</h1> : null}
      {src ? (
        <img
          alt={alt}
          className={loaded ? "share-art__image is-loaded" : "share-art__image"}
          decoding="async"
          height={format === "square_1_1" ? 1080 : 1920}
          onLoad={() => setLoadedSrc(src)}
          src={src}
          width={1080}
        />
      ) : null}
      {loaded ? null : <ShareArtSkeleton format={format} loadingText={loadingText} />}
    </figure>
  );
}
