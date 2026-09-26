import { Moon, MoonStars, ShieldCheck, Sparkle, Sun, Trash } from "@phosphor-icons/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  clearResonance,
  deleteGuest,
  getBirthProfile,
  getBirthSupplement,
  getDailyNote,
  getResonanceStatus,
  removeBirthSupplement,
} from "../../shared/api/client";
import { primarySunSign } from "../../shared/astro/chart";
import { signDetails } from "../../shared/astro/signs";
import { clearPersonalDataOnDevice } from "../../shared/storage/clearPersonalData";
import { clearCachedDailyNote } from "../../shared/storage/noteCache";
import "../../shared/styles/signal-note.css";
import { useTheme } from "../../shared/theme/useTheme";
import { AppNav } from "../../shared/ui/AppNav";
import { BrandMark } from "../../shared/ui/BrandMark";

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
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const { theme, setTheme } = useTheme();
  const sign = query.data ? primarySunSign(query.data.calculation) : null;
  const supplement = supplementQuery.data;
  const sourceSummary = noteQuery.data?.persona_mode === "aura"
    ? "Nguồn: tổng hòa nhiều hành tinh, nhà và góc chiếu. "
    : sign
      ? `Nguồn: Mặt Trời ${signDetails[sign].label}. `
      : "";
  const removeSupplement = useMutation({
    mutationFn: (kind: "time" | "place") => removeBirthSupplement({
      remove_time: kind === "time",
      remove_place: kind === "place",
    }),
    onSuccess: async () => {
      clearCachedDailyNote();
      queryClient.removeQueries({ queryKey: ["daily-note"] });
      await queryClient.invalidateQueries({ queryKey: ["birth-supplement"] });
      await queryClient.invalidateQueries({ queryKey: ["birth-profile"] });
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
    try {
      await deleteGuest();
      await clearPersonalDataOnDevice();
      queryClient.clear();
      void navigate("/welcome", { replace: true });
    } catch { setError("Chưa xóa được lúc này. Thử lại khi có kết nối nhé."); }
  };

  return (
    <main className="app-page profile-page">
      <header className="section-header"><BrandMark /><h1>Mình</h1></header>
      <section className="profile-card"><span><Sparkle aria-hidden="true" weight="duotone" /></span><div><p className="eyebrow">Lá đang được giữ trên thiết bị này</p><h2>{noteQuery.data ? `${noteQuery.data.persona_mode === "aura" ? "Aura" : "Vibe"} · ${noteQuery.data.persona_label}` : "Lá Khai Sinh"}</h2><p>{sourceSummary}Phiên khách tự hết hạn sau tối đa 30 ngày không hoạt động.</p></div></section>
      <section aria-labelledby="appearance-settings" className="settings-section">
        <div className="settings-section__heading">
          <p className="eyebrow">Cài đặt</p>
          <h2 id="appearance-settings">Giao diện</h2>
        </div>
        <div className="settings-list">
          <div className="theme-setting">
            <span className="theme-setting__icon" aria-hidden="true">{theme === "dark" ? <Moon /> : <Sun />}</span>
            <div>
              <strong>Chế độ tối</strong>
              <p>{theme === "dark" ? "Cosmic Glass · đêm sâu, điểm sáng rõ" : "Cosmic Glass · sương sáng, dễ đọc"}</p>
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
      </section>
      <section aria-labelledby="privacy-settings" className="settings-section">
        <div className="settings-section__heading">
          <p className="eyebrow">Dữ liệu & quyền riêng tư</p>
          <h2 id="privacy-settings">Chiếc Lá của bạn</h2>
        </div>
        <div className="settings-list">
        <article><ShieldCheck /><div><strong>Dữ liệu sinh đã mã hóa</strong><p>Không nằm trong cookie, URL hoặc local storage.</p></div></article>
        <Link className="settings-link" to="/birth-time"><span><MoonStars aria-hidden="true" /></span><div><strong>{supplement && supplement.profile_level > 1 ? "Sửa lớp dữ liệu sinh" : "Mở thêm lớp cá nhân"}</strong><p>{supplement && supplement.profile_level > 1 ? `${supplement.time_precision === "approximate" ? "Giờ gần đúng" : "Đã có giờ sinh"}${supplement.place_display_name ? ` · ${supplement.place_display_name}` : " · chưa có nơi sinh"}` : "Thêm giờ/nơi sinh khi bạn muốn Moon, House và note sâu hơn."}</p></div></Link>
        {supplement?.birth_time_mode !== "unknown" ? <button className="danger-row" onClick={() => {
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
      {error ? <p className="inline-error">{error}</p> : null}
      <p className="sr-only" aria-live="polite" role="status">{statusMessage}</p>
      {statusMessage ? <p className="profile-status" aria-hidden="true">{statusMessage}</p> : null}
      {confirming ? <div className="modal-backdrop"><section aria-modal="true" className="privacy-sheet" role="dialog"><h2>Xóa chiếc Lá này?</h2><p>Phiên khách, consent và mọi snapshot trên server sẽ bị xóa. Note đã lưu trên thiết bị cũng biến mất.</p><button className="danger-button" onClick={() => void remove()} type="button">Xóa vĩnh viễn</button><button className="text-button" onClick={() => setConfirming(false)} type="button">Giữ lại</button></section></div> : null}
      <AppNav />
    </main>
  );
}
