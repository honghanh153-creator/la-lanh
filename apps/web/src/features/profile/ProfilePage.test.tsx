import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  clearResonance,
  getBirthProfile,
  getBirthSupplement,
  getDailyNote,
  getResonanceStatus,
  getContentRewriteStatus,
  setContentRewriteConsent,
  removeBirthSupplement,
  getAccountStatus,
  getHistoryRetention,
  clearReadingHistory,
  logoutAccount,
} from "../../shared/api/client";
import { ProfilePage } from "./ProfilePage";
import { OPENAI_ABUSE_RETENTION_NOTICE, OPENAI_REWRITE_SCOPE_NOTICE } from "../../shared/config/externalRewriteDisclosure";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    clearResonance: vi.fn(),
    getBirthProfile: vi.fn(),
    getBirthSupplement: vi.fn(),
    getDailyNote: vi.fn(),
    getResonanceStatus: vi.fn(),
    getContentRewriteStatus: vi.fn(),
    setContentRewriteConsent: vi.fn(),
    removeBirthSupplement: vi.fn(),
    getAccountStatus: vi.fn(),
    getHistoryRetention: vi.fn(),
    clearReadingHistory: vi.fn(),
    logoutAccount: vi.fn(),
  };
});

vi.mock("../../shared/theme/useTheme", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

function renderPage(client = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><ProfilePage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ProfilePage resonance privacy controls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getBirthProfile).mockRejectedValue(new Error("not available"));
    vi.mocked(getBirthSupplement).mockRejectedValue(new Error("not available"));
    vi.mocked(getDailyNote).mockRejectedValue(new Error("not available"));
    vi.mocked(getResonanceStatus).mockResolvedValue({
      consented: true,
      feedback_count: 2,
      last_choice: "hit",
    });
    vi.mocked(clearResonance).mockResolvedValue(undefined);
    vi.mocked(getContentRewriteStatus).mockResolvedValue({ enabled: true, consented: false, pilot_eligible: true });
    vi.mocked(setContentRewriteConsent).mockResolvedValue(undefined);
    vi.mocked(getAccountStatus).mockResolvedValue({ login_enabled: false, google_login_enabled: false, signed_in: false, masked_email: null, profile_expires_at: null, guest_inactivity_days: 30, history_days: 30, daily_note_hours: 24, account_inactivity_days: 365 });
    vi.mocked(getHistoryRetention).mockResolvedValue({ enabled: true, history_days: 30, daily_note_hours: 24, activated_at: "2026-10-10T00:00:00Z", saved_notes_kept: true });
    vi.mocked(clearReadingHistory).mockResolvedValue(undefined);
    vi.mocked(logoutAccount).mockResolvedValue(undefined);
  });

  it("keeps profile and saved notes when a history clear is cancelled, and acknowledges successful clear", async () => {
    const user = userEvent.setup(); renderPage();
    await user.click(await screen.findByRole("button", { name: /Xoá lịch sử đã xem/ }));
    expect(screen.getByRole("dialog")).toHaveTextContent("Hồ sơ sinh, bản đọc hiện tại và note đã lưu vẫn được giữ");
    await user.click(screen.getByRole("button", { name: "Giữ lịch sử" }));
    expect(clearReadingHistory).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /Xoá lịch sử đã xem/ }));
    await user.click(screen.getByRole("button", { name: "Xoá lịch sử" }));
    await waitFor(() => expect(clearReadingHistory).toHaveBeenCalledOnce());
    expect(await screen.findByRole("status")).toHaveTextContent("Đã xoá lịch sử");
    expect(screen.getByRole("heading", { name: "Mình" })).toBeInTheDocument();
  });

  it("states the 24-hour Daily-note window and the 30-day window for other history", async () => {
    renderPage();
    expect(await screen.findByText("Note ngày tự động hiện tối đa 24 giờ (có thể được dọn sớm hơn); lịch sử khác tối đa 30 ngày, tính từ lúc tạo; mở lại không kéo dài thời hạn.")).toBeInTheDocument();
  });

  it("does not claim logout or history clear succeeded on a network failure", async () => {
    vi.mocked(getAccountStatus).mockResolvedValue({ login_enabled: true, google_login_enabled: true, signed_in: true, masked_email: "a***@example.org", profile_expires_at: "2027-10-10T00:00:00Z", guest_inactivity_days: 30, history_days: 30, daily_note_hours: 24, account_inactivity_days: 365 });
    vi.mocked(logoutAccount).mockRejectedValue(new TypeError("offline"));
    vi.mocked(clearReadingHistory).mockRejectedValue(new TypeError("offline"));
    const user = userEvent.setup(); renderPage();
    await user.click(await screen.findByRole("button", { name: "Đăng xuất trên máy này" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa đăng xuất được");
    expect(screen.getByRole("heading", { name: "Mình" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Xoá lịch sử đã xem/ }));
    await user.click(screen.getByRole("button", { name: "Xoá lịch sử" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa xác nhận được việc xoá lịch sử");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.queryByText(/Đã xoá lịch sử/)).not.toBeInTheDocument();
  });

  it("shows status and can reset feedback without revoking consent", async () => {
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("Đang bật · 2 phản hồi trong 30 ngày gần nhất")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xóa phản hồi" }));

    await waitFor(() => expect(clearResonance).toHaveBeenCalledWith(false));
    expect(await screen.findByRole("status")).toHaveTextContent("Đã xóa phản hồi; quyền đồng ý vẫn được giữ");
  });

  it("requires confirmation before revoking consent and deleting feedback", async () => {
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Tắt và xóa" }));

    await waitFor(() => expect(clearResonance).toHaveBeenCalledWith(true));
  });

  it("requires a separate explicit opt-in before requesting AI rewriting", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Thử AI viết lại" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("OpenAI");
    // M1: only Lá's shared catalog wording for the Daily note; never direct chart facts.
    expect(screen.getByRole("dialog")).toHaveTextContent(OPENAI_REWRITE_SCOPE_NOTICE);
    expect(screen.getByRole("dialog")).not.toHaveTextContent("nhãn chiêm tinh liên quan");
    // Tarot is refused server-side under M1; the sheet says it is not part of this consent.
    expect(screen.getByRole("dialog")).toHaveTextContent("Các mục khác, như Tarot, chưa dùng AI");
    expect(screen.getByRole("dialog")).toHaveTextContent("xử lý ngoài Việt Nam");
    expect(screen.getByRole("dialog")).toHaveTextContent("huỷ các yêu cầu chưa gửi");
    // Full OpenAI exception set, shared with the onboarding privacy page.
    expect(screen.getByRole("dialog")).toHaveTextContent(OPENAI_ABUSE_RETENTION_NOTICE);
    expect(screen.getByRole("dialog")).toHaveTextContent("bảo vệ dịch vụ hay bên thứ ba khỏi tổn hại");
    expect(setContentRewriteConsent).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Đồng ý và thử" }));
    await waitFor(() => expect(setContentRewriteConsent).toHaveBeenCalledWith(true));
  });

  it("does not opt in when the user closes the disclosure", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(await screen.findByRole("button", { name: "Thử AI viết lại" }));
    await user.click(screen.getByRole("button", { name: "Dùng bản thường" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(setContentRewriteConsent).not.toHaveBeenCalled();
  });

  it("keeps the product usable and hides opt-in when the rollout is disabled", async () => {
    vi.mocked(getContentRewriteStatus).mockResolvedValue({ enabled: false, consented: false, pilot_eligible: true });
    renderPage();
    await waitFor(() => expect(getContentRewriteStatus).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: "Thử AI viết lại" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Mình" })).toBeInTheDocument();
  });

  it("disables enrollment when the pilot is full but still permits withdrawal", async () => {
    vi.mocked(getContentRewriteStatus).mockResolvedValue({ enabled: true, consented: false, pilot_eligible: false });
    const first = renderPage();
    expect(await screen.findByRole("button", { name: "Nhóm test đã đủ người" })).toBeDisabled();
    first.unmount();
    vi.mocked(getContentRewriteStatus).mockResolvedValue({ enabled: true, consented: true, pilot_eligible: false });
    renderPage();
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Tắt AI viết lại" }));
    await waitFor(() => expect(setContentRewriteConsent).toHaveBeenCalledWith(false));
  });

  it("clears cached private readings and both Radar directions after removing birth time", async () => {
    vi.mocked(getBirthSupplement).mockResolvedValue({
      profile_level: 3,
      profile_id: "test-profile",
      time_precision: "exact",
      timezone_id: "Asia/Ho_Chi_Minh",
      birth_time_mode: "exact",
      approx_window: null,
      place_display_name: "Hà Nội",
    });
    vi.mocked(removeBirthSupplement).mockResolvedValue({
      profile_id: "test-profile", profile_level: 2, birth_time_mode: "unknown",
      approx_window: null, time_precision: "unknown", timezone_id: "Asia/Ho_Chi_Minh",
      place_display_name: "Hà Nội",
    });
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const keys = [
      ["private-reading", "natal"],
      ["radar-result", "owner", "test-result"],
      ["radar-receipt"],
      ["saved-notes"],
      ["daily-note-context", "work"],
      ["daily-experiment"],
    ];
    for (const key of keys) client.setQueryData(key, { erased: "old precise birth data" });
    renderPage(client);
    const user = userEvent.setup();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    await user.click(await screen.findByRole("button", { name: /^Xóa giờ sinh/ }));
    await waitFor(() => expect(removeBirthSupplement).toHaveBeenCalled());
    await waitFor(() => {
      for (const key of keys) expect(client.getQueryData(key)).toBeUndefined();
    });
  });
});
