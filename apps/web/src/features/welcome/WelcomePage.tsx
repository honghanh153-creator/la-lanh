import { ArrowRight, Pause, Play } from "@phosphor-icons/react";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { acceptBasicBirthConsent, enableHistoryRetention, createGuest, getSession, isGuestSessionUnavailable } from "../../shared/api/client";
import { BrandMark } from "../../shared/ui/BrandMark";
import { NightSky } from "../../shared/ui/NightSky";
import { SESSION_RESTART_REQUIRED_KEY } from "../../shared/session/sessionIdentity";
import { useOnboardingMotion } from "../../shared/ui/onboardingMotion";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";
import { useVibe } from "../../shared/vibe/useVibe";
import "./welcome-intro.css";

function idempotencyKey(): string {
  const existing = sessionStorage.getItem("la-lanh-guest-create-key");
  if (existing) return existing;
  const value = crypto.randomUUID();
  sessionStorage.setItem("la-lanh-guest-create-key", value);
  return value;
}

export function WelcomePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const motion = useOnboardingMotion();
  const { vibe } = useVibe();
  const routeState = location.state as { expired?: boolean; offline?: boolean; sessionChanged?: boolean } | null;
  const restart = new URLSearchParams(location.search).get("restart") === "1";
  const [pending, setPending] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeOperation = useRef<AbortController | null>(null);

  useEffect(() => () => {
    activeOperation.current?.abort();
    activeOperation.current = null;
  }, []);

  const begin = async () => {
    if (activeOperation.current) return;
    const operation = new AbortController();
    activeOperation.current = operation;
    const isCurrent = () => activeOperation.current === operation && !operation.signal.aborted;
    setPending(true);
    setError(null);
    const key = idempotencyKey();
    // Explicit replay starts the ordinary onboarding, not a stale Radar draft.
    // Visiting the page alone never clears a session; consent is still required.
    const radarPending = restart ? null : sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY);
    const radarOwnerStart = !restart && sessionStorage.getItem("la-lanh-radar-owner-start") === "1";
    try {
      {
        try {
          await getSession(operation.signal);
          if (!isCurrent()) return;
          await acceptBasicBirthConsent();
          if (!isCurrent()) return;
          await enableHistoryRetention();
          if (!isCurrent()) return;
          sessionStorage.removeItem(SESSION_RESTART_REQUIRED_KEY);
          void navigate("/", { replace: true });
          return;
        } catch (failure) {
          if (!isCurrent()) return;
          if (!isGuestSessionUnavailable(failure)) throw failure;
        }
      }
      // The successful creation adopts a new epoch and clears old local caches.
      // Do not discard them before an offline request has succeeded.
      setCreating(true);
      await createGuest(key, operation.signal);
      if (!isCurrent()) return;
      queryClient.clear();
      if (restart) {
        sessionStorage.removeItem(RADAR_PENDING_REQUEST_KEY);
        sessionStorage.removeItem("la-lanh-radar-owner-start");
      }
      if (radarPending) sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, radarPending);
      if (radarOwnerStart) sessionStorage.setItem("la-lanh-radar-owner-start", "1");
      sessionStorage.removeItem("la-lanh-guest-create-key");
      void navigate("/birth", { replace: true });
    } catch {
      if (!isCurrent()) return;
      sessionStorage.setItem("la-lanh-guest-create-key", key);
      setError("Chưa bật được tín hiệu. Kiểm tra kết nối rồi thử lại nhé.");
    } finally {
      if (isCurrent()) {
        activeOperation.current = null;
        setPending(false);
        setCreating(false);
      }
    }
  };

  return (
    <main className="welcome-intro uv-night-scene" aria-labelledby="welcome-title" aria-busy={pending || undefined} data-motion-paused={motion.paused}>
      <header className="welcome-intro__header">
        <BrandMark />
        <button
          type="button"
          className="welcome-intro__motion"
          aria-label={motion.paused ? "Tiếp tục chuyển động" : "Tạm dừng chuyển động"}
          onClick={motion.toggle}
        >
          {motion.paused ? <Play size={22} weight="fill" aria-hidden="true" /> : <Pause size={22} weight="fill" aria-hidden="true" />}
        </button>
      </header>
      <NightSky orbits planet />
      <div className="welcome-intro__hero" aria-hidden="true">
        <span className="welcome-intro__glow" />
        <img className="welcome-intro__moon" src="/assets/ultraviolet/moon.webp" alt="" width="250" height="250" fetchPriority="high" />
      </div>
      <section className="welcome-intro__copy" aria-labelledby="welcome-title">
        {vibe === "roast"
          ? <h1 id="welcome-title"><span>Bớt overthinking.</span>{" "}<span>Để Lá soi giùm.</span></h1>
          : <h1 id="welcome-title"><span>Hiểu mình hơn.</span>{" "}<span>Bớt đoán mò.</span></h1>}
        <p>{vibe === "roast"
          ? "Lá số để biết mình hay tự làm khó mình chỗ nào, Tarot cho chuyện đang rối, và check xem bạn với người ấy lệch sóng ở đâu."
          : "Đọc lá số để hiểu mình, rút Tarot cho chuyện đang vướng, hoặc xem mình và người ấy hợp nhau ở đâu."}</p>
      </section>
      {routeState?.expired ? (
        <p className="welcome-intro__notice" role="status">Phiên trên máy này đã hết hạn. Nếu đã liên kết tài khoản, đăng nhập lại để mở hồ sơ; chưa cần nhập lại ngày sinh.</p>
      ) : null}
      {routeState?.sessionChanged ? (
        <p className="welcome-intro__notice" role="status">Phiên trên trình duyệt này đã đổi. Lá đã ẩn nội dung cũ. Bấm bắt đầu để tiếp tục hồ sơ hiện có trên máy này; nếu dùng chung máy, hãy dùng cửa sổ riêng.</p>
      ) : null}
      {routeState?.offline ? (
        <p className="welcome-intro__notice" role="status">Bạn đang offline. Hồ sơ trên máy này vẫn được giữ. Có mạng rồi thử lại nhé.</p>
      ) : null}
      {error ? <p className="welcome-intro__notice welcome-intro__notice--error" role="alert">{error}</p> : null}
      <footer className="welcome-intro__actions">
        <button className="welcome-intro__primary" disabled={pending} onClick={() => void begin()} type="button">
          <span>{pending ? "Đang bắt đầu…" : "Đồng ý & bắt đầu"}</span>
          <ArrowRight aria-hidden="true" size={24} weight="bold" />
        </button>
        <Link className="welcome-intro__secondary" to="/existing-user?returnTo=/home"
          aria-disabled={creating || undefined} tabIndex={creating ? -1 : undefined}
          onClick={(event) => { if (creating) event.preventDefault(); }}>Đăng nhập</Link>
        <div className="welcome-intro__privacy">
          <p>Chỉ cần ngày sinh · Chưa cần tài khoản</p>
          <p>Khách: 30 ngày không hoạt động. Lịch sử tự động tối đa 30 ngày; note đã lưu giữ cùng hồ sơ.</p>
          <p>Dữ liệu riêng tư · <Link to="/privacy">Xem chi tiết</Link></p>
        </div>
      </footer>
    </main>
  );
}
