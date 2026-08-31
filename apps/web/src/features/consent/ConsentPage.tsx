import { ArrowLeft, LockKey, ShieldCheck, Sparkle, Trash, WarningCircle } from "@phosphor-icons/react";
import { Link, useNavigate } from "react-router-dom";

import { BrandMark } from "../../shared/ui/BrandMark";

export function ConsentPage() {
  const navigate = useNavigate();

  return (
    <main className="flow-page consent-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button">
          <ArrowLeft size={22} />
        </button>
        <BrandMark />
        <span className="flow-header__step">Quyền dữ liệu</span>
      </header>

      <section className="paper-panel consent-note" aria-labelledby="consent-title">
        <p className="handwritten-kicker">quyền dữ liệu của bạn</p>
        <h1 id="consent-title">Lá Lành chỉ đọc đúng phần cần đọc.</h1>
        <div className="consent-list">
          <article><Sparkle aria-hidden="true" /><div><strong>Mục đích cụ thể</strong><p>Tính Lá Khai Sinh, tạo note cá nhân hóa và lưu snapshot để bạn quay lại.</p></div></article>
          <article><ShieldCheck aria-hidden="true" /><div><strong>Dữ liệu xử lý</strong><p>Ngày sinh, phiên khách ẩn danh, trạng thái mood/save trên thiết bị.</p></div></article>
          <article><LockKey aria-hidden="true" /><div><strong>Bảo vệ</strong><p>Không đưa ngày sinh vào URL, cookie hoặc bộ nhớ trình duyệt; mã hóa dữ liệu sinh khi lưu.</p></div></article>
          <article><Trash aria-hidden="true" /><div><strong>Quyền xóa và rút lại</strong><p>Xóa Lá trong mục Mình sẽ xóa phiên, consent và snapshot trên server.</p></div></article>
          <article><WarningCircle aria-hidden="true" /><div><strong>Trẻ em</strong><p>Chưa xử lý dữ liệu người dưới 16 tuổi nếu chưa có xác nhận phụ huynh hoặc người giám hộ.</p></div></article>
        </div>
        <p className="privacy-plain">Khi bạn tick đồng ý ở màn ngày sinh, Lá Lành tạo một phiên khách để chứng minh consent. Bạn vẫn chưa cần đăng nhập.</p>
      </section>

      <footer className="flow-actions">
        <Link className="electric-button" to="/birth">Quay lại nhập ngày sinh</Link>
        <button className="text-button" onClick={() => void navigate("/demo")} type="button">Xem demo không cá nhân hóa</button>
      </footer>
    </main>
  );
}
