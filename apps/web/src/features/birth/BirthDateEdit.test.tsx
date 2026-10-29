import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  correctBirthDate,
  getBirthProfile,
  getSession,
  type BirthReveal,
} from "../../shared/api/client";
import { withdrawCorrectedChart } from "../../shared/storage/clearChartDerivedData";
import { BirthDatePage } from "./BirthDatePage";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, correctBirthDate: vi.fn(), getBirthProfile: vi.fn(), getSession: vi.fn() };
});
vi.mock("../../shared/storage/clearChartDerivedData", async (original) => {
  const actual = await original<typeof import("../../shared/storage/clearChartDerivedData")>();
  return { ...actual, withdrawCorrectedChart: vi.fn() };
});

const saved = {
  profile_id: "profile-test",
  snapshot_id: "snapshot-old",
  birth_date: "1990-01-01",
  calculation_kind: "date_only_sun",
  calculation: { status: "certain", sign: "capricorn", candidates: [] },
  created_at: "2026-09-14T00:00:00Z",
  resumed: true,
  profile_revision: "2026-10-29T08:00:00.123456Z",
} as unknown as BirthReveal;

function Where() {
  const location = useLocation();
  return <p data-testid="where">{location.pathname}{location.state ? JSON.stringify(location.state) : ""}</p>;
}

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/birth" element={<BirthDatePage />} />
          <Route path="*" element={<Where />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function typeDate(group: HTMLElement, day: string, month: string, year: string) {
  const user = userEvent.setup();
  for (const [name, value] of [["Ngày", day], ["Tháng", month], ["Năm", year]] as const) {
    const input = within(group).getByRole("textbox", { name });
    await user.clear(input);
    await user.type(input, value);
  }
}

describe("BirthDatePage edit mode (US-23)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getBirthProfile).mockResolvedValue(saved);
    vi.mocked(getSession).mockResolvedValue({
      state: "active", onboarding_status: "completed", expires_at: "2026-11-14T00:00:00Z",
      resumed: true, session_epoch: "epoch-test",
    });
    vi.mocked(withdrawCorrectedChart).mockResolvedValue(undefined);
  });

  it("prefills the saved date, asks for the new one twice and withdraws the old chart", async () => {
    const user = userEvent.setup();
    vi.mocked(correctBirthDate).mockResolvedValue({ ...saved, birth_date: "1992-07-20", snapshot_id: "snapshot-new" });
    renderAt("/birth?edit=1");
    const first = await screen.findByRole("group", { name: "Ngày sinh mới" });
    await waitFor(() => expect(within(first).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));

    await typeDate(first, "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Tiếp tục/ }));
    const again = await screen.findByRole("group", { name: "Nhập lại ngày sinh mới" });
    expect(correctBirthDate).not.toHaveBeenCalled();

    await typeDate(again, "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Đổi ngày sinh/ }));
    await waitFor(() => expect(correctBirthDate).toHaveBeenCalledWith({
      birth_date: "1992-07-20",
      confirm_birth_date: "1992-07-20",
      expected_revision: saved.profile_revision,
    }));
    expect(withdrawCorrectedChart).toHaveBeenCalledTimes(1);
    expect(await screen.findByTestId("where")).toHaveTextContent('/reveal{"corrected":true}');
  });

  it("catches a typo in the second entry without sending anything", async () => {
    const user = userEvent.setup();
    renderAt("/birth?edit=1");
    const first = await screen.findByRole("group", { name: "Ngày sinh mới" });
    await waitFor(() => expect(within(first).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));
    await typeDate(first, "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Tiếp tục/ }));
    await typeDate(await screen.findByRole("group", { name: "Nhập lại ngày sinh mới" }), "21", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Đổi ngày sinh/ }));
    expect(screen.getByRole("alert")).toHaveTextContent("Hai lần nhập chưa giống nhau");
    expect(correctBirthDate).not.toHaveBeenCalled();
  });

  it("says the same date is already saved", async () => {
    const user = userEvent.setup();
    renderAt("/birth?edit=1");
    const first = await screen.findByRole("group", { name: "Ngày sinh mới" });
    await waitFor(() => expect(within(first).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));
    await user.click(screen.getByRole("button", { name: /Tiếp tục/ }));
    expect(screen.getByRole("alert")).toHaveTextContent("Ngày này đã được lưu.");
    expect(correctBirthDate).not.toHaveBeenCalled();
  });

  it("refuses an under-18 date before sending and offers full deletion", async () => {
    const user = userEvent.setup();
    renderAt("/birth?edit=1");
    const first = await screen.findByRole("group", { name: "Ngày sinh mới" });
    await waitFor(() => expect(within(first).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));
    await typeDate(first, "01", "01", String(new Date().getFullYear() - 10));
    await user.click(screen.getByRole("button", { name: /Tiếp tục/ }));
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Lá Lành hiện dành cho người từ 18 tuổi.");
    await user.click(within(alert).getByRole("link", { name: "Xóa Lá và dữ liệu" }));
    expect(await screen.findByTestId("where")).toHaveTextContent('/profile{"confirmDelete":true}');
    expect(correctBirthDate).not.toHaveBeenCalled();
  });

  it("reloads the current date when another tab changed it first", async () => {
    const user = userEvent.setup();
    vi.mocked(correctBirthDate).mockRejectedValue(new ApiProblem(409, "BIRTH_PROFILE_CHANGED", "changed"));
    vi.mocked(getBirthProfile)
      .mockResolvedValueOnce(saved)
      .mockResolvedValue({ ...saved, birth_date: "1991-05-05", profile_revision: "2026-10-29T09:00:00Z" });
    renderAt("/birth?edit=1");
    const first = await screen.findByRole("group", { name: "Ngày sinh mới" });
    await waitFor(() => expect(within(first).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));
    await typeDate(first, "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Tiếp tục/ }));
    await typeDate(await screen.findByRole("group", { name: "Nhập lại ngày sinh mới" }), "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Đổi ngày sinh/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Hồ sơ vừa được cập nhật ở nơi khác");
    await waitFor(() => expect(within(screen.getByRole("group", { name: "Ngày sinh mới" })).getByRole("textbox", { name: "Năm" })).toHaveValue("1991"));
    expect(withdrawCorrectedChart).not.toHaveBeenCalled();
  });

  it.each([
    ["BIRTH_DATE_CHANGE_LIMITED", 429, "Bạn đã đổi ngày sinh vài lần hôm nay"],
    ["BIRTH_CHART_BUSY", 429, "Lá cũ vẫn giữ nguyên"],
  ])("explains %s calmly and keeps the old chart", async (code, status, text) => {
    const user = userEvent.setup();
    vi.mocked(correctBirthDate).mockRejectedValue(new ApiProblem(status, code, code));
    renderAt("/birth?edit=1");
    const first = await screen.findByRole("group", { name: "Ngày sinh mới" });
    await waitFor(() => expect(within(first).getByRole("textbox", { name: "Năm" })).toHaveValue("1990"));
    await typeDate(first, "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Tiếp tục/ }));
    await typeDate(await screen.findByRole("group", { name: "Nhập lại ngày sinh mới" }), "20", "07", "1992");
    await user.click(screen.getByRole("button", { name: /Đổi ngày sinh/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(text);
    expect(withdrawCorrectedChart).not.toHaveBeenCalled();
  });
});

describe("/birth for a person who already has a birth subject", () => {
  beforeEach(() => vi.clearAllMocks());

  it("redirects to Mình instead of offering a second first entry", async () => {
    vi.mocked(getSession).mockResolvedValue({ onboarding_status: "completed" } as Awaited<ReturnType<typeof getSession>>);
    vi.mocked(getBirthProfile).mockResolvedValue(saved);
    renderAt("/birth");
    expect(await screen.findByTestId("where")).toHaveTextContent("/profile");
  });

  it("stays for re-entry when no subject exists, and never asks during first onboarding", async () => {
    vi.mocked(getSession).mockResolvedValue({ onboarding_status: "basic_revealed" } as Awaited<ReturnType<typeof getSession>>);
    vi.mocked(getBirthProfile).mockRejectedValue(new ApiProblem(404, "BIRTH_PROFILE_NOT_FOUND", "missing"));
    const { unmount } = renderAt("/birth");
    await waitFor(() => expect(getBirthProfile).toHaveBeenCalled());
    expect(screen.getByRole("heading", { name: "Bạn xuất hiện ngày nào?" })).toBeInTheDocument();
    unmount();

    vi.clearAllMocks();
    vi.mocked(getSession).mockResolvedValue({ onboarding_status: "birth_pending" } as Awaited<ReturnType<typeof getSession>>);
    renderAt("/birth");
    await waitFor(() => expect(getSession).toHaveBeenCalled());
    expect(getBirthProfile).not.toHaveBeenCalled();
  });
});
