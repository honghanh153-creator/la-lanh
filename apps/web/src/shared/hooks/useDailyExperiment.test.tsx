import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  chooseDailyExperiment,
  getCurrentDailyExperiment,
  reflectDailyExperiment,
  undoDailyExperiment,
  type DailyExperiment,
} from "../api/client";
import { useDailyExperiment } from "./useDailyExperiment";

vi.mock("../api/client", async (original) => {
  const actual = await original<typeof import("../api/client")>();
  return {
    ...actual,
    chooseDailyExperiment: vi.fn(),
    getCurrentDailyExperiment: vi.fn(),
    reflectDailyExperiment: vi.fn(),
    undoDailyExperiment: vi.fn(),
  };
});

const experimentId = "10000000-0000-4000-8000-000000000001";
const dailyNoteId = "20000000-0000-4000-8000-000000000001";
const revisionId = "30000000-0000-4000-8000-000000000001";

const chosenExperiment: DailyExperiment = {
  id: experimentId,
  version: 1,
  daily_note_id: dailyNoteId,
  revision_id: revisionId,
  state: "chosen",
  background_lens: "work",
  action_key: "a".repeat(64),
  action: "Đặt một khoảng tập trung nhỏ cho việc quan trọng nhất.",
  observation: "Để ý một thay đổi nhỏ, cụ thể.",
  permission: "Bạn có thể dừng bất cứ lúc nào.",
  outcome: null,
  created_at: "2026-09-07T12:00:00Z",
  updated_at: "2026-09-07T12:00:00Z",
  expires_at: "2026-10-07T12:00:00Z",
  reflected_at: null,
};

const choice = {
  daily_note_id: dailyNoteId,
  revision_id: revisionId,
  background_lens: "work" as const,
  action_key: chosenExperiment.action_key,
  consent_version: "action-experiment-v1",
};

describe("useDailyExperiment", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(null);
  });

  it("publishes a chosen experiment to every observer sharing the QueryClient", async () => {
    vi.mocked(chooseDailyExperiment).mockResolvedValue(chosenExperiment);
    const { result } = renderSharedHooks();
    await waitFor(() => expect(result.current.first.isSuccess).toBe(true));

    await act(async () => {
      await result.current.first.chooseAsync(choice);
    });

    await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));
    expect(result.current.second.experiment).toEqual(chosenExperiment);
    expect(chooseDailyExperiment).toHaveBeenCalledWith(dailyNoteId, {
      revision_id: revisionId,
      background_lens: "work",
      action_key: chosenExperiment.action_key,
      consent_version: "action-experiment-v1",
    });
  });

  it("refetches shared server state after a 409 conflict", async () => {
    const remoteExperiment = { ...chosenExperiment, version: 2 };
    vi.mocked(getCurrentDailyExperiment)
      .mockResolvedValueOnce(null)
      .mockResolvedValue(remoteExperiment);
    vi.mocked(chooseDailyExperiment).mockRejectedValue(
      new ApiProblem(409, "EXPERIMENT_CONFLICT", "stale"),
    );
    const { result } = renderSharedHooks();
    await waitFor(() => expect(result.current.first.isSuccess).toBe(true));

    await act(async () => {
      await expect(result.current.first.chooseAsync(choice)).rejects.toMatchObject({ status: 409 });
    });

    await waitFor(() => expect(getCurrentDailyExperiment).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.second.experiment).toEqual(remoteExperiment));
    expect(result.current.first.experiment).toEqual(remoteExperiment);
    expect(result.current.first.errorMessage).toContain("đã thay đổi ở nơi khác");
  });

  it("rolls back the shared optimistic undo when the mutation fails", async () => {
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(chosenExperiment);
    const pendingUndo = deferred<void>();
    vi.mocked(undoDailyExperiment).mockReturnValue(pendingUndo.promise);
    const { result } = renderSharedHooks();
    await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));

    act(() => {
      result.current.first.undo({ experiment_id: experimentId, expected_version: 1 });
    });
    await waitFor(() => expect(result.current.second.experiment).toBeNull());

    act(() => pendingUndo.reject(new Error("offline")));
    await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));
    expect(result.current.second.experiment).toEqual(chosenExperiment);
  });

  it("rolls back the shared optimistic reflection when the mutation fails", async () => {
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(chosenExperiment);
    const pendingReflection = deferred<DailyExperiment>();
    vi.mocked(reflectDailyExperiment).mockReturnValue(pendingReflection.promise);
    const { result } = renderSharedHooks();
    await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));

    act(() => {
      result.current.first.reflect({
        experiment_id: experimentId,
        expected_version: 1,
        outcome: "helpful",
      });
    });
    await waitFor(() => {
      expect(result.current.second.experiment).toMatchObject({
        state: "reflected",
        outcome: "helpful",
        version: 2,
      });
    });

    act(() => pendingReflection.reject(new Error("offline")));
    await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));
    expect(result.current.second.experiment).toEqual(chosenExperiment);
  });
});

function renderSharedHooks() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const wrapper = ({ children }: PropsWithChildren) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(
    () => ({ first: useDailyExperiment(), second: useDailyExperiment() }),
    { wrapper },
  );
}

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}
