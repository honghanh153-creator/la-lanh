import { ArrowRight, Sparkle } from "@phosphor-icons/react";
import { Link } from "react-router-dom";

import { BrandMark } from "../../shared/ui/BrandMark";
import "./retired-feature.css";

export function RetiredFeaturePage() {
  return (
    <main className="flow-page retired-feature-page">
      <header className="flow-header"><BrandMark /></header>
      <section aria-labelledby="retired-feature-title" className="retired-feature-card">
        <span aria-hidden="true" className="retired-feature-card__icon"><Sparkle weight="fill" /></span>
        <p className="eyebrow">Một chương đã khép lại</p>
        <h1 id="retired-feature-title">Lá Chứng không còn nhận phản hồi mới.</h1>
        <p>
          Link này không mở hoặc gửi dữ liệu của lời mời cũ. Lá Lành đang tập trung vào
          những cách riêng tư hơn để bạn hiểu mình và các kết nối quanh mình.
        </p>
        <div className="retired-feature-actions">
          <Link className="electric-button" to="/">Tiếp tục với Lá Lành <ArrowRight aria-hidden="true" /></Link>
          <Link className="outline-button" to="/la-chung/history">Quản lý dữ liệu cũ</Link>
        </div>
        <Link className="retired-feature-card__withdraw" to="/la-chung/manage-response">Từng phản hồi? Rút phản hồi trên thiết bị này</Link>
        <small>Bạn vẫn có thể thu hồi lời mời, ẩn hoặc xóa kết quả và xóa toàn bộ Lá trong phần Mình.</small>
      </section>
    </main>
  );
}
