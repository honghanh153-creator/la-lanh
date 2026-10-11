import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StrictMode } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { acceptBasicBirthConsent, cancelAccountLogin, createGuest, getAccountStatus, getSession, requestGoogleLogin, restoreAccount, verifyGoogleLogin } from "../../shared/api/client";
import { ExistingUserPage } from "./ExistingUserPage";

vi.mock("../../shared/api/client", async (original) => ({
  ...await original<typeof import("../../shared/api/client")>(),
  acceptBasicBirthConsent: vi.fn(), cancelAccountLogin: vi.fn(), createGuest: vi.fn(),
  getAccountStatus: vi.fn(), getSession: vi.fn(), requestGoogleLogin: vi.fn(), restoreAccount: vi.fn(), verifyGoogleLogin: vi.fn(),
}));

const state = "s".repeat(43);
const callback = `/auth/callback?code=synthetic-provider-auth-code&state=${state}`;
const session = { state: "active", onboarding_status: "completed", session_epoch: "verified", expires_at: "2026-11-10T00:00:00Z", resumed: true, csrf_token: "synthetic-csrf" };

function renderPage(entry = "/existing-user") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<StrictMode><QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}><Routes>
    <Route path="/existing-user" element={<ExistingUserPage key="login" />} /><Route path="/auth/callback" element={<ExistingUserPage key="callback" />} />
    <Route path="/welcome" element={<h1>Tiếp tục phiên</h1>} /><Route path="/home" element={<h1>Home của tài khoản</h1>} />
    <Route path="/profile" element={<h1>Hồ sơ</h1>} /><Route path="/birth" element={<h1>Ngày sinh</h1>} />
  </Routes></MemoryRouter></QueryClientProvider></StrictMode>);
}

describe("Google account", () => {
  beforeEach(() => {
    vi.clearAllMocks(); localStorage.clear(); sessionStorage.clear();
    vi.mocked(getAccountStatus).mockResolvedValue({ login_enabled: true, google_login_enabled: true, signed_in: false, masked_email: null, profile_expires_at: null, guest_inactivity_days: 30, history_days: 30, account_inactivity_days: 365 });
    vi.mocked(getSession).mockResolvedValue(session);
    vi.mocked(acceptBasicBirthConsent).mockResolvedValue(undefined);
    vi.mocked(cancelAccountLogin).mockResolvedValue(undefined);
    vi.mocked(verifyGoogleLogin).mockResolvedValue({ status: "signed_in", session });
    vi.mocked(restoreAccount).mockResolvedValue({ status: "signed_in", session });
  });

  it("uses Google only, and disabled provider sends nothing", async () => {
    vi.mocked(getAccountStatus).mockResolvedValue({ login_enabled: false, google_login_enabled: false, signed_in: false, masked_email: null, profile_expires_at: null, guest_inactivity_days: 30, history_days: 30, account_inactivity_days: 365 });
    renderPage();
    expect(await screen.findByText(/Đăng nhập Google chưa bật/)).toBeInTheDocument();
    expect(screen.queryByLabelText("Email của bạn")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tiếp tục với Google" })).toBeDisabled();
    await userEvent.setup().click(screen.getByRole("button", { name: "Tiếp tục không đăng nhập" }));
    expect(await screen.findByRole("heading", { name: "Tiếp tục phiên" })).toBeInTheDocument();
    expect(requestGoogleLogin).not.toHaveBeenCalled();
  });

  it("needs consent, resumes the existing guest, rejects unsafe navigation without discarding data", async () => {
    vi.mocked(requestGoogleLogin).mockResolvedValue({ authorize_url: "https://evil.example/auth/v1/authorize", expires_at: "2026-10-10T00:00:00Z" });
    sessionStorage.setItem("existing-guest-marker", "kept");
    renderPage();
    const user = userEvent.setup();
    const button = await screen.findByRole("button", { name: "Tiếp tục với Google" });
    expect(button).toBeDisabled();
    await user.click(screen.getByRole("checkbox")); await user.click(button);
    expect(await screen.findByRole("alert")).toHaveTextContent("Hồ sơ trên máy này vẫn được giữ");
    expect(createGuest).not.toHaveBeenCalled();
    expect(requestGoogleLogin).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem("existing-guest-marker")).toBe("kept");
  });

  it("completes callback only once in StrictMode and strips proof from browser URL", async () => {
    const replace = vi.spyOn(window.history, "replaceState");
    renderPage(callback);
    expect(await screen.findByRole("heading", { name: "Home của tài khoản" })).toBeInTheDocument();
    expect(verifyGoogleLogin).toHaveBeenCalledTimes(1);
    expect(verifyGoogleLogin).toHaveBeenCalledWith("synthetic-provider-auth-code", state);
    expect(replace.mock.calls.some((call) => call[2] === "/auth/callback")).toBe(true);
    expect(JSON.stringify({ ...localStorage, ...sessionStorage })).not.toContain(state);
    replace.mockRestore();
  });

  it("never restores another profile automatically; cancelled restore keeps guest", async () => {
    vi.mocked(verifyGoogleLogin).mockResolvedValue({ status: "restore_required", masked_email: "s***@example.org" });
    renderPage(callback);
    expect(await screen.findByRole("heading", { name: "Mở lại hồ sơ đã giữ?" })).toBeInTheDocument();
    expect(restoreAccount).not.toHaveBeenCalled();
    await userEvent.setup().click(screen.getByRole("button", { name: "Giữ hồ sơ trên máy này" }));
    expect(await screen.findByRole("heading", { name: "Tiếp tục phiên" })).toBeInTheDocument();
    expect(cancelAccountLogin).toHaveBeenCalledWith(state);
    expect(restoreAccount).not.toHaveBeenCalled();
  });

  it("restores only after explicit confirmation", async () => {
    vi.mocked(verifyGoogleLogin).mockResolvedValue({ status: "restore_required", masked_email: "s***@example.org" });
    renderPage(callback);
    await userEvent.setup().click(await screen.findByRole("button", { name: "Mở hồ sơ của tài khoản này" }));
    expect(await screen.findByRole("heading", { name: "Home của tài khoản" })).toBeInTheDocument();
    expect(restoreAccount).toHaveBeenCalledWith(state);
  });

  it("denied or incomplete callback never calls a provider and leaves an exit", async () => {
    renderPage("/auth/callback?error=access_denied&state=" + state);
    expect(await screen.findByRole("alert")).toHaveTextContent("Hồ sơ hiện tại trên máy này vẫn được giữ");
    expect(verifyGoogleLogin).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Tiếp tục không đăng nhập" })).toBeEnabled();
  });

  it("retrying a denied callback opens a fresh Google consent screen, not the old callback", async () => {
    renderPage("/auth/callback?error=access_denied&state=" + state);
    await userEvent.setup().click(await screen.findByRole("link", { name: "Đăng nhập lại bằng Google" }));
    expect(await screen.findByRole("checkbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tiếp tục với Google" })).toBeDisabled();
    expect(verifyGoogleLogin).not.toHaveBeenCalled();
    expect(cancelAccountLogin).not.toHaveBeenCalled();
  });

  it("cancelling ordinary login returns to the originating profile", async () => {
    renderPage("/existing-user?returnTo=/profile");
    await waitFor(() => expect(screen.getByRole("checkbox")).toBeInTheDocument());
    await userEvent.setup().click(screen.getByRole("button", { name: "Tiếp tục không đăng nhập" }));
    expect(await screen.findByRole("heading", { name: "Hồ sơ" })).toBeInTheDocument();
    expect(requestGoogleLogin).not.toHaveBeenCalled();
  });
});
