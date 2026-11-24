import { ArrowRight, HeartStraight, Sparkle, Waveform } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";
import { NightSky } from "../../shared/ui/NightSky";

/** Owner-approved sentence 2 (AP2, 21.11.2026; privacy.radar.invite-first.owner-invite-body), word
 *  for word; a test keeps it equal to the copy registry. */
export const INVITE_BODY = "Người ấy chỉ cần nhập ngày sinh của mình và bấm đồng ý. Lá không lưu ngày sinh đó. Kết quả giữ 30 ngày, ai trong hai bạn cũng xoá được.";

export function RadarLandingPage() {
  return <main className="app-page matching-page radar-page radar-landing-page">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> Hợp gu</span></header>
    <section className="matching-landing__hero radar-hero">
      <NightSky stars={4} />
      <img alt="" className="radar-hero-art" src="/assets/ultraviolet/pair.webp" />
      <p className="eyebrow">Có một người làm bạn hơi tò mò?</p>
      <h1>Xem hai bạn hợp nhau ở đâu.</h1>
      <p className="matching-landing__hero-detail">Biết chỗ hai người dễ nói chuyện, dễ thích nhau và hay vướng.</p>
      <div className="matching-landing__hero-action">
        <Link className="matching-primary" to="/radar/start">Xem hợp gu với một người <ArrowRight /></Link>
        <nav aria-label="Xem lại kết quả" className="radar-landing-history">
          <Link className="radar-history-link" to="/radar/start#radar-history"><strong>Người bạn đã xem</strong> <span>Mở lại kết quả cũ</span></Link>
          <Link className="radar-history-link" to="/radar/received"><strong>Kết quả bạn đã nhận</strong> <span>Khi có người mời bạn</span></Link>
        </nav>
      </div>
    </section>

    <section className="radar-proof" aria-labelledby="radar-value">
      <p className="eyebrow">Bạn nhận được gì?</p>
      <h2 id="radar-value">Một bản đọc ngắn, không phải điểm số.</h2>
      <div className="radar-proof__grid">
        <article><Sparkle /><strong>Chỗ dễ hợp</strong><p>Hai bạn dễ nói chuyện, dễ hiểu nhau ở những chuyện nào.</p></article>
        <article><Waveform /><strong>Chỗ dễ vướng</strong><p>Chuyện gì dễ làm hai bạn khó chịu, kèm một câu hỏi nhẹ để nói rõ với nhau.</p></article>
      </div>
    </section>

    <section className="radar-how">
      <p className="eyebrow">Làm thế nào?</p>
      <ol>
        <li><span>1</span><div><strong>Bạn gửi link cho người ấy</strong><p>{INVITE_BODY}</p></div></li>
        <li><span>2</span><div><strong>Lá xem lá số của hai người</strong><p>Gồm cách hai bạn nói chuyện, cảm xúc, điều làm hai bạn để ý nhau, cách cùng làm việc và chỗ dễ vướng.</p></div></li>
        <li><span>3</span><div><strong>Bạn nhận bản đọc riêng</strong><p>Một bậc có tên kèm lý do, vài mảng hợp hoặc cần để ý, và một gợi ý nhỏ để thử. Đây không phải xác suất thành đôi; hãy đối chiếu với cách hai bạn thật sự tương tác.</p></div></li>
      </ol>
    </section>

    <section className="matching-landing__cta"><Link className="matching-primary" to="/radar/start">Bắt đầu xem <ArrowRight /></Link><Link className="matching-secondary" to="/home">Để mình xem Note trước</Link></section>
    <AppNav />
  </main>;
}
