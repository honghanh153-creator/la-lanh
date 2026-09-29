import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createGuest } from "../../shared/api/client";
import { RADAR_PENDING_REQUEST_KEY } from "../radar/radarOptions";
import { WelcomePage } from "./WelcomePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, createGuest: vi.fn() };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/welcome"]}>
        <Routes>
          <Route path="/welcome" element={<WelcomePage />} />
          <Route path="/birth" element={<h1>Ngày sinh</h1>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("WelcomePage", () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.mocked(createGuest).mockResolvedValue({
      state: "active",
      onboarding_status: "birth_pending",
      expires_at: "2026-10-14T00:00:00Z",
      resumed: false,
      session_epoch: "epoch-test",
    });
  });

  it("shows one concise consent step without a carousel or login wall", () => {
    renderPage();

    expect(screen.getByLabelText("Lá Lành")).toBeInTheDocument();
    expect(screen.getByText("BƯỚC 1/3 · BẮT ĐẦU")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Có một tín hiệu đã đi cùng bạn từ ngày bạn xuất hiện." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đồng ý & bắt đầu" })).toBeEnabled();
    expect(screen.getByRole("link", { name: "Xem bản mẫu" })).toHaveAttribute("href", "/demo");
    expect(screen.getByRole("link", { name: "Quyền riêng tư" })).toHaveAttribute("href", "/privacy");
    expect(document.querySelector('a[href="/consent"]')).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Tiến độ giới thiệu")).not.toBeInTheDocument();
    expect(screen.queryByText("Mình đã có tài khoản")).not.toBeInTheDocument();
  });

  it("creates a guest directly and moves to DOB with one affirmative action", async () => {
    const user = userEvent.setup();
    sessionStorage.setItem(RADAR_PENDING_REQUEST_KEY, "radar-request-1");
    sessionStorage.setItem("la-lanh-radar-owner-start", "1");
    renderPage();
    await user.click(screen.getByRole("button", { name: "Đồng ý & bắt đầu" }));

    expect(createGuest).toHaveBeenCalledTimes(1);
    expect(sessionStorage.getItem(RADAR_PENDING_REQUEST_KEY)).toBe("radar-request-1");
    expect(sessionStorage.getItem("la-lanh-radar-owner-start")).toBe("1");
    expect(await screen.findByRole("heading", { name: "Ngày sinh" })).toBeInTheDocument();
  });
});
