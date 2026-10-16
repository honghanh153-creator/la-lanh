import { Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

import { getShareArtifact } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { noteArtSpec } from "./noteCardSvg";
import { shareArtAlt } from "./shareArt";
import { ShareArtPreview } from "./ShareArtPreview";
import { useShareArt } from "./useShareArt";

export function SharePreviewPage() {
  const { token = "" } = useParams();
  const query = useQuery({
    queryKey: ["share-artifact", token],
    queryFn: ({ signal }) => getShareArtifact(token, signal),
    enabled: token.length > 0,
  });

  const artifact = query.data;
  const format = artifact?.format ?? "story_9_16";
  const snapshot = artifact?.safe_snapshot;
  // Only the sanitized snapshot fields are rendered; the token never enters the image or alt text.
  const spec = useMemo(
    () => (snapshot ? noteArtSpec({ title: snapshot.title, body: snapshot.body, personaLabel: snapshot.persona_label }) : null),
    [snapshot],
  );
  const art = useShareArt(spec, format);

  return (
    <main className="flow-page card-page">
      <header className="flow-header"><BrandMark /><span className="reveal-source"><Sparkle weight="fill" /> Safe share</span></header>
      {query.isLoading ? (
        <ShareArtPreview alt="" format={format} loadingText="Đang mở note được gửi…" svg={null} />
      ) : artifact && spec ? (
        <>
          <ShareArtPreview alt={shareArtAlt(spec, format)} format={format} heading={artifact.safe_snapshot.title} svg={art.svg} />
          <p className="share-art-privacy">Không chứa ngày / giờ / nơi sinh hay căn cứ riêng</p>
        </>
      ) : (
        <section className="empty-state uv-empty" role="alert">
          <div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/moon.webp" /></div>
          <h1>Note này đã bay mất.</h1>
          <p>Link có thể hết hạn hoặc không còn tồn tại.</p>
        </section>
      )}
      <footer className="flow-actions">
        <Link className="electric-button" to="/welcome">Mở Lá Lành của mình</Link>
      </footer>
    </main>
  );
}
