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
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("[]", {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }));
    renderRouter("/la-chung/history");

    expect(await screen.findByRole("heading", { name: "Quản lý những gì đã có." })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /tạo|gửi lại/i })).not.toBeInTheDocument();
  });
});
