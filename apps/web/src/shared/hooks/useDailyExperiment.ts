import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  ApiProblem,
  chooseDailyExperiment,
  getCurrentDailyExperiment,
  reflectDailyExperiment,
  undoDailyExperiment,
  type ChooseDailyExperimentInput,
  type DailyExperiment,
  type ExperimentOutcome,
} from "../api/client";

export const dailyExperimentQueryKey = ["daily-experiment"] as const;

type DailyExperimentCallbacks = {
  onChosen?: () => void;
  onUndone?: () => void;
  onReflected?: () => void;
  onError?: (error: unknown) => void;
};

type UseDailyExperimentOptions = DailyExperimentCallbacks & {
  enabled?: boolean;
};

export type DailyExperimentChoice = ChooseDailyExperimentInput & {
  daily_note_id: string;
};

export type DailyExperimentStatus =
  | "idle"
  | "loading"
  | "choosing"
  | "chosen"
  | "undoing"
  | "reflecting"
  | "reflected"
  | "error";

export function dailyExperimentErrorMessage(error: unknown): string {
  if (error instanceof ApiProblem && error.status === 409) {
    return "Việc đang giữ đã thay đổi ở nơi khác. Lá Lành đã tải lại để bạn chọn lại một cách an toàn.";
  }
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    return "Bạn đang ngoại tuyến. Ý định chưa được thay đổi; thử lại khi có mạng nhé.";
  }
  return "Chưa đồng bộ được việc nhỏ này. Ý định trước đó vẫn được giữ nguyên.";
}

export function useDailyExperiment({
  enabled = true,
  onChosen,
  onUndone,
  onReflected,
  onError,
}: UseDailyExperimentOptions = {}) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: dailyExperimentQueryKey,
    queryFn: ({ signal }) => getCurrentDailyExperiment(signal),
    enabled,
    retry: false,
    staleTime: 0,
  });

  const chooseMutation = useMutation({
    mutationFn: (input: DailyExperimentChoice) => {
      if (!input) throw new Error("Missing experiment choice");
      const { daily_note_id: dailyNoteId, ...body } = input;
      return chooseDailyExperiment(dailyNoteId, body);
    },
    onSuccess: (experiment) => {
      queryClient.setQueryData(dailyExperimentQueryKey, experiment);
      onChosen?.();
    },
    onError: (error) => {
      void queryClient.invalidateQueries({ queryKey: dailyExperimentQueryKey });
      onError?.(error);
    },
  });

  const undoMutation = useMutation({
    mutationFn: undoDailyExperiment,
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: dailyExperimentQueryKey });
      const previous = queryClient.getQueryData<DailyExperiment | null>(dailyExperimentQueryKey);
      queryClient.setQueryData(dailyExperimentQueryKey, null);
      return { previous };
    },
    onSuccess: () => onUndone?.(),
    onError: (error, _input, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(dailyExperimentQueryKey, context.previous);
      }
      void queryClient.invalidateQueries({ queryKey: dailyExperimentQueryKey });
      onError?.(error);
    },
  });

  const reflectMutation = useMutation({
    mutationFn: reflectDailyExperiment,
    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: dailyExperimentQueryKey });
      const previous = queryClient.getQueryData<DailyExperiment | null>(dailyExperimentQueryKey);
      if (previous && previous.id === input.experiment_id) {
        queryClient.setQueryData<DailyExperiment>(dailyExperimentQueryKey, {
          ...previous,
          state: "reflected",
          outcome: input.outcome,
          version: previous.version + 1,
          reflected_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }
      return { previous };
    },
    onSuccess: (experiment) => {
      queryClient.setQueryData(dailyExperimentQueryKey, experiment);
      onReflected?.();
    },
    onError: (error, _input, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(dailyExperimentQueryKey, context.previous);
      }
      void queryClient.invalidateQueries({ queryKey: dailyExperimentQueryKey });
      onError?.(error);
    },
  });

  let status: DailyExperimentStatus = "idle";
  if (query.isPending) status = "loading";
  else if (chooseMutation.isPending) status = "choosing";
  else if (undoMutation.isPending) status = "undoing";
  else if (reflectMutation.isPending) status = "reflecting";
  else if (query.isError || chooseMutation.isError || undoMutation.isError || reflectMutation.isError) status = "error";
  else if (query.data?.state === "reflected") status = "reflected";
  else if (query.data) status = "chosen";

  return {
    ...query,
    experiment: query.data ?? null,
    status,
    errorMessage: query.error
      ? dailyExperimentErrorMessage(query.error)
      : chooseMutation.error
        ? dailyExperimentErrorMessage(chooseMutation.error)
        : undoMutation.error
          ? dailyExperimentErrorMessage(undoMutation.error)
          : reflectMutation.error
            ? dailyExperimentErrorMessage(reflectMutation.error)
            : null,
    choose: chooseMutation.mutate,
    chooseAsync: chooseMutation.mutateAsync,
    undo: undoMutation.mutate,
    undoAsync: undoMutation.mutateAsync,
    reflect: (input: { experiment_id: string; expected_version: number; outcome: ExperimentOutcome }) => reflectMutation.mutate(input),
    reflectAsync: reflectMutation.mutateAsync,
    isChoosing: chooseMutation.isPending,
    isUndoing: undoMutation.isPending,
    isReflecting: reflectMutation.isPending,
  };
}
