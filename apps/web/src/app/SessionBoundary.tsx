import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiProblem, getSession, isGuestSessionUnavailable } from "../shared/api/client";
import {
  currentSessionEpoch, sessionCookieMarker, SESSION_ACCEPTED_EVENT,
  SESSION_CHANGE_NOTICE_KEY, SESSION_RESTART_REQUIRED_KEY,
} from "../shared/session/sessionIdentity";
import { clearPersonalDataOnDevice, PERSONAL_DATA_CLEARED_EVENT } from "../shared/storage/clearPersonalData";
import { LaLoading } from "../shared/ui/la/LaLoading";
import { PrivatePortalContext } from "../shared/ui/privatePortal";
import { useVibe } from "../shared/vibe/useVibe";

type Verification = { path: string; status: "checking" | "ready" | "offline"; mounted: boolean };

export function SessionBoundary({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [retry, setRetry] = useState(0);
  const [verification, setVerification] = useState<Verification>({ path: "", status: "checking", mounted: false });
  const verified = useRef<{ epoch: string; cookie: string | null } | null>(null);
  const privateContent = useRef<HTMLDivElement>(null);
  const [portalRoot, setPortalRoot] = useState<HTMLDivElement | null>(null);
  const { vibe } = useVibe();

  useEffect(() => {
    let active = true;
    let controller: AbortController | null = null;
    let checking = false;
    let suspended = document.visibilityState === "hidden";
    let revision = 0;
    const hide = () => {
      // pagehide can be snapshotted before React commits its queued update.
      if (privateContent.current) privateContent.current.hidden = true;
      setVerification((current) => {
      const mounted = current.path === pathname && current.mounted;
      if (current.path === pathname && current.status === "checking" && current.mounted === mounted) return current;
      return { path: pathname, status: "checking", mounted };
      });
    };
    const restart = () => {
      queryClient.clear();
      sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
      void navigate("/welcome?restart=1", { replace: true, state: { sessionChanged: true } });
    };
    const check = async () => {
      if (!active || checking || suspended) return;
      if (sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY) === "1") { restart(); return; }
      checking = true;
      hide();
      const expected = verified.current?.epoch ?? currentSessionEpoch();
      controller = new AbortController();
      const operation = controller;
      const expectedRevision = revision;
      const isCurrent = () => active && !suspended && expectedRevision === revision && !operation.signal.aborted;
      try {
        const session = await getSession(operation.signal);
        if (!isCurrent()) return;
        if (typeof session.session_epoch !== "string" || !session.session_epoch) throw new Error("Unverified session");
        if (expected && expected !== session.session_epoch) { restart(); return; }
        verified.current = { epoch: session.session_epoch, cookie: sessionCookieMarker() };
        setVerification({ path: pathname, status: "ready", mounted: true });
      } catch (error) {
        if (!isCurrent()) return;
        if (isGuestSessionUnavailable(error) || (error instanceof ApiProblem && error.code === "SESSION_CHANGED")) {
          await clearPersonalDataOnDevice();
          if (!isCurrent()) return;
          queryClient.clear();
          if (error instanceof ApiProblem && error.code === "SESSION_CHANGED") restart();
          else void navigate("/welcome?restart=1", { replace: true, state: { expired: true } });
        } else {
          setVerification((current) => ({ ...current, path: pathname, status: "offline" }));
        }
      } finally {
        if (controller === operation) checking = false;
      }
    };
    const suspend = () => {
      if (!active) return;
      suspended = true;
      revision += 1;
      controller?.abort();
      controller = null;
      checking = false;
      hide();
    };
    const resume = () => {
      if (!active || document.visibilityState === "hidden") return;
      suspended = false;
      void check();
    };
    const visibility = () => { if (document.visibilityState === "visible") resume(); else suspend(); };
    const cleared = () => { queryClient.clear(); hide(); };
    const accepted = () => {
      if (verified.current && verified.current.epoch !== currentSessionEpoch()) restart();
    };
    const siblingChanged = (event: StorageEvent) => {
      if (event.key === SESSION_CHANGE_NOTICE_KEY) resume();
    };
    void check();
    window.addEventListener("focus", resume);
    window.addEventListener("pageshow", resume);
    window.addEventListener("pagehide", suspend);
    document.addEventListener("visibilitychange", visibility);
    window.addEventListener("storage", siblingChanged);
    window.addEventListener(PERSONAL_DATA_CLEARED_EVENT, cleared);
    window.addEventListener(SESSION_ACCEPTED_EVENT, accepted);
    const timer = window.setInterval(() => {
      if (verified.current && verified.current.cookie !== sessionCookieMarker()) resume();
    }, 500);
    return () => {
      active = false;
      controller?.abort();
      window.clearInterval(timer);
      window.removeEventListener("focus", resume);
      window.removeEventListener("pageshow", resume);
      window.removeEventListener("pagehide", suspend);
      document.removeEventListener("visibilitychange", visibility);
      window.removeEventListener("storage", siblingChanged);
      window.removeEventListener(PERSONAL_DATA_CLEARED_EVENT, cleared);
      window.removeEventListener(SESSION_ACCEPTED_EVENT, accepted);
    };
  }, [pathname, navigate, queryClient, retry]);

  const ready = verification.path === pathname && verification.status === "ready";
  const privatePortal = useMemo(() => ({ target: portalRoot, visible: ready }), [portalRoot, ready]);
  return <>
    {!ready ? <main className="app-page session-check">
      {verification.status === "offline"
        ? <LaLoading delayMs={0} key="offline" text="Lá chưa bắt được sóng. Nội dung riêng tư đang được ẩn cho an toàn.">
          <button className="primary-link" type="button" onClick={() => setRetry((value) => value + 1)}>Thử lại</button><Link to="/welcome">Về trang đầu</Link>
        </LaLoading>
        : <LaLoading delayMs={220} key="checking" text={vibe === "roast" ? "Đợi xíu, Lá đang soi đúng hồ sơ của bạn…" : "Lá đang mở đúng hồ sơ của bạn…"} />}
    </main> : null}
    <div ref={privateContent} hidden={!ready}>
      <PrivatePortalContext.Provider value={privatePortal}>
        {verification.path === pathname && verification.mounted ? children : null}
      </PrivatePortalContext.Provider>
      {/* Sheets portal here, inside the hidden region, never to document.body. */}
      <div className="private-portal-root" ref={setPortalRoot} />
    </div>
  </>;
}
