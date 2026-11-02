// Codex r55 (US-23 U3): a correction must not overwrite a newer profile with its own older
// response, and an ambiguous failure (timeout, transport) must be reconciled instead of promising
// that the old chart is unchanged. Synthetic data only.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

import { ApiProblem, correctBirthDate, getBirthProfile, SESSION_EPOCH_KEY, type BirthReveal } from "../../shared/api/client";
import { invalidateSessionRequests } from "../../shared/session/sessionIdentity";
import { CHART_QUARANTINE_KEY } from "../../shared/storage/chartQuarantineGate";
import { chartDataRevision, chartQuarantined, endQuarantine } from "../../shared/storage/clearChartDerivedData";
import { BirthDateEdit } from "./BirthDateEdit";

vi.mock("../../shared/api/client", async (original) => ({
  ...await original<typeof import("../../shared/api/client")>(),
  getBirthProfile: vi.fn(),
  correctBirthDate: vi.fn(),
}));

const old = {
  profile_id: "synthetic-profile",
  snapshot_id: "synthetic-old",
  birth_date: "1990-01-01",
  calculation_kind: "date_only_sun",
  calculation: { status: "certain", sign: "capricorn", candidates: [] },
  created_at: "2026-10-29T08:00:00Z",
  resumed: true,
  profile_revision: "2026-10-29T08:00:00Z",
} as unknown as BirthReveal;
const first = { ...old, birth_date: "1992-07-20", snapshot_id: "synthetic-first", profile_revision: "2026-10-29T09:00:00Z" };
const newer = { ...old, birth_date: "1993-07-20", snapshot_id: "synthetic-newer", profile_revision: "2026-10-29T10:00:00Z" };

beforeEach(() => { vi.clearAllMocks(); endQuarantine(); });

function mount() {
  const query = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={query}>
      <MemoryRouter initialEntries={["/edit"]}>
        <Routes>
          <Route path="/edit" element={<BirthDateEdit />} />
          <Route path="*" element={<p>Finished</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return query;
}

async function enterNewDate() {
  const user = userEvent.setup();
  const initial = await screen.findByRole("group", { name: "Ngày sinh mới" });
  await waitFor(() => expect(within(initial).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));
  for (const group of [initial, null]) {
    const fields = group ?? await screen.findByRole("group", { name: "Nhập lại ngày sinh mới" });
    for (const [name, value] of [["Ngày", "20"], ["Tháng", "07"], ["Năm", "1992"]] as const) {
      const field = within(fields).getByRole("textbox", { name });
      await user.clear(field);
      await user.type(field, value);
    }
    await user.click(screen.getByRole("button", { name: group ? /Tiếp tục/ : /Đổi ngày sinh/ }));
  }
}

it("keeps the newer profile the cleanup refetch returned", async () => {
  vi.mocked(getBirthProfile).mockResolvedValueOnce(old).mockResolvedValue(newer);
  vi.mocked(correctBirthDate).mockResolvedValue(first);
  const query = mount();
  await enterNewDate();
  await screen.findByText("Finished");
  expect(getBirthProfile).toHaveBeenCalledTimes(2);
  expect(query.getQueryData(["birth-profile"])).toEqual(newer);
});

it("reconciles an ambiguous failure that actually committed", async () => {
  vi.mocked(getBirthProfile).mockResolvedValueOnce(old).mockResolvedValue(first);
  vi.mocked(correctBirthDate).mockRejectedValue(new Error("synthetic ambiguous transport timeout"));
  const query = mount();
  await enterNewDate();
  const alert = await screen.findByRole("alert");
  expect(alert).not.toHaveTextContent("Lá cũ vẫn giữ nguyên");
  expect(alert).toHaveTextContent("đã được đổi");
  expect(query.getQueryData(["birth-profile"])).toEqual(first);
});

it("stays uncertain when a transport failure precedes a later commit (Codex r57)", async () => {
  // The server is still computing when the reconciliation read returns the old revision.
  vi.mocked(getBirthProfile).mockResolvedValueOnce(old).mockResolvedValueOnce(old).mockResolvedValue(first);
  vi.mocked(correctBirthDate).mockRejectedValue(new Error("synthetic transport reset"));
  const query = mount();
  query.setQueryData(["daily-note"], "synthetic old note");
  const fence = chartDataRevision(query);
  await enterNewDate();
  const alert = await screen.findByText(/Chưa rõ thay đổi đã được lưu chưa/);
  expect(alert).not.toHaveTextContent("Lá cũ vẫn giữ nguyên");
  // The old chart's derived content is gone now, before any later commit (Codex r57 #2).
  expect(query.getQueryData(["daily-note"])).toBeUndefined();
  expect(chartDataRevision(query)).toBeGreaterThan(fence);
  // And it stays quarantined until the outcome is resolved (Codex r58).
  expect(chartQuarantined()).toBe(true);
});

it("withdraws the old chart after a conflict even when the refresh fails (Codex r57 #1)", async () => {
  vi.mocked(getBirthProfile).mockResolvedValueOnce(old).mockRejectedValue(new Error("offline"));
  vi.mocked(correctBirthDate).mockRejectedValue(new ApiProblem(409, "BIRTH_PROFILE_CHANGED", "changed"));
  const query = mount();
  query.setQueryData(["daily-note"], "synthetic old note");
  const fence = chartDataRevision(query);
  await enterNewDate();
  await screen.findByText(/Hồ sơ vừa được cập nhật ở nơi khác/);
  await waitFor(() => expect(query.getQueryData(["daily-note"])).toBeUndefined());
  expect(chartDataRevision(query)).toBeGreaterThan(fence);
});

it("still says the old chart stays when the server refused the request", async () => {
  vi.mocked(getBirthProfile).mockResolvedValue(old);
  vi.mocked(correctBirthDate).mockRejectedValue(new ApiProblem(429, "BIRTH_CHART_BUSY", "busy"));
  mount();
  await enterNewDate();
  expect(await screen.findByRole("alert")).toHaveTextContent("Lá cũ vẫn giữ nguyên");
});

it("does not promise anything when the reconciliation itself fails", async () => {
  vi.mocked(getBirthProfile).mockResolvedValueOnce(old).mockRejectedValue(new Error("offline"));
  vi.mocked(correctBirthDate).mockRejectedValue(new Error("synthetic transport failure"));
  mount();
  await enterNewDate();
  await screen.findByText(/Chưa rõ thay đổi đã được lưu chưa/);
  for (const alert of screen.getAllByRole("alert")) {
    expect(alert).not.toHaveTextContent("Lá cũ vẫn giữ nguyên");
  }
});

it("stops after the correction when the browser session changed meanwhile (Codex r56)", async () => {
  vi.mocked(getBirthProfile).mockResolvedValue(old);
  vi.mocked(correctBirthDate).mockImplementation(() => {
    invalidateSessionRequests(); // another account took over this browser during the request
    return Promise.resolve(first);
  });
  const query = mount();
  query.setQueryData(["unrelated"], "kept");
  await enterNewDate();
  await waitFor(() => expect(correctBirthDate).toHaveBeenCalled());
  await new Promise((resolve) => setTimeout(resolve, 50));
  expect(screen.queryByText("Finished")).not.toBeInTheDocument();
  expect(getBirthProfile).toHaveBeenCalledTimes(1); // no cleanup refetch for the old owner
});

it("clears the pending record when the server rolled the correction back (Codex r61)", async () => {
  vi.mocked(getBirthProfile).mockResolvedValueOnce(old).mockRejectedValue(new Error("offline"));
  vi.mocked(correctBirthDate).mockRejectedValue(new ApiProblem(503, "BIRTH_CORRECTION_EXPIRED", "expired"));
  mount();
  await enterNewDate();
  expect(await screen.findByRole("alert")).toHaveTextContent("Lá cũ vẫn giữ nguyên");
  expect(chartQuarantined()).toBe(false);
  expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toBeNull();
});

it("clears the pending record on a known refusal (Codex r61)", async () => {
  vi.mocked(getBirthProfile).mockResolvedValue(old);
  vi.mocked(correctBirthDate).mockRejectedValue(new ApiProblem(429, "BIRTH_DATE_CHANGE_LIMITED", "limited"));
  mount();
  await enterNewDate();
  await screen.findByText(/Bạn đã đổi ngày sinh vài lần hôm nay/);
  expect(chartQuarantined()).toBe(false);
  expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toBeNull();
});

// Codex r61: a reload while the PUT is still pending loses this page's continuation, but the
// server may commit afterwards. The record persisted before dispatch restores the quarantine.
it("restores a correction still pending at reload and purges its late commit", async () => {
  sessionStorage.setItem(SESSION_EPOCH_KEY, "synthetic-epoch");
  vi.mocked(getBirthProfile).mockResolvedValue(old);
  let storedAtDispatch: string | null = null;
  vi.mocked(correctBirthDate).mockImplementation(() => {
    storedAtDispatch = sessionStorage.getItem(CHART_QUARANTINE_KEY);
    return new Promise<BirthReveal>(() => undefined); // still pending when the page goes away
  });
  mount();
  await enterNewDate();
  await waitFor(() => expect(correctBirthDate).toHaveBeenCalled());
  expect(storedAtDispatch).toContain(old.profile_revision); // persisted before the request left
  expect(chartQuarantined()).toBe(true);
  cleanup();

  // Reload: fresh module state, only sessionStorage survives. The client mock is registered again
  // so the real request path (and its quarantine gate) is a fresh instance too.
  vi.resetModules();
  vi.doMock("../../shared/api/client", async (original) => ({
    ...await original<typeof import("../../shared/api/client")>(),
    getBirthProfile: vi.fn(),
  }));
  const api = await import("../../shared/api/client");
  const reloaded = await import("../../shared/storage/clearChartDerivedData");
  const fetchMock = vi.fn(() => Promise.resolve(Response.json({ id: "synthetic-new-note", reading_projection: null })));
  vi.stubGlobal("fetch", fetchMock);
  vi.mocked(api.getBirthProfile).mockResolvedValue(old); // the server is still computing
  vi.useFakeTimers();
  try {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    reloaded.resumeChartQuarantine(client, { intervalMs: 100 });
    expect(reloaded.chartQuarantined()).toBe(true);

    let settled = false;
    const read = api.getDailyNote().then(() => { settled = true; });
    // Old content cached before the commit still has to go once the commit lands.
    client.setQueryData(["daily-note"], "synthetic old note");
    await vi.advanceTimersByTimeAsync(250);
    expect(settled).toBe(false); // derived reads are held
    expect(fetchMock).not.toHaveBeenCalled();
    expect(api.getBirthProfile).toHaveBeenCalledWith(undefined, { bypassChartQuarantine: true });

    vi.mocked(api.getBirthProfile).mockResolvedValue(first); // the late commit
    await vi.advanceTimersByTimeAsync(100);
    await vi.waitFor(() => expect(reloaded.chartQuarantined()).toBe(false));
    expect(client.getQueryData(["daily-note"])).toBeUndefined();
    expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toBeNull();
    await read; // released to the corrected chart
    expect(fetchMock).toHaveBeenCalledTimes(1);
    client.clear();
  } finally {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    endQuarantine(); // the pre-reload instance, whose request never settles
    sessionStorage.removeItem(SESSION_EPOCH_KEY);
    sessionStorage.removeItem(CHART_QUARANTINE_KEY);
  }
});
