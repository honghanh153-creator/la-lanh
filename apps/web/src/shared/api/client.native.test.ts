import { beforeEach, describe, expect, it, vi } from "vitest";

import { createBirthProfile, createGuest } from "./client";

const nativeBridge = {
  isNativePlatform: () => true,
  getPlatform: () => "ios",
};

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

describe("native API session bridge", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    Object.defineProperty(window, "Capacitor", {
      configurable: true,
      value: nativeBridge,
    });
    vi.restoreAllMocks();
  });

  it("marks native requests and retains only the non-auth CSRF token on device", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      jsonResponse({
        state: "active",
        onboarding_status: "birth_pending",
        expires_at: "2026-10-01T00:00:00Z",
        csrf_token: "csrf-native-token",
        resumed: false,
        session_epoch: "a".repeat(64),
      }),
    );

    await createGuest("native-idempotency-key-123456");

    const init = fetchMock.mock.calls[0]?.[1];
    expect(new Headers(init?.headers).get("X-La-Lanh-Client")).toBe("capacitor-v1");
    expect(localStorage.getItem("la-lanh-native-csrf-v1")).toBe("csrf-native-token");
    expect(localStorage.getItem("la_lanh_guest")).toBeNull();
  });

  it("reuses the native CSRF token for a mutation when the API cookie is not DOM-visible", async () => {
    localStorage.setItem("la-lanh-native-csrf-v1", "csrf-native-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      jsonResponse({
        profile_id: "00000000-0000-0000-0000-000000000001",
        mode: "sun_only",
        sun_sign: "cancer",
        tradition: "western",
      }),
    );

    await createBirthProfile("2000-07-01");

    const init = fetchMock.mock.calls[0]?.[1];
    const headers = new Headers(init?.headers);
    expect(headers.get("X-La-Lanh-Client")).toBe("capacitor-v1");
    expect(headers.get("X-CSRF-Token")).toBe("csrf-native-token");
  });
});
