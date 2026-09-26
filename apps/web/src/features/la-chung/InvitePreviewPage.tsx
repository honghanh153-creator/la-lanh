import { ArrowLeft, Check, Copy, PaperPlaneTilt, ShieldCheck } from "@phosphor-icons/react";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ApiProblem, claimOwner, createLaChungInvite, type LaChungInvite } from "../../shared/api/client";
import "./la-chung.css";

type Draft = { recipientLabel: string; context: "bff" | "crush" | "couple" | "friend" | "workmate" };

export function InvitePreviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const draft = location.state as Draft | null;
  const [invite, setInvite] = useState<LaChungInvite | null>(null);
  const [idempotencyKey] = useState(() => crypto.randomUUID().replaceAll("-", ""));
  const [checkpoint, setCheckpoint] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const create = useMutation({
    mutationFn: () => createLaChungInvite({
      recipient_label: draft!.recipientLabel,
      context: draft!.context,
      idempotency_key: idempotencyKey,
    }),
    onSuccess: (payload) => { setInvite(payload); setMessage("Link đã sẵn sàng. Chưa có trạng thái đã gửi hay đã xem."); },
    onError: (error) => { if (error instanceof ApiProblem && error.status === 401) setCheckpoint(true); else setMessage("Chưa tạo được link. Draft vẫn còn nguyên."); },
  });
  const claim = useMutation({
    mutationFn: claimOwner,
    onSuccess: () => { setCheckpoint(false); create.mutate(); },
    onError: () => setMessage("Chưa xác nhận được quyền sở hữu trên thiết bị này."),
  });
  if (!draft) return <main className="flow-page la-chung-page"><section className="cosmic-state"><h1>Draft không còn trên máy.</h1><p>Để bảo mật, Lá Lành không lưu nháp này vào trình duyệt.</p><Link to="/la-chung">Tạo lại lời mời</Link></section></main>;

  const fullUrl = invite?.share_url ? new URL(invite.share_url, window.location.origin).toString() : null;
  const copy = async () => { if (!fullUrl) return; try { await navigator.clipboard.writeText(fullUrl); setMessage("Đã copy link."); } catch { setMessage("Chưa copy được. Hãy dùng bảng chia sẻ."); } };
  const share = async () => { if (!fullUrl) return; try { await navigator.share({ title: "Một Lá Chứng dành cho bạn", text: "Chọn giúp mình vài câu nhé — không cần tài khoản.", url: fullUrl }); setMessage("Bảng chia sẻ đã đóng. Link vẫn ở trạng thái chờ."); } catch (error) { setMessage(error instanceof DOMException && error.name === "AbortError" ? "Bạn đã đóng bảng chia sẻ. Link vẫn còn nguyên." : "Chưa mở được bảng chia sẻ. Bạn có thể copy link."); } };

  return <main className="flow-page la-chung-page">
    <header className="cosmic-header"><button className="icon-button" onClick={() => void navigate(-1)} type="button"><ArrowLeft /></button><span className="eyebrow">Preview</span><span /></header>
    <section className="invite-preview-card"><p>Gửi tới · {draft.recipientLabel}</p><h1>Mình muốn biết<br />bạn nhìn thấy gì ở mình.</h1><blockquote>Chọn 3–5 câu gần nhất. Không cần tài khoản, ngày sinh hay danh bạ.</blockquote><small>Lá Chứng · tự hết hạn sau 7 ngày</small></section>
    <section className="disclosure-list"><p><Check /> Người nhận thấy tên gọi “{draft.recipientLabel}” và bộ câu đã kiểm duyệt.</p><p><Check /> Mặc định họ phản hồi ẩn danh.</p><p><Check /> Link không có read receipt.</p></section>
    {checkpoint ? <section className="owner-checkpoint" role="dialog" aria-modal="true"><ShieldCheck size={34} /><h2>Giữ Lá Chứng thuộc về bạn</h2><p>Đây là lúc cần xác nhận thiết bị để bạn có thể thu hồi link và xem phản hồi. Bản local chưa có khôi phục trên máy mới.</p><button className="electric-button" disabled={claim.isPending} onClick={() => claim.mutate()} type="button">Xác nhận & tiếp tục</button><button className="text-button" onClick={() => setCheckpoint(false)} type="button">Để sau</button></section> : null}
    {message ? <p className="success-message" role="status">{message}</p> : null}
    {!invite ? <button className="electric-button" disabled={create.isPending} onClick={() => create.mutate()} type="button">Tạo link riêng tư</button> : <section className="share-actions"><button className="electric-button" onClick={() => void share()} type="button"><PaperPlaneTilt /> Chia sẻ</button><button className="outline-button" onClick={() => void copy()} type="button"><Copy /> Copy link</button><button className="text-button" onClick={() => void navigate("/la-chung/history")} type="button">Xong · xem trạng thái</button></section>}
  </main>;
}
