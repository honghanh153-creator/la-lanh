import { Clock, Planet } from "@phosphor-icons/react";
import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  getBirthSupplement,
  isGuestSessionUnavailable,
  type getInsightOverview,
} from "../../shared/api/client";
import { birthCompletionPrompt } from "../../shared/astro/birthReadiness";

type Overview = Awaited<ReturnType<typeof getInsightOverview>>;

/** Loading, closed session, error and locked states shared by Khám phá and the overview page. */
export function InsightQueryStates({ insight }: { insight: UseQueryResult<Overview> }) {
  const supplement = useQuery({ queryKey: ["birth-supplement"], queryFn: ({ signal }) => getBirthSupplement(signal), retry: false });
  const completionPrompt = birthCompletionPrompt(supplement.data);
  const missingSession = isGuestSessionUnavailable(insight.error);
  return (
    <>
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
    </>
  );
}

function InsightLoading() {
  return <section className="insight-loading" aria-busy="true" aria-label="Đang tính Bản đồ Lá"><div className="uv-skeleton uv-skeleton--night" /><div className="uv-skeleton" /><div className="uv-skeleton" /></section>;
}
