import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { createRadarCard, getPublicRadarCard, getRadarConsentOptions, listRadarCards, type RadarResult } from "../../shared/api/client";
import { RadarCardPage } from "./RadarCardPage";
import { RadarShareCard } from "./RadarShareCard";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, createRadarCard: vi.fn(), getPublicRadarCard: vi.fn(), getRadarConsentOptions: vi.fn(), listRadarCards: vi.fn(), revokeRadarCard: vi.fn() };
});
// jsdom cannot fetch bundled fonts or rasterize; render with the system-font fallback.
vi.mock("../card/shareFonts", () => ({ cachedShareFontCss: () => "", loadShareFontCss: () => Promise.resolve("") }));
vi.mock("../card/shareRaster", async (original) => ({
  ...(await original<typeof import("../card/shareRaster")>()),
  rasterizeSvg: vi.fn(() => Promise.resolve(new Blob(["png"], { type: "image/png" }))),
}));

const result = {
  request_id: "r-1",
  recipient_label: "Mèo Hoang",
  context: "crush",
  headline: "Hai bạn dễ bắt chuyện.",
  summary: "",
  pair_signature: { kicker: "Dễ bắt chuyện", headline: "Hai bạn dễ bắt chuyện.", summary: "", tier: { key: "easy", label: "Dễ bắt chuyện" }, areas: [], themes: [] },
  sections: [],
  disclaimer: "",
} as unknown as RadarResult;

function withClient(ui: React.ReactNode) {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>{ui}</QueryClientProvider>);
}

const off = { invite_first: false, sentences: {}, authorized_input_version: "radar-authorized-input-v1", date_consent_version: "radar-pair-date-v1", card_links: false };

describe("RadarShareCard (Hợp gu C)", () => {
  it("draws the card without a name unless the owner asks for the first letter", async () => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue(off);
    const user = userEvent.setup();
    withClient(<RadarShareCard result={result} />);

    await user.click(screen.getByRole("button", { name: /Tạo thẻ/ }));
    const image = await screen.findByRole("img");
    expect(image.getAttribute("alt")).toContain("Dễ bắt chuyện");
    expect(image.getAttribute("alt")).toContain("Không kèm ngày / giờ / nơi sinh");
    expect(image.getAttribute("alt")).not.toMatch(/Mèo|Hoang|M\./);
    expect(screen.getByRole("checkbox", { name: "Hiện chữ cái đầu của tên" })).not.toBeChecked();

    await user.click(screen.getByRole("checkbox", { name: "Hiện chữ cái đầu của tên" }));
    expect((await screen.findByRole("img")).getAttribute("alt")).toContain("Bạn × M.");
    expect(screen.getByRole("img").getAttribute("alt")).not.toMatch(/Mèo|Hoang/);
    expect(screen.getByRole("button", { name: /Lưu ảnh/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Gửi link xem thẻ/ })).not.toBeInTheDocument();
  });

  it("offers a revocable link only when the server has card links on", async () => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue({ ...off, card_links: true });
    vi.mocked(listRadarCards).mockResolvedValue([]);
    vi.mocked(createRadarCard).mockResolvedValue({ id: "c-1", status: "active", created_at: "2026-11-20T08:00:00Z", expires_at: "2026-11-21T08:00:00Z", share_url: "/radar/the/token" });
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: vi.fn(() => Promise.resolve()) } });
    const user = userEvent.setup();
    withClient(<RadarShareCard result={result} />);

    await user.click(screen.getByRole("button", { name: /Tạo thẻ/ }));
    await user.click(await screen.findByRole("button", { name: /Gửi link xem thẻ/ }));
    expect(createRadarCard).toHaveBeenCalledWith("r-1", false);
    expect(await screen.findByText("Đã chép link xem thẻ. Bạn thu hồi được bất cứ lúc nào.")).toBeInTheDocument();
  });
});

describe("RadarCardPage", () => {
  function renderPage() {
    return withClient(<MemoryRouter initialEntries={["/radar/the/token"]}><Routes><Route element={<RadarCardPage />} path="/radar/the/:token" /></Routes></MemoryRouter>);
  }

  it("shows the shared card", async () => {
    vi.mocked(getPublicRadarCard).mockResolvedValue({ version: "radar-card-v1", context: "coworker", tier: "Dễ làm chung", line: "Hai bạn dễ chia việc.", initial: null });
    renderPage();
    expect((await screen.findByRole("img")).getAttribute("alt")).toContain("Dễ làm chung");
    expect(screen.getByRole("img").getAttribute("alt")).toContain("Đồng nghiệp");
  });

  it("says plainly when the link no longer opens", async () => {
    vi.mocked(getPublicRadarCard).mockRejectedValue(new Error("404"));
    renderPage();
    expect(await screen.findByRole("heading", { name: "Link này không còn mở được." })).toBeInTheDocument();
  });
});
