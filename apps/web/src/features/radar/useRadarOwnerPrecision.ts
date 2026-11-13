import { useQuery } from "@tanstack/react-query";

import { getBirthSupplement } from "../../shared/api/client";

export const RADAR_OWNER_PRECISION_QUERY_KEY = "radar-owner-precision";

export type RadarOwnerPrecision = "checking" | "needs_birth_time" | "ready";

/**
 * Radar needs the owner's own chart with birth time and place (server profile level 3,
 * the same rule that makes create answer 409 RADAR_CHART_REQUIRED). Ask before the user
 * types anything about the other person. Only a boolean is cached, keyed by session epoch.
 * Any failure falls back to "ready": the server 409 stays the safety net.
 */
export function useRadarOwnerPrecision(owner: { epoch: string | null; isReady: boolean }): RadarOwnerPrecision {
  const query = useQuery({
    queryKey: [RADAR_OWNER_PRECISION_QUERY_KEY, owner.epoch],
    queryFn: async ({ signal }) => (await getBirthSupplement(signal)).profile_level >= 3,
    enabled: owner.isReady,
    retry: false,
    staleTime: 0,
    gcTime: 0,
  });
  if (!owner.isReady) return "checking";
  if (query.isPending) return "checking";
  if (query.isError) return "ready";
  return query.data ? "ready" : "needs_birth_time";
}
