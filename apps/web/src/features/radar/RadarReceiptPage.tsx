import { Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { getRadarReceipt, withdrawRadarResult } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { RadarResultView } from "./RadarContinuePage";
import { evictRadarReadings, isTerminalDenial } from "./radarReadingCache";

export function RadarReceiptPage() {
  const queryClient = useQueryClient();
  const [withdrawn, setWithdrawn] = useState(false);
  const [unconfirmed, setUnconfirmed] = useState(false);
  const query = useQuery({
    queryKey: ["radar-receipt"],
    queryFn: ({ signal }) => getRadarReceipt(signal),
    gcTime: 0,
    refetchOnMount: "always",
    retry: false,
  });
  const withdraw = useMutation({
    mutationFn: () => withdrawRadarResult(query.data?.request_id ?? ""),
    onMutate: () => queryClient.cancelQueries({ queryKey: ["radar-receipt"] }),
    onSuccess: async () => {
      await evictRadarReadings(queryClient);
      setWithdrawn(true);
    },
    onError: async (error) => {
      await evictRadarReadings(queryClient);
      if (!isTerminalDenial(error)) setUnconfirmed(true);
    },
  });
  // A definitive denial never shows retained prose.
  const denied = query.isError && isTerminalDenial(query.error);

  if (query.isLoading || (unconfirmed && query.isFetching)) return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang mở lại bản đọc của bạn…</p></main>;
  if (withdrawn) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/pair.webp" /></div><h1>Chart của bạn đã được rút.</h1><p>Kết quả chung đã bị xóa; cả hai phía đều không thể mở lại.</p><Link className="matching-primary" to="/radar">Về Radar Hợp Gu</Link></section></main>;
  if (denied) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/moon.webp" /></div><h1>Bản đọc này không còn mở được.</h1><p>Có thể bản đọc đã hết hạn hoặc chart đã được rút.</p><Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link></section></main>;
  if (!query.data) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/moon.webp" /></div><h1>Bản đọc này không còn trên thiết bị.</h1><p>Có thể đã quá 30 ngày, bị rút hoặc dữ liệu trình duyệt đã được xóa.</p><button className="matching-primary" onClick={() => void query.refetch()} type="button">Thử mở lại</button><Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link></section></main>;

  return <>
    {unconfirmed ? <p className="matching-message radar-receipt-error" role="alert">Chưa rút được chart: bản đọc vẫn còn trên máy chủ. Bạn có thể thử rút lại.</p> : null}
    <RadarResultView
      actionLabel={unconfirmed ? "Thử rút chart lại" : "Rút chart của tôi khỏi kết quả này"}
      onWithdraw={() => withdraw.mutate()}
      result={query.data}
      withdrawing={withdraw.isPending}
    />
  </>;
}
