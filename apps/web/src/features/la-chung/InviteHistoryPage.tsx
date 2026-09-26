import { ArrowClockwise, ArrowLeft, LinkSimple, Prohibit } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  listLaChungInvites,
  replaceLaChungInvite,
  resendLaChungInvite,
  revokeLaChungInvite,
} from "../../shared/api/client";
import "./la-chung.css";

const statusLabel: Record<string, string> = {
  pending: "Đang chờ phản hồi",
  completed: "Đã có Lá Chứng",
  revoked: "Đã thu hồi",
  expired: "Đã hết hạn",
};

const contextLabel: Record<string, string> = {
  bff: "BFF",
  crush: "Crush",
  couple: "Couple",
  friend: "Bạn bè",
  workmate: "Đồng đội",
};

export function InviteHistoryPage() {
  const cache = useQueryClient();
  const query = useQuery({
    queryKey: ["la-chung-invites"],
    queryFn: ({ signal }) => listLaChungInvites(signal),
    retry: false,
  });
  const copyShareUrl = async (shareUrl?: string | null) => {
    if (shareUrl) await navigator.clipboard.writeText(new URL(shareUrl, window.location.origin).toString());
  };
  const resend = useMutation({ mutationFn: resendLaChungInvite, onSuccess: (invite) => copyShareUrl(invite.share_url) });
  const revoke = useMutation({ mutationFn: revokeLaChungInvite, onSuccess: () => cache.invalidateQueries({ queryKey: ["la-chung-invites"] }) });
  const replace = useMutation({ mutationFn: replaceLaChungInvite, onSuccess: async (invite) => { await cache.invalidateQueries({ queryKey: ["la-chung-invites"] }); await copyShareUrl(invite.share_url); } });

  return <main className="flow-page la-chung-page">
    <header className="cosmic-header"><Link className="icon-button" to="/la-chung"><ArrowLeft /></Link><span className="eyebrow">Lá Chứng đã tạo</span><span /></header>
    <section className="insight-hero"><h1>Những Lá Chứng của bạn.</h1><p>Link đang chờ không có read receipt; khi có phản hồi, Lá sẽ hiện rõ tại đây.</p></section>
    {query.isError ? <section className="cosmic-state"><h2>Chưa mở được danh sách.</h2><p>Thiết bị này có thể chưa được xác nhận.</p><Link to="/la-chung">Quay lại Lá Chứng</Link></section> : null}
    {query.data?.length === 0 ? <section className="cosmic-state"><LinkSimple size={34} /><h2>Chưa có lời mời nào.</h2><Link to="/la-chung">Tạo Lá Chứng đầu tiên</Link></section> : null}
    <section className="invite-list">{query.data?.map((invite) => <article key={invite.id}>
      <div><span className={`status-chip status-chip--${invite.status}`}>{statusLabel[invite.status] ?? invite.status}</span><h2>{invite.recipient_label}</h2><p>{contextLabel[invite.context] ?? invite.context} · hết hạn {new Date(invite.expires_at).toLocaleDateString("vi-VN")}</p></div>
      {invite.status === "completed" ? <Link className="outline-button" to={`/la-chung/result/${invite.id}`}>Xem Lá Chứng</Link> : null}
      {invite.status === "pending" ? <div className="compact-actions">
        <button onClick={() => resend.mutate(invite.id)} type="button"><ArrowClockwise /> Gửi lại link</button>
        <button onClick={() => revoke.mutate(invite.id)} type="button"><Prohibit /> Thu hồi</button>
        <button onClick={() => replace.mutate(invite.id)} type="button"><LinkSimple /> Thay link</button>
      </div> : null}
      {invite.status === "revoked" || invite.status === "expired" ? <button className="outline-button" onClick={() => replace.mutate(invite.id)} type="button"><LinkSimple /> Tạo link mới</button> : null}
    </article>)}</section>
  </main>;
}
