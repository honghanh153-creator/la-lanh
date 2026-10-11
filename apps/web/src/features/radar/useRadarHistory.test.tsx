import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { describe, expect, it, vi } from "vitest";
import { listRadarInvites, type RadarInvite } from "../../shared/api/client";
import { useRadarCreateKey, useRadarHistory } from "./useRadarHistory";

vi.mock("../../shared/api/client", () => ({ listRadarInvites: vi.fn() }));

describe("Radar retry and bounded history", () => {
  it("keeps a retry key only for the same draft and owner", () => {
    const { result, rerender } = renderHook(({ epoch }) => useRadarCreateKey(epoch), {
      initialProps: { epoch: "owner-a" },
    });
    const draft = { recipient_label: "An", context: "friend" };
    const key = result.current.forDraft(draft);
    expect(result.current.forDraft({ ...draft })).toBe(key);
    rerender({ epoch: "owner-b" });
    expect(result.current.forDraft(draft)).not.toBe(key);
    const next = result.current.forDraft(draft);
    result.current.reset();
    expect(result.current.forDraft(draft)).not.toBe(next);
  });

  it("loads another page explicitly and never shows another owner's pages", async () => {
    const page = Array.from({ length: 20 }, (_, i) => ({
      id: `a-${i}`, recipient_label: "An", mode: "private_check", status: "completed",
    })) as RadarInvite[];
    vi.mocked(listRadarInvites).mockReset().mockResolvedValueOnce(page).mockResolvedValueOnce([]);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = ({ children }: PropsWithChildren) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
    const { result, rerender } = renderHook(({ epoch }) => useRadarHistory(epoch, true, "private_check"), {
      wrapper, initialProps: { epoch: "owner-a" },
    });
    await waitFor(() => expect(result.current.items).toHaveLength(20));
    expect(listRadarInvites).toHaveBeenCalledWith(expect.any(AbortSignal), undefined, "private_check");
    expect(listRadarInvites).toHaveBeenCalledTimes(1);
    await act(() => result.current.fetchNextPage());
    expect(listRadarInvites).toHaveBeenLastCalledWith(expect.any(AbortSignal), "a-19", "private_check");
    await waitFor(() => expect(result.current.hasNextPage).toBe(false));
    vi.mocked(listRadarInvites).mockImplementation(() => new Promise(() => {}));
    rerender({ epoch: "owner-b" });
    expect(result.current.items).toHaveLength(0);
  });
});
