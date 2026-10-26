import { ArrowRight, EyeSlash, LockKey, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { declineRadarInvite, getPublicRadarInvite, withdrawRadarByInvite } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { RadarFlowSteps } from "./RadarFlowSteps";
import { radarVoiceLabel, RADAR_PENDING_REQUEST_KEY } from "./radarOptions";
import { WithdrawSheet } from "./RadarReceivedPage";

export function PublicRadarPage() {
  return <div className="app-shell ultraviolet-app"><PublicRadarContent /></div>;
}

function PublicRadarContent() {
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
  if (!query.data) return <UsedInvite token={token} />;
  const invite = query.data;
  const continueFlow = () => sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, invite.request_id);
  return <main className="matching-page radar-public">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><LockKey /> link riêng</span></header>
    <RadarFlowSteps current={1} />
    <section className="radar-public__signal"><span><Sparkle weight="fill" /></span><p className="eyebrow">Có người muốn check độ bắt sóng</p><h1>{invite.recipient_label}, bật Radar cùng họ?</h1><p>Radar đặt hai birth chart cạnh nhau để đọc nhịp giao tiếp, cảm xúc, sức hút và chỗ dễ lệch sóng.</p></section>
    <section className="radar-public__card"><article><EyeSlash /><div><strong>Dữ liệu sinh không được trao đổi</strong><p>Người gửi không nhìn thấy ngày, giờ hay nơi sinh của bạn.</p></div></article><article><ShieldCheck /><div><strong>Bạn quyết định riêng cho lần này</strong><p>Chưa đồng ý thì Radar chưa tính. Bạn có thể rút kết quả sau đó.</p></div></article><article><LockKey /><div><strong>Giọng đọc: {radarVoiceLabel(invite.voice)}</strong><p>Bạn biết trước cách Radar sẽ nói. Đây không phải lời phán hay xác suất thành công.</p></div></article></section>
    <Link className="matching-primary" onClick={continueFlow} to="/radar/continue">Xem mình cần làm gì <ArrowRight /></Link>
    {decline.isError ? <p className="matching-message" role="alert">Chưa đóng được lời mời. Dữ liệu chưa thay đổi—bạn có thể thử lại.</p> : null}
    <button className="matching-secondary" disabled={decline.isPending} onClick={() => decline.mutate()} type="button">{decline.isPending ? "Đang đóng lời mời…" : decline.isError ? "Thử đóng lại" : "Không tham gia"}</button>
  </main>;
}

// P09 D2: a used invite no longer previews. Whoever holds the link may still withdraw the result; this page
// never opens the reading, because the person who sent the link holds it too.
function UsedInvite({ token }: { token: string }) {
  const [confirming, setConfirming] = useState(false);
  const withdraw = useMutation({ mutationFn: () => withdrawRadarByInvite(token) });
  if (withdraw.isSuccess) return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty"><div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/pair.webp" /></div><h1>Chart của bạn đã được rút.</h1><p>Kết quả chung đã bị xóa; cả hai phía đều không thể mở lại.</p><Link className="matching-primary" to="/radar">Về Radar Hợp Gu</Link></section></main>;
  return <main className="matching-page radar-public"><BrandMark /><section className="radar-public__card uv-empty">
    <div aria-hidden="true" className="uv-empty-art"><img alt="" src="/assets/ultraviolet/moon.webp" /></div>
    <h1>Link này không còn mở lời mời.</h1>
    <p>Có thể link đã hết hạn, bị thu hồi hoặc đã được dùng. Nếu bạn là người đã đồng ý và muốn rút chart của mình khỏi kết quả, bạn có thể làm ngay tại đây. Trang này không mở lại bản đọc.</p>
    {withdraw.isError ? <p className="matching-message" role="alert">Link này không còn dùng được. Có thể kết quả đã hết hạn hoặc đã được rút trước đó.</p> : null}
    <button className="matching-primary" disabled={withdraw.isPending} onClick={() => setConfirming(true)} type="button">{withdraw.isPending ? "Đang rút chart…" : "Rút chart khỏi kết quả"}</button>
    <Link className="matching-secondary" to="/radar/received">Xem kết quả bạn đã nhận</Link>
    <Link className="matching-secondary" to="/radar">Tìm hiểu Radar Hợp Gu</Link>
    <WithdrawSheet onCancel={() => setConfirming(false)} onConfirm={() => { setConfirming(false); withdraw.mutate(); }} open={confirming} pending={withdraw.isPending} />
  </section></main>;
}
