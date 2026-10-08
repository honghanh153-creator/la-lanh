import { ArrowLeft, Clock, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { getCurrentSky, isGuestSessionUnavailable, type Tradition } from "../../shared/api/client";
import "./insights.css";

const BODY_LABELS: Record<string, string> = {
  sun: "Mặt Trời",
  moon: "Mặt Trăng",
  mercury: "Sao Thủy",
  venus: "Sao Kim",
  mars: "Sao Hỏa",
  jupiter: "Sao Mộc",
  saturn: "Sao Thổ",
  uranus: "Thiên Vương",
  neptune: "Hải Vương",
  pluto: "Diêm Vương",
};

const SIGN_LABELS: Record<string, string> = {
  aries: "Bạch Dương",
  taurus: "Kim Ngưu",
  gemini: "Song Tử",
  cancer: "Cự Giải",
  leo: "Sư Tử",
  virgo: "Xử Nữ",
  libra: "Thiên Bình",
  scorpio: "Bọ Cạp",
  sagittarius: "Nhân Mã",
  capricorn: "Ma Kết",
  aquarius: "Bảo Bình",
  pisces: "Song Ngư",
};

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
    <header className="cosmic-header"><Link aria-label="Quay lại" className="icon-button" to={backTo}><ArrowLeft /></Link><span className="eyebrow">Bầu trời hiện tại</span><Sparkle /></header>
    <section className="insight-hero"><h1>Bầu trời hôm nay đang ở đâu?</h1><p>Mỗi ô cho biết một hành tinh đang ở cung nào. Đây là dữ liệu chung; ý nghĩa với riêng bạn chỉ có khi đối chiếu cùng lá số cá nhân.</p></section>
    {query.data ? <>
      <p className="sky-time"><Clock /> {new Date(query.data.observed_at).toLocaleString("vi-VN")}</p>
      <section className="sky-grid">{query.data.bodies.map((body) => <article key={body.body}><span>{BODY_LABELS[body.body] ?? body.body}</span><strong>{SIGN_LABELS[body.sign] ?? body.sign}</strong><small>{body.degree_in_sign.toFixed(1)}° {body.retrograde ? "· nghịch hành" : ""}</small></article>)}</section>
      <p className="privacy-plain">{query.data.note}</p>
    </> : missingSession ? <section className="cosmic-state"><h2>Phiên đọc đã khép lại.</h2><p>Mở lại Trạm Bắt Sóng để nối đúng chart trước khi xem bầu trời hôm nay.</p><Link className="outline-button" to="/welcome">Mở lại Trạm Bắt Sóng</Link></section> : query.isError ? <section className="cosmic-state"><h2>Chưa đọc được bầu trời lúc này.</h2><p>Dữ liệu hiện tại chưa về; bạn có thể thử lại mà không cần nhập thêm thông tin.</p><button className="outline-button" onClick={() => void query.refetch()} type="button">Thử lại</button></section> : <section className="cosmic-state"><p>Đang đọc vị trí hiện tại…</p></section>}
  </main>;
}
