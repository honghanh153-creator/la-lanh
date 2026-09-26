import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createBirthProfile,
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
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("BirthDatePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
});
