import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";

export function AppShell() {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  }, [pathname]);

  return (
    <div className="app-shell">
      <Outlet />
    </div>
  );
}
