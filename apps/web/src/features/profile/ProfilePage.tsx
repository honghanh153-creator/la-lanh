import { BookmarkSimple, GearSix, LockSimple, Moon, MoonStars, ShareNetwork, ShieldCheck, Sun, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  clearResonance,
  ApiProblem,
  clearReadingHistory,
  enableHistoryRetention,
  getAccountStatus,
  getHistoryRetention,
  logoutAccount,
  deleteGuest,
  getBirthProfile,
  getBirthSupplement,
  getContentRewriteStatus,
  getDailyNote,
  getResonanceStatus,
  removeBirthSupplement,
  setContentRewriteConsent,
} from "../../shared/api/client";
import { primarySunSign } from "../../shared/astro/chart";
import { signDetails } from "../../shared/astro/signs";
import { ELEMENT_LABEL, identityFromCalculation, SIGN_ELEMENT } from "../../shared/astro/identity";
import { VibeSegmented } from "../../shared/vibe/VibePicker";
import "./profile-identity.css";
import { clearPersonalDataOnDevice } from "../../shared/storage/clearPersonalData";
import { clearChartDerivedData } from "../../shared/storage/clearChartDerivedData";
import "../../shared/styles/signal-note.css";
import { OPENAI_ABUSE_RETENTION_NOTICE } from "../../shared/config/externalRewriteDisclosure";
import { useTheme } from "../../shared/theme/useTheme";
import { AppNav } from "../../shared/ui/AppNav";
import { AppSheet } from "../../shared/ui/AppSheet";
import { NightSky } from "../../shared/ui/NightSky";

export function ProfilePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["birth-profile"], queryFn: ({ signal }) => getBirthProfile(signal) });
  const supplementQuery = useQuery({
    queryKey: ["birth-supplement"],
    queryFn: ({ signal }) => getBirthSupplement(signal),
    retry: false,
  });
  const noteQuery = useQuery({ queryKey: ["daily-note"], queryFn: ({ signal }) => getDailyNote(signal) });
  const resonanceQuery = useQuery({
    queryKey: ["daily-note-resonance"],
    queryFn: ({ signal }) => getResonanceStatus(signal),
    retry: false,
  });
  const [confirming, setConfirming] = useState(false);
  const [confirmingHistory, setConfirmingHistory] = useState(false);
  const [confirmingRetention, setConfirmingRetention] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const accountQuery = useQuery({ queryKey: ["account-status"], queryFn: ({ signal }) => getAccountStatus(signal), retry: false, gcTime: 0 });
  const historyQuery = useQuery({ queryKey: ["history-retention"], queryFn: ({ signal }) => getHistoryRetention(signal), retry: false });
  const [confirmingAI, setConfirmingAI] = useState(false);
  const rewriteQuery = useQuery({
    queryKey: ["content-rewrite-status"],
    queryFn: ({ signal }) => getContentRewriteStatus(signal),
    retry: false,
  });
  const rewriteMutation = useMutation({
    mutationFn: (enabled: boolean) => setContentRewriteConsent(enabled),
    onSuccess: async (_result, enabled) => {
      setConfirmingAI(false);
      setStatusMessage(enabled ? "Đã bật AI viết lại. Nội dung mới sẽ được kiểm tra trước khi hiển thị." : "Đã tắt AI viết lại.");
      await queryClient.invalidateQueries({ queryKey: ["content-rewrite-status"] });
      await queryClient.invalidateQueries({ queryKey: ["daily-note"] });
    },
    onError: () => setError("Chưa cập nhật được AI viết lại. Nội dung hiện tại vẫn dùng được nhé."),
  });
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const { theme, setTheme } = useTheme();
  const logoutMutation = useMutation({
    mutationFn: () => logoutAccount(),
    onSuccess: () => { queryClient.clear(); void navigate("/welcome", { replace: true }); },
    onError: () => setError("Chưa đăng xuất được. Hồ sơ vẫn được giữ; kiểm tra kết nối rồi thử lại."),
  });
  const retentionMutation = useMutation({
    mutationFn: enableHistoryRetention,
    onSuccess: async () => {
      setConfirmingRetention(false);
      setStatusMessage("Đã bật thời hạn riêng cho lịch sử. Hồ sơ và note đã lưu vẫn được giữ.");
      await queryClient.invalidateQueries({ queryKey: ["history-retention"] });
    },
    onError: () => setError("Chưa cập nhật được thời hạn. Dữ liệu cũ chưa bị xoá; thử lại nhé."),
  });
  const historyMutation = useMutation({
    mutationFn: async () => {
      await queryClient.cancelQueries();
      await clearReadingHistory();
    },
    onSuccess: async () => {
      for (const key of ["tarot-session", "radar-invites", "radar-result", "daily-note-mood", "daily-note-resonance", "daily-experiment"]) {
        queryClient.removeQueries({ queryKey: [key] });
      }
      try { localStorage.removeItem("la-lanh-pending-mood-v1"); } catch { /* No persistence is available on this device. */ }
      setConfirmingHistory(false);
      setStatusMessage("Đã xoá lịch sử. Hồ sơ sinh, bản đọc hiện tại và note đã lưu vẫn được giữ.");
      await queryClient.invalidateQueries({ queryKey: ["daily-note-resonance"] });
    },
    onError: (failure) => setError(failure instanceof ApiProblem && failure.code === "HISTORY_BUSY"
      ? "Nội dung đang cập nhật. Chờ vài giây rồi thử xoá lại; lịch sử chưa bị xoá."
      : "Chưa xác nhận được việc xoá lịch sử. Kiểm tra kết nối rồi thử lại; hồ sơ vẫn được giữ."),
  });
  const sign = query.data ? primarySunSign(query.data.calculation) : null;
  const identity = identityFromCalculation(query.data?.calculation);
  const element = sign ? SIGN_ELEMENT[sign] : null;
  const supplement = supplementQuery.data;
  const removeSupplement = useMutation({
    mutationFn: (kind: "time" | "place") => removeBirthSupplement({
      remove_time: kind === "time",
      remove_place: kind === "place",
    }),
    onSuccess: async () => {
      await clearChartDerivedData(queryClient);
    },
    onError: () => setError("Chưa xóa được dữ liệu bổ sung. Thử lại sau nhé."),
  });
  const resonanceMutation = useMutation({
    mutationFn: (revokeConsent: boolean) => clearResonance(revokeConsent),
    onSuccess: async (_payload, revokeConsent) => {
      setStatusMessage(revokeConsent
        ? "Đã tắt quyền đồng ý và xóa toàn bộ phản hồi."
        : "Đã xóa phản hồi; quyền đồng ý vẫn được giữ.");
      await queryClient.invalidateQueries({ queryKey: ["daily-note-resonance"] });
    },
    onError: () => setError("Chưa cập nhật được phản hồi. Thử lại khi có kết nối nhé."),
  });

  const remove = async () => {
    if (deleting) return;
    setDeleting(true);
    try {
      await deleteGuest();
      await clearPersonalDataOnDevice();
      queryClient.clear();
      void navigate("/welcome", { replace: true });
    } catch (failure) {
      setError(failure instanceof ApiProblem && failure.code === "ACCOUNT_ERASURE_PENDING"
        ? "Hồ sơ đã khoá. Việc xoá tài khoản đang chờ hệ thống đăng nhập xác nhận; hệ thống sẽ thử lại."
        : "Chưa xóa được lúc này. Thử lại khi có kết nối nhé.");
    }
    finally { setDeleting(false); }
  };

  return (
    <main className="app-page profile-page">
      <header className="section-header uv-tab-header"><h1>Mình</h1></header>
      <section aria-labelledby="profile-identity-title" className="profile-identity uv-night">
        <NightSky moon stars={4} />
        <p className="eyebrow">Lá Khai Sinh của bạn</p>
        <h2 id="profile-identity-title">{sign ? <><span aria-hidden="true" className="profile-identity__glyph">{signDetails[sign].symbol}</span>{signDetails[sign].label}</> : "Lá Khai Sinh"}</h2>
        <p className="profile-identity__tags">
          {[element ? `Nguyên tố ${ELEMENT_LABEL[element]}` : null, noteQuery.data ? `${noteQuery.data.persona_mode === "aura" ? "Aura" : "Vibe"} ${noteQuery.data.persona_label}` : null].filter(Boolean).join(" · ")}
        </p>
        <ul aria-label="Bộ ba của bạn" className="profile-identity__trio">
          {identity.map((slot) => slot.sign
            ? <li key={slot.key}><small>{slot.label}</small><strong>{signDetails[slot.sign].label}</strong></li>
            : <li className="is-locked" key={slot.key}><Link to="/birth-time"><small>{slot.label}</small><strong><LockSimple aria-hidden="true" /> Lá ẩn</strong></Link></li>)}
        </ul>
        <Link className="profile-identity__share" to="/birth-card"><ShareNetwork aria-hidden="true" /> Tạo thẻ chia sẻ</Link>
      </section>
      <nav aria-label="Lối tắt" className="settings-list profile-shortcuts">
        <Link className="settings-link" to="/saved"><span><BookmarkSimple aria-hidden="true" /></span><div><strong>Note đã lưu</strong><p>Mở lại đúng bản bạn đã giữ.</p></div></Link>
      </nav>
      <section aria-labelledby="appearance-settings" className="settings-section">
        <h2 id="appearance-settings">Giao diện & giọng đọc</h2>
        <div className="settings-list">
          <div className="theme-setting">
            <span className="theme-setting__icon" aria-hidden="true">{theme === "dark" ? <Moon /> : <Sun />}</span>
            <div>
              <strong>Chế độ tối</strong>
              <p>{theme === "dark" ? "Nền tối, chữ sáng" : "Nền sáng, chữ tím đậm"}</p>
            </div>
            <button
              aria-checked={theme === "dark"}
              aria-label={theme === "dark" ? "Tắt chế độ tối" : "Bật chế độ tối"}
              className="theme-switch"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              role="switch"
              type="button"
            >
              <span aria-hidden="true" />
            </button>
          </div>
        </div>
        <VibeSegmented />
      </section>
      <section className="settings-section" aria-labelledby="account-settings">
        <h2 id="account-settings">Giữ hồ sơ khi đổi máy</h2>
        <p>{accountQuery.data?.signed_in ? "Hồ sơ đã liên kết tài khoản, giữ tới 365 ngày không sử dụng." : "Hồ sơ khách giữ 30 ngày không hoạt động; dùng lại sẽ gia hạn."}</p>
        {accountQuery.isPending ? <p role="status">Đang kiểm tra đăng nhập…</p> : accountQuery.data?.signed_in ? <><p>Đã đăng nhập · {accountQuery.data.masked_email}</p><p>Đăng xuất chỉ đóng phiên trên máy này. Các máy khác và hồ sơ vẫn được giữ.</p><button className="text-button" disabled={logoutMutation.isPending} onClick={() => { setError(null); logoutMutation.mutate(); }} type="button">{logoutMutation.isPending ? "Đang đăng xuất…" : "Đăng xuất trên máy này"}</button></> : <><p>Đăng nhập Google là tuỳ chọn. Liên kết một lần để mở lại đúng hồ sơ khi đổi máy hoặc xoá cookie.</p><Link className="settings-link" to="/existing-user?returnTo=/profile">Đăng nhập để giữ hồ sơ</Link>{accountQuery.data && !accountQuery.data.google_login_enabled ? <p>Đăng nhập Google chưa bật trên bản này; chế độ khách vẫn dùng bình thường.</p> : null}</>}
      </section>
      <details className="profile-more">
      <summary><GearSix aria-hidden="true" /> Dữ liệu & quyền riêng tư</summary>
      <section className="settings-section" aria-labelledby="history-settings">
        <h2 id="history-settings">Lịch sử, không phải hồ sơ</h2>
        <p>{historyQuery.isPending ? "Đang kiểm tra thời hạn…" : historyQuery.isError ? "Chưa đọc được thời hạn. Chưa có dữ liệu nào bị xoá từ thao tác này." : historyQuery.data.enabled ? "Note ngày tự động hiện tối đa 24 giờ (có thể được dọn sớm hơn); lịch sử khác tối đa 30 ngày, tính từ lúc tạo; mở lại không kéo dài thời hạn." : "Hồ sơ này chưa bật thời hạn mới. Lịch sử cũ không bị rút ngắn khi chưa đồng ý."}</p>
        <p>Hồ sơ sinh, bản đọc hiện tại và note đã lưu vẫn được giữ theo thời hạn của hồ sơ.</p>
        {historyQuery.data && !historyQuery.data.enabled ? <button className="text-button" onClick={() => { setError(null); setConfirmingRetention(true); }} type="button">Bật thời hạn lịch sử</button> : null}
        <button className="text-button" onClick={() => { setError(null); setConfirmingHistory(true); }} type="button">Xoá lịch sử đã xem</button>
      </section>
      <section aria-labelledby="privacy-settings" className="settings-section">
        <div className="settings-section__heading">
          <p className="eyebrow">Dữ liệu & quyền riêng tư</p>
          <h2 id="privacy-settings">Chiếc Lá của bạn</h2>
        </div>
        <div className="settings-list">
        <article><ShieldCheck /><div><strong>Dữ liệu sinh đã mã hóa</strong><p>Không nằm trong cookie, URL hoặc local storage.</p></div></article>
        <Link className="settings-link" to="/birth-time"><span><MoonStars aria-hidden="true" /></span><div><strong>{supplement && supplement.profile_level > 1 ? "Sửa lớp dữ liệu sinh" : "Mở thêm lớp cá nhân"}</strong><p>{supplement && supplement.profile_level > 1 ? `${supplement.time_precision === "approximate" ? "Giờ gần đúng" : "Đã có giờ sinh"}${supplement.place_display_name ? ` · ${supplement.place_display_name}` : " · chưa có nơi sinh"}` : "Thêm giờ/nơi sinh khi bạn muốn Moon, House và note sâu hơn."}</p></div></Link>
        {supplement && supplement.birth_time_mode !== "unknown" ? <button className="danger-row" onClick={() => {
          if (window.confirm("Xóa giờ sinh và mọi note, bản lưu, link chia sẻ hiện có? Ngày sinh vẫn được giữ.")) removeSupplement.mutate("time");
        }} type="button"><Trash /><span><strong>Xóa giờ sinh</strong><small>Xóa luôn nội dung đã suy ra từ giờ/nơi sinh</small></span></button> : null}
        {supplement?.place_display_name ? <button className="danger-row" onClick={() => {
          if (window.confirm("Xóa nơi sinh và mọi note, bản lưu, link chia sẻ hiện có? Ngày sinh vẫn được giữ.")) removeSupplement.mutate("place");
        }} type="button"><Trash /><span><strong>Xóa nơi sinh</strong><small>Xóa nội dung liên quan; vẫn giữ ngày sinh</small></span></button> : null}
        <button className="danger-row" onClick={() => setConfirming(true)} type="button"><Trash /><span><strong>Xóa Lá và dữ liệu</strong><small>Không thể hoàn tác</small></span></button>
        </div>
      </section>
      <section aria-labelledby="resonance-settings" className="settings-section resonance-settings">
        <div className="settings-section__heading">
          <p className="eyebrow">Cá nhân hóa có kiểm soát</p>
          <h2 id="resonance-settings">Phản hồi về Note</h2>
        </div>
        <div className="resonance-settings__card">
          <div>
            <strong>Trạng thái</strong>
            <p>{resonanceQuery.isLoading
              ? "Đang kiểm tra…"
              : resonanceQuery.isError
                ? "Chưa đọc được trạng thái lúc này."
                : resonanceQuery.data?.consented
                  ? `Đang bật · ${resonanceQuery.data.feedback_count} phản hồi trong 30 ngày gần nhất`
                  : "Chưa bật · chỉ hỏi khi bạn gửi trúng/chưa trúng lần đầu"}</p>
          </div>
          <p className="resonance-settings__explain">
            Chỉ giữ lựa chọn trúng/chưa trúng để xem cách diễn đạt có hữu ích không; không có ghi chú tự do và không suy đoán tính cách.
          </p>
          <div className="resonance-settings__actions">
            <button
              disabled={resonanceMutation.isPending || !resonanceQuery.data?.feedback_count}
              onClick={() => resonanceMutation.mutate(false)}
              type="button"
            >
              Xóa phản hồi
            </button>
            <button
              disabled={resonanceMutation.isPending || !resonanceQuery.data?.consented}
              onClick={() => {
                if (window.confirm("Tắt quyền đồng ý và xóa toàn bộ phản hồi về Note?")) {
                  resonanceMutation.mutate(true);
                }
              }}
              type="button"
            >
              Tắt và xóa
            </button>
          </div>
        </div>
      </section>
      </details>
      {rewriteQuery.data?.enabled ? <section className="settings-section" aria-labelledby="ai-writing-settings">
        <h2 id="ai-writing-settings">AI viết lại cho dễ đọc</h2>
        <p>Nhóm test có tối đa 20 phiên đã đồng ý. AI chỉ viết lại những mục đang thử nghiệm, không đổi dữ kiện chart hay lá Tarot.</p>
        <button className="text-button" disabled={rewriteMutation.isPending || (!rewriteQuery.data.pilot_eligible && !rewriteQuery.data.consented)}
          onClick={() => rewriteQuery.data?.consented ? rewriteMutation.mutate(false) : setConfirmingAI(true)} type="button">
          {rewriteQuery.data.consented ? "Tắt AI viết lại" : rewriteQuery.data.pilot_eligible ? "Thử AI viết lại" : "Nhóm test đã đủ người"}
        </button>
        <p className="profile-status">{rewriteQuery.data.consented ? "Đã đồng ý · kết quả chỉ hiện khi qua kiểm tra. Khi hết ngân sách, vẫn có bản đọc thường." : "Mặc định tắt. Chưa có đồng ý thì không gửi nội dung sang OpenAI."}</p>
      </section> : null}
      <AppSheet open={confirmingAI} title="Đồng ý để OpenAI sửa lời văn?" closeDisabled={rewriteMutation.isPending} onClose={() => setConfirmingAI(false)}>
        <p>Với mục đang thử nghiệm, Lá Lành gửi sang OpenAI (công ty Hoa Kỳ, xử lý ngoài Việt Nam) bản tóm tắt ý nghĩa và nhãn chiêm tinh liên quan (hành tinh, cung, nhà, góc chiếu), hoặc ý nghĩa các lá Tarot. Không gửi tên, ngày/giờ/nơi sinh hay tọa độ. Nội dung suy ra vẫn có thể là thông tin cá nhân. Với Tarot, không gửi nguyên văn câu hỏi, chỉ gửi nhóm chủ đề đã phân loại sẵn. Dữ liệu riêng của người khác không nằm trong quyền đồng ý này.</p>
        <p>Yêu cầu không lưu lịch sử trả lời, nhưng {OPENAI_ABUSE_RETENTION_NOTICE} Bạn có thể tắt bất cứ lúc nào trong Mình; tắt sẽ huỷ các yêu cầu chưa gửi và dừng các yêu cầu sau, không thu hồi được dữ liệu đã gửi. Bản AI đã hiện trước đó vẫn được giữ như các bản đọc khác.</p>
        <button className="primary-button" disabled={rewriteMutation.isPending} onClick={() => rewriteMutation.mutate(true)} type="button">Đồng ý và thử</button>
        <button className="text-button" disabled={rewriteMutation.isPending} onClick={() => setConfirmingAI(false)} type="button">Dùng bản thường</button>
      </AppSheet>
      <AppSheet open={confirmingHistory} title="Xoá lịch sử đã xem?" closeDisabled={historyMutation.isPending} onClose={() => setConfirmingHistory(false)}>
        <p>Xoá kết quả Tarot và Hợp gu đã hoàn thành, check-in, phản hồi và note tự động của những ngày trước chưa lưu.</p>
        <p>Hồ sơ sinh, bản đọc hiện tại và note đã lưu vẫn được giữ. Phiên đang bốc Tarot hoặc lời mời chưa hoàn thành không nằm trong thao tác này.</p>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="danger-button" disabled={historyMutation.isPending} onClick={() => { setError(null); historyMutation.mutate(); }} type="button">{historyMutation.isPending ? "Đang xoá…" : "Xoá lịch sử"}</button>
        <button className="text-button" disabled={historyMutation.isPending} onClick={() => setConfirmingHistory(false)} type="button">Giữ lịch sử</button>
      </AppSheet>
      <AppSheet open={confirmingRetention} title="Bật thời hạn cho lịch sử?" closeDisabled={retentionMutation.isPending} onClose={() => setConfirmingRetention(false)}>
        <p>Note ngày mới chỉ hiện tối đa 24 giờ, kèm mood của ngày đó, và có thể được xoá sớm hơn ở đợt dọn dữ liệu định kỳ; note đang gắn với việc nhỏ chờ nhìn lại, phản hồi hoặc link chia sẻ còn hạn được giữ ẩn tới khi các mục đó hết hạn. Lịch sử khác hết hạn sau tối đa 30 ngày. Bấm Lưu để giữ một note lâu hơn. Lịch sử cũ được thêm 30 ngày chuyển tiếp từ khi bạn đồng ý, không bị xoá ngay.</p>
        <p>Hồ sơ sinh, bản đọc hiện tại và note đã lưu không theo thời hạn này. Tarot và Hợp gu vẫn giữ thời hạn đã báo khi tạo.</p>
        {error ? <p className="inline-error" role="alert">{error}</p> : null}
        <button className="primary-button" disabled={retentionMutation.isPending} onClick={() => { setError(null); retentionMutation.mutate(); }} type="button">Đồng ý thời hạn lịch sử</button>
        <button className="text-button" disabled={retentionMutation.isPending} onClick={() => setConfirmingRetention(false)} type="button">Chưa thay đổi</button>
      </AppSheet>
      {error && !confirmingHistory && !confirmingRetention ? <p className="inline-error" role="alert">{error}</p> : null}
      <p className="sr-only" aria-live="polite" role="status">{statusMessage}</p>
      {statusMessage ? <p className="profile-status" aria-hidden="true">{statusMessage}</p> : null}
      <AppSheet open={confirming} title="Xoá hồ sơ Lá Lành?" closeDisabled={deleting} onClose={() => setConfirming(false)}><p>Xoá hồ sơ sinh, mọi bản đọc, note đã lưu và liên kết tài khoản trên hệ thống Lá Lành. Tất cả thiết bị mất quyền truy cập hồ sơ này; không thể khôi phục bằng đăng nhập lại.</p><p>Nếu đã liên kết tài khoản, hệ thống cũng yêu cầu xoá danh tính đăng nhập tại Supabase. Chỉ báo hoàn tất sau khi xác nhận; nếu lỗi sẽ khoá hồ sơ và thử lại. Tài khoản Google của bạn không bị xoá.</p><button className="danger-button" disabled={deleting} onClick={() => void remove()} type="button">{deleting ? "Đang xoá…" : "Xóa vĩnh viễn"}</button><button className="text-button" disabled={deleting} onClick={() => setConfirming(false)} type="button">Giữ lại</button></AppSheet>
      <AppNav />
    </main>
  );
}
