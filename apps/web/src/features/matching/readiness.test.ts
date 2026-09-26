import { describe, expect, it } from "vitest";

import type { MatchingReadiness } from "../../shared/api/client";
import { deriveMatchingDeck } from "./readiness";

function readiness(overrides: Partial<MatchingReadiness> = {}): MatchingReadiness {
  return {
    ready: false,
    profile: null,
    consent_version: null,
    verification_status: "not_started",
    verification_reason_code: null,
    birth_profile_level: 3,
    checks: [
      { key: "photo_verification", complete: false, blocking: true },
      { key: "matching_consent", complete: false, blocking: true },
      { key: "matching_profile", complete: false, blocking: true },
      { key: "birth_profile_level_3", complete: true, blocking: true },
      { key: "age_18_plus", complete: true, blocking: true },
    ],
    ...overrides,
  };
}

describe("deriveMatchingDeck", () => {
  it("uses canonical blocker order even when API checks are reversed", () => {
    const result = deriveMatchingDeck(readiness());
    expect(result.action).toBe("profile");
    expect(result.ctaLabel).toBe("Tạo hồ sơ ghép");
    expect(result.completed).toBe(2);
  });

  it("does not pass pending or failed verification", () => {
    const base = readiness({
      profile: profile(false),
      consent_version: "matching-v1",
      checks: [
        { key: "age_18_plus", complete: true, blocking: true },
        { key: "birth_profile_level_3", complete: true, blocking: true },
        { key: "matching_profile", complete: true, blocking: true },
        { key: "matching_consent", complete: true, blocking: true },
        { key: "photo_verification", complete: false, blocking: true },
      ],
    });
    expect(deriveMatchingDeck({ ...base, verification_status: "pending" }).title).toBe("Ảnh đang được kiểm tra");
    expect(deriveMatchingDeck({ ...base, verification_status: "fail" }).action).toBe("verification");
  });

  it("only exposes join or leave after server readiness", () => {
    const checks = [
      { key: "age_18_plus", complete: true, blocking: true },
      { key: "birth_profile_level_3", complete: true, blocking: true },
      { key: "matching_profile", complete: true, blocking: true },
      { key: "matching_consent", complete: true, blocking: true },
      { key: "photo_verification", complete: true, blocking: true },
    ];
    expect(deriveMatchingDeck(readiness({ ready: true, profile: profile(false), checks, verification_status: "pass" })).action).toBe("join");
    expect(deriveMatchingDeck(readiness({ ready: true, profile: profile(true), checks, verification_status: "pass" })).action).toBe("leave");
  });
});

function profile(active: boolean) {
  return {
    active,
    display_name: "An",
    gender_identity: "nonbinary" as const,
    gender_preference: "everyone" as const,
    intent: "open" as const,
    joined_at: active ? "2026-09-18T00:00:00Z" : null,
    max_age: 35,
    min_age: 22,
    region_code: "ho-chi-minh",
    updated_at: "2026-09-18T00:00:00Z",
    weekly_intent: "de_la_can" as const,
  };
}
