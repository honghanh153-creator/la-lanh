import {
  ArrowRight,
  EyeSlash,
  HeartStraight,
  ShieldCheck,
  Sparkle,
  Waveform,
} from "@phosphor-icons/react";
import { useState } from "react";
import { Link } from "react-router-dom";

import {
  registerMatchingIntroVisit,
  type MatchingIntroVisit,
} from "../../shared/storage/matchingIntroExposure";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";
import "./matching.css";

const benefits = [
  {
    icon: Waveform,
    title: "Biết vì sao dễ bắt chuyện",
    detail: "Khi vòng ghép mở, mỗi gợi ý sẽ đi kèm nhịp giao tiếp và một kiểu mở lời có lý do.",
  },
  {
    icon: Sparkle,
    title: "Thấy chỗ dễ lệch nhịp",
    detail: "Không chấm điểm hợp hay không. Lá sẽ gọi tên điểm cần nói rõ, nhịp cần chậm và ranh giới nên giữ.",
  },
  {
    icon: HeartStraight,
    title: "Ít hơn, nhưng có lý do",
    detail: "Mỗi vòng dự kiến có tối đa năm lá úp theo năm kiểu kết nối, thay vì một feed vuốt mãi không hết.",
  },
] as const;

const introByVisit: Record<MatchingIntroVisit, {
  eyebrow: string;
  title: string;
  detail: string;
  cta: string;
  note: string;
}> = {
  1: {
    eyebrow: "Gu của bạn đâu chỉ có một kiểu",
    title: "Có kiểu người nào cứ làm bạn nghĩ mãi?",
    detail: "Vòng Lá bắt đầu bằng điều bạn thật sự muốn. Khi vòng ghép mở, chart sẽ giúp gợi tối đa năm người có một lý do đáng thử nói chuyện.",
    cta: "Bật radar hợp gu",
    note: "Bước đầu là đặt ranh giới · chưa vào pool cho tới khi bạn đồng ý.",
  },
  2: {
    eyebrow: "Không chỉ là hợp cung",
    title: "Bắt sóng ở đâu? Dễ cấn ở chỗ nào?",
    detail: "Bạn sẽ thấy nhịp giao tiếp dễ vào, chỗ hai người có thể lệch sóng và ranh giới nên giữ — trước khi quyết định mở lời.",
    cta: "Tạo hồ sơ hợp gu",
    note: "Bạn đặt intent và ranh giới trước · Lá chưa ghép ai ở bước này.",
  },
  3: {
    eyebrow: "Đừng swipe thêm vội",
    title: "Thử một vòng có lý do.",
    detail: "Không feed vô tận, không điểm hợp công khai. Bắt đầu bằng một hồ sơ có chủ đích; năm gợi ý chỉ mở khi các chốt an toàn đã sẵn sàng.",
    cta: "Vào trạm ghép",
    note: "Không GPS · chưa gửi request hay tự nhắn ai ở bước này.",
  },
};

export function MatchingLandingPage() {
  const [visit] = useState(registerMatchingIntroVisit);
  const intro = introByVisit[visit];

  return <main className="app-page matching-page matching-landing">
    <header className="matching-header"><BrandMark /><span className="matching-signal"><HeartStraight weight="fill" /> Vòng Lá</span></header>

    <section className="matching-landing__hero">
      <div aria-hidden="true" className="matching-card-orbit">
        <span>01</span><span>02</span><span>03</span><span>04</span><span>05</span>
        <i><Sparkle weight="fill" /></i>
      </div>
      <p className="eyebrow">{intro.eyebrow}</p>
      <h1>{intro.title}</h1>
      <p className="matching-landing__hero-detail">{intro.detail}</p>
      <div className="matching-landing__hero-action">
        <Link className="matching-primary" to="/vong-la/setup?start=profile">{intro.cta} <ArrowRight /></Link>
        <small>{intro.note}</small>
      </div>
    </section>

    <section aria-labelledby="matching-value-title" className="matching-landing__value">
      <p className="eyebrow">Khi vòng ghép mở</p>
      <h2 id="matching-value-title">Một lời giới thiệu có chiều sâu trước câu “hi”.</h2>
      <div className="matching-benefit-list">
        {benefits.map(({ icon: Icon, title, detail }, index) => <article key={title}>
          <span><Icon weight="duotone" /></span>
          <div><small>0{index + 1}</small><h3>{title}</h3><p>{detail}</p></div>
        </article>)}
      </div>
    </section>

    <section aria-labelledby="matching-flow-title" className="matching-landing__flow">
      <p className="eyebrow">Vòng chạy thế nào?</p>
      <h2 id="matching-flow-title">Ba bước để sẵn sàng vào vòng ghép.</h2>
      <ol>
        <li><span>1</span><div><strong>Bạn đặt ranh giới</strong><p>Intent, khoảng tuổi, thành phố và điều bạn muốn tuần này.</p></div></li>
        <li><span>2</span><div><strong>Lá kiểm tra chốt an toàn</strong><p>Consent và xác minh phải sẵn sàng trước khi hồ sơ có thể bước vào pool.</p></div></li>
        <li><span>3</span><div><strong>Chờ vòng ghép mở</strong><p>Ghép năm người, request kín và mutual chat là chặng tiếp theo; bản này chưa tự gửi hồ sơ cho ai.</p></div></li>
      </ol>
    </section>

    <section className="matching-landing__privacy">
      <EyeSlash weight="duotone" />
      <div><strong>Kín từ bước chuẩn bị</strong><p>Chỉ lưu thành phố và lựa chọn bạn chủ động nhập; bản hiện tại chưa phát hồ sơ hay request cho người khác.</p></div>
      <ShieldCheck weight="fill" />
    </section>

    <section className="matching-landing__cta">
      <p>Bạn đang chuẩn bị hồ sơ và quyền ghép. Vòng năm gợi ý sẽ chỉ mở sau khi các chốt an toàn hoàn tất.</p>
      <Link className="matching-primary" to="/vong-la/setup?start=profile">Tạo hồ sơ Vòng Lá <ArrowRight /></Link>
      <Link className="matching-secondary" to="/home">Để mình xem Note trước</Link>
    </section>
    <AppNav />
  </main>;
}
