import { ArrowLeft, LockKey, ShieldCheck, Sparkle, Trash, WarningCircle } from "@phosphor-icons/react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { createGuest } from "../../shared/api/client";
import { clearPersonalDataOnDevice } from "../../shared/storage/clearPersonalData";
import { BrandMark } from "../../shared/ui/BrandMark";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";

function idempotencyKey(): string {
  const existing = sessionStorage.getItem("la-lanh-guest-create-key");
  if (existing) return existing;
  const value = crypto.randomUUID();
  sessionStorage.setItem("la-lanh-guest-create-key", value);
  return value;
}

export function ConsentPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const location = useLocation();
  const isDetail = location.pathname === "/privacy";
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accept = async () => {
    const radarPending = sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY);
    const radarOwnerStart = sessionStorage.getItem("la-lanh-radar-owner-start") === "1";
    setPending(true);
    setError(null);
    try {
      await clearPersonalDataOnDevice();
      if (radarPending) sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, radarPending);
      if (radarOwnerStart) sessionStorage.setItem("la-lanh-radar-owner-start", "1");
      queryClient.clear();
      await createGuest(idempotencyKey());
      sessionStorage.removeItem("la-lanh-guest-create-key");
      void navigate("/birth", { replace: true });
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
        <span className="flow-header__step">{isDetail ? "Chi tiết" : "Quyền dữ liệu"}</span>
      </header>

      <section className="paper-panel consent-note" aria-labelledby="consent-title">
        <p className="accent-kicker">ngày sinh của bạn vẫn là của bạn</p>
        <h1 id="consent-title">{isDetail ? "Lá Lành dùng dữ liệu thế nào?" : "Cho phép một lần, kiểm soát bất cứ lúc nào."}</h1>
        <div className="consent-list">
          <article><Sparkle aria-hidden="true" /><div><strong>Dùng để làm gì?</strong><p>Tính Mặt Trời và tạo Lá Khai Sinh cùng note cá nhân hóa.</p></div></article>
          <article><ShieldCheck aria-hidden="true" /><div><strong>Chưa cần tài khoản</strong><p>Không cần phone hay email. Phiên khách tự xóa sau 30 ngày không hoạt động.</p></div></article>
          <article><Trash aria-hidden="true" /><div><strong>Bạn luôn có quyền xóa</strong><p>Xem, sửa, rút đồng ý hoặc xóa toàn bộ trong mục Mình. Dữ liệu trên máy có thể mất nếu gỡ app.</p></div></article>
          {isDetail ? <>
            <article><LockKey aria-hidden="true" /><div><strong>Cách bảo vệ</strong><p>Ngày sinh được xử lý trên server, mã hóa khi lưu và không đặt trong URL, cookie hay link chia sẻ.</p></div></article>
            <article><WarningCircle aria-hidden="true" /><div><strong>Độ tuổi & phiên bản</strong><p>Lá Lành hiện dành cho người từ 18 tuổi. Chính sách áp dụng: birth-profile-v1.</p></div></article>
          </> : null}
        </div>
        <p className="privacy-plain">Đồng ý dữ liệu sinh tách biệt với đăng nhập và marketing. Bạn vẫn có thể dùng app ở chế độ khách.</p>
      </section>

      <footer className="flow-actions">
        {isDetail ? (
          <button className="electric-button" onClick={() => void navigate(-1)} type="button">Mình hiểu rồi</button>
        ) : <>
          {error ? <p className="inline-error" role="alert">{error}</p> : null}
          <button className="electric-button" disabled={pending} onClick={() => void accept()} type="button">
            {pending ? "Đang mở một chỗ tạm cho Lá của bạn…" : "Đồng ý & dùng thử"}
          </button>
          <Link className="detail-link" to="/privacy">Đọc cách Lá Lành dùng dữ liệu</Link>
          <button className="text-button" onClick={() => void navigate("/demo")} type="button">Chưa đồng ý</button>
        </>}
      </footer>
    </main>
  );
}
