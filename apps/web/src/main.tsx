import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@fontsource/be-vietnam-pro/400.css";
import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/700.css";
import "@fontsource/be-vietnam-pro/800.css";
import "@fontsource/be-vietnam-pro/900.css";

import { AppProviders } from "./app/AppProviders";
import { createAppRouter } from "./app/router";
import { applyThemePreference, readThemePreference } from "./shared/theme/theme";
import "./shared/styles/global.css";
import "./shared/styles/ultraviolet.css";

applyThemePreference(readThemePreference());

const root = document.getElementById("root");

if (!root) {
  throw new Error("App root element is missing");
}

createRoot(root).render(
  <StrictMode>
    <AppProviders router={createAppRouter()} />
  </StrictMode>,
);

if ("serviceWorker" in navigator && import.meta.env.PROD && !navigator.webdriver) {
  window.addEventListener("load", () => {
    const isLocalPreview = ["127.0.0.1", "localhost"].includes(window.location.hostname);

    if (isLocalPreview) {
      // Local QA builds change often. A previously installed PWA worker can
      // otherwise keep an already-open review tab on an older bundle.
      void navigator.serviceWorker
        .getRegistrations()
        .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())));
      return;
    }

    void navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((registration) => registration.update());
  });
}
