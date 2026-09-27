import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  claimOwner,
  getMatchingReadiness,
  grantMatchingConsent,
  saveMatchingProfile,
} from "../../shared/api/client";
import { MATCHING_INTRO_STORAGE_KEY } from "../../shared/storage/matchingIntroExposure";
import { MatchingPage } from "./MatchingPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    claimOwner: vi.fn(),
    getMatchingReadiness: vi.fn(),
    grantMatchingConsent: vi.fn(),
    saveMatchingProfile: vi.fn(),
    setMatchingPoolMembership: vi.fn(),
    withdrawMatchingConsent: vi.fn(),
  };
});

function renderPage(entry = "/vong-la/setup") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}><MatchingPage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("MatchingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("asks for an owner identity only when entering Vòng Lá", async () => {
    vi.mocked(getMatchingReadiness).mockRejectedValue(
      new ApiProblem(401, "OWNER_REQUIRED", "owner required"),
    );
    renderPage();

    expect(await screen.findByText("Đây mới là lúc cần xác nhận thiết bị")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Bắt đầu chuẩn bị" })).toBeInTheDocument();
    expect(screen.getByText("Daily Note vẫn dùng như khách. Vòng Lá cần một hồ sơ riêng ổn định để giữ ranh giới và các chốt an toàn; ghép và mutual là chặng sau.")).toBeInTheDocument();
    expect(screen.getByText("Request kín · chặng sau")).toBeInTheDocument();
  });

  it("opens profile directly from the landing CTA and claims owner in the background", async () => {
    vi.mocked(getMatchingReadiness)
      .mockRejectedValueOnce(new ApiProblem(401, "OWNER_REQUIRED", "owner required"))
      .mockResolvedValue({
        ready: false,
        profile: null,
        consent_version: null,
        verification_status: "not_started",
        verification_reason_code: null,
        birth_profile_level: 3,
        checks: [
          { key: "age_18_plus", complete: true, blocking: true },
          { key: "birth_profile_level_3", complete: true, blocking: true },
          { key: "matching_profile", complete: false, blocking: true },
          { key: "matching_consent", complete: false, blocking: true },
          { key: "photo_verification", complete: false, blocking: true },
        ],
      });
    vi.mocked(claimOwner).mockResolvedValue({
      principal_id: "00000000-0000-4000-8000-000000000099",
      expires_at: "2026-10-19T00:00:00Z",
      resumed: false,
    });
    renderPage("/vong-la/setup?start=profile");

    await waitFor(() => expect(claimOwner).toHaveBeenCalledOnce());
    expect(await screen.findByRole("dialog", { name: "Tạo hồ sơ ghép" })).toBeInTheDocument();
  });

  it("shows every safety gate and never auto-grants matching consent", async () => {
    const user = userEvent.setup();
    vi.mocked(getMatchingReadiness).mockResolvedValue({
      ready: false,
      profile: {
        active: false,
        display_name: "An",
        gender_identity: "nonbinary",
        gender_preference: "everyone",
        intent: "open",
        joined_at: null,
        max_age: 36,
        min_age: 24,
        region_code: "ho-chi-minh",
        updated_at: "2026-09-17T00:00:00Z",
        weekly_intent: "de_la_can",
      },
      consent_version: null,
      verification_status: "not_started",
      verification_reason_code: null,
      birth_profile_level: 3,
      checks: [
        { key: "age_18_plus", complete: true, blocking: true },
        { key: "birth_profile_level_3", complete: true, blocking: true },
        { key: "matching_profile", complete: true, blocking: true },
        { key: "matching_consent", complete: false, blocking: true },
        { key: "photo_verification", complete: false, blocking: true },
      ],
    });
    vi.mocked(grantMatchingConsent).mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findByText("3/5 chốt")).toBeInTheDocument();
    expect(screen.getByText("Ghép và mutual chưa mở ở bản này")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xem và đồng ý" })).toBeInTheDocument();
    expect(grantMatchingConsent).not.toHaveBeenCalled();

    await user.click(screen.getByText("Xem đủ 5 điều kiện"));
    expect(screen.getByText("Xác minh ảnh")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Xem và đồng ý" }));
    expect(screen.getByRole("dialog", { name: "Dữ liệu nào được dùng cho Vòng Lá?" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Tôi đồng ý dùng dữ liệu cho Vòng Lá" }));
    await waitFor(() => expect(grantMatchingConsent).toHaveBeenCalledOnce());
  });

  it("lets a new user choose a coarse region instead of silently using a default", async () => {
    const user = userEvent.setup();
    vi.mocked(getMatchingReadiness).mockResolvedValue({
      ready: false,
      profile: null,
      consent_version: null,
      verification_status: "not_started",
      verification_reason_code: null,
      birth_profile_level: 3,
      checks: [
        { key: "age_18_plus", complete: true, blocking: true },
        { key: "birth_profile_level_3", complete: true, blocking: true },
        { key: "matching_profile", complete: false, blocking: true },
        { key: "matching_consent", complete: false, blocking: true },
        { key: "photo_verification", complete: false, blocking: true },
      ],
    });
    vi.mocked(saveMatchingProfile).mockResolvedValue({
      active: false,
      display_name: "An",
      gender_identity: "nonbinary",
      gender_preference: "everyone",
      intent: "open",
      joined_at: null,
      max_age: 35,
      min_age: 22,
      region_code: "da-nang",
      updated_at: "2026-09-18T00:00:00Z",
      weekly_intent: "de_la_can",
    });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Tạo hồ sơ ghép" }));
    expect(screen.getByRole("dialog", { name: "Tạo hồ sơ ghép" })).toBeInTheDocument();
    expect(screen.getByText("Chỉ lưu thành phố; không dùng GPS hoặc hiển thị khoảng cách số.")).toBeInTheDocument();
    await user.type(await screen.findByLabelText("Tên hiển thị"), "An");
    const regionSelect = screen.getByLabelText("Khu vực muốn kết nối");
    expect(within(regionSelect).getByRole("option", { name: "Lào Cai" })).toBeInTheDocument();
    expect(within(regionSelect).getAllByRole("option")).toHaveLength(35);
    await user.selectOptions(regionSelect, "da-nang");
    expect(screen.getByRole("button", { name: "Lưu hồ sơ ghép" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Lưu hồ sơ ghép" }));

    await waitFor(() =>
      expect(saveMatchingProfile).toHaveBeenCalledWith(
        expect.objectContaining({ region_code: "da-nang" }),
        expect.anything(),
      ),
    );
    expect(JSON.parse(localStorage.getItem(MATCHING_INTRO_STORAGE_KEY) ?? "{}")).toEqual({
      converted: true,
      visit: 1,
    });
  });

  it("asks before discarding an unsaved profile draft", async () => {
    const user = userEvent.setup();
    vi.mocked(getMatchingReadiness).mockResolvedValue({
      ready: false,
      profile: null,
      consent_version: null,
      verification_status: "not_started",
      verification_reason_code: null,
      birth_profile_level: 3,
      checks: [
        { key: "age_18_plus", complete: true, blocking: true },
        { key: "birth_profile_level_3", complete: true, blocking: true },
        { key: "matching_profile", complete: false, blocking: true },
        { key: "matching_consent", complete: false, blocking: true },
        { key: "photo_verification", complete: false, blocking: true },
      ],
    });
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Tạo hồ sơ ghép" }));
    await user.type(screen.getByLabelText("Tên hiển thị"), "An");
    await user.click(screen.getByRole("button", { name: "Đóng" }));

    expect(screen.getByRole("dialog", { name: "Bỏ những gì vừa sửa?" })).toBeInTheDocument();
    expect(saveMatchingProfile).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Tiếp tục chỉnh" }));
    expect(screen.getByLabelText("Tên hiển thị")).toHaveValue("An");
  });

  it("does not freeze the intro ladder when profile saving fails", async () => {
    const user = userEvent.setup();
    vi.mocked(getMatchingReadiness).mockResolvedValue({
      ready: false,
      profile: null,
      consent_version: null,
      verification_status: "not_started",
      verification_reason_code: null,
      birth_profile_level: 3,
      checks: [
        { key: "age_18_plus", complete: true, blocking: true },
        { key: "birth_profile_level_3", complete: true, blocking: true },
        { key: "matching_profile", complete: false, blocking: true },
        { key: "matching_consent", complete: false, blocking: true },
        { key: "photo_verification", complete: false, blocking: true },
      ],
    });
    vi.mocked(saveMatchingProfile).mockRejectedValue(new Error("offline"));
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Tạo hồ sơ ghép" }));
    await user.type(screen.getByLabelText("Tên hiển thị"), "An");
    await user.selectOptions(screen.getByLabelText("Khu vực muốn kết nối"), "da-nang");
    await user.click(screen.getByRole("button", { name: "Lưu hồ sơ ghép" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa lưu được");
    expect(localStorage.getItem(MATCHING_INTRO_STORAGE_KEY)).toBeNull();
  });
});
