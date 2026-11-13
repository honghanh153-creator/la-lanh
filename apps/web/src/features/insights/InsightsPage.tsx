import { ArrowLeft, ArrowRight, Info, Sparkle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";

import {
  getInsightOverview,
  type Tradition,
} from "../../shared/api/client";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
import { NightSky } from "../../shared/ui/NightSky";
import { readingModeLabel } from "../../shared/ui/readingLabels";
import { InsightQueryStates } from "./InsightQueryStates";
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

      <InsightQueryStates insight={insight} />

      {richReading ? (
        <Link className="insight-synthesis" to={`/insights/synthesis?${configQuery}`}>
          <NightSky planet stars={4} />
          <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {readingModeLabel(richReading)}</p>
          <h2>{richReading.sections.hook}</h2>
          <p>{richReading.sections.thesis}</p>
          <span>Mở Lá đọc sâu <ArrowRight aria-hidden="true" /></span>
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
          {insight.data.reading.claims.length > 0 ? <Link className="electric-button" to={`/insights/overview?${configQuery}`}>Xem bản đọc tổng quan <ArrowRight aria-hidden="true" /></Link> : null}
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
