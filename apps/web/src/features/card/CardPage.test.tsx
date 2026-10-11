import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { createShareArtifact, getDailyNote, type DailyNote, type ShareArtifact } from "../../shared/api/client";
import { CardPage } from "./CardPage";

vi.mock("../../shared/api/client", async (original) => ({
  ...await original<typeof import("../../shared/api/client")>(),
  getDailyNote: vi.fn(),
  createShareArtifact: vi.fn(),
}));
// jsdom cannot fetch bundled fonts or rasterize; render with the system-font fallback.
vi.mock("./shareFonts", () => ({ cachedShareFontCss: () => "", loadShareFontCss: () => Promise.resolve("") }));
vi.mock("./shareRaster", async (original) => ({
  ...await original<typeof import("./shareRaster")>(),
  rasterizeSvg: vi.fn(() => Promise.resolve(new Blob(["png"], { type: "image/png" }))),
}));

const note: DailyNote = {
  id: "00000000-0000-4000-8000-000000000001", note_date: "2026-10-10",
  title: "Một note để chia sẻ", body: "Nội dung", full_body: "Nội dung",
  context_label: "Tự động", content_version: "v1", created_at: "2026-10-10T00:00:00Z",
  fallback_used: false, fallback_reason: null, persona_mode: "vibe", persona_label: "Mộng",
  persona_version: "v1", source_level: "date_only_sun", astrology_source_version: "v1",
};
const artifact: ShareArtifact = {
  id: "00000000-0000-4000-8000-000000000002", daily_note_id: note.id,
  format: "story_9_16", created_at: note.created_at, expires_at: "2026-10-11T00:00:00Z",
  public_path: "/share/synthetic-test-token",
  safe_snapshot: {
    title: note.title, body: "", persona_mode: "vibe", persona_label: "Mộng",
    content_version: "v1", context_label: "Tự động", persona_version: "v1", watermark: "Lá Lành",
  },
};

function renderPage() {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <MemoryRouter><CardPage /></MemoryRouter>
  </QueryClientProvider>);
}

describe("CardPage", () => {
  it("offers a retry instead of spinning forever when the current note fails", async () => {
    vi.mocked(getDailyNote).mockRejectedValueOnce(new Error("Note unavailable"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa tải được note để tạo card.");
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Tạo safe link" })).toBeDisabled();
  });

  it("shows a selectable link when clipboard access fails", async () => {
    const user = userEvent.setup();
    vi.spyOn(navigator.clipboard, "writeText").mockRejectedValueOnce(new Error("Clipboard denied"));
    vi.mocked(getDailyNote).mockResolvedValue(note);
    vi.mocked(createShareArtifact).mockResolvedValue(artifact);
    renderPage();
    await screen.findByRole("heading", { name: note.title });
    await user.click(screen.getByRole("button", { name: "Tạo safe link" }));
    await user.click(await screen.findByRole("button", { name: "Copy link" }));
    expect(await screen.findByRole("textbox", { name: "Link chia sẻ" })).toHaveValue(
      new URL(artifact.public_path!, window.location.origin).toString(),
    );
  });

  it("shows a branded skeleton while loading, then an accessible preview image", async () => {
    let resolveNote: (value: DailyNote) => void = () => undefined;
    vi.mocked(getDailyNote).mockReturnValueOnce(new Promise((resolve) => { resolveNote = resolve; }));
    renderPage();
    expect(screen.getByRole("status")).toHaveTextContent("Lá đang vẽ thẻ của bạn…");
    expect(screen.getByRole("button", { name: /Chia sẻ card/ })).toBeDisabled();
    resolveNote(note);
    const image = await screen.findByRole("img", { name: /Một note để chia sẻ/ });
    expect(image.getAttribute("alt")).toContain("Vibe · Mộng");
    expect(image.getAttribute("alt")).not.toMatch(/Chất|Aura/);
    expect(image.getAttribute("src")).toMatch(/^data:image\/svg\+xml/);
    fireEvent.load(image);
    expect(screen.queryByText("Lá đang vẽ thẻ của bạn…")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: note.title })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Chia sẻ card/ })).toBeEnabled();
    expect(screen.getByRole("button", { name: /Tải ảnh PNG/ })).toBeEnabled();
  });
});
