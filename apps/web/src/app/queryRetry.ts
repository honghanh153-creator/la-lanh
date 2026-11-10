import { isReadingContentRejected } from "../shared/api/client";

/**
 * Default query retry policy: one retry for transient failures.
 * A 422 READING_CONTENT_REJECTED is deterministic for the same chart (#143 E2), so a retry
 * only repeats the server work and delays the plain "content" message on the note page.
 */
export function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (isReadingContentRejected(error)) return false;
  return failureCount < 1;
}
