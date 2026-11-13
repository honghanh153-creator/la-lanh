// Codex r61 (US-23): while a birth correction's outcome is unknown, Mình must not show the old
// birth date or its Sun/Moon/Rising from a fresh profile read; only the reconciliation read passes.
// Synthetic data only.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import {
  getAccountStatus, getBirthSupplement, getContentRewriteStatus, getDailyNote, getHistoryRetention,
  getResonanceStatus, type BirthReveal,
} from "../../shared/api/client";
import { CHART_QUARANTINE_KEY } from "../../shared/storage/chartQuarantineGate";
import { chartQuarantined, endQuarantine, quarantineChartDerivedData } from "../../shared/storage/clearChartDerivedData";
import { ProfilePage } from "./ProfilePage";

vi.mock("../../shared/api/client", async (original) => ({
  ...await original<typeof import("../../shared/api/client")>(),
  // getBirthProfile stays real: its reads go through the quarantine gate.
  getBirthSupplement: vi.fn(),
  getDailyNote: vi.fn(),
  getResonanceStatus: vi.fn(),
  getContentRewriteStatus: vi.fn(),
  getAccountStatus: vi.fn(),
  getHistoryRetention: vi.fn(),
}));

vi.mock("../../shared/theme/useTheme", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

const OLD_REVISION = "2026-10-29T08:00:00Z";
const profile = (birthDate: string, revision: string) => ({
  profile_id: "synthetic-profile",
  snapshot_id: `synthetic-${revision}`,
  birth_date: birthDate,
  calculation_kind: "date_only_sun",
  calculation: { status: "certain", sign: "capricorn", candidates: [] },
  created_at: "2026-10-29T08:00:00Z",
  resumed: true,
  profile_revision: revision,
}) as unknown as BirthReveal;

type Server = { mode: "computing" | "offline" | "committed" };
const server: Server = { mode: "computing" };
const pageReads: string[] = [];

beforeEach(() => {
  server.mode = "computing";
  pageReads.length = 0;
  vi.mocked(getBirthSupplement).mockRejectedValue(new Error("not available"));
  vi.mocked(getDailyNote).mockRejectedValue(new Error("not available"));
  vi.mocked(getResonanceStatus).mockResolvedValue({ consented: false, feedback_count: 0, last_choice: null });
  vi.mocked(getContentRewriteStatus).mockResolvedValue({ enabled: false, consented: false, pilot_eligible: false });
  vi.mocked(getAccountStatus).mockResolvedValue({ login_enabled: false, google_login_enabled: false, signed_in: false, masked_email: null, profile_expires_at: null, guest_inactivity_days: 30, history_days: 30, daily_note_hours: 24, account_inactivity_days: 365 });
  vi.mocked(getHistoryRetention).mockResolvedValue({ enabled: true, history_days: 30, daily_note_hours: 24, activated_at: "2026-10-10T00:00:00Z", saved_notes_kept: true });
  vi.stubGlobal("fetch", vi.fn((input: string | URL) => {
    const url = input.toString();
    if (!url.endsWith("/birth-profile")) return Promise.resolve(Response.json({ code: "NOT_FOUND" }, { status: 404 }));
    pageReads.push(server.mode);
    if (server.mode === "offline") return Promise.reject(new TypeError("Failed to fetch"));
    return Promise.resolve(Response.json(server.mode === "committed"
      ? profile("1992-07-20", "2026-10-29T09:00:00Z")
      : profile("1990-01-01", OLD_REVISION)));
  }));
});

afterEach(() => {
  endQuarantine();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

it("keeps Mình loading while the correction is unresolved and shows the new date after release", async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><MemoryRouter><ProfilePage /></MemoryRouter></QueryClientProvider>);
  expect(await screen.findByRole("button", { name: /Ngày sinh: 01\/01\/1990 · Sửa/ })).toBeInTheDocument();

  // Ambiguous failure: the old profile is withdrawn at quarantine start (date and calculation).
  await act(() => quarantineChartDerivedData(client, OLD_REVISION, { intervalMs: 40, windowMs: 60_000 }));
  expect(client.getQueryData(["birth-profile"])).toBeUndefined();
  await waitFor(() => expect(screen.queryByText(/01\/01\/1990/)).not.toBeInTheDocument());

  // The server still has the old revision (computing), then reconciliation goes offline. Only the
  // reconciliation polls reach the server; Mình's own read waits at the gate.
  await waitFor(() => expect(pageReads).toContain("computing"));
  const readsWhileComputing = pageReads.length;
  server.mode = "offline";
  await waitFor(() => expect(pageReads.length).toBeGreaterThan(readsWhileComputing + 1));
  expect(chartQuarantined()).toBe(true);
  expect(sessionStorage.getItem(CHART_QUARANTINE_KEY)).toContain(OLD_REVISION);
  expect(screen.queryByText(/01\/01\/1990/)).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: /Ngày sinh:/ })).not.toBeInTheDocument();
  expect(client.getQueryState(["birth-profile"])?.status).toBe("pending");

  // The correction committed late: withdraw, release, and Mình reads the corrected profile.
  server.mode = "committed";
  expect(await screen.findByRole("button", { name: /Ngày sinh: 20\/07\/1992 · Sửa/ })).toBeInTheDocument();
  expect(chartQuarantined()).toBe(false);
  expect(screen.queryByText(/01\/01\/1990/)).not.toBeInTheDocument();
  client.clear();
});
