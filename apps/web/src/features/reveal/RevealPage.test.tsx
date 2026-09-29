import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { type BirthReveal, type DailyNote } from "../../shared/api/client";
import { RevealPage } from "./RevealPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return {
    ...actual,
    getBirthProfile: vi.fn(),
    getDailyNote: vi.fn(),
    updateOnboardingStatus: vi.fn(),
  };
});

describe("RevealPage", () => {
  it("names a cusp without guessing one fixed Sun sign", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData<BirthReveal>(["birth-profile"], {
      profile_id: "profile-cusp",
      snapshot_id: "snapshot-cusp",
      birth_date: "1990-03-20",
      calculation_kind: "date_only_sun",
      calculation: {
        status: "ambiguous",
        sign: null,
        candidates: ["pisces", "aries"],
        provenance: {
          engine: "swiss_ephemeris",
          version: "2.10.3",
          ephemeris_set: "sepl_18+semo_18+seas_18",
          profile: "natal-date-only-v1",
        },
      },
      created_at: "2026-09-14T00:00:00Z",
      resumed: false,
    } as unknown as BirthReveal);
    client.setQueryData<DailyNote>(["daily-note"], {
      persona_label: "Mộng",
    } as DailyNote);

    render(
      <QueryClientProvider client={client}>
        <MemoryRouter><RevealPage /></MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "Vibe · Giao mùa" })).toBeInTheDocument();
    expect(screen.getByText(/không đoán cung khi chưa có giờ sinh/)).toBeInTheDocument();
    expect(screen.getByText(/Mặt Trời ở ranh giới Song Ngư · Bạch Dương/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mở Note hôm nay" })).toBeEnabled();
    expect(screen.getByRole("note", { name: "Lưu ý về bản đọc" })).toHaveTextContent(
      /quyết định vẫn thuộc về bạn/i,
    );
  });
});
