import type { components, paths } from "@la-lanh/contracts";

import { runtimeConfig } from "../config/runtime";

export type HealthResponse =
  paths["/v1/health"]["get"]["responses"][200]["content"]["application/json"];
export type GuestSession = components["schemas"]["GuestSessionResponse"];
export type BirthReveal = components["schemas"]["BirthRevealResponse"];
export type ZodiacSign = components["schemas"]["ZodiacSign"];

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return request<HealthResponse>("/health", { signal });
}

export class ApiProblem extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

function readCookie(name: string): string | null {
  const prefix = `${encodeURIComponent(name)}=`;
  const value = document.cookie.split("; ").find((item) => item.startsWith(prefix));
  return value ? decodeURIComponent(value.slice(prefix.length)) : null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${runtimeConfig.VITE_API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: { Accept: "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const problem = (await response.json().catch(() => null)) as {
      code?: string;
      title?: string;
    } | null;
    throw new ApiProblem(
      response.status,
      problem?.code ?? "REQUEST_FAILED",
      problem?.title ?? `Request failed with status ${response.status}`,
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function getSession(signal?: AbortSignal): Promise<GuestSession> {
  return request<GuestSession>("/session", { signal });
}

export function createGuest(idempotencyKey: string): Promise<GuestSession> {
  return request<GuestSession>("/guest-sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      consent_version: "birth-profile-v1",
      purpose: "birth_profile_basic",
      idempotency_key: idempotencyKey,
    }),
  });
}

export function getBirthProfile(signal?: AbortSignal): Promise<BirthReveal> {
  return request<BirthReveal>("/birth-profile", { signal });
}

export function createBirthProfile(birthDate: string): Promise<BirthReveal> {
  const csrfToken = readCookie("la_lanh_csrf");
  return request<BirthReveal>("/birth-profile", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
    },
    body: JSON.stringify({ birth_date: birthDate }),
  });
}

export function deleteGuest(): Promise<void> {
  const csrfToken = readCookie("la_lanh_csrf");
  return request<void>("/guest-session", {
    method: "DELETE",
    headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
  });
}
