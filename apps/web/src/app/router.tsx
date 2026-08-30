import {
  createBrowserRouter,
  isRouteErrorResponse,
  Link,
  type RouteObject,
  useRouteError,
} from "react-router-dom";

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
        element: <WelcomePage />,
      },
    ],
  },
];

export function createAppRouter() {
  return createBrowserRouter(appRoutes);
}
