import { ArrowRight, EyeSlash, HeartStraight, LockKey, Sparkle, Waveform } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
import "../matching/matching.css";
import "./radar.css";

export function RadarLandingPage() {
  return <main className="app-page matching-page radar-page radar-landing-page">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> Radar hợp gu</span></header>
    <section className="matching-landing__hero radar-hero">
      <img alt="" className="radar-hero-art" src="/assets/ultraviolet/pair.webp" />
      <p className="eyebrow">Có một người làm bạn hơi tò mò?</p>
      <h1>Check thử hai bạn bắt sóng ở đâu.</h1>
      <p className="matching-landing__hero-detail">Không chỉ “hợp cung” hay không. Radar đọc hai chart để tìm chỗ dễ nói chuyện, dễ rung động và cả chỗ hay cấn—mà không cần nhắn hay báo cho người ấy.</p>
      <div className="matching-landing__hero-action">
        <Link className="matching-primary" to="/radar/start">Check kín một người <ArrowRight /></Link>
        <Link className="radar-history-link" to="/radar/start#radar-history">Xem kết quả đã có</Link>
        <small>Bạn chỉ nhập thông tin sinh khi đã được người ấy cho phép dùng.</small>
      </div>
    </section>

    <section className="radar-proof" aria-labelledby="radar-value">
      <p className="eyebrow">Bạn sẽ mở được gì?</p>
      <h2 id="radar-value">Một bản đồ để hiểu nhau, không phải điểm phán xét.</h2>
      <div className="radar-proof__grid">
        <article><Sparkle /><strong>Chỗ dễ vào gu</strong><p>Điểm chạm về giao tiếp, cảm xúc, sức hút và nhịp hành động.</p></article>
        <article><Waveform /><strong>Chỗ hay lệch sóng</strong><p>Gọi đúng tên điều dễ cấn và gợi một câu hỏi đủ nhẹ để nói rõ.</p></article>
        <article><EyeSlash /><strong>Không ai bị báo</strong><p>Không gửi link, không tạo hồ sơ cho người ấy, không đưa họ vào pool tìm kiếm.</p></article>
      </div>
    </section>

    <section className="radar-how">
      <p className="eyebrow">Chạy như nào?</p>
      <ol>
        <li><span>1</span><div><strong>Bạn nhập thông tin đã được cho phép</strong><p>Ngày, giờ và nơi sinh chỉ dùng trong lúc tính; không được lưu thành hồ sơ.</p></div></li>
        <li><span>2</span><div><strong>Radar đọc hai chart</strong><p>Tìm điểm chạm về giao tiếp, cảm xúc, sức hút, nhịp hành động và chỗ dễ lệch sóng.</p></div></li>
        <li><span>3</span><div><strong>Bạn nhận bản đọc riêng</strong><p>Không phần trăm hợp nhau, không “định mệnh”; chỉ có tín hiệu cụ thể để tự kiểm chứng ngoài đời.</p></div></li>
      </ol>
    </section>

    <section className="matching-landing__privacy radar-privacy"><LockKey /><div><strong>“Kín” không có nghĩa là dùng lén dữ liệu</strong><p>Không gửi thông báo, nhưng Lá vẫn hỏi bạn xác nhận đã được phép dùng thông tin sinh. Nếu chưa, người ấy có thể tự nhập qua lời mời riêng.</p></div></section>
    <section className="matching-landing__cta"><Link className="matching-primary" to="/radar/start">Check kín ngay <ArrowRight /></Link><Link className="matching-secondary" to="/home">Để mình xem Note trước</Link></section>
    <AppNav />
  </main>;
}
