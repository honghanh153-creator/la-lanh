import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

import { getPublicLaChungInvite } from "../../shared/api/client";
import { PublicResponsePage } from "./PublicResponsePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getPublicLaChungInvite: vi.fn() };
});

beforeEach(() => {
  vi.mocked(getPublicLaChungInvite).mockResolvedValue({
    recipient_label: "bestie", context: "bff", expires_at: "2026-09-11T00:00:00Z",
    privacy_note: "Không cần tài khoản, ngày sinh hay danh bạ.",
    statements: [
      { id: "one", text: "Câu một", domain: "care" },
      { id: "two", text: "Câu hai", domain: "mind" },
      { id: "three", text: "Câu ba", domain: "drive" },
    ],
  });
});

it("explains privacy before enforcing the 3-statement minimum", async () => {
  const user = userEvent.setup();
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={["/la-chung/i/secret"]}><Routes><Route path="/la-chung/i/:token" element={<PublicResponsePage />} /></Routes></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByText("Không cần tài khoản, ngày sinh hay danh bạ.")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: /Bắt đầu/ }));
  const review = screen.getByRole("button", { name: /Xem lại/ });
  expect(review).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Câu một" }));
  await user.click(screen.getByRole("button", { name: "Câu hai" }));
  await user.click(screen.getByRole("button", { name: "Câu ba" }));
  expect(review).toBeEnabled();
});
