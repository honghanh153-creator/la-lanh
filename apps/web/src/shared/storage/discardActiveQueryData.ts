import type { Query, QueryClient } from "@tanstack/react-query";

type QueryPredicate = (query: Query) => boolean;

/**
 * Deletion paths must empty the queries a mounted screen still watches, then reload them.
 *
 * resetQueries is not enough (Codex, PR #410): it restores the query's initial state, and a
 * screen that seeded the query from the offline cache (initialData) brings the deleted note back;
 * a failed reload then leaves it cached. Writing an empty pending state instead keeps nothing old,
 * so a failed reload shows an empty screen rather than deleted text.
 */
export async function discardActiveQueryData(client: QueryClient, predicate: QueryPredicate): Promise<void> {
  for (const query of client.getQueryCache().findAll({ predicate, type: "active" })) {
    query.setState({
      data: undefined,
      dataUpdateCount: 0,
      dataUpdatedAt: 0,
      error: null,
      errorUpdateCount: 0,
      errorUpdatedAt: 0,
      fetchFailureCount: 0,
      fetchFailureReason: null,
      fetchMeta: null,
      isInvalidated: true,
      status: "pending",
    });
  }
  await client.refetchQueries({ predicate, type: "active" });
}
