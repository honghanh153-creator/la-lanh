import type { Query, QueryClient } from "@tanstack/react-query";

import { ApiProblem } from "../../shared/api/client";

// Every cached Radar reading that a withdrawal can revoke, whichever route withdrew it: the receipt,
// B's received list and results, and the owner's result. A token-only withdrawal does not know the
// result id, so the shared contract clears them all.
const RADAR_READING_KEYS = new Set(["radar-receipt", "radar-received", "radar-received-result", "radar-result"]);

function isRadarReading(query: Query) {
  return RADAR_READING_KEYS.has(String(query.queryKey[0]));
}

export async function evictRadarReadings(queryClient: QueryClient) {
  await queryClient.cancelQueries({ predicate: isRadarReading });
  queryClient.removeQueries({ predicate: isRadarReading });
  void queryClient.invalidateQueries({ queryKey: ["radar-invites"] });
}

// A definitive answer from the server: the reading is gone or not this session's. Retained data must
// not be shown after it. Anything else (a timeout, a lost response, a 5xx) is not a verdict.
export function isTerminalDenial(error: unknown) {
  return error instanceof ApiProblem && [401, 403, 404].includes(error.status);
}
