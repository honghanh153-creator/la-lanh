import { ArrowLeft, LinkSimple, Prohibit } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  listLaChungInvites,
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
  const revoke = useMutation({ mutationFn: revokeLaChungInvite, onSuccess: () => cache.invalidateQueries({ queryKey: ["la-chung-invites"] }) });

  return <main className="flow-page la-chung-page">
    <header className="cosmic-header"><Link className="icon-button" to="/la-chung"><ArrowLeft /></Link><span className="eyebrow">Dữ liệu Lá Chứng cũ</span><span /></header>
    <section className="insight-hero"><h1>Quản lý những gì đã có.</h1><p>Không thể tạo hoặc gửi lại link mới. Bạn vẫn có thể thu hồi lời mời đang chờ, ẩn hoặc xóa kết quả cũ.</p></section>
    {query.isError ? <section className="cosmic-state"><h2>Chưa mở được danh sách.</h2><p>Thiết bị này có thể chưa được xác nhận.</p><Link to="/la-chung">Quay lại Lá Chứng</Link></section> : null}
    {query.data?.length === 0 ? <section className="cosmic-state"><LinkSimple size={34} /><h2>Không có dữ liệu Lá Chứng cũ.</h2><Link to="/home">Về Lá Lành</Link></section> : null}
    <section className="invite-list">{query.data?.map((invite) => <article key={invite.id}>
      <div><span className={`status-chip status-chip--${invite.status}`}>{statusLabel[invite.status] ?? invite.status}</span><h2>{invite.recipient_label}</h2><p>{contextLabel[invite.context] ?? invite.context} · hết hạn {new Date(invite.expires_at).toLocaleDateString("vi-VN")}</p></div>
      {invite.status === "completed" ? <Link className="outline-button" to={`/la-chung/result/${invite.id}`}>Xem Lá Chứng</Link> : null}
      {invite.status === "pending" ? <button className="outline-button" disabled={revoke.isPending} onClick={() => revoke.mutate(invite.id)} type="button"><Prohibit /> Thu hồi lời mời</button> : null}
    </article>)}</section>
  </main>;
}
