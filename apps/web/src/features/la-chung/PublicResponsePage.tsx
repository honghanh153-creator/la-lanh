import { ArrowLeft, ArrowRight, Check, EyeSlash, Flag, Sparkle } from "@phosphor-icons/react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getPublicLaChungInvite, reportLaChungInvite, submitLaChungResponse, withdrawLaChungResponse } from "../../shared/api/client";
import "./la-chung.css";

type Step = "landing" | "select" | "review" | "done";

export function PublicResponsePage() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>("landing");
  const [selected, setSelected] = useState<string[]>([]);
  const [identity, setIdentity] = useState<"anonymous" | "alias">("anonymous");
  const [alias, setAlias] = useState("");
  const [showReport, setShowReport] = useState(false);
  const idempotencyKey = useMemo(() => crypto.randomUUID(), []);
  const invite = useQuery({ queryKey: ["public-la-chung", token], queryFn: ({ signal }) => getPublicLaChungInvite(token, signal), retry: false });
  const submit = useMutation({ mutationFn: () => submitLaChungResponse(token, { statement_ids: selected, identity_mode: identity, display_alias: identity === "alias" ? alias : null, idempotency_key: idempotencyKey }), onSuccess: () => setStep("done") });
  const withdraw = useMutation({ mutationFn: withdrawLaChungResponse });
  const report = useMutation({
    mutationFn: (reason: "not_for_me" | "unsafe" | "spam" | "other") => reportLaChungInvite(token, reason),
  });
  const toggle = (id: string) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 5 ? [...current, id] : current);

  if (invite.isLoading) return <main className="public-la-page"><section className="public-signal"><span /><p>Đang mở một lời nhắc nhỏ…</p></section></main>;
  if (!invite.data) return <main className="public-la-page"><section className="safe-terminal"><Sparkle size={36} /><h1>Lá này không còn mở.</h1><p>Link có thể đã hết hạn, được thu hồi hoặc đã có người phản hồi. Lá Lành không tiết lộ thêm để bảo vệ người gửi.</p><button onClick={() => window.close()} type="button">Đóng</button></section></main>;

  return <main className="public-la-page">
    <header className="public-header"><span className="mini-brand">Lá Lành*</span><button aria-label="Báo cáo lời mời" onClick={() => setShowReport(true)} type="button"><Flag /></button></header>
    {showReport ? <section aria-modal="true" className="report-sheet" role="dialog"><div><p className="eyebrow">An toàn của bạn</p><h2>Bạn muốn báo điều gì?</h2>{report.isSuccess ? <><p>Cảm ơn bạn. Báo cáo đã được ghi nhận mà không tiết lộ danh tính.</p><button className="outline-button" onClick={() => setShowReport(false)} type="button">Đóng</button></> : <><button onClick={() => report.mutate("not_for_me")} type="button">Lời mời không dành cho tôi</button><button onClick={() => report.mutate("unsafe")} type="button">Khiến tôi không an toàn</button><button onClick={() => report.mutate("spam")} type="button">Spam hoặc lạm dụng</button><button className="text-button" onClick={() => setShowReport(false)} type="button">Hủy</button></>}</div></section> : null}
    {step === "landing" ? <section className="public-landing"><span className="witness-orbit"><Sparkle weight="fill" /></span><p className="eyebrow">Một Lá Chứng dành cho {invite.data.recipient_label}</p><h1>Ai đó muốn nghe bạn nhìn thấy gì ở họ.</h1><p>Bạn chỉ chọn 3–5 câu có sẵn. Không viết tự do, không cần tài khoản.</p><div className="public-privacy"><EyeSlash /><span><strong>Ẩn danh là mặc định</strong><small>Người gửi chỉ thấy những câu bạn chọn.</small></span></div><button className="electric-button" onClick={() => setStep("select")} type="button">Bắt đầu · khoảng 1 phút <ArrowRight /></button><small>{invite.data.privacy_note}</small></section> : null}
    {step === "select" ? <section className="statement-step"><header><button className="icon-button" onClick={() => setStep("landing")} type="button"><ArrowLeft /></button><div><p className="eyebrow">Chọn điều gần nhất</p><strong>{selected.length}/5</strong></div></header><h1>Ở họ, bạn thấy…</h1><div className="statement-list">{invite.data.statements.map((statement) => <button aria-pressed={selected.includes(statement.id)} key={statement.id} onClick={() => toggle(statement.id)} type="button"><span>{statement.text}</span>{selected.includes(statement.id) ? <Check weight="bold" /> : null}</button>)}</div><div className="sticky-public-action"><p>{selected.length < 3 ? `Chọn thêm ${3 - selected.length} câu` : "Đủ rồi — bạn vẫn có thể chọn tối đa 5"}</p><button className="electric-button" disabled={selected.length < 3} onClick={() => setStep("review")} type="button">Xem lại <ArrowRight /></button></div></section> : null}
    {step === "review" ? <section className="review-step"><button className="text-button" onClick={() => setStep("select")} type="button">← Chỉnh lựa chọn</button><p className="eyebrow">Trước khi gửi</p><h1>Chỉ những điều này sẽ tới người gửi.</h1><div className="review-statements">{invite.data.statements.filter((item) => selected.includes(item.id)).map((item) => <p key={item.id}><Check /> {item.text}</p>)}</div><fieldset><legend>Bạn muốn hiện diện thế nào?</legend><label><input checked={identity === "anonymous"} name="identity" onChange={() => setIdentity("anonymous")} type="radio" /> Ẩn danh <small>khuyên dùng</small></label><label><input checked={identity === "alias"} name="identity" onChange={() => setIdentity("alias")} type="radio" /> Dùng biệt danh</label>{identity === "alias" ? <input maxLength={24} onChange={(event) => setAlias(event.target.value)} placeholder="1–24 ký tự · không email/số điện thoại" value={alias} /> : null}</fieldset>{submit.isError ? <p role="alert">Chưa gửi được. Bạn có thể thử lại; Lá Lành không tạo phản hồi trùng.</p> : null}<button className="electric-button" disabled={submit.isPending || (identity === "alias" && !alias.trim())} onClick={() => submit.mutate()} type="button">Gửi Lá Chứng</button></section> : null}
    {step === "done" ? <section className="receipt-step"><span className="witness-orbit"><Check weight="bold" /></span><p className="eyebrow">Đã gửi</p><h1>Một góc nhìn thật đã tới đúng chỗ.</h1><p>Bạn có thể rút phản hồi trên thiết bị này trong thời hạn link.</p>{withdraw.isSuccess ? <p className="success-message">Phản hồi đã được rút và không còn hiển thị.</p> : <button className="outline-button" disabled={withdraw.isPending} onClick={() => withdraw.mutate()} type="button">Quản lý · rút phản hồi</button>}<button className="text-button" onClick={() => void navigate("/welcome")} type="button">Tìm hiểu Lá Lành</button></section> : null}
  </main>;
}
