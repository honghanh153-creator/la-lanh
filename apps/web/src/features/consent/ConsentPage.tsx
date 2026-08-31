import { ArrowLeft, CheckCircle, LockKey, Sparkle, Trash } from "@phosphor-icons/react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createGuest } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";

function idempotencyKey(): string {
  const existing = sessionStorage.getItem("la-lanh-guest-create-key");
  if (existing) return existing;
  const value = crypto.randomUUID();
  sessionStorage.setItem("la-lanh-guest-create-key", value);
  return value;
}

export function ConsentPage() {
  const navigate = useNavigate();
  const [detailOpen, setDetailOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accept = async () => {
    setPending(true);
    setError(null);
    try {
      await createGuest(idempotencyKey());
      sessionStorage.removeItem("la-lanh-guest-create-key");
      void navigate("/birth");
    } catch {
      setError("Chưa bắt đầu được. Kiểm tra kết nối và thử lại nhé.");
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="flow-page consent-page">
      <header className="flow-header">
        <button aria-label="Quay lại" className="icon-button" onClick={() => void navigate(-1)} type="button">
          <ArrowLeft size={22} />
        </button>
        <BrandMark />
        <span className="flow-header__step">01 / 02</span>
      </header>

      <section className="paper-panel consent-note" aria-labelledby="consent-title">
        <p className="handwritten-kicker">trước khi bật mí...</p>
        <h1 id="consent-title">Ngày sinh của bạn vẫn là của bạn.</h1>
        <div className="consent-list">
          <article><Sparkle aria-hidden="true" /><div><strong>Dùng đúng một việc</strong><p>Tính Lá Khai Sinh và note dành cho bạn.</p></div></article>
          <article><LockKey aria-hidden="true" /><div><strong>Chưa cần tài khoản</strong><p>Không hỏi phone, email hay tên thật.</p></div></article>
          <article><Trash aria-hidden="true" /><div><strong>Tự xóa sau 30 ngày</strong><p>Bạn cũng có thể xóa ngay bất cứ lúc nào.</p></div></article>
        </div>
        <button className="detail-link" onClick={() => setDetailOpen(true)} type="button">
          Đọc cách Lá Lành dùng dữ liệu
        </button>
      </section>

      {error ? <p className="inline-error" role="alert">{error}</p> : null}
      <footer className="flow-actions">
        <button className="electric-button" disabled={pending} onClick={() => void accept()} type="button">
          <CheckCircle size={22} weight="fill" />
          {pending ? "Đang mở một chỗ tạm…" : "Đồng ý & dùng thử"}
        </button>
        <button className="text-button" onClick={() => void navigate("/demo")} type="button">Chưa đồng ý</button>
      </footer>

      {detailOpen ? (
        <div className="modal-backdrop">
          <section aria-labelledby="privacy-title" aria-modal="true" className="privacy-sheet" role="dialog">
            <p className="eyebrow">Quyền riêng tư · bản birth-profile-v1</p>
            <h2 id="privacy-title">Một lời hứa ngắn, nói cho rõ.</h2>
            <ul>
              <li>Ngày sinh được gửi tới server để Swiss Ephemeris tính vị trí Mặt Trời.</li>
              <li>Dữ liệu sinh được mã hóa; token phiên không chứa ngày sinh.</li>
              <li>Phiên khách hết hạn sau tối đa 30 ngày không hoạt động.</li>
              <li>Xóa dữ liệu sẽ xóa phiên, consent và mọi snapshot thuộc phiên đó.</li>
              <li>Lá trên thiết bị có thể mất khi xóa dữ liệu trình duyệt.</li>
            </ul>
            <button className="electric-button" onClick={() => setDetailOpen(false)} type="button">Mình hiểu rồi</button>
          </section>
        </div>
      ) : null}
    </main>
  );
}
