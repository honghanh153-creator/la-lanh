import { Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { getShareArtifact } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";

export function SharePreviewPage() {
  const { token = "" } = useParams();
  const query = useQuery({
    queryKey: ["share-artifact", token],
    queryFn: ({ signal }) => getShareArtifact(token, signal),
    enabled: token.length > 0,
  });

  const artifact = query.data;
  const title = artifact?.safe_snapshot.title ?? "";
  const body = artifact?.safe_snapshot.body ?? "";
  const persona = artifact
    ? `${artifact.safe_snapshot.persona_mode === "aura" ? "Aura" : "Vibe"} · ${artifact.safe_snapshot.persona_label}`
    : "";

  return (
    <main className="flow-page card-page">
      <header className="flow-header"><BrandMark /><span className="reveal-source"><Sparkle weight="fill" /> Safe share</span></header>
      {query.isLoading ? (
        <section className="entry-loading"><span className="entry-loading__orbit" /><p>Đang mở note được gửi…</p></section>
      ) : artifact ? (
        <section className={artifact.format === "square_1_1" ? "share-card share-card--square" : "share-card"}>
          <span className="share-card__logo">LÁ LÀNH*</span>
          <p>{persona}</p>
          <h1>{title}</h1>
          <blockquote>{body}</blockquote>
          <small>Không chứa ngày/giờ/nơi sinh hay căn cứ riêng</small>
        </section>
      ) : (
        <section className="empty-state">
          <Sparkle size={52} />
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
