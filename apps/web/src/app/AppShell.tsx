import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { OnboardingMotionContext } from "../shared/ui/onboardingMotion";
import { SessionBoundary } from "./SessionBoundary";

const PUBLIC_PATHS = new Set([
  "/", "/welcome", "/consent", "/privacy", "/demo", "/radar", "/vong-la",
  "/tarot", "/existing-user", "/auth/callback",
]);

export function AppShell() {
  const { pathname } = useLocation();
  const [motionPaused, setMotionPaused] = useState(false);
  const retiredLaChung = pathname.startsWith("/la-chung")
    && !["/la-chung/history", "/la-chung/manage-response"].includes(pathname)
    && !pathname.startsWith("/la-chung/result/");
  const privatePage = !PUBLIC_PATHS.has(pathname) && !pathname.startsWith("/share/") && !retiredLaChung;

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [pathname]);

  return (
    <div className="app-shell ultraviolet-app">
      <OnboardingMotionContext.Provider value={{
        paused: motionPaused,
        toggle: () => setMotionPaused((value) => !value),
      }}>
        {privatePage ? <SessionBoundary><Outlet /></SessionBoundary> : <Outlet />}
      </OnboardingMotionContext.Provider>
    </div>
  );
}
