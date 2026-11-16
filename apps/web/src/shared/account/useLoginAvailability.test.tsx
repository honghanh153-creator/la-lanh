import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getAccountStatus, type AccountStatus } from "../api/client";
import { useLoginAvailability } from "./useLoginAvailability";

vi.mock("../api/client", async (original) => ({ ...await original<typeof import("../api/client")>(), getAccountStatus: vi.fn() }));

const note = "Câu tổng hợp đã duyệt: hồ sơ khách.";
function status(overrides: Partial<AccountStatus> = {}): AccountStatus {
  return { login_enabled: false, google_login_enabled: false, signed_in: false, masked_email: null, profile_expires_at: null, guest_inactivity_days: 30, history_days: 30, daily_note_hours: 24, account_inactivity_days: 365, guest_storage_note: note, ...overrides };
}
function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useLoginAvailability", () => {
  beforeEach(() => vi.clearAllMocks());

  it("gives a guest the approved storage sentence", async () => {
    vi.mocked(getAccountStatus).mockResolvedValue(status());
    const { result } = renderHook(() => useLoginAvailability(), { wrapper });
    await waitFor(() => expect(result.current.storageNote).toBe(note));
    expect(result.current.googleLoginEnabled).toBe(false);
  });

  it("never gives the guest sentence to a signed-in account, even with sign-in off (Codex auto-1 on #503)", async () => {
    vi.mocked(getAccountStatus).mockResolvedValue(status({ signed_in: true, masked_email: "s***@example.org" }));
    const { result } = renderHook(() => useLoginAvailability(), { wrapper });
    await waitFor(() => expect(getAccountStatus).toHaveBeenCalled());
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(result.current.storageNote).toBeNull();
    expect(result.current.googleLoginEnabled).toBe(false);
  });
});
