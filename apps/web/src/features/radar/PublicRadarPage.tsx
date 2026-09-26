import { ArrowRight, EyeSlash, LockKey, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";

import { declineRadarInvite, getPublicRadarInvite } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { RADAR_PENDING_REQUEST_KEY } from "./radarOptions";

export function PublicRadarPage() {
  const navigate = useNavigate();
  const token = useParams().token ?? "";
  const query = useQuery({ queryKey: ["public-radar", token], queryFn: ({ signal }) => getPublicRadarInvite(token, signal), retry: false });
  const decline = useMutation({
    mutationFn: () => declineRadarInvite(query.data?.request_id ?? ""),
    onSuccess: () => {
      sessionStorage.removeItem(RADAR_PENDING_REQUEST_KEY);
      void navigate("/", { replace: true });
    },
  });
  if (query.isLoading) return <main className="matching-page matching-page--loading"><Sparkle className="matching-pulse" /><p>Đang bắt link Radar…</p></main>;
  if (!query.data) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card"><h1>Link này không còn hoạt động.</h1><p>Có thể link đã hết hạn, bị thu hồi hoặc đã được dùng.</p><Link className="matching-primary" to="/radar">Tìm hiểu Radar Hợp Gu</Link></section></main>;
  const invite = query.data;
  const continueFlow = () => sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, invite.request_id);
  return <main className="matching-page radar-public">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><LockKey /> link riêng</span></header>
    <RadarFlowSteps current={1} />
    <section className="radar-public__signal"><span><Sparkle weight="fill" /></span><p className="eyebrow">Có người muốn check độ bắt sóng</p><h1>{invite.recipient_label}, bật Radar cùng họ?</h1><p>Radar đặt hai birth chart cạnh nhau để đọc nhịp giao tiếp, cảm xúc, sức hút và chỗ dễ lệch sóng.</p></section>
    <section className="radar-public__card"><article><EyeSlash /><div><strong>Dữ liệu sinh không được trao đổi</strong><p>Người gửi không nhìn thấy ngày, giờ hay nơi sinh của bạn.</p></div></article><article><ShieldCheck /><div><strong>Bạn quyết định riêng cho lần này</strong><p>Chưa đồng ý thì Radar chưa tính. Bạn có thể rút kết quả sau đó.</p></div></article><article><LockKey /><div><strong>Không phải lời phán</strong><p>Không điểm hợp nhau, không suy ra ý định hay độ an toàn của một người.</p></div></article></section>
    <Link className="matching-primary" onClick={continueFlow} to="/radar/continue">Xem mình cần làm gì <ArrowRight /></Link>
    {decline.isError ? <p className="matching-message" role="alert">Chưa đóng được lời mời. Dữ liệu chưa thay đổi—bạn có thể thử lại.</p> : null}
    <button className="matching-secondary" disabled={decline.isPending} onClick={() => decline.mutate()} type="button">{decline.isPending ? "Đang đóng lời mời…" : decline.isError ? "Thử đóng lại" : "Không tham gia"}</button>
  </main>;
}
