import { runtimeConfig } from "../config/runtime";

export type ContentFinding = {
  rule_id: string;
  severity: "critical" | "high" | "medium";
  path: string;
  message: string;
};

export type ContentValidation = {
  validator_version: string;
  payload_hash: string;
  passed: boolean;
  findings: ContentFinding[];
};

export type ContentRevision = {
  id: string;
  status: "draft" | "validated" | "published";
  parent_revision_id: string | null;
  payload_hash: string;
  validation: ContentValidation | null;
  created_at: string;
};

export type RewriteCandidateSummary = {
  id: string;
  surface: string;
  status: string;
  last_result: string | null;
  candidate_variant: string;
  provider: string;
  model: string;
  prompt_version: string;
  schema_version: string;
  gate_version: string;
  gate_receipt_id: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  attempt_count: number;
  created_at: string;
  updated_at: string;
};

export type RewriteSurfaceManifest = {
  surface: string;
  fields: string[];
  schema_version: string;
  gate_version: string;
  forbidden_claims: string[];
  privacy_manifest: string;
};

export type ContentWorkspace = {
  source: "published" | "bundled-baseline";
  channel: {
    active_revision_id: string | null;
    generation: number;
    updated_at: string;
  };
  active_revision: ContentRevision | null;
  payload: Record<string, Record<string, Record<string, string | string[]>>>;
  summary: Record<string, number>;
  revisions: ContentRevision[];
  events: Array<{
    id: string;
    action: string;
    revision_id: string;
    previous_revision_id: string | null;
    channel_generation: number;
    reason: string;
    created_at: string;
  }>;
  rewrite_candidates?: RewriteCandidateSummary[];
  rewrite_surfaces?: RewriteSurfaceManifest[];
};

export class StudioApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly validation: ContentValidation | null = null,
  ) {
    super(message);
  }
}

async function studioRequest<T>(
  token: string,
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${runtimeConfig.VITE_API_BASE_URL}/studio${path}`, {
    ...init,
    credentials: "omit",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => null) as {
      title?: string;
      validation?: ContentValidation;
    } | null;
    throw new StudioApiError(
      response.status,
      problem?.title ?? "Content Studio request failed",
      problem?.validation ?? null,
    );
  }
  return await response.json() as T;
}

export function getContentWorkspace(token: string): Promise<ContentWorkspace> {
  return studioRequest(token, "/workspace");
}

export function createContentDraft(
  token: string,
  payload: ContentWorkspace["payload"],
  parentRevisionId: string | null,
  reason: string,
): Promise<{ revision: ContentRevision; validation: ContentValidation }> {
  return studioRequest(token, "/drafts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify({
      payload,
      parent_revision_id: parentRevisionId,
      reason,
    }),
  });
}

export function publishContentRevision(
  token: string,
  revisionId: string,
  expectedGeneration: number,
  reason: string,
  rollback = false,
): Promise<{ revision: ContentRevision; channel: ContentWorkspace["channel"] }> {
  return studioRequest(token, `/revisions/${revisionId}/${rollback ? "rollback" : "publish"}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify({ expected_generation: expectedGeneration, reason }),
  });
}

export function rollbackContentRevision(
  token: string,
  revisionId: string,
  expectedGeneration: number,
  reason: string,
): Promise<{ revision: ContentRevision; channel: ContentWorkspace["channel"] }> {
  return publishContentRevision(token, revisionId, expectedGeneration, reason, true);
}
