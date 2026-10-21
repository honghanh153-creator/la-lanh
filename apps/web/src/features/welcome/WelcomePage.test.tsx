import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StrictMode } from "react";
import { Link, MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiProblem, acceptBasicBirthConsent, enableHistoryRetention, createGuest, getBirthProfile, getSession } from "../../shared/api/client";
import { SESSION_RESTART_REQUIRED_KEY } from "../../shared/session/sessionIdentity";
import { EntryPage } from "../entry/EntryPage";
import { AppShell } from "../../app/AppShell";
import { SignalStationFrame } from "../../shared/ui/SignalStationFrame";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";
import { WelcomePage } from "./WelcomePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, acceptBasicBirthConsent: vi.fn(), enableHistoryRetention: vi.fn(), createGuest: vi.fn(), getBirthProfile: vi.fn(), getSession: vi.fn() };
});

function renderPage(entry = "/welcome") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = render(
    <StrictMode><QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>
        <Routes>
          <Route path="/welcome" element={<WelcomePage />} />
          <Route path="/birth" element={<h1>Ngày sinh</h1>} />
          <Route path="/" element={<h1>Tiếp tục hồ sơ</h1>} />
          <Route path="/existing-user" element={<><h1>Đăng nhập với Google</h1><Link to="/welcome">Quay lại</Link></>} />
          <Route path="/privacy" element={<h1>Privacy</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider></StrictMode>,
  );
  return { ...view, client };
}

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("WelcomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(acceptBasicBirthConsent).mockResolvedValue(undefined);
    vi.mocked(enableHistoryRetention).mockResolvedValue({ enabled: true, history_days: 30, daily_note_hours: 24, activated_at: "2026-10-10T00:00:00Z", saved_notes_kept: true });
    sessionStorage.clear();
    vi.mocked(getSession).mockRejectedValue(new ApiProblem(401, "GUEST_SESSION_MISSING", "missing"));
    vi.mocked(createGuest).mockResolvedValue({
      state: "active",
      onboarding_status: "birth_pending",
      expires_at: "2026-10-14T00:00:00Z",
      resumed: false,
      session_epoch: "epoch-test",
    });
  });

  it("resumes an active profile instead of creating a replacement on a normal return", async () => {
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "same-person", resumed: true });
    renderPage();
    await userEvent.setup().click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("heading", { name: "Tiếp tục hồ sơ" })).toBeInTheDocument();
    expect(createGuest).not.toHaveBeenCalled();
  });

  it.each(["active", "missing", "offline"])("keeps Google navigation when departed session verification finishes as %s", async (outcome) => {
    const verification = deferred<Awaited<ReturnType<typeof getSession>>>();
    vi.mocked(getSession).mockReturnValueOnce(verification.promise);
    sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(screen.getByRole("button", { name: "Đang bắt đầu…" })).toBeDisabled();
    const signal = vi.mocked(getSession).mock.calls[0][0];
    await user.click(screen.getByRole("link", { name: "Đăng nhập" }));
    expect(screen.getByRole("heading", { name: "Đăng nhập với Google" })).toBeInTheDocument();
    await act(async () => {
      if (outcome === "active") {
        verification.resolve({ state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "same-person", resumed: true });
      } else {
        verification.reject(outcome === "missing" ? new ApiProblem(401, "GUEST_SESSION_MISSING", "missing") : new TypeError("offline"));
      }
      await verification.promise.catch(() => undefined);
    });
    expect(screen.getByRole("heading", { name: "Đăng nhập với Google" })).toBeInTheDocument();
    expect(signal?.aborted).toBe(true);
    expect(acceptBasicBirthConsent).not.toHaveBeenCalled();
    expect(enableHistoryRetention).not.toHaveBeenCalled();
    expect(createGuest).not.toHaveBeenCalled();
    expect(sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY)).toBe("1");
  });

  it.each(["active", "missing"])("ignores old %s verification after returning for a fresh Welcome attempt", async (outcome) => {
    const oldVerification = deferred<Awaited<ReturnType<typeof getSession>>>();
    const newVerification = deferred<Awaited<ReturnType<typeof getSession>>>();
    vi.mocked(getSession).mockReturnValueOnce(oldVerification.promise).mockReturnValueOnce(newVerification.promise);
    sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    await user.click(screen.getByRole("link", { name: "Đăng nhập" }));
    await user.click(screen.getByRole("link", { name: "Quay lại" }));
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(getSession).toHaveBeenCalledTimes(2);
    const session = { state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "same-person", resumed: true };
    await act(async () => {
      if (outcome === "active") oldVerification.resolve(session);
      else oldVerification.reject(new ApiProblem(401, "GUEST_SESSION_MISSING", "missing"));
      await oldVerification.promise.catch(() => undefined);
    });
    expect(screen.getByRole("button", { name: "Đang bắt đầu…" })).toBeDisabled();
    expect(acceptBasicBirthConsent).not.toHaveBeenCalled();
    expect(enableHistoryRetention).not.toHaveBeenCalled();
    expect(createGuest).not.toHaveBeenCalled();
    expect(sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY)).toBe("1");
    await act(async () => {
      newVerification.resolve(session);
      await newVerification.promise;
    });
    expect(screen.getByRole("heading", { name: "Tiếp tục hồ sơ" })).toBeInTheDocument();
    expect(acceptBasicBirthConsent).toHaveBeenCalledTimes(1);
    expect(enableHistoryRetention).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY)).toBeNull();
    expect(createGuest).not.toHaveBeenCalled();
  });

  it("does not start history consent after leaving during birth consent", async () => {
    const consent = deferred<void>();
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "same-person", resumed: true });
    vi.mocked(acceptBasicBirthConsent).mockReturnValueOnce(consent.promise);
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(acceptBasicBirthConsent).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("link", { name: "Đăng nhập" }));
    await act(async () => {
      consent.resolve(undefined);
      await consent.promise;
    });
    expect(screen.getByRole("heading", { name: "Đăng nhập với Google" })).toBeInTheDocument();
    expect(enableHistoryRetention).not.toHaveBeenCalled();
    expect(createGuest).not.toHaveBeenCalled();
  });

  it("does not acknowledge or navigate after leaving during history consent", async () => {
    const consent = deferred<Awaited<ReturnType<typeof enableHistoryRetention>>>();
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "same-person", resumed: true });
    vi.mocked(enableHistoryRetention).mockReturnValueOnce(consent.promise);
    sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(enableHistoryRetention).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("link", { name: "Đăng nhập" }));
    await act(async () => {
      consent.resolve({ enabled: true, history_days: 30, daily_note_hours: 24, activated_at: "2026-10-10T00:00:00Z", saved_notes_kept: true });
      await consent.promise;
    });
    expect(screen.getByRole("heading", { name: "Đăng nhập với Google" })).toBeInTheDocument();
    expect(sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY)).toBe("1");
    expect(createGuest).not.toHaveBeenCalled();
  });

  it.each(["success", "failure"])("ignores departed guest creation %s without clearing cache or Radar intent", async (outcome) => {
    const creation = deferred<Awaited<ReturnType<typeof createGuest>>>();
    vi.mocked(createGuest).mockReturnValueOnce(creation.promise);
    sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "keep-radar");
    sessionStorage.setItem("la-lanh-radar-owner-start", "1");
    const user = userEvent.setup();
    const view = renderPage("/welcome?restart=1");
    expect(createGuest).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(createGuest).toHaveBeenCalledTimes(1);
    view.client.setQueryData(["login-operation"], "keep-cache");
    const key = sessionStorage.getItem("la-lanh-guest-create-key");
    await user.click(screen.getByRole("link", { name: "Đăng nhập" }));
    expect(screen.getByRole("link", { name: "Đăng nhập" })).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("heading", { name: "Hiểu mình hơn. Bớt đoán mò." })).toBeVisible();
    await user.click(screen.getByRole("link", { name: "Xem chi tiết" }));
    sessionStorage.setItem("la-lanh-guest-create-key", "login-operation-key");
    await act(async () => {
      if (outcome === "success") {
        creation.resolve({ state: "active", onboarding_status: "birth_pending", expires_at: "2026-11-10T00:00:00Z", session_epoch: "new-person", resumed: false });
      } else {
        creation.reject(new TypeError("offline"));
      }
      await creation.promise.catch(() => undefined);
    });
    expect(screen.getByRole("heading", { name: "Privacy" })).toBeInTheDocument();
    expect(view.client.getQueryData(["login-operation"])).toBe("keep-cache");
    expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBe("keep-radar");
    expect(sessionStorage.getItem("la-lanh-radar-owner-start")).toBe("1");
    expect(key).not.toBeNull();
    expect(sessionStorage.getItem("la-lanh-guest-create-key")).toBe("login-operation-key");
  });

  it("does not replace or clear the current guest when session verification is offline", async () => {
    vi.mocked(getSession).mockRejectedValue(new TypeError("offline"));
    sessionStorage.setItem("existing-profile", "keep"); renderPage();
    await userEvent.setup().click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(createGuest).not.toHaveBeenCalled();
    expect(sessionStorage.getItem("existing-profile")).toBe("keep");
  });

  it("shows one concise consent step without a carousel or login wall", () => {
    renderPage();

    expect(screen.getByLabelText("Lá Lành")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Hiểu mình hơn. Bớt đoán mò." })).toBeInTheDocument();
    expect(screen.getByText("Đọc lá số để hiểu mình, rút Tarot cho chuyện đang vướng, hoặc xem mình và người ấy hợp nhau ở đâu.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đồng ý & bắt đầu" })).toBeEnabled();
    expect(screen.queryByRole("link", { name: "Xem bản mẫu" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Đăng nhập" })).toHaveAttribute("href", "/existing-user?returnTo=/home");
    expect(screen.queryByRole("link", { name: /hồ sơ khác/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Tiếp tục hồ sơ trên máy này" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Xem chi tiết" })).toHaveAttribute("href", "/privacy");
    expect(document.querySelector('a[href="/consent"]')).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Tiến độ giới thiệu")).not.toBeInTheDocument();
    expect(screen.queryByText("Mình đã có tài khoản")).not.toBeInTheDocument();
    expect(createGuest).not.toHaveBeenCalled();
  });

  it("pauses every hero layer without recording consent or blocking the CTA", async () => {
    const user = userEvent.setup();
    renderPage();
    expect(document.querySelector(".welcome-intro__hero")).toHaveAttribute("aria-hidden", "true");
    await user.click(screen.getByRole("button", { name: "Tạm dừng chuyển động" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "true");
    expect(screen.getByRole("button", { name: "Đồng ý & bắt đầu" })).toBeEnabled();
    expect(createGuest).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Tiếp tục chuyển động" }));
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "false");
  });

  it("keeps an unsuccessful consent action retryable with the same idempotency key", async () => {
    const user = userEvent.setup();
    vi.mocked(createGuest).mockRejectedValueOnce(new Error("offline"));
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Kiểm tra kết nối rồi thử lại nhé.");
    const key = vi.mocked(createGuest).mock.calls[0][0];
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("heading", { name: "Ngày sinh" })).toBeInTheDocument();
    expect(vi.mocked(createGuest).mock.calls[1][0]).toBe(key);
  });

  it("creates a guest directly and moves to DOB with one affirmative action", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "radar-request-1");
    sessionStorage.setItem("la-lanh-radar-owner-start", "1");
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));

    expect(createGuest).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBe("radar-request-1");
    expect(sessionStorage.getItem("la-lanh-radar-owner-start")).toBe("1");
    expect(await screen.findByRole("heading", { name: "Ngày sinh" })).toBeInTheDocument();
  });

  it("preserves the user's animation pause when the real app shell moves to birth", async () => {
    vi.mocked(getSession).mockRejectedValueOnce(new ApiProblem(401, "GUEST_SESSION_MISSING", "missing"));
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "birth_pending", session_epoch: "epoch-test", expires_at: "2026-11-09T00:00:00Z", resumed: true });
    vi.spyOn(globalThis, "fetch").mockImplementation(() => Promise.resolve(new Response(JSON.stringify({
      state: "active", onboarding_status: "birth_pending", session_epoch: "epoch-test",
      expires_at: "2026-11-09T00:00:00Z",
    }), { status: 200 })));
    vi.spyOn(window, "scrollTo").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/welcome"]}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/welcome" element={<WelcomePage />} />
              <Route path="/birth" element={<SignalStationFrame act={1} titleId="birth-title"><h1 id="birth-title">Ngày sinh</h1></SignalStationFrame>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Tạm dừng chuyển động" }));
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("heading", { name: "Ngày sinh" })).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveAttribute("data-motion-paused", "true");
    expect(screen.getByRole("button", { name: "Tiếp tục chuyển động" })).toBeEnabled();
  });

  it("replays normal onboarding without resuming an old Radar intent, only after consent", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "old-radar-draft");
    sessionStorage.setItem("la-lanh-radar-owner-start", "1");
    renderPage("/welcome?restart=1");
    expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBe("old-radar-draft");
    expect(createGuest).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("heading", { name: "Ngày sinh" })).toBeInTheDocument();
    expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBeNull();
    expect(sessionStorage.getItem("la-lanh-radar-owner-start")).toBeNull();
  });

  it("never replaces an active profile even through the old restart URL", async () => {
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "same-person", resumed: true });
    renderPage("/welcome?restart=1");
    await userEvent.setup().click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("heading", { name: "Tiếp tục hồ sơ" })).toBeInTheDocument();
    expect(createGuest).not.toHaveBeenCalled();
  });

  it("acknowledges a cross-tab change before the real entry guard resumes the existing owner", async () => {
    sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "birth_pending", expires_at: "2026-11-10T00:00:00Z", session_epoch: "current-owner", resumed: true });
    vi.mocked(getBirthProfile).mockRejectedValue(new ApiProblem(404, "BIRTH_PROFILE_MISSING", "missing"));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/welcome?restart=1"]}><Routes>
      <Route path="/welcome" element={<WelcomePage />} /><Route path="/" element={<EntryPage />} />
      <Route path="/birth" element={<h1>Tiếp tục ngày sinh của hồ sơ</h1>} />
    </Routes></MemoryRouter></QueryClientProvider>);
    await userEvent.setup().click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("heading", { name: "Tiếp tục ngày sinh của hồ sơ" })).toBeInTheDocument();
    expect(sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY)).toBeNull();
    expect(createGuest).not.toHaveBeenCalled();
  });

  it("does not acknowledge a cross-tab change while a consent request failed", async () => {
    sessionStorage.setItem(SESSION_RESTART_REQUIRED_KEY, "1");
    vi.mocked(getSession).mockResolvedValue({ state: "active", onboarding_status: "completed", expires_at: "2026-11-10T00:00:00Z", session_epoch: "current-owner", resumed: true });
    vi.mocked(enableHistoryRetention).mockRejectedValue(new TypeError("offline"));
    renderPage("/welcome?restart=1");
    await userEvent.setup().click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(sessionStorage.getItem(SESSION_RESTART_REQUIRED_KEY)).toBe("1");
    expect(createGuest).not.toHaveBeenCalled();
  });
});
