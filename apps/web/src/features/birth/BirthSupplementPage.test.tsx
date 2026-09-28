import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  addBirthSupplement,
  getDailyNote,
  searchBirthPlaces,
  type DailyNote,
} from "../../shared/api/client";
import { clearCachedDailyNote } from "../../shared/storage/noteCache";
import { BirthSupplementPage } from "./BirthSupplementPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    addBirthSupplement: vi.fn(),
    getDailyNote: vi.fn(),
    searchBirthPlaces: vi.fn(),
  };
});

describe("BirthSupplementPage Aura handoff", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    clearCachedDailyNote();
  });

  it("routes an exact full-synthesis result directly to Aura Cutover", async () => {
    const user = userEvent.setup();
    vi.mocked(addBirthSupplement).mockResolvedValue({
      profile_id: "00000000-0000-4000-8000-000000000020",
      profile_level: 3,
      chart: null,
      place_display_name: null,
      snapshot_id: null,
      time_precision: "exact",
      timezone_id: null,
    });
    vi.mocked(getDailyNote).mockResolvedValue(fullSynthesisNote);

    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <BirthSupplementPage />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>);

    await user.click(screen.getByRole("button", { name: "Thêm để mở lớp mới" }));
    await user.type(screen.getByLabelText(/Giờ sinh/), "08:15");
    await user.click(screen.getByRole("button", { name: "Tiếp tục" }));
    await user.click(screen.getByRole("button", { name: "Bỏ qua nơi sinh" }));
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Mở lớp Moon / House" }));

    expect(await screen.findByTestId("location")).toHaveTextContent("/aura-cutover");
  });

  it("hands an exact supplement to Aura Cutover when the follow-up note fetch fails", async () => {
    const user = userEvent.setup();
    vi.mocked(addBirthSupplement).mockResolvedValue({
      profile_id: "00000000-0000-4000-8000-000000000020",
      profile_level: 3,
      chart: null,
      place_display_name: null,
      snapshot_id: null,
      time_precision: "exact",
      timezone_id: null,
    });
    vi.mocked(getDailyNote).mockRejectedValue(new Error("daily note unavailable"));

    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <BirthSupplementPage />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>);

    await user.click(screen.getByRole("button", { name: "Thêm để mở lớp mới" }));
    await user.type(screen.getByLabelText(/Giờ sinh/), "08:15");
    await user.click(screen.getByRole("button", { name: "Tiếp tục" }));
    await user.click(screen.getByRole("button", { name: "Bỏ qua nơi sinh" }));
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Mở lớp Moon / House" }));

    expect(await screen.findByTestId("location")).toHaveTextContent("/aura-cutover");
    expect(screen.queryByRole("heading", { name: "Một lớp Lá mới đã mở." })).not.toBeInTheDocument();
  });

  it("lets users browse the complete current Vietnam birthplace catalog", async () => {
    const user = userEvent.setup();
    vi.mocked(searchBirthPlaces).mockResolvedValue([]);

    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter>
        <BirthSupplementPage />
      </MemoryRouter>
    </QueryClientProvider>);

    await user.click(screen.getByRole("button", { name: "Thêm để mở lớp mới" }));
    await user.type(screen.getByLabelText(/Giờ sinh/), "08:15");
    await user.click(screen.getByRole("button", { name: "Tiếp tục" }));
    await user.click(screen.getByRole("button", { name: "Xem đủ 34 tỉnh/thành" }));

    expect(searchBirthPlaces).toHaveBeenCalledWith("", expect.any(AbortSignal));
    expect(screen.getByRole("button", { name: "Thu gọn danh mục" })).toBeVisible();
  });
});

function LocationProbe() {
  return <output data-testid="location">{useLocation().pathname}</output>;
}

const fullSynthesisNote = {
  id: "00000000-0000-4000-8000-000000000001",
  note_date: "2026-09-16",
  title: "Note hôm nay",
  body: "Một note.",
  full_body: "Một note đầy đủ.",
  context_label: "Tự động",
  content_version: "v1",
  persona_mode: "vibe",
  persona_label: "Mềm",
  persona_version: "v1",
  source_level: "date_only_sun",
  astrology_source_version: "2.10.03",
  fallback_used: false,
  fallback_reason: null,
  created_at: "2026-09-16T00:00:00Z",
  awakening: null,
  sky_chapter: null,
  reading_projection: {
    scope_key: "s".repeat(64),
    active: {
      revision_id: "00000000-0000-4000-8000-000000000010",
      source: "deterministic",
      mode: "vibe_fallback",
      purpose: "daily_note",
      tradition: "western",
      precision: "unknown",
      sections: { hook: "Vibe", thesis: "Thesis", manifestation: "Manifestation", transit: null, micro_action: "Action" },
      evidence: { title: "Evidence", claims: ["Claim"], framework_disclosure: "Disclosure" },
      disclaimer: "Disclaimer",
      created_at: "2026-09-16T00:00:00Z",
    },
    available_update: {
      revision_id: "00000000-0000-4000-8000-000000000011",
      message: "Aura sẵn sàng",
      content: {
        revision_id: "00000000-0000-4000-8000-000000000011",
        source: "deterministic",
        mode: "full_synthesis",
        purpose: "daily_note",
        tradition: "western",
        precision: "exact",
        sections: { hook: "Aura", thesis: "Thesis", manifestation: "Manifestation", transit: null, micro_action: "Action", },
        evidence: { title: "Evidence", claims: ["Claim"], framework_disclosure: "Disclosure" },
        disclaimer: "Disclaimer",
        created_at: "2026-09-16T00:00:00Z",
      },
    },
    aura_transition: {
      profile_readiness: "aura_ready",
      transition_id: "t".repeat(64),
      acknowledged: false,
      unlock_layers: ["multi_factor"],
    },
  },
} satisfies DailyNote;
