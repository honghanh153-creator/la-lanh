import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { getBirthProfile, getDailyNote, type BirthReveal, type DailyNote } from "../../shared/api/client";
import { BirthCardPage } from "./BirthCardPage";

vi.mock("../../shared/api/client", async (original) => ({
  ...await original<typeof import("../../shared/api/client")>(),
  getBirthProfile: vi.fn(),
  getDailyNote: vi.fn(),
}));
vi.mock("./shareFonts", () => ({ cachedShareFontCss: () => "", loadShareFontCss: () => Promise.resolve("") }));
vi.mock("./shareRaster", async (original) => ({
  ...await original<typeof import("./shareRaster")>(),
  rasterizeSvg: vi.fn(() => Promise.resolve(new Blob(["png"], { type: "image/png" }))),
}));

const profile = {
  birth_date: "1996-06-01",
  calculation: { status: "certain", sign: "gemini", candidates: ["gemini"] },
  calculation_kind: "date_only_sun",
  created_at: "2026-10-10T00:00:00Z",
  profile_id: "00000000-0000-4000-8000-0000000000aa",
  resumed: false,
  snapshot_id: "00000000-0000-4000-8000-0000000000bb",
} as unknown as BirthReveal;

const note = { persona_label: "Lanh", persona_mode: "vibe", title: "Note" } as unknown as DailyNote;

describe("BirthCardPage", () => {
  it("renders a sticker-style Lá Khai Sinh preview without any birth data", async () => {
    vi.mocked(getBirthProfile).mockResolvedValue(profile);
    vi.mocked(getDailyNote).mockResolvedValue(note);
    const { container } = render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter><BirthCardPage /></MemoryRouter>
    </QueryClientProvider>);

    expect(screen.getByRole("status")).toHaveTextContent("Lá đang vẽ thẻ của bạn…");
    const image = await screen.findByRole("img", { name: /Mặt Trời Song Tử · Khí/ });
    fireEvent.load(image);
    expect(screen.getByRole("heading", { name: "Lá Khai Sinh · Mặt Trời Song Tử" })).toBeInTheDocument();
    expect(image.getAttribute("alt")).toContain("Vibe · Lanh");
    expect(screen.getByRole("button", { name: /Tải PNG/ })).toBeEnabled();

    const svg = decodeURIComponent(image.getAttribute("src") ?? "");
    for (const output of [container.innerHTML, svg]) {
      for (const secret of ["1996", "06-01", profile.profile_id, profile.snapshot_id, "Chất"]) expect(output).not.toContain(secret);
    }
  });
});
