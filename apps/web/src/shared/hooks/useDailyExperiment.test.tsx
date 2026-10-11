import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiProblem,
  chooseDailyExperiment,
  getCurrentDailyExperiment,
  reflectDailyExperiment,
  undoDailyExperiment,
  type DailyExperiment,
} from "../api/client";
import { dailyExperimentQueryKey, useDailyExperiment } from "./useDailyExperiment";
import { invalidateSessionRequests, SESSION_EPOCH_KEY } from "../session/sessionIdentity";
import { clearChartDerivedData } from "../storage/clearChartDerivedData";
import { clearPersonalDataOnDevice } from "../storage/clearPersonalData";

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
    sessionStorage.clear();
    invalidateSessionRequests();
    vi.mocked(getCurrentDailyExperiment).mockResolvedValue(null);
  });

  afterEach(() => vi.restoreAllMocks());

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

  it.each(["choose", "undo", "reflect"] as const)(
    "does not restore erased chart data when an in-flight %s settles",
    async (operation) => {
      vi.mocked(getCurrentDailyExperiment).mockResolvedValue(chosenExperiment);
      const pending = deferred<DailyExperiment>();
      if (operation === "choose") vi.mocked(chooseDailyExperiment).mockReturnValue(pending.promise);
      if (operation === "reflect") vi.mocked(reflectDailyExperiment).mockReturnValue(pending.promise);
      if (operation === "undo") vi.mocked(undoDailyExperiment).mockReturnValue(pending.promise.then(() => undefined));
      const { result, client } = renderSharedHooks();
      await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));
      act(() => {
        if (operation === "choose") result.current.first.choose(choice);
        if (operation === "undo") result.current.first.undo({ experiment_id: experimentId, expected_version: 1 });
        if (operation === "reflect") result.current.first.reflect({ experiment_id: experimentId, expected_version: 1, outcome: "helpful" });
      });
      await waitFor(() => expect(
        result.current.first.isChoosing || result.current.first.isUndoing || result.current.first.isReflecting,
      ).toBe(true));
      vi.mocked(getCurrentDailyExperiment).mockResolvedValue(null);
      await act(async () => { await clearChartDerivedData(client); });
      const restored: unknown[] = [];
      const unsubscribe = client.getQueryCache().subscribe((event) => {
        if (event.query.queryKey[0] === "daily-experiment" && event.query.state.data) {
          restored.push(event.query.state.data);
        }
      });
      act(() => {
        if (operation === "choose") pending.resolve(chosenExperiment);
        else pending.reject(new Error("late error after erasure"));
      });
      await waitFor(() => expect(
        result.current.first.isChoosing || result.current.first.isUndoing || result.current.first.isReflecting,
      ).toBe(false));
      expect(result.current.first.experiment).toBeNull();
      expect(result.current.second.experiment).toBeNull();
      expect(restored).toEqual([]);
      unsubscribe();
      client.clear();
    },
  );

  describe.each(["choose", "undo", "reflect"] as const)("pending %s across sessions", (operation) => {
    it.each([
      { change: "generation", outcome: "success" },
      { change: "generation", outcome: "error" },
      { change: "epoch", outcome: "success" },
      { change: "epoch", outcome: "error" },
      { change: "erasure", outcome: "success" },
      { change: "erasure", outcome: "error" },
    ])("ignores $outcome after $change changes and the cache is cleared", async ({ change, outcome }) => {
      sessionStorage.setItem(SESSION_EPOCH_KEY, "owner-a");
      const pending = deferred<DailyExperiment>();
      const mutation = operation === "choose" ? chooseDailyExperiment
        : operation === "undo" ? undoDailyExperiment : reflectDailyExperiment;
      if (operation === "choose") vi.mocked(chooseDailyExperiment).mockReturnValue(pending.promise);
      if (operation === "undo") vi.mocked(undoDailyExperiment).mockReturnValue(pending.promise.then(() => undefined));
      if (operation === "reflect") vi.mocked(reflectDailyExperiment).mockReturnValue(pending.promise);
      const callbacks = { onChosen: vi.fn(), onUndone: vi.fn(), onReflected: vi.fn(), onError: vi.fn() };
      const { result, client } = renderSharedHooks({ enabled: false, ...callbacks });
      act(() => { client.setQueryData(dailyExperimentQueryKey, chosenExperiment); });
      await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));

      let settled: Promise<string> | undefined;
      act(() => {
        const request = operation === "choose" ? result.current.first.chooseAsync(choice)
          : operation === "undo" ? result.current.first.undoAsync({ experiment_id: experimentId, expected_version: 1 })
            : result.current.first.reflectAsync({ experiment_id: experimentId, expected_version: 1, outcome: "helpful" });
        settled = request.then(() => "success", () => "error");
      });
      await waitFor(() => expect(mutation).toHaveBeenCalledTimes(1));
      if (operation === "undo") expect(client.getQueryData(dailyExperimentQueryKey)).toBeNull();
      if (operation === "reflect") expect(client.getQueryData(dailyExperimentQueryKey)).toMatchObject({ state: "reflected" });

      await act(async () => {
        if (change === "generation") invalidateSessionRequests();
        if (change === "epoch") sessionStorage.setItem(SESSION_EPOCH_KEY, "owner-b");
        if (change === "erasure") await clearPersonalDataOnDevice();
        client.clear();
      });
      const writes: unknown[] = [];
      const unsubscribe = client.getQueryCache().subscribe((event) => {
        if (event.query.queryKey[0] === dailyExperimentQueryKey[0]
          && event.type === "updated" && event.query.state.data !== undefined) {
          writes.push(event.query.state.data);
        }
      });
      const invalidate = vi.spyOn(client, "invalidateQueries");
      await act(async () => {
        if (outcome === "success") pending.resolve({ ...chosenExperiment, state: "reflected", outcome: "helpful" });
        else pending.reject(new Error("late failure from owner A"));
        expect(await settled).toBe(outcome);
      });

      // A mounted disabled observer may recreate an empty pending query when
      // mutation status changes. The privacy contract forbids data restoration,
      // not that harmless cache container.
      expect(client.getQueryData(dailyExperimentQueryKey)).toBeUndefined();
      expect(client.getQueryState(dailyExperimentQueryKey)?.dataUpdateCount ?? 0).toBe(0);
      expect(writes).toEqual([]);
      expect(invalidate).not.toHaveBeenCalled();
      for (const callback of Object.values(callbacks)) expect(callback).not.toHaveBeenCalled();
      unsubscribe();
      client.clear();
    });
  });

  describe.each(["undo", "reflect"] as const)("%s cancellation race", (operation) => {
    it.each(["generation", "epoch"])("does not write optimistically after %s changes during cancellation", async (change) => {
      sessionStorage.setItem(SESSION_EPOCH_KEY, "owner-a");
      const pending = deferred<DailyExperiment>();
      if (operation === "undo") vi.mocked(undoDailyExperiment).mockReturnValue(pending.promise.then(() => undefined));
      else vi.mocked(reflectDailyExperiment).mockReturnValue(pending.promise);
      const { result, client } = renderSharedHooks({ enabled: false });
      act(() => { client.setQueryData(dailyExperimentQueryKey, chosenExperiment); });
      await waitFor(() => expect(result.current.first.experiment).toEqual(chosenExperiment));
      const cancellation = deferred<void>();
      const cancel = vi.spyOn(client, "cancelQueries").mockReturnValue(cancellation.promise);
      let settled: Promise<unknown> | undefined;
      act(() => {
        const request = operation === "undo" ? result.current.first.undoAsync({ experiment_id: experimentId, expected_version: 1 })
          : result.current.first.reflectAsync({ experiment_id: experimentId, expected_version: 1, outcome: "helpful" });
        settled = request.catch(() => undefined);
      });
      await waitFor(() => expect(cancel).toHaveBeenCalledTimes(1));
      act(() => {
        if (change === "generation") invalidateSessionRequests();
        else sessionStorage.setItem(SESSION_EPOCH_KEY, "owner-b");
        client.clear();
      });
      const newOwnerExperiment = { ...chosenExperiment, action: "Owner B's experiment" };
      act(() => { client.setQueryData(dailyExperimentQueryKey, newOwnerExperiment); });
      const setQueryData = vi.spyOn(client, "setQueryData");
      await act(async () => {
        cancellation.resolve(undefined);
        await cancellation.promise;
      });
      expect(setQueryData).not.toHaveBeenCalled();
      expect(client.getQueryData(dailyExperimentQueryKey)).toEqual(newOwnerExperiment);
      await act(async () => {
        pending.reject(new Error("late failure from owner A"));
        await settled;
      });
      expect(setQueryData).not.toHaveBeenCalled();
      expect(client.getQueryData(dailyExperimentQueryKey)).toEqual(newOwnerExperiment);
      client.clear();
    });
  });
});

function renderSharedHooks(options: Parameters<typeof useDailyExperiment>[0] = {}) {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  const wrapper = ({ children }: PropsWithChildren) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...renderHook(
    () => ({ first: useDailyExperiment(options), second: useDailyExperiment({ enabled: options.enabled }) }),
    { wrapper },
  ) };
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
