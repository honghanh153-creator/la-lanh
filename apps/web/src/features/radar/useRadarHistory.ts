import { useInfiniteQuery } from "@tanstack/react-query";
import { useRef } from "react";
import { listRadarInvites, type RadarInvite } from "../../shared/api/client";
import { RADAR_HISTORY_QUERY_KEY } from "./useRadarOwnerBinding";

export function useRadarHistory(epoch: string | null, ready: boolean, mode: RadarInvite["mode"]) {
  const query = useInfiniteQuery({
    queryKey: [...RADAR_HISTORY_QUERY_KEY, epoch, mode],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ signal, pageParam }) => listRadarInvites(signal, pageParam, mode),
    getNextPageParam: (page) => page.length === 20 ? page.at(-1)?.id : undefined,
    enabled: ready,
    retry: false,
  });
  return { ...query, items: query.data?.pages.flat() ?? [] };
}

// Keep one retry key in memory only. Never persist the draft's birth input.
export function useRadarCreateKey(epoch: string | null) {
  const latest = useRef<{ draft: string; key: string } | null>(null);
  return {
    forDraft: (input: object) => {
      const draft = JSON.stringify([epoch, input]);
      if (latest.current?.draft !== draft) latest.current = { draft, key: crypto.randomUUID() };
      return latest.current.key;
    },
    reset: () => { latest.current = null; },
  };
}
