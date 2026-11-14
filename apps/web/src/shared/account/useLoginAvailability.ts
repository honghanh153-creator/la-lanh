import { useQuery } from "@tanstack/react-query";

import { getAccountStatus } from "../api/client";

/**
 * Whether the optional Google sign-in can actually be used on this build.
 *
 * Sign-in invites render only when the API confirms it is on; while the answer
 * is loading or failed they stay hidden, so no screen offers a locked button.
 * `storageNote` is the owner-approved sentence telling a guest where the
 * profile lives; it is null until approved (copy registry, privacy).
 */
export function useLoginAvailability(): { googleLoginEnabled: boolean; storageNote: string | null } {
  const query = useQuery({
    queryKey: ["account-login-availability"],
    queryFn: ({ signal }) => getAccountStatus(signal),
    retry: false,
    staleTime: 5 * 60_000,
  });
  return {
    googleLoginEnabled: query.data?.google_login_enabled === true,
    storageNote: query.data?.guest_storage_note?.trim() || null,
  };
}
