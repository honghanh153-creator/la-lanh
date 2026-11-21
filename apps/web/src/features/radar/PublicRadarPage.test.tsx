import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { acceptRadarInviteWithDate, getPublicRadarInvite, getRadarConsentOptions } from "../../shared/api/client";
import { PublicRadarPage } from "./PublicRadarPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getPublicRadarInvite: vi.fn(), getRadarConsentOptions: vi.fn(), acceptRadarInviteWithDate: vi.fn() };
});

const invite = {
  request_id: "request-1",
  context: "coworker",
  voice: "straight_warm",
  expires_at: "2026-09-27T00:00:00Z",
  consent_version: "radar-pair-v1",
  requires_exact_birth_profile: false,
  privacy_note: "private",
} as const;

const WEEKLY_OPTIN = "Giữ ngày sinh của tôi, đã mã hoá, tối đa 90 ngày để hai bạn xem phần mỗi tuần. Tôi xoá được bất cứ lúc nào.";

function renderInvite() {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <MemoryRouter initialEntries={["/radar/i/token"]}>
      <Routes><Route element={<PublicRadarPage />} path="/radar/i/:token" /><Route element={<p>receipt page</p>} path="/radar/receipt" /></Routes>
    </MemoryRouter>
  </QueryClientProvider>);
}

describe("PublicRadarPage", () => {
  beforeEach(() => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue({ invite_first: false, sentences: {}, authorized_input_version: "radar-authorized-input-v1", date_consent_version: "radar-pair-date-v1" });
  });

  // AL1: the one-field invite shows only with the server switch on and every sentence owner-approved.
  it("asks only for the recipient's own birth date when the one-field invite is live", async () => {
    vi.mocked(getPublicRadarInvite).mockResolvedValue(invite);
    vi.mocked(getRadarConsentOptions).mockResolvedValue({
      invite_first: true,
      // Test stand-ins: the real sentences are owner-only and come from the server once approved.
      sentences: { "recipient-heading": "Tiêu đề.", "recipient-body": "Thân bài.", "recipient-consent": "Câu đồng ý.", "recipient-decline": "Câu từ chối." },
      authorized_input_version: "radar-authorized-input-v2",
      date_consent_version: "radar-pair-date-v1",
    });
    vi.mocked(acceptRadarInviteWithDate).mockResolvedValue({} as Awaited<ReturnType<typeof acceptRadarInviteWithDate>>);
    const user = userEvent.setup();
    renderInvite();

    expect(await screen.findByRole("heading", { name: "Tiêu đề." })).toBeInTheDocument();
    expect(screen.getByText("Câu từ chối.")).toBeInTheDocument();
    expect(screen.getAllByRole("textbox")).toHaveLength(3);
    const submit = screen.getByRole("button", { name: /Đồng ý & xem kết quả/ });
    expect(submit).toBeDisabled();
    await user.type(screen.getByLabelText("Ngày sinh của bạn — ngày"), "21");
    await user.type(screen.getByLabelText("Ngày sinh của bạn — tháng"), "07");
    await user.type(screen.getByLabelText("Ngày sinh của bạn — năm"), "1996");
    expect(submit).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: "Câu đồng ý." }));
    await user.click(submit);

    await waitFor(() => expect(acceptRadarInviteWithDate).toHaveBeenCalledWith("request-1", expect.stringMatching(/^1996-07-\d{2}$/), "radar-pair-date-v1", false));
    expect(await screen.findByText("receipt page")).toBeInTheDocument();
    // No weekly offer from the server: no second box, nothing kept.
    expect(screen.queryByRole("checkbox", { name: WEEKLY_OPTIN })).not.toBeInTheDocument();
  });

  // Owner AR1 (21.11.2026): the recipient's own weekly box, word for word, separate and unticked; only a tick keeps the date.
  it.each([
    [false, false],
    [true, true],
  ])("offers the separate weekly box unticked and sends keep_weekly only when ticked (tick=%s)", async (tick, kept) => {
    vi.mocked(getPublicRadarInvite).mockResolvedValue({ ...invite, weekly_offer: true });
    vi.mocked(getRadarConsentOptions).mockResolvedValue({
      invite_first: true,
      sentences: { "recipient-heading": "Tiêu đề.", "recipient-body": "Thân bài.", "recipient-consent": "Câu đồng ý.", "recipient-decline": "Câu từ chối." },
      authorized_input_version: "radar-authorized-input-v2",
      date_consent_version: "radar-pair-date-v1",
      weekly: true,
      weekly_sentences: { "recipient-optin": WEEKLY_OPTIN },
    });
    vi.mocked(acceptRadarInviteWithDate).mockResolvedValue({} as Awaited<ReturnType<typeof acceptRadarInviteWithDate>>);
    const user = userEvent.setup();
    renderInvite();

    const box = await screen.findByRole("checkbox", { name: WEEKLY_OPTIN });
    expect(box).not.toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Câu đồng ý." })).not.toBeChecked();
    await user.type(screen.getByLabelText("Ngày sinh của bạn — ngày"), "21");
    await user.type(screen.getByLabelText("Ngày sinh của bạn — tháng"), "07");
    await user.type(screen.getByLabelText("Ngày sinh của bạn — năm"), "1996");
    await user.click(screen.getByRole("checkbox", { name: "Câu đồng ý." }));
    // The weekly box alone never enables the result, and the consent tick never ticks it.
    expect(box).not.toBeChecked();
    if (tick) await user.click(box);
    await user.click(screen.getByRole("button", { name: /Đồng ý & xem kết quả/ }));

    await waitFor(() => expect(acceptRadarInviteWithDate).toHaveBeenCalledWith("request-1", expect.stringMatching(/^1996-07-\d{2}$/), "radar-pair-date-v1", kept));
  });

  it("keeps the current invite page while the one-field invite is off", async () => {
    vi.mocked(getPublicRadarInvite).mockResolvedValue(invite);
    renderInvite();
    expect(await screen.findByRole("link", { name: /Xem mình cần làm gì/ })).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("shows purpose and privacy before collecting any recipient data", async () => {
    // An older API may still send the sender's private label; the page must never show it (issue #95).
    const staleInvite = {
      request_id: "request-1",
      recipient_label: "CanaryNhanRieng7f3a",
      context: "crush",
      voice: "straight_warm",
      expires_at: "2026-09-27T00:00:00Z",
      consent_version: "radar-pair-v1",
      requires_exact_birth_profile: true,
      privacy_note: "private",
    } as const;
    vi.mocked(getPublicRadarInvite).mockResolvedValue(staleInvite);
    const { container } = render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={["/radar/i/token"]}>
        <Routes><Route element={<PublicRadarPage />} path="/radar/i/:token" /></Routes>
      </MemoryRouter>
    </QueryClientProvider>);

    expect(await screen.findByRole("heading", { name: "Hai bạn hợp nhau ở điểm nào? Mở ra xem cùng nhau nhé." })).toBeInTheDocument();
    expect(container).not.toHaveTextContent("CanaryNhanRieng7f3a");
    expect(screen.getByText("Dữ liệu sinh không được trao đổi")).toBeInTheDocument();
    expect(screen.getByText("Bạn quyết định riêng cho lần này")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Tiến độ Radar" })).toBeInTheDocument();
    expect(screen.getByText("Bắt đầu").closest('[aria-current="step"]')).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});
