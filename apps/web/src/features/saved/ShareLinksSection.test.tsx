import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { listShareLinks, revokeShareArtifact, type ShareLink } from "../../shared/api/client";
import { ShareLinksSection } from "./ShareLinksSection";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, listShareLinks: vi.fn(), revokeShareArtifact: vi.fn() };
});

const active: ShareLink = {
  id: "11111111-1111-4111-8111-111111111111",
  format: "story_9_16",
  status: "active",
  created_at: "2026-10-20T08:00:00Z",
  expires_at: "2026-11-03T08:00:00Z",
  revoked_at: null,
};
const revoked: ShareLink = {
  ...active,
  id: "22222222-2222-4222-8222-222222222222",
  format: "square_1_1",
  status: "revoked",
  revoked_at: "2026-10-21T08:00:00Z",
};

function renderSection() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><ShareLinksSection /></QueryClientProvider>);
}

describe("ShareLinksSection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(revokeShareArtifact).mockResolvedValue(undefined);
  });
  afterEach(() => vi.restoreAllMocks());

  it("lists links by date and status and revokes only an active one after confirmation", async () => {
    vi.mocked(listShareLinks)
      .mockResolvedValueOnce({ items: [active, revoked], next_cursor: null })
      .mockResolvedValueOnce({ items: [{ ...active, status: "revoked", revoked_at: "2026-10-29T08:00:00Z" }, revoked], next_cursor: null });
    const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValueOnce(true);
    const user = userEvent.setup();
    renderSection();

    expect(await screen.findByText(/Ảnh dọc 9:16 · Đang mở/)).toBeInTheDocument();
    expect(screen.getByText(/Ảnh vuông 1:1 · Đã thu hồi/)).toBeInTheDocument();
    const buttons = screen.getAllByRole("button", { name: /Thu hồi link/ });
    expect(buttons).toHaveLength(1);

    await user.click(buttons[0]);
    expect(revokeShareArtifact).not.toHaveBeenCalled();
    await user.click(buttons[0]);
    await waitFor(() => expect(revokeShareArtifact).toHaveBeenCalledWith(active.id));
    expect(confirm).toHaveBeenCalledTimes(2);
    expect(await screen.findByRole("status")).toHaveTextContent("Đã thu hồi link");
    await waitFor(() => expect(screen.queryByRole("button", { name: /Thu hồi link/ })).not.toBeInTheDocument());
    // Never a token, a public path or note content: the server does not send them.
    expect(document.body.textContent).not.toMatch(/\/share\//);
  });

  it("pages with the server cursor and shows an empty state", async () => {
    vi.mocked(listShareLinks)
      .mockResolvedValueOnce({ items: [active], next_cursor: "next-page" })
      .mockResolvedValueOnce({ items: [revoked], next_cursor: null });
    const user = userEvent.setup();
    renderSection();
    await user.click(await screen.findByRole("button", { name: "Xem thêm link" }));
    expect(await screen.findByText(/Ảnh vuông 1:1/)).toBeInTheDocument();
    expect(vi.mocked(listShareLinks).mock.calls[1][1]).toBe("next-page");
    expect(screen.queryByRole("button", { name: "Xem thêm link" })).not.toBeInTheDocument();
  });

  it("says so when there is no link", async () => {
    vi.mocked(listShareLinks).mockResolvedValue({ items: [], next_cursor: null });
    renderSection();
    expect(await screen.findByText("Bạn chưa có link chia sẻ nào.")).toBeInTheDocument();
  });
});
