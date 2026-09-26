import { ArrowLeft, Clock, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import { getCurrentSky, type Tradition } from "../../shared/api/client";
import "./insights.css";

export function CurrentSkyPage() {
  const [params] = useSearchParams();
  const tradition: Tradition = params.get("tradition") === "jyotish" ? "jyotish" : "western";
  const query = useQuery({ queryKey: ["current-sky", tradition], queryFn: ({ signal }) => getCurrentSky(tradition, signal) });
  return <main className="flow-page current-sky-page">
    <header className="cosmic-header"><Link className="icon-button" to={`/insights?tradition=${tradition}`}><ArrowLeft /></Link><span className="eyebrow">Current Sky</span><Sparkle /></header>
    <section className="insight-hero"><h1>Bầu trời hôm nay đang đổi nhịp thế nào?</h1><p>Đây là ảnh chụp theo ngày, tách biệt khỏi natal chart của bạn.</p></section>
    {query.data ? <>
      <p className="sky-time"><Clock /> {new Date(query.data.observed_at).toLocaleString("vi-VN")}</p>
      <section className="sky-grid">{query.data.bodies.map((body) => <article key={body.body}><span>{body.body}</span><strong>{body.sign}</strong><small>{body.degree_in_sign.toFixed(1)}° {body.retrograde ? "· Rx" : ""}</small></article>)}</section>
      <p className="privacy-plain">{query.data.note}</p>
    </> : <section className="cosmic-state"><p>Đang đọc vị trí hiện tại…</p></section>}
  </main>;
}
