import { ArrowLeft, ArrowRight, Clock, Info, Planet, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import {
  getInsightOverview,
  type Tradition,
} from "../../shared/api/client";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
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
        <p>Vì sao một kiểu chuyện hay chạm đúng bạn? Pattern nào cứ quay lại, và bạn đang học cách phản ứng khác đi ở đâu?</p>
        <small>Chart không gây ra sự kiện và không viết sẵn số phận. Bản đọc này nối các pattern để bạn đối chiếu với đời thật.</small>
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
      {insight.isError ? (
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
          <p className="eyebrow">Còn một lớp chưa mở</p>
          <h2>Cần giờ và nơi sinh để đọc đủ chart.</h2>
          <p>Lá Lành chỉ dùng dữ liệu này để tính chart. Bạn có thể xóa lại trong Mình.</p>
          <Link className="electric-button" to="/birth-time">Mở lớp sâu</Link>
        </section>
      ) : null}

      {richReading ? (
        <Link className="insight-synthesis" to={`/insights/synthesis?${configQuery}`}>
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(richReading)}</p>
          <h2>{richReading.sections.hook}</h2>
          <p>{richReading.sections.thesis}</p>
          <span>Mở bản đọc Natal đầy đủ <ArrowRight aria-hidden="true" /></span>
        </Link>
      ) : null}

      {insight.data?.reading ? (
        <>
          <section className="insight-factors" aria-labelledby="factor-heading">
            <header>
              <p className="eyebrow">Các lớp kỹ thuật</p>
              <h2 id="factor-heading">Điều gì đang tạo nên pattern của bạn?</h2>
            </header>
            <div className="insight-grid">
              {insight.data.reading.claims.map((claim, index) => (
                <Link className="insight-tile" key={claim.id} to={`/insights/${claim.id}?${configQuery}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div><p>{claim.domain}</p><h3>{claim.title}</h3><strong>{claim.summary}</strong></div>
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
          <section className="provenance-strip">
            <p>{traditionCopy[tradition].label} · {insight.data.reading.provenance.zodiac}</p>
            <small>Engine {insight.data.reading.provenance.version} · {insight.data.reading.config_hash.slice(0, 8)}</small>
          </section>
        </>
      ) : null}
      <AppNav />
    </main>
  );
}

function InsightLoading() {
  return <section className="insight-loading" aria-label="Đang tính Bản đồ Lá"><div /><div /><div /></section>;
}
