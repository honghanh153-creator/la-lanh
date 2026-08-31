import {
  createBrowserRouter,
  isRouteErrorResponse,
  Link,
  type RouteObject,
  useRouteError,
} from "react-router-dom";

import { ExistingUserPage } from "../features/account/ExistingUserPage";
import { BirthDatePage } from "../features/birth/BirthDatePage";
import { CardPage } from "../features/card/CardPage";
import { ConsentPage } from "../features/consent/ConsentPage";
import { DemoPage } from "../features/consent/DemoPage";
import { EntryPage } from "../features/entry/EntryPage";
import { HomePage } from "../features/home/HomePage";
import { ProfilePage } from "../features/profile/ProfilePage";
import { RevealPage } from "../features/reveal/RevealPage";
import { SavedPage } from "../features/saved/SavedPage";
import { WelcomePage } from "../features/welcome/WelcomePage";
import { AppShell } from "./AppShell";

function RouteErrorPage() {
  const error = useRouteError();
  const title = isRouteErrorResponse(error) && error.status === 404
    ? "Trang này chưa nảy mầm."
    : "Lá Lành đang cần một nhịp nghỉ.";

  return (
    <main className="route-error">
      <p className="eyebrow">Có một nốt lặng</p>
      <h1>{title}</h1>
      <p>Quay về điểm bắt đầu và thử lại nhé.</p>
      <Link className="primary-link" to="/">
        Về trang chào
      </Link>
    </main>
  );
}

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <AppShell />,
    errorElement: <RouteErrorPage />,
    children: [
      {
        index: true,
        element: <EntryPage />,
      },
      {
        path: "welcome",
        element: <WelcomePage />,
      },
      { path: "consent", element: <ConsentPage /> },
      { path: "privacy", element: <ConsentPage /> },
      { path: "demo", element: <DemoPage /> },
      { path: "birth", element: <BirthDatePage /> },
      { path: "reveal", element: <RevealPage /> },
      { path: "home", element: <HomePage /> },
      { path: "card", element: <CardPage /> },
      { path: "saved", element: <SavedPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "existing-user", element: <ExistingUserPage /> },
    ],
  },
];

export function createAppRouter() {
  return createBrowserRouter(appRoutes);
}
