import { ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { getRadarReceipt, withdrawRadarResult } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { RadarResultView } from "./RadarContinuePage";

export function RadarReceiptPage() {
  const queryClient = useQueryClient();
  const [withdrawn, setWithdrawn] = useState(false);
  const query = useQuery({
    queryKey: ["radar-receipt"],
    queryFn: ({ signal }) => getRadarReceipt(signal),
    retry: false,
  });
  const withdraw = useMutation({
    mutationFn: () => withdrawRadarResult(query.data?.request_id ?? ""),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["radar-receipt"] });
      setWithdrawn(true);
    },
  });

  if (query.isLoading) return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang mở lại bản đọc của bạn…</p></main>;
  if (withdrawn) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card"><ShieldCheck /><h1>Chart của bạn đã được rút.</h1><p>Kết quả chung đã bị xóa; cả hai phía đều không thể mở lại.</p><Link className="matching-primary" to="/radar">Về Radar Hợp Gu</Link></section></main>;
  if (!query.data) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card"><h1>Bản đọc này không còn trên thiết bị.</h1><p>Có thể đã quá 7 ngày, bị rút hoặc dữ liệu trình duyệt đã được xóa.</p><button className="matching-primary" onClick={() => void query.refetch()} type="button">Thử mở lại</button><Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link></section></main>;

  return <>
    {withdraw.isError ? <p className="matching-message radar-receipt-error" role="alert">Chưa rút được chart. Kết quả vẫn được giữ nguyên; kiểm tra mạng rồi thử lại.</p> : null}
    <RadarResultView
      actionLabel={withdraw.isError ? "Thử rút chart lại" : "Rút chart của tôi khỏi kết quả này"}
      onWithdraw={() => withdraw.mutate()}
      result={query.data}
      withdrawing={withdraw.isPending}
    />
  </>;
}
