import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import {
  claimOwner,
  currentSessionEpoch,
  getSession,
  ownerClaimNeedsRefresh,
} from "../../shared/api/client";

export const RADAR_HISTORY_QUERY_KEY = ["radar-invites"] as const;

function isPrivateRadarQuery(queryKey: readonly unknown[]) {
  return queryKey[0] === "radar-invites"
    || queryKey[0] === "radar-result"
    || queryKey[0] === "radar-places";
}

export function useRadarOwnerBinding() {
  const queryClient = useQueryClient();
  const session = useQuery({
    queryKey: ["radar-owner-session"],
    queryFn: ({ signal }) => getSession(signal),
    refetchOnMount: "always",
    refetchOnWindowFocus: "always",
    retry: false,
    staleTime: 0,
  });
  const sessionEpoch = session.isSuccess ? currentSessionEpoch() : null;
  const ownerBindingStale = session.isSuccess && ownerClaimNeedsRefresh();
  const claim = useMutation({
    mutationFn: claimOwner,
    onMutate: () => {
      queryClient.removeQueries({ predicate: (query) => isPrivateRadarQuery(query.queryKey) });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: RADAR_HISTORY_QUERY_KEY }),
  });
  const { isError, isPending, isSuccess, mutate, reset } = claim;

  useEffect(() => {
    if (session.isSuccess && (ownerBindingStale || !isSuccess) && !isPending && !isError) {
      mutate();
    }
  }, [isError, isPending, isSuccess, mutate, ownerBindingStale, session.isSuccess]);

  return {
    epoch: sessionEpoch,
    error: session.error ?? claim.error,
    isError: session.isError || claim.isError,
    isPending: session.isPending || session.isFetching || claim.isPending || ownerBindingStale,
    isReady: session.isSuccess
      && !session.isFetching
      && Boolean(sessionEpoch)
      && !ownerBindingStale
      && claim.isSuccess,
    retry: () => {
      if (session.isError) void session.refetch();
      else reset();
    },
  };
}
