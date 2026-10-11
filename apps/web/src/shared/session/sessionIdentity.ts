export const SESSION_EPOCH_KEY = "la-lanh-session-epoch";
export const OWNER_SESSION_EPOCH_KEY = "la-lanh-owner-session-epoch";
export const SESSION_ACCEPTED_EVENT = "la-lanh-session-accepted";
export const SESSION_CHANGE_NOTICE_KEY = "la-lanh-session-change-notice-v1";
export const SESSION_RESTART_REQUIRED_KEY = "la-lanh-session-restart-required-v1";

let generation = 0;
const requests = new Set<AbortController>();
let verifiedCookie: { epoch: string; marker: string | null } | null = null;

export function currentSessionEpoch(): string | null {
  return sessionStorage.getItem(SESSION_EPOCH_KEY);
}

export function sessionGeneration(): number {
  return generation;
}

export function trackSessionRequest(controller: AbortController): () => void {
  requests.add(controller);
  return () => requests.delete(controller);
}

export function invalidateSessionRequests(): void {
  generation += 1;
  verifiedCookie = null;
  for (const controller of requests) {
    controller.abort(new DOMException("Session changed", "AbortError"));
  }
  requests.clear();
}

export function rememberVerifiedSession(epoch: string): void {
  verifiedCookie = { epoch, marker: sessionCookieMarker() };
}

export function verifiedCookieHasChanged(): boolean {
  return verifiedCookie !== null && verifiedCookie.epoch === currentSessionEpoch()
    && verifiedCookie.marker !== sessionCookieMarker();
}

// This cookie is only a change detector. It never grants access; the server
// remains responsible for verifying its HttpOnly session credential.
export function sessionCookieMarker(): string | null {
  const value = document.cookie.split("; ").find((item) => item.startsWith("la_lanh_csrf="));
  return value ?? null;
}

export function announceSessionChange(): void {
  window.dispatchEvent(new Event(SESSION_ACCEPTED_EVENT));
  try {
    // Notify sibling tabs without transferring epochs, credentials or content.
    localStorage.setItem(SESSION_CHANGE_NOTICE_KEY, crypto.randomUUID());
  } catch {
    // Focus/pageshow verification still works with blocked local storage.
  }
}
