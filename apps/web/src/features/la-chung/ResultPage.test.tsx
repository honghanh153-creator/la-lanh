import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { deleteLaChungResult, getLaChungResult, hideLaChungResult } from "../../shared/api/client";
import { ResultPage } from "./ResultPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getLaChungResult: vi.fn(), hideLaChungResult: vi.fn(), deleteLaChungResult: vi.fn() };
});

const ID = "00000000-0000-4000-8000-000000000001";

function renderPage(client: QueryClient) {
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/la-chung/results/${ID}`]}>
        <Routes>
          <Route path="/la-chung/results/:requestId" element={<ResultPage />} />
          <Route path="/la-chung/history" element={<p>history</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ResultPage (P03 RC-07)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getLaChungResult).mockResolvedValue({
      request_id: ID, display_alias: null, statements: ["zqcanary statement"],
    } as unknown as Awaited<ReturnType<typeof getLaChungResult>>);
    vi.mocked(hideLaChungResult).mockResolvedValue(undefined);
    vi.mocked(deleteLaChungResult).mockResolvedValue(undefined);
  });

  it.each([["Xóa vĩnh viễn"], ["Ẩn kết quả"]])("%s removes the result from the cache", async (label) => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    renderPage(client);
    await userEvent.click(await screen.findByRole("button", { name: label }));
    await screen.findByText("history");
    expect(client.getQueryData(["la-chung-result", ID])).toBeUndefined();
  });

  it("does not render cached statements when the reload fails", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    client.setQueryData(["la-chung-result", ID], { request_id: ID, display_alias: null, statements: ["zqcanary statement"] });
    vi.mocked(getLaChungResult).mockRejectedValue(new Error("gone"));
    renderPage(client);
    await waitFor(() => expect(screen.getByRole("heading", { name: "Lá Chứng này không còn mở." })).toBeInTheDocument());
    expect(screen.queryByText("zqcanary statement")).toBeNull();
  });
});
