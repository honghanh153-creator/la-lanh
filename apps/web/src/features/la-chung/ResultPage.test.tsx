import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiProblem, deleteLaChungResult, getLaChungResult, hideLaChungResult } from "../../shared/api/client";
import { ResultPage } from "./ResultPage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getLaChungResult: vi.fn(), hideLaChungResult: vi.fn(), deleteLaChungResult: vi.fn() };
});

const ID = "00000000-0000-4000-8000-000000000001";
const RESULT = { request_id: ID, display_alias: null, statements: ["zqcanary statement"] } as unknown as Awaited<
  ReturnType<typeof getLaChungResult>
>;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

// The real service never returns a hidden, deleted or withdrawn result: every read after the hide
// or delete succeeds is denied, as on the server.
function serverFaithful(action: typeof hideLaChungResult) {
  let gone = false;
  vi.mocked(getLaChungResult).mockImplementation(() =>
    gone ? Promise.reject(new ApiProblem(404, "LA_CHUNG_UNAVAILABLE", "Unavailable")) : Promise.resolve(RESULT));
  const done = deferred<undefined>();
  vi.mocked(action).mockImplementation(async () => {
    await done.promise;
    gone = true;
  });
  return done;
}

function page(client: QueryClient) {
  return <QueryClientProvider client={client}>
    <MemoryRouter initialEntries={[`/la-chung/results/${ID}`]}>
      <Routes>
        <Route path="/la-chung/results/:requestId" element={<ResultPage />} />
        <Route path="/la-chung/history" element={<p>history</p>} />
      </Routes>
    </MemoryRouter>
  </QueryClientProvider>;
}

function renderPage(client: QueryClient) {
  return render(page(client));
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

  it.each([["Ẩn kết quả", hideLaChungResult], ["Xóa vĩnh viễn", deleteLaChungResult]] as const)(
    "%s: no read after success and no cache left after the page unmounts (deferred lifecycle)",
    async (label, action) => {
      // Codex r34 (P3): the cache must be empty for a reason, not because a refetch happened to fail.
      vi.mocked(action).mockReset();
      const done = deferred<undefined>();
      vi.mocked(action).mockReturnValue(done.promise);
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      renderPage(client);
      await userEvent.click(await screen.findByRole("button", { name: label }));
      expect(getLaChungResult).toHaveBeenCalledTimes(1);
      done.resolve(undefined);
      await screen.findByText("history");
      await waitFor(() => expect(client.getQueryCache().find({ queryKey: ["la-chung-result", ID] })).toBeUndefined());
      // The mock still answers with the reading, so only the page's own fence keeps it out.
      expect(getLaChungResult).toHaveBeenCalledTimes(1);
      expect(client.getQueryData(["la-chung-result", ID])).toBeUndefined();
    },
  );

  it.each([["Ẩn kết quả", hideLaChungResult], ["Xóa vĩnh viễn", deleteLaChungResult]] as const)(
    "%s: a server-faithful denial after success leaves nothing cached",
    async (label, action) => {
      const done = serverFaithful(action);
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      renderPage(client);
      await userEvent.click(await screen.findByRole("button", { name: label }));
      done.resolve(undefined);
      await screen.findByText("history");
      await waitFor(() => expect(client.getQueryCache().find({ queryKey: ["la-chung-result", ID] })).toBeUndefined());
      expect(screen.queryByText("zqcanary statement")).toBeNull();
    },
  );

  it.each([["Ẩn kết quả"], ["Xóa vĩnh viễn"]])(
    "%s: a re-render before navigation cannot refetch the removed reading",
    async (label) => {
      // Codex r34 (P3): hold the window between removing the reading and leaving the page open, then
      // re-render once, as any parent update would. The still-mounted observer must not rebuild and
      // refetch the reading; the mock keeps answering with it, so only the page's fence stops it.
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      const gate = deferred<void>();
      const invalidate = vi.spyOn(client, "invalidateQueries").mockImplementation(() => gate.promise);
      const view = renderPage(client);
      await userEvent.click(await screen.findByRole("button", { name: label }));
      await waitFor(() => expect(invalidate).toHaveBeenCalled());
      view.rerender(page(client));
      await new Promise((settle) => setTimeout(settle, 0));
      expect(getLaChungResult).toHaveBeenCalledTimes(1);
      expect(client.getQueryData(["la-chung-result", ID])).toBeUndefined();
      gate.resolve();
      await screen.findByText("history");
      await waitFor(() => expect(client.getQueryCache().find({ queryKey: ["la-chung-result", ID] })).toBeUndefined());
      expect(getLaChungResult).toHaveBeenCalledTimes(1);
    },
  );

  it("a read still in flight when the hide succeeds cannot put the reading back", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    renderPage(client);
    await screen.findByText("zqcanary statement");
    const late = deferred<Awaited<ReturnType<typeof getLaChungResult>>>();
    vi.mocked(getLaChungResult).mockImplementationOnce(() => late.promise);
    void client.refetchQueries({ queryKey: ["la-chung-result", ID] });
    await waitFor(() => expect(getLaChungResult).toHaveBeenCalledTimes(2));
    await userEvent.click(screen.getByRole("button", { name: "Ẩn kết quả" }));
    await screen.findByText("history");
    late.resolve(RESULT);
    await late.promise;
    await new Promise((settle) => setTimeout(settle, 0));
    expect(client.getQueryData(["la-chung-result", ID])).toBeUndefined();
    expect(client.getQueryCache().find({ queryKey: ["la-chung-result", ID] })).toBeUndefined();
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
