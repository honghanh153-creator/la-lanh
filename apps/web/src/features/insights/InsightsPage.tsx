import { ArrowLeft, ArrowRight, Clock, Info, Planet, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import {
  getInsightOverview,
  getBirthSupplement,
  isGuestSessionUnavailable,
  type Tradition,
} from "../../shared/api/client";
import { AppNav } from "../../shared/ui/AppNav";
import { birthCompletionPrompt } from "../../shared/astro/birthReadiness";
import { BrandMark } from "../../shared/ui/BrandMark";
import { NightSky } from "../../shared/ui/NightSky";
import { readingModeLabel } from "../../shared/ui/readingLabels";
import { parseAyanamsa, parseHouseSystem, parseTradition } from "./insightConfig";
import "./insights.css";

const traditionCopy: Record<Tradition, { label: string; detail: string }> = {
  western: { label: "Tây phương", detail: "Tropical · nhà · góc chiếu" },
  jyotish: { label: "Jyotish", detail: "Sidereal · nakshatra · drishti" },
};

export function InsightsPage() {
  const [params, setParams] = useSearchParams();
  const tradition = parseTradition(params.get("tradition"));
  const houseSystem = parseHouseSystem(params.get("house"));
  const ayanamsa = parseAyanamsa(params.get("ayanamsa"));
  const configQuery = params.toString();
  const insight = useQuery({
    queryKey: ["insight-overview", tradition, houseSystem, ayanamsa],
    queryFn: ({ signal }) => getInsightOverview({ tradition, houseSystem, ayanamsa }, signal),
    retry: false,
  });
  const richReading = insight.data?.reading_projection?.active;
  const supplement = useQuery({ queryKey: ["birth-supplement"], queryFn: ({ signal }) => getBirthSupplement(signal), retry: false });
  const completionPrompt = birthCompletionPrompt(supplement.data);
  const missingSession = isGuestSessionUnavailable(insight.error);

  function selectTradition(value: Tradition) {
    const next = new URLSearchParams(params);
    next.set("tradition", value);
    if (value === "western") next.delete("ayanamsa");
    setParams(next);
  }

  return (
    <main className="app-page insight-page">
      <header className="cosmic-header">
        <Link aria-label="Về hôm nay" className="icon-button" to="/home"><ArrowLeft aria-hidden="true" /></Link>
        <BrandMark />
        <Link aria-label="Cách tính" className="icon-button" to={`/insights/settings?${configQuery}`}><Info aria-hidden="true" /></Link>
      </header>

      <section className="insight-hero">
        <p className="eyebrow"><Sparkle aria-hidden="true" weight="fill" /> Bản đọc Natal</p>
        <h1>Bạn có muốn<br />hiểu mình hơn?</h1>
        <p>Vì sao một kiểu chuyện hay chạm đúng bạn? Điều gì cứ quay lại, và bạn đang học cách phản ứng khác đi ở đâu?</p>
        <small>Chart không gây ra sự kiện và không viết sẵn số phận. Bản đọc nối các dữ kiện để bạn đối chiếu với đời thật.</small>
      </section>

      <section aria-label="Chọn hệ đọc" className="signal-switch">
        {(Object.keys(traditionCopy) as Tradition[]).map((value) => (
          <button
            aria-pressed={tradition === value}
            className={tradition === value ? "is-active" : ""}
            key={value}
            onClick={() => selectTradition(value)}
            type="button"
          >
            <strong>{traditionCopy[value].label}</strong>
            <small>{traditionCopy[value].detail}</small>
          </button>
        ))}
      </section>

      {insight.isLoading ? <InsightLoading /> : null}
      {missingSession ? (
        <section className="cosmic-state" role="alert">
          <Planet size={36} />
          <h2>Phiên đọc đã khép lại.</h2>
          <p>Mở lại Trạm Bắt Sóng để nối đúng Bản đồ của bạn. Chưa cần tạo tài khoản.</p>
          <Link className="electric-button" to="/welcome">Mở lại Trạm Bắt Sóng</Link>
        </section>
      ) : insight.isError ? (
        <section className="cosmic-state" role="alert">
          <Planet size={36} />
          <h2>Chart chưa về kịp.</h2>
          <p>Giữ nguyên hệ đọc và thử lại khi kết nối ổn hơn.</p>
          <button className="electric-button" onClick={() => void insight.refetch()} type="button">Thử lại</button>
        </section>
      ) : null}
      {insight.data?.status === "locked" ? (
        <section className="cosmic-state cosmic-state--locked">
          <Clock size={36} />
          <p className="eyebrow">Bản đọc tổng quan</p>
          <h2>{completionPrompt ? "Hiểu mình rõ hơn, từ lá số của bạn." : "Đang kiểm tra thông tin bản đọc."}</h2>
          {completionPrompt ? <><p>{completionPrompt.body}</p><small>Dữ liệu bổ sung dùng để tính lá số và cá nhân hóa bản đọc. Bạn có thể xóa trong Mình.</small><Link className="electric-button" to="/birth-time">{completionPrompt.cta}</Link></> : supplement.isPending ? <p role="status">Đang kiểm tra giờ và nơi sinh đã lưu…</p> : <><p>Chưa mở được bản đọc. Không cần điền lại khi thông tin đã đủ.</p><button className="electric-button" type="button" onClick={() => { void supplement.refetch(); void insight.refetch(); }}>Thử tải lại bản đọc</button></>}
        </section>
      ) : null}

      {richReading ? (
        <Link className="insight-synthesis" to={`/insights/synthesis?${configQuery}`}>
          <NightSky planet stars={4} />
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(richReading)}</p>
          <h2>{richReading.sections.hook}</h2>
          <p>{richReading.sections.thesis}</p>
          <span>Mở bản đọc Natal đầy đủ <ArrowRight aria-hidden="true" /></span>
        </Link>
      ) : null}
      {/* Approximate-time synthesis (#143 E1): what an exact time would add, in everyday words.
          Copy approved by the owner on 31.10.2026. */}
      {richReading?.mode === "full_synthesis" && richReading.precision === "approximate" ? (
        <p className="insight-precision-note">
          Bạn biết giờ sinh chính xác? <Link to="/birth-time">Thêm vào nhé</Link>, Lá sẽ đọc thêm được cách người khác nhìn thấy bạn lúc mới gặp, và những chuyện bạn hay gặp trong cuộc sống thường xoay quanh điều gì.
        </p>
      ) : null}

      {insight.data?.reading ? (
        <>
          <section className="insight-factors" aria-labelledby="factor-heading">
            <header>
              <p className="eyebrow">Các lớp kỹ thuật</p>
              <h2 id="factor-heading">Điều gì đang ảnh hưởng tới cách bạn phản ứng?</h2>
            </header>
            <div className="insight-grid">
              {insight.data.reading.claims.map((claim, index) => (
                <Link className="insight-tile" key={claim.id} to={`/insights/${claim.id}?${configQuery}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div><h3>{claim.title}</h3><strong>{claim.summary}</strong></div>
                  <ArrowRight aria-hidden="true" />
                </Link>
              ))}
            </div>
          </section>

          <Link className="sky-signal" to={`/insights/current-sky?tradition=${tradition}`}>
            <span><Sparkle aria-hidden="true" weight="fill" /> Bầu trời hiện tại · không phải natal</span>
            <strong>Xem bối cảnh chung của hôm nay</strong>
            <ArrowRight aria-hidden="true" />
          </Link>
          {/* Engine version and config hash are for support, not the reader: folded like Tarot's (#143 E4). */}
          <details className="provenance-strip">
            <summary>Chi tiết kỹ thuật</summary>
            <p>{traditionCopy[tradition].label} · {insight.data.reading.provenance.zodiac}</p>
            <small>Engine {insight.data.reading.provenance.version} · {insight.data.reading.config_hash.slice(0, 8)}</small>
          </details>
        </>
      ) : null}
      <AppNav />
    </main>
  );
}

function InsightLoading() {
  return <section className="insight-loading" aria-busy="true" aria-label="Đang tính Bản đồ Lá"><div className="uv-skeleton uv-skeleton--night" /><div className="uv-skeleton" /><div className="uv-skeleton" /></section>;
}
