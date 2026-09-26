import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { deleteRadarResult, getRadarResult } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { RadarResultView } from "./RadarContinuePage";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { RADAR_HISTORY_QUERY_KEY, useRadarOwnerBinding } from "./useRadarOwnerBinding";

export function RadarOwnerResultPage() {
  const requestId = useParams().requestId ?? "";
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const owner = useRadarOwnerBinding();
  const query = useQuery({ queryKey: ["radar-result", owner.epoch, requestId], queryFn: ({ signal }) => getRadarResult(requestId, signal), enabled: owner.isReady && Boolean(requestId), retry: false });
  const remove = useMutation({
    mutationFn: () => deleteRadarResult(requestId),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: ["radar-result", owner.epoch, requestId] });
      void queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY });
      const destination = query.data?.mode === "consented_invite" ? "/radar/invite#radar-history" : "/radar/start#radar-history";
      void navigate(destination, { replace: true });
    },
  });
  if (owner.isPending || query.isLoading) return <main className="matching-page matching-page--loading"><p>Đang mở lại tín hiệu…</p></main>;
  if (owner.isError) return <main className="matching-page radar-public"><header className="matching-header"><BrandMark /></header><section className="radar-public__card"><h1>Chưa nối được đúng phiên chart.</h1><p>Kết quả không được hiển thị cho đến khi Radar xác nhận đúng người sở hữu.</p><button className="matching-primary" onClick={owner.retry} type="button">Thử nối lại</button><Link className="matching-secondary" to="/radar">Về Radar</Link></section></main>;
  if (query.isError && !query.data) return <main className="matching-page radar-public"><header className="matching-header"><BrandMark /></header><RadarFlowSteps current={3} /><section className="radar-public__card radar-missing-result"><h1>Kết quả này không còn khả dụng.</h1><p>Có thể bản đọc đã hết hạn hoặc đã được xóa. Bạn vẫn có thể bắt đầu một lần check mới.</p><button className="matching-secondary" onClick={() => void query.refetch()} type="button">Thử mở lại</button><Link className="matching-primary" to="/radar/start">Check một người khác</Link><Link className="matching-secondary" to="/radar">Về Radar Hợp Gu</Link></section></main>;
  if (!query.data) return null;
  return <><RadarResultView actionLabel={confirmingDelete ? "Chạm lại để xóa hẳn kết quả" : "Xóa kết quả này"} onWithdraw={() => { if (confirmingDelete) remove.mutate(); else setConfirmingDelete(true); }} ownerView result={query.data} withdrawing={remove.isPending} />{remove.isError ? <p className="matching-message radar-receipt-error" role="alert">Chưa xóa được kết quả. Dữ liệu vẫn còn nguyên; thử lại khi mạng ổn định.</p> : null}</>;
}
