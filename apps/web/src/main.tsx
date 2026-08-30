import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AppProviders } from "./app/AppProviders";
import { createAppRouter } from "./app/router";
import "./shared/styles/global.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("App root element is missing");
}

createRoot(root).render(
  <StrictMode>
    <AppProviders router={createAppRouter()} />
  </StrictMode>,
);
