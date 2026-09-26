import { ArrowLeft, ChartBar, Sparkle, WarningCircle } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";

import {
  getInsightOverview,
  getPrivateReading,
} from "../../shared/api/client";
import { ReadingContent } from "../../shared/ui/ReadingContent";
import { parseAyanamsa, parseHouseSystem, parseTradition } from "./insightConfig";
import "./insights.css";

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
    queryKey: ["insight-overview", tradition, houseSystem, ayanamsa],
    queryFn: ({ signal }) => getInsightOverview({ tradition, houseSystem, ayanamsa }, signal),
    enabled: claimId !== "synthesis",
    retry: false,
  });
  const focusedClaim = claimId === "synthesis"
    ? null
    : overviewQuery.data?.reading?.claims.find((claim) => claim.id === claimId);

  return (
    <main className="flow-page reading-page cosmic-reading-page">
      <header className="cosmic-header reading-detail-header">
        <Link aria-label="Quay lại Bản đồ Lá" className="icon-button" to={`/insights?${configQuery}`}><ArrowLeft aria-hidden="true" /></Link>
        <span className="eyebrow">Lá đọc sâu · {tradition === "jyotish" ? "Jyotish" : "Tây phương"}</span>
        <span />
      </header>

      {focusedClaim ? <p className="reading-context">Bạn mở từ: {focusedClaim.title}</p> : null}
      {claimId === "synthesis" && readingQuery.isLoading ? <section className="reading-skeleton" aria-label="Đang mở bản đọc" /> : null}
      {claimId !== "synthesis" && overviewQuery.isLoading ? <section className="reading-skeleton" aria-label="Đang mở bản đọc" /> : null}
      {claimId === "synthesis" && readingQuery.data ? <ReadingContent content={readingQuery.data.active} /> : null}
      {focusedClaim && overviewQuery.data?.reading ? (
        <FocusedClaimContent claim={focusedClaim} disclaimer={overviewQuery.data.reading.disclaimer} />
      ) : null}
      {claimId === "synthesis" && readingQuery.isError ? (
        <section className="cosmic-state" role="alert">
          <h1>Bản đọc sâu chưa về kịp.</h1>
          <p>Dữ liệu hiện tại vẫn được giữ nguyên. Bạn có thể thử lại mà không cần nhập lại thông tin sinh.</p>
          <button className="electric-button" onClick={() => void readingQuery.refetch()} type="button">Thử lại</button>
        </section>
      ) : null}
      {claimId !== "synthesis" && !overviewQuery.isLoading && !focusedClaim ? (
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

function FocusedClaimContent({ claim, disclaimer }: { claim: FocusedClaim; disclaimer: string }) {
  const evidence = claim.evidence.length > 0 ? claim.evidence : [claim.summary];
  return (
    <article className="reading-content focused-reading-content">
      <header className="reading-content__intro">
        <p className="reading-mode"><Sparkle aria-hidden="true" weight="fill" /> {claim.title}</p>
        <h1>{claim.hook || claim.summary}</h1>
        <p>{claim.meaning || claim.summary}</p>
      </header>
      <section>
        <h2>Ngoài đời có thể trông như…</h2>
        <p>{claim.manifestation || claim.summary}</p>
      </section>
      {claim.watch_for ? (
        <section className="focused-reading-content__watch">
          <h2>Chỗ dễ lệch nhịp</h2>
          <p>{claim.watch_for}</p>
        </section>
      ) : null}
      {claim.micro_action ? (
        <section className="reading-content__action">
          <h2>Thử một việc nhỏ</h2>
          <p>{claim.micro_action}</p>
        </section>
      ) : null}
      <details className="reading-evidence">
        <summary><ChartBar aria-hidden="true" /><span>Căn cứ trong lá số</span></summary>
        <ul>{evidence.map((item) => <li key={item}>{item}</li>)}</ul>
        <p>Vị trí, nhà và góc chiếu được tính từ chart; phần diễn giải là một khung để tự đối chiếu.</p>
      </details>
      <footer className="reading-content__disclaimer">{disclaimer}</footer>
    </article>
  );
}
