import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { getPublicRadarInvite } from "../../shared/api/client";
import { PublicRadarPage } from "./PublicRadarPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getPublicRadarInvite: vi.fn() };
});

describe("PublicRadarPage", () => {
  it("shows purpose and privacy before collecting any recipient data", async () => {
    vi.mocked(getPublicRadarInvite).mockResolvedValue({
      request_id: "request-1",
      recipient_label: "Mèo",
      context: "crush",
      expires_at: "2026-09-27T00:00:00Z",
      consent_version: "radar-pair-v1",
      requires_exact_birth_profile: true,
      privacy_note: "private",
    });
    render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={["/radar/i/token"]}>
        <Routes><Route element={<PublicRadarPage />} path="/radar/i/:token" /></Routes>
      </MemoryRouter>
    </QueryClientProvider>);

    expect(await screen.findByRole("heading", { name: "Mèo, bật Radar cùng họ?" })).toBeInTheDocument();
    expect(screen.getByText("Dữ liệu sinh không được trao đổi")).toBeInTheDocument();
    expect(screen.getByText("Bạn quyết định riêng cho lần này")).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Tiến độ Radar" })).toBeInTheDocument();
    expect(screen.getByText("Bắt đầu").closest('[aria-current="step"]')).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});
