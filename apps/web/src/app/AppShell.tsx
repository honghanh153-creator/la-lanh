import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { OnboardingMotionContext } from "../shared/ui/onboardingMotion";

export function AppShell() {
  const { pathname } = useLocation();
  const [motionPaused, setMotionPaused] = useState(false);

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [pathname]);

  return (
    <div className="app-shell ultraviolet-app">
      <OnboardingMotionContext.Provider value={{
        paused: motionPaused,
        toggle: () => setMotionPaused((value) => !value),
      }}>
        <Outlet />
      </OnboardingMotionContext.Provider>
    </div>
  );
}
