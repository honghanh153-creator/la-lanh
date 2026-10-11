import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { appRoutes } from "./router";

afterEach(() => vi.restoreAllMocks());
Object.defineProperty(window, "scrollTo", { value: vi.fn(), writable: true });

function renderRouter(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(appRoutes, { initialEntries: [path] });
  return render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("retired Lá Chứng routes", () => {
  it.each([
    "/la-chung",
    "/la-chung/preview",
    "/la-chung/i/secret-token",
  ])("opens %s as a static retirement page without fetching invite data", async (path) => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    renderRouter(path);

    expect(await screen.findByRole("heading", { name: "Lá Chứng không còn nhận phản hồi mới." })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Tiếp tục với Lá Lành/ })).toHaveAttribute("href", "/");
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("keeps the owner data-management route available", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((url) => Promise.resolve(new Response(
      (typeof url === "string" ? url : url instanceof URL ? url.href : url.url).endsWith("/session") ? JSON.stringify({
        state: "active", session_epoch: "synthetic-owner", onboarding_status: "completed",
        expires_at: "2026-11-09T00:00:00Z",
      }) : "[]", { status: 200, headers: { "Content-Type": "application/json" } },
    )));
    renderRouter("/la-chung/history");

    expect(await screen.findByRole("heading", { name: "Quản lý những gì đã có." })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /tạo|gửi lại/i })).not.toBeInTheDocument();
  });
});
