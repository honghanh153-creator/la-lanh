import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  activateReadingProjection,
  ApiProblem,
  type DailyNote,
} from "../api/client";
import {
  replaceCachedReadingProjection,
  writeCachedDailyNote,
} from "../storage/noteCache";

type ActivationTarget = {
  scopeKey: string;
  revisionId: string;
};

type UseReadingUpdateActivationOptions = {
  onSuccess: () => void;
  onError: (error: unknown) => void;
};

export function useReadingUpdateActivation({
  onSuccess,
  onError,
}: UseReadingUpdateActivationOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ scopeKey, revisionId }: ActivationTarget) => (
      activateReadingProjection(scopeKey, revisionId)
    ),
    onMutate: async () => {
      // Stop an older GET from restoring the pre-activation projection.
      await queryClient.cancelQueries({ queryKey: ["daily-note"], exact: true });
    },
    onSuccess: (projection, target) => {
      if (projection.scope_key !== target.scopeKey) {
        onError(new Error("Activation scope changed"));
        return;
      }
      queryClient.setQueryData<DailyNote>(["daily-note"], (current) => {
        if (!current || current.reading_projection?.scope_key !== projection.scope_key) {
          return current;
        }
        const next = { ...current, reading_projection: projection };
        if (!replaceCachedReadingProjection(projection)) writeCachedDailyNote(next);
        return next;
      });
      onSuccess();
    },
    onError: async (error) => {
      if (error instanceof ApiProblem && error.status === 409) {
        await queryClient.invalidateQueries({
          queryKey: ["daily-note"],
          exact: true,
          refetchType: "active",
        });
      }
      onError(error);
    },
  });
}
