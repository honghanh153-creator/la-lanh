import { Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

import { getPublicRadarCard } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { shareArtAlt } from "../card/shareArt";
import { ShareArtPreview } from "../card/ShareArtPreview";
import { useShareArt } from "../card/useShareArt";
import "../matching/matching.css";
import "./radar.css";
import { radarCardSpec } from "./radarCardArt";

/** /radar/the/:token: a Hợp gu card shared by link. The server answers one not-found for a
 *  revoked, expired or removed card; the page never shows why. */
export function RadarCardPage() {
  return <div className="app-shell ultraviolet-app"><RadarCardContent /></div>;
}

function RadarCardContent() {
  const token = useParams().token ?? "";
  const card = useQuery({ queryKey: ["public-radar-card", token], queryFn: ({ signal }) => getPublicRadarCard(token, signal), retry: false, gcTime: 0 });
  const spec = useMemo(() => (card.data ? radarCardSpec(card.data) : null), [card.data]);
  const art = useShareArt(spec, "square_1_1");
  if (card.isLoading) return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang mở thẻ…</p></main>;
  if (!spec) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><h1>Link này không còn mở được.</h1><p>Có thể link đã hết hạn hoặc đã được thu hồi.</p><Link className="matching-secondary" to="/radar">Xem Hợp gu là gì</Link></section></main>;
  return <main className="matching-page radar-public radar-card-page">
    <BrandMark />
    <ShareArtPreview alt={shareArtAlt(spec, "square_1_1")} format="square_1_1" heading="Thẻ Hợp gu" svg={art.svg} />
    <Link className="matching-primary" to="/radar">Xem hợp gu của bạn</Link>
  </main>;
}
