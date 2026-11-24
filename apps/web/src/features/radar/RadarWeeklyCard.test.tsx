import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { deleteRadarWeekly, getRadarConsentOptions, getRadarWeekly } from "../../shared/api/client";
import { RadarWeeklyCard } from "./RadarWeeklyCard";

vi.mock("../../shared/api/client", async (original) => {
  const actual = await original<typeof import("../../shared/api/client")>();
  return { ...actual, getRadarConsentOptions: vi.fn(), getRadarWeekly: vi.fn(), deleteRadarWeekly: vi.fn() };
});

const base = { invite_first: false, sentences: {}, authorized_input_version: "radar-authorized-input-v1", date_consent_version: "radar-pair-date-v1" };

function renderCard() {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><RadarWeeklyCard /></QueryClientProvider>);
}

describe("RadarWeeklyCard (Hợp gu C, off by default)", () => {
  it("renders nothing and asks for no pair while the feature is off", async () => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue({ ...base, weekly: false });
    const { container } = renderCard();
    await waitFor(() => expect(getRadarConsentOptions).toHaveBeenCalled());
    expect(getRadarWeekly).not.toHaveBeenCalled();
    expect(container).toBeEmptyDOMElement();
  });

  it("shows a kept pair by initial only and turning it off deletes it", async () => {
    vi.mocked(getRadarConsentOptions).mockResolvedValue({ ...base, weekly: true, weekly_sentences: { "home-note": "Câu ghi chú." } });
    vi.mocked(getRadarWeekly).mockResolvedValue({ version: "radar-weekly-v1", items: [{ id: "p-1", context: "partner", initial: "M.", week_of: "2026-11-16", easy: "Tuần này dễ: một điều.", watch: null, try_line: "Thử: một việc.", quiet: null, expires_at: "2027-02-18T00:00:00Z" }] });
    vi.mocked(deleteRadarWeekly).mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderCard();

    expect(await screen.findByRole("heading", { name: /Hai bạn tuần này/ })).toBeInTheDocument();
    expect(screen.getByText("Bạn × M. · Người yêu")).toBeInTheDocument();
    expect(screen.getByText("Câu ghi chú.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Tắt nhắc cặp Bạn × M." }));
    expect(deleteRadarWeekly).toHaveBeenCalledWith("p-1", expect.anything());
  });
});
