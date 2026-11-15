import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiProblem, createLaChungInvite } from "../../shared/api/client";
import { InvitePreviewPage } from "./InvitePreviewPage";

vi.mock("../../shared/api/client", async (original) => ({ ...await original<typeof import("../../shared/api/client")>(), createLaChungInvite: vi.fn() }));

let seenState: unknown = "unset";
function StateProbe() {
  seenState = useLocation().state;
  return null;
}

describe("InvitePreviewPage keeps the label out of browser history (Codex auto-1 on #505)", () => {
  beforeEach(() => { vi.clearAllMocks(); seenState = "unset"; });

  it("drops the history-state copy on arrival and keeps the draft in memory, also after a crisis notice", async () => {
    const notice = "Câu thông báo tổng hợp để thử.";
    vi.mocked(createLaChungInvite).mockRejectedValue(new ApiProblem(422, "CRISIS_NOTICE", "", { notice: { text: notice } }));
    const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
    render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[{ pathname: "/la-chung/preview", state: { recipientLabel: "nhãn tổng hợp", context: "bff" } }]}>
      <Routes><Route path="/la-chung/preview" element={<><InvitePreviewPage /><StateProbe /></>} /></Routes>
    </MemoryRouter></QueryClientProvider>);

    expect(screen.getByText("Gửi tới · nhãn tổng hợp")).toBeInTheDocument();
    await waitFor(() => expect(seenState).toBeNull());
    await userEvent.setup().click(screen.getByRole("button", { name: "Tạo link riêng tư" }));
    await waitFor(() => expect(createLaChungInvite).toHaveBeenCalled());
    expect(await screen.findByText(notice)).toBeInTheDocument();
    expect(seenState).toBeNull();
    expect(screen.getByText("Gửi tới · nhãn tổng hợp")).toBeInTheDocument();
  });
});
