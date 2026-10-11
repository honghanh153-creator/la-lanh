import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { SESSION_EPOCH_KEY, SESSION_CHANGE_NOTICE_KEY, SESSION_RESTART_REQUIRED_KEY } from "../shared/session/sessionIdentity";
import { SessionBoundary } from "./SessionBoundary";
import { testLocks, testRequestUrl } from "../shared/session/testLocks";

function response(epoch: string) {
  return new Response(JSON.stringify({ state: "active", onboarding_status: "completed",
    expires_at: "2026-11-09T00:00:00Z", session_epoch: epoch }), { status: 200 });
}

function renderPrivate() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  client.setQueryData(["daily-note"], { title: "cached private A" });
  const router = createMemoryRouter([
    { path: "/home", element: <SessionBoundary><p>Private reading</p></SessionBoundary> },
    { path: "/welcome", element: <p>Start safely</p> },
  ], { initialEntries: ["/home"] });
  const view = render(<QueryClientProvider client={client}><RouterProvider router={router} /></QueryClientProvider>);
  return { client, router, unmount: view.unmount };
}

beforeEach(() => {
  vi.stubGlobal("navigator", Object.create(navigator, { locks: { value: testLocks(), configurable: true } }));
  localStorage.clear(); sessionStorage.clear();
  document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
  // Memory-router Request uses undici while jsdom owns AbortSignal. Only the
  // router's synthetic Request needs this adapter; API abort signals stay real.
  const NativeRequest = globalThis.Request;
  vi.stubGlobal("Request", class extends NativeRequest {
    constructor(input: RequestInfo | URL, init?: RequestInit) {
      super(input, { ...init, signal: undefined });
    }
  });
});
afterEach(() => {
  document.cookie = "la_lanh_csrf=; Max-Age=0; path=/";
  vi.restoreAllMocks(); vi.unstubAllGlobals();
});

it("polls a changed cookie without focus or storage events and hides until verified", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  document.cookie = "la_lanh_csrf=owner-a; path=/";
  let finish: (value: Response) => void = () => { throw new Error("Poll not started"); };
  const requests = vi.spyOn(globalThis, "fetch")
    .mockImplementation((url) => {
      if (testRequestUrl(url).endsWith("/session/renew")) return Promise.resolve(response("epoch-a"));
      if (requests.mock.calls.filter(([path]) => testRequestUrl(path).endsWith("/session")).length === 1) return Promise.resolve(response("epoch-a"));
      return new Promise((resolve) => { finish = resolve; });
    });
  const { client } = renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  document.cookie = "la_lanh_csrf=owner-b; path=/";
  await waitFor(() => expect(requests.mock.calls.filter(([path]) => testRequestUrl(path).endsWith("/session"))).toHaveLength(2));
  expect(screen.getByText("Private reading")).not.toBeVisible();
  await act(async () => { finish(response("epoch-b")); await Promise.resolve(); });
  expect(await screen.findByText("Start safely")).toBeVisible();
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
});

it("removes its cookie polling timer when the private boundary unmounts", async () => {
  const interval = vi.spyOn(window, "setInterval");
  const clear = vi.spyOn(window, "clearInterval");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(response("epoch-a"));
  const { unmount } = renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  const poll = interval.mock.results[0]?.value;
  expect(poll).toBeDefined();
  unmount();
  expect(clear).toHaveBeenCalledWith(poll);
});

it("does not mount private content before session verification", async () => {
  let finish: (value: Response) => void = () => { throw new Error("Session check not started"); };
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  renderPrivate();
  expect(screen.queryByText("Private reading")).not.toBeInTheDocument();
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  await act(async () => { finish(response("epoch-a")); await Promise.resolve(); });
  expect(await screen.findByText("Private reading")).toBeVisible();
});

it("does not silently render B when A's stored epoch no longer matches the server", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(response("epoch-b"));
  const { client, router } = renderPrivate();
  expect(await screen.findByText("Start safely")).toBeVisible();
  expect(screen.queryByText("Private reading")).not.toBeInTheDocument();
  expect(router.state.location.state).toMatchObject({ sessionChanged: true });
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
});

it("revalidates on tab focus and clears private queries when a sibling tab has changed guest", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response("epoch-a"))
    .mockResolvedValueOnce(response("epoch-b"));
  const { client } = renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  act(() => { window.dispatchEvent(new Event("focus")); });
  expect(screen.getByText("Private reading")).not.toBeVisible();
  expect(await screen.findByText("Start safely")).toBeVisible();
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
});

it("checks a sibling-tab notification without trusting its payload as an identity", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => Promise.resolve(response("epoch-a")));
  renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  act(() => { window.dispatchEvent(new StorageEvent("storage", {
    key: SESSION_CHANGE_NOTICE_KEY, newValue: "not an epoch",
  })); });
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  await waitFor(() => expect(screen.getByText("Private reading")).toBeVisible());
  expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("epoch-a");
});

it("keeps private content hidden if resume fails offline", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response("epoch-a"))
    .mockRejectedValueOnce(new TypeError("offline"));
  renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  act(() => { window.dispatchEvent(new Event("focus")); });
  expect(await screen.findByRole("button", { name: "Thử lại" })).toBeVisible();
  expect(screen.getByText("Private reading")).not.toBeVisible();
});

it("cannot use Back or a direct private URL to adopt B after a session-change warning", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-b");
  sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
  const fetchMock = vi.spyOn(globalThis, "fetch");
  const { client, router } = renderPrivate();
  expect(await screen.findByText("Start safely")).toBeVisible();
  expect(router.state.location.state).toMatchObject({ sessionChanged: true });
  expect(screen.queryByText("Private reading")).not.toBeInTheDocument();
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
  expect(fetchMock).not.toHaveBeenCalled();
});

it("does not reveal a check that completes in the background; visible requires a fresh check", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  let finish: (value: Response) => void = () => { throw new Error("check not started"); };
  const fetchMock = vi.spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(response("epoch-a"))
    .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }))
    .mockResolvedValueOnce(response("epoch-a"));
  renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  await act(() => window.dispatchEvent(new Event("focus")));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");
  await act(() => document.dispatchEvent(new Event("visibilitychange")));
  await act(async () => { finish(response("epoch-a")); await Promise.resolve(); });
  expect(screen.getByText("Private reading")).not.toBeVisible();
  vi.spyOn(document, "visibilityState", "get").mockReturnValue("visible");
  await act(() => document.dispatchEvent(new Event("visibilitychange")));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  expect(screen.getByText("Private reading")).toBeVisible();
});

it.each(["epoch-a", "epoch-b"])("pagehide/BFCache stays hidden until fresh verification of %s", async (epoch) => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  let finish: (value: Response) => void = () => { throw new Error("resume not started"); };
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response("epoch-a"))
    .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  const { client, router } = renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  act(() => { window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true })); });
  expect(screen.getByText("Private reading")).not.toBeVisible();
  act(() => { window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })); });
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(screen.getByText("Private reading")).not.toBeVisible();
  await act(async () => { finish(response(epoch)); await vi.dynamicImportSettled(); });
  if (epoch === "epoch-a") {
    expect(screen.getByText("Private reading")).toBeVisible();
    expect(client.getQueryData(["daily-note"])).toEqual({ title: "cached private A" });
  } else {
    expect(await screen.findByText("Start safely")).toBeVisible();
    expect(router.state.location.state).toMatchObject({ sessionChanged: true });
    expect(client.getQueryData(["daily-note"])).toBeUndefined();
  }
});

it.each(["GUEST_EXPIRED", "SESSION_CHANGED"])("clears private data and routes safely on %s", async (code) => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  sessionStorage.setItem("la-lanh-radar-pending", "old draft");
  vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ code }), { status: 401 }));
  const { client, router } = renderPrivate();
  expect(await screen.findByText("Start safely")).toBeVisible();
  expect(router.state.location.state).toMatchObject(code === "GUEST_EXPIRED" ? { expired: true } : { sessionChanged: true });
  expect(client.getQueryData(["daily-note"])).toBeUndefined();
  expect(sessionStorage.getItem("la-lanh-radar-pending")).toBeNull();
  expect(screen.queryByText("Private reading")).not.toBeInTheDocument();
});

it("offline Retry keeps content hidden until a successful same-owner verification", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  let finish: (value: Response) => void = () => { throw new Error("retry not started"); };
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(response("epoch-a"))
    .mockRejectedValueOnce(new TypeError("offline"))
    .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
  renderPrivate();
  expect(await screen.findByText("Private reading")).toBeVisible();
  act(() => { window.dispatchEvent(new Event("focus")); });
  const retry = await screen.findByRole("button", { name: "Thử lại" });
  act(() => { retry.click(); });
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  expect(screen.getByText("Private reading")).not.toBeVisible();
  await act(async () => { finish(response("epoch-a")); await Promise.resolve(); });
  expect(screen.getByText("Private reading")).toBeVisible();
});

it("unmount ignores late responses and lifecycle events without navigation or adoption", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "epoch-a");
  let finish: (value: Response) => void = () => { throw new Error("check not started"); };
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  const { unmount, router } = renderPrivate();
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  unmount();
  act(() => {
    window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
    window.dispatchEvent(new Event("pagehide"));
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await act(async () => { finish(response("epoch-b")); await vi.dynamicImportSettled(); });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(router.state.location.pathname).toBe("/home");
  expect(sessionStorage.getItem(SESSION_EPOCH_KEY)).toBe("epoch-a");
  expect(screen.queryByText("Private reading")).not.toBeInTheDocument();
});
