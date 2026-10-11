import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { requestGoogleLogin } from "../../shared/api/client";
import { SESSION_EPOCH_KEY } from "../../shared/session/sessionIdentity";
import { testLocks, testRequestUrl } from "../../shared/session/testLocks";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";
import { WelcomePage } from "./WelcomePage";

beforeEach(() => {
  sessionStorage.clear(); localStorage.clear();
  vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it("departed creation cannot erase the next screen's draft/key or abort its Google transport", async () => {
  let finishCreation: (response: Response) => void = () => { throw new Error("not creating"); };
  let finishGoogle: (response: Response) => void = () => { throw new Error("not signing in"); };
  let googleSignal: AbortSignal | null | undefined;
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((url, init) => {
    if (testRequestUrl(url).endsWith("/session")) return Promise.resolve(new Response(JSON.stringify({ code: "GUEST_SESSION_MISSING" }), { status: 401 }));
    if (testRequestUrl(url).endsWith("/guest-sessions")) return new Promise((resolve) => { finishCreation = resolve; });
    if (testRequestUrl(url).endsWith("/account/login/google")) {
      googleSignal = init?.signal;
      return new Promise((resolve) => { finishGoogle = resolve; });
    }
    throw new Error(`Unexpected request: ${testRequestUrl(url)}`);
  });
  let google: Promise<unknown> = Promise.resolve();
  function NextScreen() {
    useEffect(() => {
      sessionStorage.setItem("la-lanh-guest-create-key", "new-screen-key");
      sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "new-screen-draft");
      google = requestGoogleLogin();
      void google.catch(() => undefined);
    }, []);
    return <p>Next screen</p>;
  }
  render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={["/welcome"]}>
    <Routes><Route path="/welcome" element={<WelcomePage />} /><Route path="/privacy" element={<NextScreen />} /></Routes>
  </MemoryRouter></QueryClientProvider>);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  await user.click(screen.getByRole("link", { name: "Xem chi tiết" }));
  expect(screen.getByText("Next screen")).toBeVisible();
  await act(async () => {
    finishCreation(new Response(JSON.stringify({ state: "active", onboarding_status: "birth_pending", expires_at: "2026-11-09T00:00:00Z", session_epoch: "abandoned-a" }), { status: 200 }));
    await vi.dynamicImportSettled();
  });
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  expect(sessionStorage.getItem("la-lanh-guest-create-key")).toBe("new-screen-key");
  expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBe("new-screen-draft");
  expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBeNull();
  expect(googleSignal?.aborted).toBe(false);
  await act(async () => { finishGoogle(new Response(JSON.stringify({ authorize_url: "https://synthetic.invalid", expires_at: "2026-11-09T00:00:00Z" }))); await google; });
});
