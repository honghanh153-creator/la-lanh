import { ArrowLeft, ChartBar, Sparkle, WarningCircle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";

import {
  getInsightOverview,
  getPrivateReading,
} from "../../shared/api/client";
import { ReadingContent } from "../../shared/ui/ReadingContent";
import { ReadingDisclaimer } from "../../shared/ui/ReadingDisclaimer";
import { InsightQueryStates } from "./InsightQueryStates";
import { parseAyanamsa, parseHouseSystem, parseTradition } from "./insightConfig";
import "./insights.css";
import { LaLoading } from "../../shared/ui/la/LaLoading";

export function ReadingDetailPage() {
  const { claimId = "synthesis" } = useParams();
  const [params] = useSearchParams();
  const tradition = parseTradition(params.get("tradition"));
  const houseSystem = parseHouseSystem(params.get("house"));
  const ayanamsa = parseAyanamsa(params.get("ayanamsa"));
  const configQuery = params.toString();
  const readingQuery = useQuery({
    queryKey: ["private-reading", "reading_detail", tradition, houseSystem, ayanamsa],
    queryFn: ({ signal }) => getPrivateReading(
      "reading_detail",
      { tradition, houseSystem, ayanamsa },
      signal,
    ),
    enabled: claimId === "synthesis",
    retry: false,
  });
  const overviewQuery = useQuery({
    enabled: claimId !== "synthesis",
    queryKey: ["insight-overview", tradition, houseSystem, ayanamsa],
    queryFn: ({ signal }) => getInsightOverview({ tradition, houseSystem, ayanamsa }, signal),
    retry: false,
  });
  const focusedClaim = claimId === "synthesis" || claimId === "overview"
    ? null
    : overviewQuery.data?.reading?.claims.find((claim) => claim.id === claimId);

  return (
    <main className="flow-page reading-page cosmic-reading-page">
      <header className="cosmic-header reading-detail-header">
        <Link aria-label="Quay lại Bản đồ Lá" className="icon-button" to={`/insights?${configQuery}`}><ArrowLeft aria-hidden="true" /></Link>
        {claimId === "overview"
          ? <h1 className="eyebrow">Bản đọc tổng quan · {tradition === "jyotish" ? "Jyotish" : "Tây phương"}</h1>
          : <span className="eyebrow">Lá đọc sâu · {tradition === "jyotish" ? "Jyotish" : "Tây phương"}</span>}
        <span />
      </header>

      {focusedClaim ? <p className="reading-context">Bạn mở từ: {focusedClaim.title}</p> : null}
      {claimId === "synthesis" && readingQuery.isLoading ? <LaLoading delayMs={0} text="Lá đang mở bản đọc…" variant="reading" /> : null}
      {claimId === "overview" ? <InsightQueryStates insight={overviewQuery} /> : null}
      {claimId !== "synthesis" && claimId !== "overview" && overviewQuery.isLoading ? <LaLoading delayMs={0} text="Lá đang mở bản đọc…" variant="reading" /> : null}
      {claimId === "synthesis" && readingQuery.data ? <ReadingContent content={readingQuery.data.active} /> : null}
      {focusedClaim && overviewQuery.data?.reading ? (
        <FocusedClaimContent
          claim={focusedClaim}
          disclaimer={overviewQuery.data.reading.disclaimer}
          housesAndAspects={overviewQuery.data.time_precision === "exact" && overviewQuery.data.houses_available}
        />
      ) : null}
      {claimId === "synthesis" && readingQuery.data ? (
        <Link className="electric-button" to={`/insights/overview?${configQuery}`}>Xem bản đọc tổng quan</Link>
      ) : null}
      {claimId === "overview" && overviewQuery.data?.reading?.claims.length ? (
        <div className="overview-claims">
          {overviewQuery.data.time_precision !== "exact" ? (
            <p className="insight-precision-note">
              Bạn biết giờ sinh chính xác? <Link to="/birth-time">Thêm vào nhé</Link>, Lá sẽ đọc thêm được cách người khác nhìn thấy bạn lúc mới gặp, và những chuyện bạn hay gặp trong cuộc sống thường xoay quanh điều gì.
            </p>
          ) : null}
          {overviewQuery.data.reading.claims.map((claim) => (
            <FocusedClaimContent
              claim={claim}
              housesAndAspects={overviewQuery.data?.time_precision === "exact" && Boolean(overviewQuery.data?.houses_available)}
              key={claim.id}
              nested
            />
          ))}
          <ReadingDisclaimer>{overviewQuery.data.reading.disclaimer}</ReadingDisclaimer>
        </div>
      ) : null}
      {claimId === "synthesis" && readingQuery.isError ? (
        <section className="cosmic-state" role="alert">
          <h1>Bản đọc sâu chưa về kịp.</h1>
          <p>Dữ liệu hiện tại vẫn được giữ nguyên. Bạn có thể thử lại mà không cần nhập lại thông tin sinh.</p>
          <button className="electric-button" onClick={() => void readingQuery.refetch()} type="button">Thử lại</button>
        </section>
      ) : null}
      {claimId !== "synthesis" && !overviewQuery.isLoading && !overviewQuery.isError && overviewQuery.data?.status !== "locked" && !focusedClaim && (claimId !== "overview" || !overviewQuery.data?.reading?.claims.length) ? (
        <section className="cosmic-state" role="alert">
          <WarningCircle aria-hidden="true" size={30} />
          <h1>Lớp này chưa có trong chart.</h1>
          <p>Quay lại Bản đồ Lá để chọn một lớp đang có dữ liệu.</p>
        </section>
      ) : null}
    </main>
  );
}

type FocusedClaim = NonNullable<NonNullable<Awaited<ReturnType<typeof getInsightOverview>>["reading"]>["claims"]>[number];

function FocusedClaimContent({ claim, disclaimer, housesAndAspects, nested = false }: { claim: FocusedClaim; disclaimer?: string; housesAndAspects: boolean; nested?: boolean }) {
  const Title = nested ? "h2" : "h1";
  const Sub = nested ? "h3" : "h2";
  const evidence = claim.evidence.length > 0 ? claim.evidence : [claim.summary];
  return (
    <article className="reading-content focused-reading-content">
      <header className="reading-content__intro">
        <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {claim.title}</p>
        <Title>{claim.hook || claim.summary}</Title>
        <p>{claim.meaning || claim.summary}</p>
      </header>
      <section>
        <Sub>Ngoài đời có thể trông như…</Sub>
        <p>{claim.manifestation || claim.summary}</p>
      </section>
      {claim.watch_for ? (
        <section className="focused-reading-content__watch">
          <Sub>Chỗ dễ lệch nhịp</Sub>
          <p>{claim.watch_for}</p>
        </section>
      ) : null}
      {claim.micro_action ? (
        <section className="reading-content__action">
          <Sub>Thử một việc nhỏ</Sub>
          <p>{claim.micro_action}</p>
        </section>
      ) : null}
      <details className="reading-evidence">
        <summary><ChartBar aria-hidden="true" /><span>Căn cứ trong lá số</span></summary>
        <ul>{evidence.map((item) => <li key={item}>{item}</li>)}</ul>
        {/* An approximate time reads no houses or aspects (#143 E4): only say so when the chart has them. */}
        {housesAndAspects ? <p>Vị trí, nhà và góc chiếu được tính từ chart; phần diễn giải là một khung để tự đối chiếu.</p> : null}
      </details>
      {disclaimer ? <ReadingDisclaimer>{disclaimer}</ReadingDisclaimer> : null}
    </article>
  );
}
