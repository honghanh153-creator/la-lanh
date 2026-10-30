// Codex r55 (US-23 U3): a correction must not overwrite a newer profile with its own older
// response, and an ambiguous failure (timeout, transport) must be reconciled instead of promising
// that the old chart is unchanged. Synthetic data only.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";

import { correctBirthDate, getBirthProfile, type BirthReveal } from "../../shared/api/client";
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

beforeEach(() => vi.clearAllMocks());

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

it("still says the old chart stays when the server shows no change", async () => {
  vi.mocked(getBirthProfile).mockResolvedValue(old);
  vi.mocked(correctBirthDate).mockRejectedValue(new Error("synthetic transport failure"));
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
