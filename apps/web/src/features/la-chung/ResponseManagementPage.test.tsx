import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiProblem, withdrawLaChungResponse } from "../../shared/api/client";
import { ResponseManagementPage } from "./ResponseManagementPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, withdrawLaChungResponse: vi.fn() };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter><ResponseManagementPage /></MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ResponseManagementPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("withdraws only after an explicit action and confirms success", async () => {
    const user = userEvent.setup();
    vi.mocked(withdrawLaChungResponse).mockResolvedValue(undefined);
    renderPage();

    expect(withdrawLaChungResponse).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Rút phản hồi đã gửi" }));

    expect(await screen.findByRole("heading", { name: "Phản hồi đã được rút." })).toBeInTheDocument();
    expect(withdrawLaChungResponse).toHaveBeenCalledOnce();
  });

  it("does not claim success when no valid receipt exists", async () => {
    const user = userEvent.setup();
    vi.mocked(withdrawLaChungResponse).mockRejectedValue(new ApiProblem(404, "NOT_FOUND", "not found"));
    renderPage();

    await user.click(screen.getByRole("button", { name: "Rút phản hồi đã gửi" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Không tìm thấy receipt còn hiệu lực");
    expect(screen.queryByRole("heading", { name: "Phản hồi đã được rút." })).not.toBeInTheDocument();
  });

  it("keeps connectivity failures distinct from a missing receipt", async () => {
    const user = userEvent.setup();
    vi.mocked(withdrawLaChungResponse).mockRejectedValue(new Error("offline"));
    renderPage();

    await user.click(screen.getByRole("button", { name: "Rút phản hồi đã gửi" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Chưa kết nối được để rút phản hồi");
  });
});
