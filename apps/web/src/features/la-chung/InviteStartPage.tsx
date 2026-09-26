import { ArrowLeft, ArrowRight, EyeSlash, ShieldCheck, Sparkle } from "@phosphor-icons/react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { BrandMark } from "../../shared/ui/BrandMark";
import "./la-chung.css";

const contexts = [
  ["bff", "BFF", "người hiểu những phiên bản kỳ lạ nhất của bạn"],
  ["crush", "Crush", "một người bạn muốn nghe góc nhìn thật"],
  ["couple", "Couple", "người đang cùng bạn xây một nhịp chung"],
  ["friend", "Bạn bè", "một người đã nhìn thấy bạn qua nhiều mùa"],
  ["workmate", "Đồng đội", "người từng làm việc và va chạm cùng bạn"],
] as const;

export function InviteStartPage() {
  const navigate = useNavigate();
  const [started, setStarted] = useState(false);
  const [label, setLabel] = useState("");
  const [context, setContext] = useState<(typeof contexts)[number][0]>("bff");
  const valid = label.trim().length > 0 && label.trim().length <= 40;

  return <main className="flow-page la-chung-page">
    <header className="cosmic-header"><Link className="icon-button" to="/home"><ArrowLeft /></Link><BrandMark /><Link className="text-link" to="/la-chung/history">Đã gửi</Link></header>
    {!started ? <>
      <section className="witness-hero">
        <span className="witness-orbit"><Sparkle weight="fill" /></span>
        <p className="eyebrow">Lá Chứng · một lời nhắc từ người thật</p>
        <h1>Bạn hiện lên thế nào trong mắt ai đó?</h1>
        <p>Mời đúng một người chọn vài câu đã được Lá Lành kiểm duyệt. Không chấm điểm. Không đăng công khai.</p>
      </section>
      <section className="privacy-bento">
        <article><EyeSlash /><strong>Mặc định ẩn danh</strong><p>Họ không cần tài khoản hay cung cấp ngày sinh.</p></article>
        <article><ShieldCheck /><strong>Bạn kiểm soát link</strong><p>Thu hồi bất cứ lúc nào, tự hết hạn sau 7 ngày.</p></article>
      </section>
      <button className="electric-button" onClick={() => setStarted(true)} type="button">Tạo một Lá Chứng <ArrowRight /></button>
    </> : <>
      <section className="insight-hero"><p className="eyebrow">01 · Chọn người</p><h1>Một người là đủ.</h1><p>Tên gọi này chỉ giúp bạn nhớ lời mời dành cho ai.</p></section>
      <label className="cosmic-field"><span>Bạn gọi họ là gì?</span><input autoComplete="off" maxLength={40} onChange={(event) => setLabel(event.target.value)} placeholder="ví dụ: An, bestie, người ấy…" value={label} /><small>{label.length}/40 · không nhập số điện thoại hay email</small></label>
      <fieldset className="context-grid"><legend>Hai bạn là…</legend>{contexts.map(([value, title, detail]) => <button aria-pressed={context === value} className={context === value ? "is-active" : ""} key={value} onClick={() => setContext(value)} type="button"><strong>{title}</strong><small>{detail}</small></button>)}</fieldset>
      <button className="electric-button" disabled={!valid} onClick={() => void navigate("/la-chung/preview", { state: { recipientLabel: label.trim(), context } })} type="button">Xem trước lời mời <ArrowRight /></button>
    </>}
  </main>;
}
