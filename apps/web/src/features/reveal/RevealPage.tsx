import { ArrowRight, Info, ShareNetwork, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { getBirthProfile } from "../../shared/api/client";
import { signDetails } from "../../shared/astro/signs";
import { BrandMark } from "../../shared/ui/BrandMark";

export function RevealPage() {
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });

  if (query.isLoading) return <main className="entry-loading"><span className="entry-loading__orbit" /><p>Đang lật Lá Khai Sinh…</p></main>;
  if (!query.data) return <main className="route-error"><h1>Chưa tìm thấy Lá.</h1><button className="electric-button" onClick={() => void navigate("/birth")} type="button">Nhập ngày sinh</button></main>;

  const { calculation } = query.data;
  const signs = calculation.status === "certain" && calculation.sign
    ? [calculation.sign]
    : calculation.candidates;
  const primary = signDetails[signs[0]];

  return (
    <main className="flow-page reveal-page">
      <header className="flow-header"><BrandMark /><span className="reveal-source"><Sparkle weight="fill" /> Swiss Ephemeris thật</span></header>
      <section className="reveal-stage" aria-labelledby="reveal-title">
        <div className="reveal-orbits" aria-hidden="true"><span /><span /><span /></div>
        <p className="handwritten-kicker">vũ trụ ghi lại...</p>
        {calculation.status === "certain" ? (
          <><span className="zodiac-symbol" aria-hidden="true">{primary.symbol}</span><p className="eyebrow">Mặt Trời của bạn ở</p><h1 id="reveal-title">{primary.label}</h1><p className="reveal-line">“{primary.note}”</p></>
        ) : (
          <><p className="eyebrow">Ngày này chạm đúng ranh giới</p><h1 id="reveal-title">{signs.map((sign) => signDetails[sign].label).join(" · ")}</h1><p className="reveal-line">Không đoán giờ sinh của bạn. Thêm giờ sau để chốt chính xác.</p></>
        )}
      </section>
      <aside className="provenance-note"><Info size={19} /><p>Tính từ chuyển động Mặt Trời trong toàn bộ khoảng giờ có thể của ngày sinh. Engine {calculation.provenance.version}; không dùng mốc ngày cố định.</p></aside>
      <footer className="flow-actions reveal-actions">
        <button className="electric-button" onClick={() => void navigate("/home")} type="button">Xem note hôm nay <ArrowRight /></button>
        <Link className="outline-button" to="/card"><ShareNetwork /> Tạo card để chia sẻ</Link>
      </footer>
    </main>
  );
}
