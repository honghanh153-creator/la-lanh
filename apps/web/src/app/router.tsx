import {
  createBrowserRouter,
  isRouteErrorResponse,
  Link,
  type RouteObject,
  useRouteError,
} from "react-router-dom";

import { ExistingUserPage } from "../features/account/ExistingUserPage";
import { BirthDatePage } from "../features/birth/BirthDatePage";
import { BirthSupplementPage } from "../features/birth/BirthSupplementPage";
import { CardPage } from "../features/card/CardPage";
import { BirthCardPage } from "../features/card/BirthCardPage";
import { SharePreviewPage } from "../features/card/SharePreviewPage";
import { ConsentPage } from "../features/consent/ConsentPage";
import { DemoPage } from "../features/consent/DemoPage";
import { EntryPage } from "../features/entry/EntryPage";
import { HomePage } from "../features/home/HomePage";
import { NoteDetailPage } from "../features/home/NoteDetailPage";
import { CalculationSettingsPage } from "../features/insights/CalculationSettingsPage";
import { CurrentSkyPage } from "../features/insights/CurrentSkyPage";
import { InsightsPage } from "../features/insights/InsightsPage";
import { ReadingDetailPage } from "../features/insights/ReadingDetailPage";
import { InviteHistoryPage } from "../features/la-chung/InviteHistoryPage";
import { InvitePreviewPage } from "../features/la-chung/InvitePreviewPage";
import { InviteStartPage } from "../features/la-chung/InviteStartPage";
import { PublicResponsePage } from "../features/la-chung/PublicResponsePage";
import { ResultPage } from "../features/la-chung/ResultPage";
import { PublicRadarPage } from "../features/radar/PublicRadarPage";
import { RadarContinuePage } from "../features/radar/RadarContinuePage";
import { RadarLandingPage } from "../features/radar/RadarLandingPage";
import { RadarOwnerResultPage } from "../features/radar/RadarOwnerResultPage";
import { RadarPrivateStartPage } from "../features/radar/RadarPrivateStartPage";
import { RadarReceiptPage } from "../features/radar/RadarReceiptPage";
import { RadarStartPage } from "../features/radar/RadarStartPage";
import { ProfilePage } from "../features/profile/ProfilePage";
import { AuraCutoverPage } from "../features/reveal/AuraCutoverPage";
import { RevealPage } from "../features/reveal/RevealPage";
import { SavedPage } from "../features/saved/SavedPage";
import { WelcomePage } from "../features/welcome/WelcomePage";
import { TarotPage } from "../features/tarot/TarotPage";
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
      { path: "birth-time", element: <BirthSupplementPage /> },
      { path: "reveal", element: <RevealPage /> },
      { path: "aura-cutover", element: <AuraCutoverPage /> },
      { path: "reveal/aura", element: <AuraCutoverPage /> },
      { path: "insights", element: <InsightsPage /> },
      { path: "natal", element: <InsightsPage /> },
      { path: "insights/settings", element: <CalculationSettingsPage /> },
      { path: "insights/current-sky", element: <CurrentSkyPage /> },
      { path: "insights/:claimId", element: <ReadingDetailPage /> },
      { path: "la-chung", element: <InviteStartPage /> },
      { path: "la-chung/preview", element: <InvitePreviewPage /> },
      { path: "la-chung/history", element: <InviteHistoryPage /> },
      { path: "la-chung/result/:requestId", element: <ResultPage /> },
      { path: "radar", element: <RadarLandingPage /> },
      { path: "radar/start", element: <RadarPrivateStartPage /> },
      { path: "radar/invite", element: <RadarStartPage /> },
      { path: "radar/continue", element: <RadarContinuePage /> },
      { path: "radar/receipt", element: <RadarReceiptPage /> },
      { path: "radar/result/:requestId", element: <RadarOwnerResultPage /> },
      { path: "vong-la", element: <RadarLandingPage /> },
      { path: "vong-la/setup", element: <RadarStartPage /> },
      { path: "home", element: <HomePage /> },
      { path: "note/today", element: <NoteDetailPage /> },
      { path: "card", element: <CardPage /> },
      { path: "birth-card", element: <BirthCardPage /> },
      { path: "share/:token", element: <SharePreviewPage /> },
      { path: "saved", element: <SavedPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "existing-user", element: <ExistingUserPage /> },
      { path: "tarot", element: <TarotPage /> },
      { path: "tarot/:sessionId", element: <TarotPage /> },
    ],
  },
  {
    path: "/la-chung/i/:token",
    element: <PublicResponsePage />,
    errorElement: <RouteErrorPage />,
  },
  {
    path: "/radar/i/:token",
    element: <PublicRadarPage />,
    errorElement: <RouteErrorPage />,
  },
];

export function createAppRouter() {
  return createBrowserRouter(appRoutes);
}
