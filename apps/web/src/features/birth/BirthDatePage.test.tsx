import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createBirthProfile,
  addBirthSupplement,
  searchBirthPlaces,
  updateOnboardingStatus,
  getBirthProfile,
  getDailyNote,
  getSession,
  type BirthReveal,
  type DailyNote,
} from "../../shared/api/client";
import { RevealPage } from "../reveal/RevealPage";
import { BirthDatePage } from "./BirthDatePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    createBirthProfile: vi.fn(),
    addBirthSupplement: vi.fn(),
    searchBirthPlaces: vi.fn(),
    updateOnboardingStatus: vi.fn(),
    getBirthProfile: vi.fn(),
    getDailyNote: vi.fn(),
    getSession: vi.fn(),
  };
});

const birthReveal = {
  profile_id: "profile-test",
  snapshot_id: "snapshot-test",
  birth_date: "1990-01-01",
  calculation: {
    status: "certain",
    sign: "capricorn",
    candidates: [],
    provenance: {
      engine: "swiss_ephemeris",
      version: "2.10.3",
      ephemeris_set: "sepl_18+semo_18+seas_18",
      profile: "natal-date-only-v1",
    },
  },
  created_at: "2026-09-14T00:00:00Z",
  resumed: false,
} as unknown as BirthReveal;

const dailyNote = {
  id: "note-test",
  note_date: "2026-09-14",
  title: "Một nhịp riêng.",
  body: "Bạn có thể đi chậm để nghe rõ hơn.",
  full_body: "Bạn có thể đi chậm để nghe rõ hơn.",
  context_label: "Mặt Trời Ma Kết",
  content_version: "daily-note-v1",
  persona_mode: "vibe",
  persona_label: "Vững",
  persona_version: "persona-v1",
  source_level: "date_only",
  astrology_source_version: "2.10.3",
  fallback_used: false,
  fallback_reason: null,
  awakening: null,
  sky_chapter: null,
  created_at: "2026-09-14T00:00:00Z",
  reading_projection: null,
} as unknown as DailyNote;

function renderFlow() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/birth"]}>
        <Routes>
          <Route path="/birth" element={<BirthDatePage />} />
          <Route path="/reveal" element={<RevealPage />} />
          <Route path="/radar/start" element={<h1>Radar tiếp tục</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("BirthDatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    vi.mocked(searchBirthPlaces).mockResolvedValue([{ place_id: "hanoi", display_name: "Hà Nội", timezone_id: "Asia/Ho_Chi_Minh", confidence: "province-centroid", country_code: "VN" }]);
    vi.mocked(addBirthSupplement).mockResolvedValue({ profile_id: "test", profile_level: 3, chart: null, place_display_name: "Hà Nội", snapshot_id: null, time_precision: "exact", timezone_id: "Asia/Ho_Chi_Minh" });
    vi.mocked(getBirthProfile).mockResolvedValue(birthReveal);
    vi.mocked(updateOnboardingStatus).mockResolvedValue({ state: "active", onboarding_status: "completed" } as Awaited<ReturnType<typeof updateOnboardingStatus>>);
    vi.mocked(getSession).mockResolvedValue({
      state: "active",
      onboarding_status: "birth_pending",
      expires_at: "2026-10-14T00:00:00Z",
      resumed: true,
      session_epoch: "epoch-test",
    });
    vi.mocked(createBirthProfile).mockResolvedValue(birthReveal);
    vi.mocked(getDailyNote).mockResolvedValue(dailyNote);
  });

  it("warms the Reveal data without a fake delay or duplicate fetch", async () => {
    const user = userEvent.setup();
    renderFlow();

    await user.type(screen.getByRole("textbox", { name: "Ngày" }), "01");
    await user.type(screen.getByRole("textbox", { name: "Tháng" }), "01");
    await user.type(screen.getByRole("textbox", { name: "Năm" }), "1990");
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));

    expect(await screen.findByRole("heading", { name: "Vibe · Vững" })).toBeInTheDocument();
    expect(createBirthProfile).toHaveBeenCalledTimes(1);
    expect(getDailyNote).toHaveBeenCalledTimes(1);
    expect(getBirthProfile).not.toHaveBeenCalled();
    expect(addBirthSupplement).not.toHaveBeenCalled();
  });

  it("announces an invalid date and keeps it off the network", async () => {
    const user = userEvent.setup();
    renderFlow();

    await user.type(screen.getByRole("textbox", { name: "Ngày" }), "31");
    await user.type(screen.getByRole("textbox", { name: "Tháng" }), "02");
    await user.type(screen.getByRole("textbox", { name: "Năm" }), "1990");
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Ngày này chưa đúng");
    expect(screen.getByRole("textbox", { name: "Ngày" })).toHaveFocus();
    expect(createBirthProfile).not.toHaveBeenCalled();
  });

  it("saves optional exact time with separate consent before fetching the note", async () => {
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await fillDetails(user);
    expect(screen.getByRole("checkbox")).not.toBeChecked();
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Đồng ý dùng giờ/nơi sinh");
    expect(createBirthProfile).not.toHaveBeenCalled();
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(await screen.findByRole("heading", { name: "Vibe · Vững" })).toBeInTheDocument();
    expect(addBirthSupplement).toHaveBeenCalledWith({ birth_time_mode: "exact", birth_time_local: "00:00", approx_window: null, place_id: "hanoi" });
    expect(vi.mocked(addBirthSupplement).mock.invocationCallOrder[0]).toBeLessThan(vi.mocked(getDailyNote).mock.invocationCallOrder[0]);
  });

  it("clears optional values and consent on skip, without sending them", async () => {
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await fillDetails(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Bỏ qua giờ & nơi sinh" }));
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(await screen.findByRole("heading", { name: "Vibe · Vững" })).toBeInTheDocument();
    expect(addBirthSupplement).not.toHaveBeenCalled();
  });

  it("does not invent minutes when only the hour was selected", async () => {
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await user.click(screen.getByRole("button", { name: /Thêm giờ & nơi sinh/ }));
    await user.click(screen.getByRole("button", { name: "Biết giờ" }));
    await user.selectOptions(screen.getByLabelText("Giờ (0–23)"), "07");
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Chọn đủ giờ và phút");
    expect(createBirthProfile).not.toHaveBeenCalled();
  });

  it("retries only the failed supplement and keeps the saved date locked", async () => {
    vi.mocked(addBirthSupplement).mockRejectedValueOnce(new Error("offline"));
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await fillDetails(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("giờ/nơi sinh chưa lưu được");
    expect(screen.getByRole("textbox", { name: "Ngày" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Thử tải lại" }));
    expect(await screen.findByRole("heading", { name: "Vibe · Vững" })).toBeInTheDocument();
    expect(createBirthProfile).toHaveBeenCalledTimes(1);
    expect(addBirthSupplement).toHaveBeenCalledTimes(2);
  });

  it("returns to Radar without asking for complete birth details twice", async () => {
    sessionStorage.setItem("la-lanh-radar-owner-start", "1");
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await fillDetails(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(await screen.findByRole("heading", { name: "Radar tiếp tục" })).toBeInTheDocument();
    expect(updateOnboardingStatus).toHaveBeenCalledWith("completed");
    expect(sessionStorage.getItem("la-lanh-radar-owner-start")).toBeNull();
  });

  it("retries note loading without resubmitting saved optional data", async () => {
    vi.mocked(getDailyNote).mockRejectedValueOnce(new Error("offline"));
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await fillDetails(user);
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Thử tải lại");
    await user.click(screen.getByRole("button", { name: "Thử tải lại" }));
    expect(await screen.findByRole("heading", { name: "Vibe · Vững" })).toBeInTheDocument();
    expect(createBirthProfile).toHaveBeenCalledTimes(1);
    expect(addBirthSupplement).toHaveBeenCalledTimes(1);
  });

  it("requires fresh consent when the time changes", async () => {
    const user = userEvent.setup();
    renderFlow();
    await fillDate(user);
    await fillDetails(user);
    await user.click(screen.getByRole("checkbox"));
    await user.selectOptions(screen.getByLabelText("Phút (0–59)"), "15");
    expect(screen.getByRole("checkbox")).not.toBeChecked();
    await user.click(screen.getByRole("button", { name: "Khớp tín hiệu" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Đồng ý dùng giờ/nơi sinh");
    expect(createBirthProfile).not.toHaveBeenCalled();
  });
});

async function fillDate(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole("textbox", { name: "Ngày" }), "01");
  await user.type(screen.getByRole("textbox", { name: "Tháng" }), "01");
  await user.type(screen.getByRole("textbox", { name: "Năm" }), "1990");
}

async function fillDetails(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: /Thêm giờ & nơi sinh/ }));
  await user.click(screen.getByRole("button", { name: "Biết giờ" }));
  await user.selectOptions(screen.getByLabelText("Giờ (0–23)"), "00");
  await user.selectOptions(screen.getByLabelText("Phút (0–59)"), "00");
  await user.type(screen.getByPlaceholderText("Tìm thành phố / tỉnh"), "Hà Nội");
  await user.click(await screen.findByRole("button", { name: /Hà Nội/ }));
}
