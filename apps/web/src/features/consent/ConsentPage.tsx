import { ArrowLeft, ShieldCheck, Sparkle, Trash } from "@phosphor-icons/react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { acceptBasicBirthConsent, enableHistoryRetention, createGuest, getSession, isGuestSessionUnavailable } from "../../shared/api/client";
import { OPENAI_ABUSE_RETENTION_NOTICE } from "../../shared/config/externalRewriteDisclosure";
import { SESSION_RESTART_REQUIRED_KEY } from "../../shared/session/sessionIdentity";
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
    if (pending) return;
    const radarPending = sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY);
    const radarOwnerStart = sessionStorage.getItem("la-lanh-radar-owner-start") === "1";
    setPending(true);
    setError(null);
    try {
      try {
        await getSession();
        await acceptBasicBirthConsent();
        await enableHistoryRetention();
        sessionStorage.removeItem(SESSION_RESTART_REQUIRED_KEY);
        void navigate("/", { replace: true });
        return;
      } catch (failure) {
        if (!isGuestSessionUnavailable(failure)) throw failure;
      }
      await createGuest(idempotencyKey());
      if (radarPending) sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, radarPending);
      if (radarOwnerStart) sessionStorage.setItem("la-lanh-radar-owner-start", "1");
      queryClient.clear();
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
      <header className="flow-header uv-topbar">
        <button aria-label="Quay lại" className="icon-button uv-topbar__icon" onClick={() => void navigate(-1)} type="button">
          <ArrowLeft size={22} />
        </button>
        <span className="flow-header__step uv-topbar__title">{isDetail ? "Chi tiết" : "Quyền dữ liệu"}</span>
        <span aria-hidden="true" className="uv-topbar__spacer" />
      </header>

      <section className="paper-panel consent-note" aria-labelledby="consent-title">
        <p className="accent-kicker eyebrow">ngày sinh của bạn vẫn là của bạn</p>
        <h1 id="consent-title">{isDetail ? "Lá Lành dùng dữ liệu thế nào?" : "Cho phép một lần, kiểm soát bất cứ lúc nào."}</h1>
        <div className="consent-list">
          <article><Sparkle aria-hidden="true" /><div><strong>Dùng để làm gì?</strong><p>Tính Mặt Trời và tạo Lá Khai Sinh cùng note cá nhân hóa.</p></div></article>
          <article><ShieldCheck aria-hidden="true" /><div><strong>Chưa cần tài khoản</strong><p>Không cần số điện thoại hay email. Hồ sơ khách hết hạn sau 30 ngày không hoạt động. Mỗi lần dùng tính năng riêng tư hợp lệ sẽ kéo dài thời hạn này.</p></div></article>
          <article><ShieldCheck aria-hidden="true" /><div><strong>Đăng nhập là tuỳ chọn</strong><p>Khi Google đã bật, bạn có thể đăng nhập để mở lại cùng hồ sơ trên máy khác. Hồ sơ tài khoản giữ tối đa 365 ngày không hoạt động; phiên mỗi thiết bị là 30 ngày. Đăng xuất chỉ thu hồi phiên máy đó, không xoá hồ sơ.</p></div></article>
          <article><Trash aria-hidden="true" /><div><strong>Lịch sử có thời hạn riêng</strong><p>Khi đồng ý, note ngày tự động chỉ giữ tối đa 24 giờ từ lúc tạo, kèm mood của ngày đó; lịch sử khác giữ tối đa 30 ngày. Không kéo dài khi xem lại. Bấm Lưu để giữ một note lâu hơn. Chart, bản đọc hiện tại và note đã lưu giữ cùng hồ sơ. Hồ sơ cũ chưa bật chính sách này có thể chọn đồng ý trong Mình; có đủ 30 ngày để lưu note trước lần dọn đầu tiên.</p></div></article>
          <article><Trash aria-hidden="true" /><div><strong>Bạn luôn có quyền xóa</strong><p>Xem, sửa, rút đồng ý hoặc xóa toàn bộ trong mục Mình. Dữ liệu trên máy có thể mất nếu gỡ app.</p></div></article>
        </div>
        {isDetail ? <>
          <h2 className="consent-detail-title">Chi tiết thêm</h2>
          <div className="consent-details">
            <details className="consent-detail"><summary>Đăng nhập Google nhận gì?</summary><p>Google và Supabase xử lý mã định danh, email và thông tin hồ sơ cơ bản như tên, ảnh đại diện để xác thực. Lá Lành lưu mã tài khoản đã xác minh và email che một phần, không lưu ảnh đại diện. App không xin quyền đọc Gmail, danh bạ hay lịch. Đăng nhập không tự bật AI và không cấp quyền dùng dữ liệu của người khác.</p></details>
            <details className="consent-detail"><summary>Radar check kín</summary><p>Chỉ nhập thông tin sinh của người khác khi họ đã cho phép dùng vào lần check này. Việc bạn đánh dấu xác nhận không thay thế sự cho phép của họ. Ngày, giờ và nơi sinh của họ chỉ được xử lý để tính kết quả, không lưu thành hồ sơ và không gửi sang AI. Hệ thống mã hoá tên gọi và kết quả trước khi lưu. Nhóm quan hệ và giọng đọc là các trường vận hành không mã hoá riêng trong app. Hệ thống còn giữ dấu kiểm tra có khoá, tạo từ thông tin yêu cầu, để bấm lại không tạo kết quả trùng. Dấu này được xoá cùng kết quả.</p></details>
            <details className="consent-detail"><summary>Lời mời Radar</summary><p>Kết quả dùng link mời chỉ mở khi người nhận tự nhập dữ liệu và đồng ý. Link là quyền truy cập riêng, hãy gửi đúng người. Người nhận có thể rút đồng ý; người tạo có thể xoá kết quả. Check kín không có link công khai. Mỗi hồ sơ giữ tối đa 100 lần Radar, kể cả lời mời đã thu hồi; xoá một lần để tạo thêm.</p></details>
            <details className="consent-detail"><summary>Xoá và bản sao lưu</summary><p>Khi hết hạn, dữ liệu không còn được mở qua app và chờ tác vụ dọn định kỳ. Xoá trong app không có nghĩa mọi bản sao lưu hay dữ liệu nhà cung cấp đã xoá ngay. Bản beta chưa xác minh đầy đủ thời hạn xoá trong backup và mọi nhà cung cấp. Nếu khôi phục backup, cần áp dụng lại các yêu cầu xoá trước khi mở dịch vụ.</p></details>
            <details className="consent-detail"><summary>Khôi phục và xoá tài khoản</summary><p>Khách không có cách khôi phục nếu mất cookie hoặc dữ liệu máy. Với tài khoản đã liên kết, xoá hồ sơ thu hồi các phiên và yêu cầu xoá danh tính Supabase trước khi báo hoàn tất. Nếu nhà cung cấp lỗi, hồ sơ bị khoá và hệ thống thử lại; không khôi phục bằng đăng nhập lại. Tài khoản Google không bị xoá. Hủy đăng nhập không đồng nghĩa xoá danh tính nhà cung cấp.</p></details>
            <details className="consent-detail"><summary>Cách bảo vệ</summary><p>Thông tin sinh được mã hóa trong ứng dụng trước khi lưu và không đặt trong URL, cookie hay link chia sẻ. Kết nối tới hệ thống dùng HTTPS/TLS.</p></details>
            <details className="consent-detail"><summary>Dữ liệu beta đi đâu?</summary><p>Khi bạn đồng ý, dữ liệu được truyền từ Việt Nam để xử lý trên máy chủ Hetzner tại Đức và lưu trong cơ sở dữ liệu Supabase tại Frankfurt, Đức. Lá Lành chỉ dùng dữ liệu để vận hành tính năng, không bán hoặc dùng cho quảng cáo.</p></details>
            <details className="consent-detail"><summary>AI viết lại là lựa chọn riêng</summary><p>Đồng ý dữ liệu sinh không bật AI. Khi có nhóm test AI, bạn có thể đồng ý riêng trong Mình để gửi bản tóm tắt ý nghĩa và nhãn chiêm tinh liên quan sang OpenAI (công ty Hoa Kỳ, xử lý ngoài Việt Nam). Không gửi tên, ngày/giờ/nơi sinh, tọa độ hay nguyên văn câu hỏi tự do. Thông tin suy ra vẫn có thể là dữ liệu cá nhân. {OPENAI_ABUSE_RETENTION_NOTICE} Tắt sẽ dừng các yêu cầu tiếp theo, không thu hồi được dữ liệu đã gửi.</p></details>
            <details className="consent-detail"><summary>Độ tuổi & phiên bản</summary><p>Lá Lành hiện dành cho người từ 18 tuổi. Chính sách áp dụng: birth-profile-v1.</p></details>
            <details className="consent-detail"><summary>Liên hệ về dữ liệu</summary><p>Gửi yêu cầu về quyền riêng tư tới <a href="mailto:honghanh153@gmail.com">honghanh153@gmail.com</a>. Không gửi mật khẩu, mã đăng nhập hay API key trong email.</p></details>
          </div>
        </> : null}
        <p className="privacy-plain">Đồng ý dữ liệu sinh tách biệt với đăng nhập và marketing. Bạn vẫn có thể dùng app ở chế độ khách.</p>
        {isDetail ? (
          <p className="privacy-plain">
            Lá Lành là phần mềm nguồn mở AGPL, được cung cấp không kèm bảo hành. {" "}
            <a
              className="detail-link"
              href="https://github.com/honghanh153-creator/la-lanh"
              rel="noreferrer"
              target="_blank"
            >
              Xem mã nguồn tương ứng
            </a>
            {" · "}
            <a
              className="detail-link"
              href="https://github.com/honghanh153-creator/la-lanh/blob/main/LICENSE"
              rel="noreferrer"
              target="_blank"
            >
              Đọc giấy phép
            </a>
          </p>
        ) : null}
      </section>

      <footer className="flow-actions">
        {isDetail ? (
          <button className="electric-button" onClick={() => void navigate(-1)} type="button">Mình hiểu rồi</button>
        ) : <>
          {error ? <p className="inline-error" role="alert">{error}</p> : null}
          <button className="electric-button" disabled={pending} onClick={() => void accept()} type="button">
            {pending ? "Đang bắt đầu…" : "Đồng ý & bắt đầu"}
          </button>
          <Link className="detail-link" to="/privacy">Đọc cách Lá Lành dùng dữ liệu</Link>
          <Link className="text-button" to="/existing-user?returnTo=/home">Đăng nhập</Link>
        </>}
      </footer>
    </main>
  );
}
