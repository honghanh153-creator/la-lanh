import { ArrowLeft, Clock, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { getCurrentSky, isGuestSessionUnavailable, type Tradition } from "../../shared/api/client";
import "./insights.css";

export function CurrentSkyPage() {
  const [params] = useSearchParams();
  const location = useLocation();
  const routeState = location.state as { from?: unknown } | null;
  const tradition: Tradition = params.get("tradition") === "jyotish" ? "jyotish" : "western";
  const query = useQuery({ queryKey: ["current-sky", tradition], queryFn: ({ signal }) => getCurrentSky(tradition, signal) });
  const missingSession = isGuestSessionUnavailable(query.error);
  const backTo = routeState?.from === "home"
    ? "/home"
    : `/insights?tradition=${tradition}`;
  return <main className="flow-page current-sky-page">
    <header className="cosmic-header"><Link className="icon-button" to={backTo}><ArrowLeft /></Link><span className="eyebrow">Bầu trời hiện tại</span><Sparkle /></header>
    <section className="insight-hero"><h1>Bầu trời hôm nay đang đổi nhịp thế nào?</h1><p>Đây là ảnh chụp theo ngày, tách biệt khỏi bản đồ sinh của bạn.</p></section>
    {query.data ? <>
      <p className="sky-time"><Clock /> {new Date(query.data.observed_at).toLocaleString("vi-VN")}</p>
      <section className="sky-grid">{query.data.bodies.map((body) => <article key={body.body}><span>{body.body}</span><strong>{body.sign}</strong><small>{body.degree_in_sign.toFixed(1)}° {body.retrograde ? "· Rx" : ""}</small></article>)}</section>
      <p className="privacy-plain">{query.data.note}</p>
    </> : missingSession ? <section className="cosmic-state"><h2>Phiên đọc đã khép lại.</h2><p>Mở lại Trạm Bắt Sóng để nối đúng chart trước khi xem bầu trời hôm nay.</p><Link className="outline-button" to="/welcome">Mở lại Trạm Bắt Sóng</Link></section> : query.isError ? <section className="cosmic-state"><h2>Chưa đọc được bầu trời lúc này.</h2><p>Dữ liệu hiện tại chưa về; bạn có thể thử lại mà không cần nhập thêm thông tin.</p><button className="outline-button" onClick={() => void query.refetch()} type="button">Thử lại</button></section> : <section className="cosmic-state"><p>Đang đọc vị trí hiện tại…</p></section>}
  </main>;
}
