import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { getShareArtifact, type PublicShareArtifact } from "../../shared/api/client";
import { SharePreviewPage } from "./SharePreviewPage";

vi.mock("../../shared/api/client", async (original) => ({
  ...await original<typeof import("../../shared/api/client")>(),
  getShareArtifact: vi.fn(),
}));
vi.mock("./shareFonts", () => ({ cachedShareFontCss: () => "", loadShareFontCss: () => Promise.resolve("") }));
vi.mock("./shareRaster", async (original) => ({
  ...await original<typeof import("./shareRaster")>(),
  rasterizeSvg: vi.fn(() => Promise.resolve(new Blob(["png"], { type: "image/png" }))),
}));

const token = "synthetic-public-token-123";
const artifact = {
  expires_at: "2026-10-12T00:00:00Z",
  format: "square_1_1",
  safe_snapshot: {
    title: "Đầu có ba câu thì chọn một câu chính.", body: "Nói điều quan trọng nhất trước.",
    persona_mode: "vibe", persona_label: "Lanh", content_version: "v1", context_label: "Tự động",
    persona_version: "v1", watermark: "Lá Lành",
  },
} as PublicShareArtifact;

describe("SharePreviewPage", () => {
  it("renders the sanitized snapshot with the same art and keeps the token out of the image", async () => {
    vi.mocked(getShareArtifact).mockResolvedValue(artifact);
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={[`/share/${token}`]}><Routes><Route element={<SharePreviewPage />} path="/share/:token" /></Routes></MemoryRouter>
    </QueryClientProvider>);

    const image = await screen.findByRole("img", { name: /Đầu có ba câu thì chọn một câu chính/ });
    expect(screen.getByRole("heading", { name: artifact.safe_snapshot.title })).toBeInTheDocument();
    expect(image.getAttribute("alt")).toContain("Chất Lanh · Khí");
    expect(image.getAttribute("alt")).toContain("vuông 1:1");
    expect(decodeURIComponent(image.getAttribute("src") ?? "")).not.toContain(token);
    expect(image.getAttribute("alt")).not.toContain(token);
  });
});
