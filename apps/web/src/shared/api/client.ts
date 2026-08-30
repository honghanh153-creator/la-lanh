import type { paths } from "@la-lanh/contracts";

import { runtimeConfig } from "../config/runtime";

export type HealthResponse = paths["/v1/health"]["get"]["responses"][200]["content"]["application/json"];

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${runtimeConfig.VITE_API_BASE_URL}/health`, {
    credentials: "include",
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Health request failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}
